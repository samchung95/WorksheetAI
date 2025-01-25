from .models import (
    DifficultyLevel,
    Topic,
    QuestionType,
    LanguageConfig,
    SubjectConfig,
    WorksheetConfig
)
from typing import Optional, Dict, List
import random
import os
import yaml

class WorksheetGenerator:
    def __init__(self):
        self.subjects = self._load_subjects()
        self.question_types = self._load_question_types()

    def _load_subjects(self) -> Dict[str, SubjectConfig]:
        """Load and parse subjects from coding.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), "config/subjects/coding.yaml")
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        return {subj["name"]: SubjectConfig(**subj) for subj in raw["subjects"]}

    def _load_question_types(self) -> Dict[str, QuestionType]:
        """Load and parse question types from type.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), "config/questions/type.yaml")
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        return {qt["name"]: QuestionType(**qt) for qt in raw["question_types"]}

    def generate_config(
        self,
        subject: str,
        language: str,
        selected_topics: List[str],
        selected_question_types: List[str],
        num_questions: int,
        flavour: Optional[str] = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> WorksheetConfig:
        """Generate a validated worksheet configuration"""
        # Validate inputs against configs
        self._validate_selections(subject, language, selected_topics, selected_question_types)
        
        # Get full topic objects
        topics = [
            t for t in self.subjects[subject].languages[language].topics
            if t.name in selected_topics
        ]
        
        # Get full question type objects
        qtypes = [
            self.question_types[qt] 
            for qt in selected_question_types
        ]
        
        return WorksheetConfig(
            subject=subject,
            language=language,
            topics=topics,
            question_types=qtypes,
            num_questions=num_questions,
            flavour=self._select_flavour(flavour),
            difficulty=difficulty
        )

    def _validate_selections(
        self,
        subject: str,
        language: str,
        topics: List[str],
        question_types: List[str]
    ):
        """Validate user selections against config"""
        if subject not in self.subjects:
            raise ValueError(f"Invalid subject: {subject}")
            
        lang_config = self.subjects[subject].languages.get(language)
        if not lang_config:
            raise ValueError(f"Language {language} not found in {subject}")
            
        valid_topics = {t.name for t in lang_config.topics}
        invalid_topics = set(topics) - valid_topics
        if invalid_topics:
            raise ValueError(f"Invalid topics: {', '.join(invalid_topics)}")
            
        valid_qt = set(lang_config.question_types)
        invalid_qt = set(question_types) - valid_qt
        if invalid_qt:
            raise ValueError(f"Invalid question types: {', '.join(invalid_qt)}")

    def _select_flavour(self, flavour: Optional[str]) -> str:
        """Select or generate a random flavour"""
        FLAVOUR_CHOICES = [
            "real-world",
            "academic", 
            "interview-prep",
            "project-based",
            "beginner-friendly"
        ]
        return flavour or random.choice(FLAVOUR_CHOICES)
