from flask import Flask, request, Response, jsonify
import json
from worksheetai.cli.cli import generate_config
from worksheetai.utils.helpers import generate_response_from_complex_questions_config

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_worksheet():
    data = request.get_json()
    required_fields = ["subject", "topics", "difficulty", "count", "file_extension"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required parameter: {field}"}), 400

    subject = data["subject"]
    topics = data["topics"]
    difficulty = data["difficulty"]
    count = int(data["count"])
    file_ext = data["file_extension"]

    config = generate_config(subject, topics, difficulty, count, file_ext)
    agent_profile = "You are a worksheet material generator. You have been given a set of topics and subtopics to generate questions for."
    base_prompt = (
        "Expected file output:\n" +
        file_ext + "\n\n" +
        "Task:\n" +
        "- To generate python fill-in-the-blanks coding questions.\n" +
        "- Questions should include 1 sentence of instructions as markdown, code boilerplate with blanks\n\n" +
        "Rules:\n" +
        "- Each question must have at least 4 to 5 blanks in meaningful places that helps encourage critical thinking.\n" +
        "- Questions should be challenging enough to test the student's understanding of the topic.\n" +
        "- You should use ____ to indicate blanks in the questions.\n" +
        "- Do not give the answer but you can give hints in comments\n"
    )
    combined_prompt = agent_profile + base_prompt

    question_generator = generate_response_from_complex_questions_config(config, None, combined_prompt)

    if file_ext == "ipynb":
        from worksheetai.models.file_models import IPYNBModel
        ipynb = IPYNBModel()
        for question_response in question_generator:
            ipynb.cells += question_response.cells
        file_content = json.dumps(ipynb.dict(), indent=2, default=str)
        output_filename = "worksheet_output.ipynb"
    else:
        worksheet_content_list = [config.to_markdown()]
        for question_response in question_generator:
            worksheet_content_list.extend(question_response.markdown_content)
        file_content = "\n".join(worksheet_content_list)
        output_filename = "worksheet_output.md"

    response = Response(
        file_content.encode("utf-8"),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=" + output_filename}
    )
    return response

if __name__ == "__main__":
    app.run(debug=True)