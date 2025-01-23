import nbformat as nbf
from worksheetai.models import Worksheet
from typing import Optional
import json

class WorksheetConverter:
    @staticmethod
    def convert(worksheet: Worksheet) -> bytes:
        """Convert worksheet to specified format"""
        if worksheet.output_format == "ipynb":
            return WorksheetConverter._to_ipynb(worksheet)
        raise ValueError(f"Unsupported format: {worksheet.output_format}")

    @staticmethod
    def _to_ipynb(worksheet: Worksheet) -> bytes:
        """Convert worksheet to Jupyter notebook format"""
        nb = nbf.v4.new_notebook()
        nb.metadata.update(worksheet.metadata.get("ipynb", {}))
        
        # Add worksheet description as first cell
        if worksheet.description:
            nb.cells.append(nbf.v4.new_markdown_cell(
                f"# {worksheet.title}\n{worksheet.description}"
            ))
        
        # Process each question
        for question in worksheet.questions:
            # Create markdown cell for question description
            md_content = f"## {question.topic} ({question.difficulty})\n{question.description}"
            
            # Add type-specific content
            if question.question_type == "coding" and question.content.get("code"):
                md_content += f"\n\n**Example Code:**\n```python\n{question.content['code']}\n```"
            
            nb.cells.append(nbf.v4.new_markdown_cell(md_content))
            
            # Add code cell if present
            if question.content.get("code_solution"):
                nb.cells.append(nbf.v4.new_code_cell(question.content["code_solution"]))
                
        return nbf.writes(nb).encode("utf-8")
