from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Dict, Optional
import random

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Subtopic(BaseModel):
    name: str
    difficulty: DifficultyLevel
    description: str

class Topic(BaseModel):
    name: str
    subtopics: List[Subtopic]

class QuestionType(BaseModel):
    name: str 
    description: str
    examples: Dict[DifficultyLevel, List[str]]

class Module(BaseModel):
    name: str
    topics: List[Topic]

class ModuleConfig(BaseModel):
    modules: List[Module]

class Question(BaseModel):
    topic: str
    difficulty: DifficultyLevel
    description: str

class WorksheetConfig(BaseModel):
    subject: str
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

class QuestionBank:
    def __init__(self):
        self.questions = []
        self._load_questions()
        
    def _load_questions(self):
        """Load questions from YAML config files"""
        import yaml
        try:
            with open('src/worksheetai/config/subjects/coding.yaml') as f:
                config = yaml.safe_load(f)
                # Flatten subject/topic/subtopic hierarchy into questions
                for subject in config['modules']:
                    for topic in subject['topics']:
                        for subtopic in topic['subtopics']:
                            self.questions.append({
                                'subject': subject['name'],
                                'topic': topic['name'],
                                'subtopic': subtopic['name'],
                                'difficulty': subtopic['difficulty'],
                                'description': subtopic['description']
                            })
        except Exception as e:
            print(f"Error loading questions: {e}")
            
    def get_questions(self, subject: str, topics: List[str], min_difficulty: str, max_difficulty: str) -> List[Dict]:
        """Filter questions by subject, topic and difficulty range"""
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
        min_level = difficulty_order[min_difficulty.lower()]
        max_level = difficulty_order[max_difficulty.lower()]
        
        return [q for q in self.questions 
               if q['subject'] == subject
               and q['topic'] in topics
               and difficulty_order[q['difficulty']] >= min_level
               and difficulty_order[q['difficulty']] <= max_level]
               
    def select_questions(self, questions: List[Dict], count: int) -> List[Dict]:
        """Randomly select questions with balanced topic distribution"""
        selected = []
        topics = list(set(q['topic'] for q in questions))
        if not topics:
            return []
            
        questions_per_topic = max(1, count // len(topics))
        
        for topic in topics:
            topic_questions = [q for q in questions if q['topic'] == topic]
            selected.extend(random.sample(topic_questions, min(questions_per_topic, len(topic_questions))))
        
        remaining = count - len(selected)
        if remaining > 0:
            selected.extend(random.sample(
                [q for q in questions if q not in selected], 
                min(remaining, len(questions)-len(selected))
            ))
            
        return selected
