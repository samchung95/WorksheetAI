from flask import Flask, request, jsonify, send_file
from worksheetai.ai import WorksheetGenerator
from worksheetai.converters import WorksheetConverter
from worksheetai.models import Worksheet
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize components
generator = WorksheetGenerator()

@app.route('/api/generate', methods=['POST'])
async def generate_worksheet():
    """Generate worksheet endpoint"""
    try:
        data = request.json
        worksheet = await generator.generate_worksheet(
            topics=data.get('topics', []),
            num_questions=data.get('num_questions', 5),
            difficulty_distribution=data.get('difficulty_distribution')
        )
        return jsonify(worksheet.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert_worksheet():
    """Convert worksheet to desired format"""
    try:
        data = request.json
        worksheet = Worksheet.model_validate(data)
        converted = WorksheetConverter.convert(worksheet)
        return send_file(
            converted,
            mimetype='application/octet-stream',
            download_name=f"{worksheet.title}.{worksheet.output_format}"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
