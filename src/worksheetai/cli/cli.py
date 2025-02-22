import questionary
import json
import random
from pathlib import Path
from typing import List, Type, Any
from worksheetai.models import QuestionBank, DifficultyLevel, WorksheetConfig, StudentLevel
from worksheetai.services.ai import WorksheetGenerator
from worksheetai.utils.helpers import generate_response_from_config, generate_response_from_complex_questions_config
from worksheetai.models.file_models import IPYNBModel, NotebookCells
from pydantic import BaseModel
import yaml
from datetime import datetime

def select_subject(generator: WorksheetGenerator) -> str:
    """Interactive subject selection using loaded config"""
    return questionary.select(
        "Select subject:",
        choices=list(generator.subjects.keys())
    ).ask()

def select_modules(generator: WorksheetGenerator, subject: str) -> List[str]:
    """Interactive module selection using checkboxes"""
    module_configs = generator.subjects[subject]
    return questionary.checkbox(
        "Select modules:",
        choices=[module.name for module in module_configs.modules],
        validate=lambda result: len(result) >= 1
    ).ask()

def select_difficulty() -> str:
    return questionary.select(
        "Select difficulty:",
        choices=["easy", "medium", "hard"]
    ).ask()

def select_topics(generator: WorksheetGenerator, subject: str, modules: List[str], difficulty: str) -> List[dict]:
    """Interactive topic selection. Let user select topics, then automatically include all subtopics of the selected difficulty."""
    module_configs = generator.subjects[subject]
    # Use set comprehension to get unique topic names
    available_topics = list({topic.name for module in module_configs.modules if module.name in modules for topic in module.topics})
    available_topics.sort()
    selected_topics = questionary.checkbox(
        "Select topics:",
        choices=available_topics,
        validate=lambda result: len(result) >= 1
    ).ask()

    # Precompute allowed difficulties based on selected difficulty
    mapping = {"easy": 1, "medium": 2, "hard": 3}
    allowed_diffs = [d for d in ["easy", "medium", "hard"] if mapping[d] <= mapping[difficulty.lower()]]

    topics_selection = []
    for module in module_configs.modules:
        if module.name in modules:
            for topic in module.topics:
                if topic.name in selected_topics:
                    matching = []
                    for subtopic in topic.subtopics:
                        sub_diff = (subtopic.get('difficulty') if isinstance(subtopic, dict) else subtopic.difficulty).lower()
                        if sub_diff in allowed_diffs:
                            subtopic_name = subtopic.get('name') if isinstance(subtopic, dict) else subtopic.name
                            matching.append({
                                "name": subtopic_name,
                                "difficulty": sub_diff,
                                "description": subtopic.get('description') if isinstance(subtopic, dict) else subtopic.description
                            })
                    if matching:
                        topics_selection.append({
                            "name": topic.name,
                            "subtopics": matching
                        })
    return topics_selection

def get_question_count() -> int:
    return int(questionary.text(
        "Number of questions:",
        validate=lambda val: val.isdigit() and int(val) > 0
    ).ask())

def select_file_extension() -> str:
    return questionary.select(
        "Select worksheet file extension:",
        choices=["ipynb", "md"]
    ).ask()

def select_flavour() -> str:
    return questionary.text("Enter worksheet flavour:").ask()

def select_student_level() -> str:
    return StudentLevel[questionary.select(
        "Select student level:",
        choices=[level.name for level in StudentLevel]
    ).ask()]

def generate_config(subject: str, topics: List[dict], difficulty: str, count: int, file_extension: str, flavour: str, student_level: str) -> WorksheetConfig:
    """Generate worksheet configuration with actual questions and grouped topics."""
    bank = QuestionBank()
    # Extract subtopic names from topics
    subtopic_names = [subtopic if isinstance(subtopic, str) else subtopic['name'] for topic in topics for subtopic in topic["subtopics"]]
    selected_questions = bank.generate_questions(
        subject,
        subtopic_names,
        difficulty,
        count
    )
    transformed_questions = bank.transform_questions(selected_questions)
    config = {
        "version": "1.0",
        "file_extension": file_extension,
        "subject": subject,
        "difficulty": difficulty,
        "total_questions": count,
        "topics": topics,
        "questions": transformed_questions,
        "flavour": flavour,
        "student_level": student_level
    }
    return WorksheetConfig(**config)

def get_ext_model(file_extension: str) -> Any:
    if file_extension == "ipynb":
        return NotebookCells
    else:
        return None

def main():
    print("WorksheetAI Configuration Generator\n")
    generator = WorksheetGenerator()
    subject = select_subject(generator)
    modules = select_modules(generator, subject)
    difficulty = select_difficulty()
    topics = select_topics(generator, subject, modules, difficulty)
    count = get_question_count()
    file_ext = select_file_extension()
    flavour = select_flavour()
    student_level = select_student_level()
    file_ext_model = get_ext_model(file_ext)
    config = generate_config(subject, topics, difficulty, count, file_ext, flavour, student_level)
    timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
    output_path = f"worksheet_config_{timestamp}.json"
    try:
        print(config)
        with open(output_path, 'w') as f:
            json.dump(config.dict(), f, indent=2, default=str)
        print(f"\nConfiguration saved to {output_path}")
    except Exception as e:
        print(f"Error saving config: {e}")
        exit(1)
    print("Generating worksheet using LlamaIndex...")
    agent_profile = """
    You are a worksheet material generator. You have been given a set of topics and subtopics to generate questions for.
    """
    base_prompt = f"""
    Expected file output:
    ipynb
    
    Task:
        -To generate python fill-in-the-blanks coding questions.
        -Questions should include 1 sentence of instructions as markdown, code boilerplate with blanks
    
    Rules:
        -Each question must have at least 4 to 5 blanks in meaningful places that helps encourage critical thinking.
        -Questions should be challenging enough to test the student's understanding of the topic.
        -You should use ____ to indicate blanks in the questions.
        -Do not give the answer but you can give hints in comments
    """
    base_prompt = agent_profile + base_prompt
    # question_generator = generate_response_from_config(config, file_ext_model, base_prompt)
    question_generator = generate_response_from_complex_questions_config(config, file_ext_model, base_prompt)
    if file_ext == "ipynb":
        ipynb = IPYNBModel()
    else:
        worksheet_content_list = [config.to_markdown()]
    for question_response in question_generator:
        if file_ext == "ipynb":
            ipynb.cells += question_response.cells
        else:
            worksheet_content_list.extend(question_response.markdown_content)
    worksheet_output_path = f"worksheet_output_{timestamp}.{file_ext}"
    try:
        print(ipynb if file_ext == "ipynb" else worksheet_content_list)
        with open(worksheet_output_path, 'w') as f:
            if file_ext == "ipynb":
                json.dump(ipynb.dict(), f, indent=2, default=str)
            else:
                f.write("\n".join(worksheet_content_list))
        print(f"Worksheet generated and saved to {worksheet_output_path}")
    except Exception as e:
        print(f"Error saving worksheet: {e}")
        exit(1)

if __name__ == '__main__':
    main()