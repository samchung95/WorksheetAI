from pathlib import Path
from typing import Optional, Dict, List, Type
import random
import os
import yaml
from pydantic import BaseModel
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv
from worksheetai.models.models import (
    DifficultyLevel, QuestionType, ModuleConfig, WorksheetConfig, Question
)

load_dotenv()

def get_llama_index_openai_client():
    """Initialize and return LlamaIndex OpenAI client."""
    return OpenAI(model="o3-mini-2025-01-31")  # Or specify your preferred model

def generate_question_prompt(
    question_config: Optional[Dict] = None, 
    base_prompt: Optional[str] = None
) -> str:
    """
    Generates a detailed prompt for generating a question,
    including base configuration and question configuration.
    """
    prompt = base_prompt or "Generate a question based on the following configuration:\n"
    if question_config:
        prompt += "\nQuestion Configuration:\n"
        for key, value in question_config.items():
            prompt += f"- {key}: {value}\n"
    return prompt

class WorksheetGenerator:
    def __init__(self, subject_filename="coding.yaml", question_type_filename="python.yaml"):
        self.subject_filename = subject_filename
        self.question_type_filename = question_type_filename
        self.subjects = self._load_subjects()
        self.question_types = self._load_question_types()
    
    def _load_subjects(self) -> Dict[str, ModuleConfig]:
        """Load and parse subjects from coding.yaml"""
        config_path = os.path.join(os.path.join(os.path.dirname(__file__), f"../config/subjects/{self.subject_filename}"))
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        return {self.subject_filename.split(".")[0]: ModuleConfig(**raw)}
    
    def _load_question_types(self) -> Dict[str, QuestionType]:
        """Load and parse question types from type.yaml"""
        config_path = os.path.join(os.path.join(os.path.dirname(__file__), f"../config/questions/{self.question_type_filename}"))
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        return {qt["name"]: QuestionType(**qt) for qt in raw["question_types"]}
    
    def generate_worksheet(self, config: Dict, file_extension: str) -> str:
        """
        Generate worksheet by iteratively prompting an AI agent (simulated) to generate each question.
        The base context prompt includes all data except the questions.
        """
        base_prompt = "Base Context Prompt:\n"
        selections = config.get("selection", {})
        difficulty = selections.get("difficulty", "medium")
        topics = selections.get("topics", [])
        base_prompt += f"Difficulty: {difficulty}\nTopics:\n"
        for topic in topics:
            base_prompt += f"- {topic.get('name', 'Unknown')}\n"
        base_prompt += "\nPlease generate a question based on the above settings."
    
        generated_questions = []
        questions = selections.get("questions", [])
        history = base_prompt
        for idx, q in enumerate(questions, 1):
            prompt = history + f"\nGenerate question {idx} with description: {q.get('description', '')}\nReturn in the structure: {{'question': str}}"
            output = {"question": f"Simulated question {idx}: {q.get('description', '')}"}
            history += f"\nOutput: {output['question']}"
            generated_questions.append(output["question"])
    
        if file_extension == "ipynb":
            notebook = {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": [
                            base_prompt,
                            "\n\nGenerated Questions:\n" + "\n".join(generated_questions)
                        ]
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5
            }
            import json
            return json.dumps(notebook, indent=2)
        else:
            worksheet_md = base_prompt + "\n\nGenerated Questions:\n"
            for i, question in enumerate(generated_questions, 1):
                worksheet_md += f"{i}. {question}\n"
            return worksheet_md
    
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
        self._validate_selections(subject, language, selected_topics, selected_question_types)
        # Filter topics based on selected topics and difficulty for subtopics
        allowed = {
            "hard": {"easy", "medium", "hard"},
            "medium": {"easy", "medium"},
            "easy": {"easy"}
        }
        # Convert difficulty to lower-case string; if it's an enum, use its value.
        diff = difficulty if isinstance(difficulty, str) else difficulty.value.lower()
        filtered_topics = []
        for t in self.subjects[subject].languages[language].topics:
            if t.name in selected_topics:
                topic_copy = t.copy(deep=True)
                topic_copy.subtopics = [
                    st for st in topic_copy.subtopics
                    if st.difficulty in allowed.get(diff, {"easy", "medium", "hard"})
                ]
                if topic_copy.subtopics:
                    filtered_topics.append(topic_copy)
        topics = filtered_topics
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
        FLAVOUR_CHOICES = [
            "real-world",
            "academic", 
            "interview-prep",
            "project-based",
            "beginner-friendly"
        ]
        return flavour or random.choice(FLAVOUR_CHOICES)