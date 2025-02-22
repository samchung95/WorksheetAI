from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Dict, Optional
import random

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very hard"

class Subtopic(BaseModel):
    name: str = Field(..., description="Name of the subtopic")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level of the subtopic")
    description: str = Field(..., description="Description of the subtopic")

class Topic(BaseModel):
    name: str = Field(..., description="Name of the topic")
    subtopics: List[Subtopic] = Field(..., description="List of subtopics under the topic")

class QuestionType(BaseModel):
    name: str = Field(..., description="Name of the question type")
    description: str = Field(..., description="Description of the question type")
    example: str = Field(..., description="Example question content")

class Module(BaseModel):
    name: str = Field(..., description="Name of the module")
    topics: List[Topic] = Field(..., description="List of topics included in the module")

class ModuleConfig(BaseModel):
    modules: List[Module] = Field(..., description="List of modules in the configuration")

class Question(BaseModel):
    topic: str = Field(..., description="Topic associated with the question")
    subtopic: str = Field(..., description="Subtopic associated with the question")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level of the question")
    description: str = Field(..., description="Detailed description of the question")

class ComplexQuestion(BaseModel):
    subtopics: List[Subtopic] = Field(..., description="List of subtopics for the complex question")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level of the complex question despite subtopics having different difficulties, the overall difficulty of the complex question") 
    description: str = Field(..., description="Detailed description of the planned complex question")

class StudentLevel(Enum):
    LOWER_PRIMARY = "Primary 1-3"
    UPPER_PRIMARY = "Primary 4-6"
    LOWER_SECONDARY = "Secondary 1-3"
    UPPER_SECONDARY = "Secondary 4-5"
    TERTIARY = "Tertiary"
    JC = "Junior College"
    UNIVERSITY = "University"


class WorksheetConfig(BaseModel):
    student_level: StudentLevel = Field(..., description="Student level for the worksheet")
    subject: str = Field(..., description="Subject of the worksheet")
    topics: List[Topic] = Field(..., description="List of topics included in the worksheet")
    questions: List[Question] = Field(..., description="List of questions for the worksheet")
    flavour: str = Field(..., description="Flavour or style description of the worksheet")
    difficulty: DifficultyLevel = Field(..., description="Overall difficulty level of the worksheet")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation datetime of the worksheet configuration")

    @validator('questions')
    def validate_question_difficulties(cls, v, values):
        difficulty = values.get('difficulty', None)
        if difficulty:
            for q in v:
                if q.difficulty.value != difficulty.value:
                    raise ValueError(
                        f"Question difficulty {q.difficulty.value} does not match selected difficulty {difficulty.value}"
                    )
        return v

    def to_filtered_json(self) -> str:
        filtered_config = self.filter_topics_by_difficulty()
        return filtered_config.json(indent=2)
    
    def filter_topics_by_difficulty(self) -> "WorksheetConfig":
        allowed = {
            "hard": ["hard", "medium", "easy"],
            "medium": ["medium", "easy"],
            "easy": ["easy"]
        }
        diff = self.difficulty.value.lower()
        allowed_diffs = allowed.get(diff, ["easy"])
        filtered_topics = []
        for topic in self.topics:
            filtered_subtopics = [sub for sub in topic.subtopics if sub.difficulty.value.lower() in allowed_diffs]
            if filtered_subtopics:
                new_topic = topic.copy(update={"subtopics": filtered_subtopics})
                filtered_topics.append(new_topic)
        return self.copy(update={"topics": filtered_topics})

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
            
    def get_questions(self, subject: str, subtopics: List[str], difficulties: List[str]) -> List[Dict]:
        """Filter questions by subject, subtopic and allowed difficulties"""
        return [q for q in self.questions
                if q['subject'] == subject
                and q['subtopic'] in subtopics
                and q['difficulty'].lower() in difficulties]
               
    def select_questions(self, questions: List[Dict], count: int) -> List[Dict]:
        """Randomly select questions with balanced topic distribution"""
        selected = []
        topics = list(set(q['topic'] for q in questions))
        if not topics:
            return []
        questions_per_topic = max(1, count // len(topics))
        for topic in topics:
            topic_questions = [q for q in questions if q['topic'] == topic]
            if len(topic_questions) >= questions_per_topic:
                selected.extend(random.sample(topic_questions, questions_per_topic))
            else:
                selected.extend(topic_questions)
        remaining = count - len(selected)
        if remaining > 0:
            available = [q for q in questions if q not in selected]
            if len(available) >= remaining:
                selected.extend(random.sample(available, remaining))
            else:
                selected.extend(available)
        return selected
    
    def subtopic_details(self) -> Dict[str, Dict[str, str]]:
        """Return a mapping from subtopic name to its parent topic and description."""
        details = {}
        for q in self.questions:
            details[q["subtopic"]] = {"topic": q["topic"], "description": q["description"]}
        return details
    
    def transform_questions(self, selected_questions: List[Dict]) -> List[Dict]:
        """Transform selected questions using subtopic details to include parent topic and proper description."""
        details = self.subtopic_details()
        transformed = []
        for q in selected_questions:
            mapping = details.get(q["subtopic"], {})
            parent_topic = mapping.get("topic", q["topic"])
            description = mapping.get("description", q["description"])
            transformed.append({
                "topic": parent_topic,
                "subtopic": q["subtopic"],
                "difficulty": q["difficulty"],
                "description": description,
            })
        return transformed
    
    def generate_questions(self, subject: str, subtopics: List[str], main_difficulty: str, count: int) -> List[Dict]:
        """Generate questions based on selected difficulty and proportions.
           For 'easy' selected, all questions are easy.
           For 'medium' selected, 75% medium and 25% easy.
           For 'hard' selected, 75% hard and 25% mixture of medium and easy.
           If no matching questions are found in the question bank, generate dummy questions.
        """
        mapping = {"easy": 1, "medium": 2, "hard": 3}
        main_diff = main_difficulty.lower()
        if main_diff == "easy":
            distribution = {"easy": count}
        elif main_diff == "medium":
            distribution = {
                "medium": int(count * 0.75),
                "easy": count - int(count * 0.75)
            }
        else:
            hard_count = int(count * 0.75)
            remaining = count - hard_count
            distribution = {
                "hard": hard_count,
                "medium": remaining // 2,
                "easy": remaining - (remaining // 2)
            }
        if not subtopics:
            subtopics = ["DefaultSubtopic"]
        selected = []
        for diff, diff_count in distribution.items():
            if diff_count > 0:
                allowed_difficulties = []
                if diff == "easy":
                    allowed_difficulties = ["easy"]
                elif diff == "medium":
                    allowed_difficulties = ["medium", "easy"]
                else:
                    allowed_difficulties = ["hard", "medium", "easy"]
                diff_questions = self.get_questions(subject, subtopics, allowed_difficulties)
                if not diff_questions:
                    for i in range(diff_count):
                        s = subtopics[i % len(subtopics)]
                        diff_questions.append({
                            'topic': s,
                            'subtopic': s,
                            'difficulty': diff,
                            'description': f"Description for {s} (dummy {diff})"
                        })
                target_diff_questions = [q for q in diff_questions if q['difficulty'].lower() == diff]
                other_diff_questions = [q for q in diff_questions if q['difficulty'].lower() != diff]
                needed = diff_count
                if target_diff_questions:
                    to_select = min(len(target_diff_questions), needed)
                    selected.extend(random.sample(target_diff_questions, to_select))
                    needed -= to_select
                if needed > 0 and other_diff_questions:
                    to_select = min(len(other_diff_questions), needed)
                    selected.extend(random.sample(other_diff_questions, to_select))
        return selected