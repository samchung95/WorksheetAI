from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any

class Question(BaseModel):
    """Base question model supporting multiple types"""
    question_type: Literal["coding", "multiple_choice", "essay"] = Field(
        "coding", 
        description="Type of question"
    )
    topic: str = Field(..., description="Subject topic or category")
    difficulty: str = Field("medium", description="easy, medium, hard")
    description: str = Field(..., description="Question prompt/description")
    content: Dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific content (code examples, choices, etc)"
    )

class Worksheet(BaseModel):
    """Universal worksheet structure supporting multiple formats"""
    title: str = Field("Practice Worksheet", description="Worksheet title")
    description: str = Field("", description="Worksheet overview")
    questions: List[Question] = Field(..., min_items=1)
    output_format: str = Field(
        "ipynb", 
        description="Output format: ipynb, pdf, docx (future support)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Format-specific metadata"
    )
