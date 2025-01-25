from pydantic import BaseModel
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

class WorksheetConfig(BaseModel):
    subject: str
    language: str
    topics: List[Topic]
    question_types: List[QuestionType]
    num_questions: int
    flavour: str
    difficulty: DifficultyLevel
