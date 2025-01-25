from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Dict, Optional

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Topic(BaseModel):
    name: str
    description: str
    difficulty: DifficultyLevel
    subtopics: Optional[List['Topic']] = None

class QuestionType(BaseModel):
    name: str 
    description: str
    examples: Dict[DifficultyLevel, List[str]]

class LanguageConfig(BaseModel):
    name: str
    topics: List[Topic]
    question_types: List[str]

class SubjectConfig(BaseModel):
    name: str
    languages: Dict[str, LanguageConfig]

class Question(BaseModel):
    topic: str
    difficulty: DifficultyLevel
    description: str
    question_type: str
    example: Optional[str] = None

class WorksheetConfig(BaseModel):
    subject: str
    language: str
    topics: List[Topic]
    question_types: List[QuestionType]
    questions: List[Question]
    flavour: str
    minimum_difficulty: DifficultyLevel
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('questions')
    def validate_question_difficulties(cls, v, values):
        min_difficulty = values.get('minimum_difficulty', DifficultyLevel.MEDIUM)
        for q in v:
            if q.difficulty.value < min_difficulty.value:
                raise ValueError(
                    f"Question difficulty {q.difficulty.value} cannot be lower than "
                    f"minimum {min_difficulty.value}"
                )
        return v

    def to_markdown(self) -> str:
        """Convert worksheet configuration to markdown format"""
        md = [
            f"# {self.subject} Worksheet ({self.language})",
            f"**Flavour**: {self.flavour}",
            f"**Minimum Difficulty**: {self.minimum_difficulty.value.capitalize()}",
            "\n## Questions:"
        ]
        
        for i, question in enumerate(self.questions, 1):
            md.extend([
                f"{i}. **{question.topic}** ({question.difficulty.value.capitalize()})",
                f"   - Type: {question.question_type}",
                f"   - {question.description}"
            ])
            if question.example:
                md.append(f"   ```{self.language}\n   {question.example}\n   ```")
        
        return '\n'.join(md)
