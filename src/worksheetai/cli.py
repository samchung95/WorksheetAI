import questionary
import json
import random
from pathlib import Path
from typing import List, Dict
from worksheetai.models import QuestionBank, DifficultyLevel
from worksheetai.ai import WorksheetGenerator
import yaml

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

def select_topics(generator: WorksheetGenerator, subject: str, modules: List[str]) -> List[str]:
    """Interactive topic selection from selected modules"""
    module_configs = generator.subjects[subject]
    all_topics = [topic for module in module_configs.modules 
                 if module.name in modules 
                 for topic in module.topics]
    
    return questionary.checkbox(
        "Select topics:",
        choices=[topic.name for topic in all_topics],
        validate=lambda result: len(result) >= 1
    ).ask()

def select_question_types(generator: WorksheetGenerator) -> List[str]:
    """Interactive question type selection using checkboxes"""
    return questionary.checkbox(
        "Select question types:",
        choices=list(generator.question_types.keys())
    ).ask()

def select_min_difficulty() -> str:
    return questionary.select(
        "Select minimum difficulty:",
        choices=["easy", "medium", "hard"]
    ).ask()

def select_max_difficulty(min_difficulty: str) -> str:
    choices = []
    if min_difficulty == "easy":
        choices = ["easy", "medium", "hard"]
    elif min_difficulty == "medium":
        choices = ["medium", "hard"]
    else:
        choices = ["hard"]
        
    return questionary.select(
        "Select maximum difficulty:",
        choices=choices,
        default=choices[-1]
    ).ask()

def get_question_count() -> int:
    return int(questionary.text(
        "Number of questions:",
        validate=lambda val: val.isdigit() and int(val) > 0
    ).ask())

def generate_config(subject: str, topics: List[str], min_difficulty: str, max_difficulty: str, count: int, question_types: List[str]) -> Dict:
    """Generate worksheet configuration with actual questions"""
    bank = QuestionBank()
    filtered_questions = bank.get_questions(subject, topics, min_difficulty, max_difficulty)
    selected_questions = bank.select_questions(filtered_questions, count)
    
    return {
        "version": "1.0",
        "selection": {
            "topics": topics,
            "min_difficulty": min_difficulty,
            "max_difficulty": max_difficulty,
            "total_questions": count,
            "questions": selected_questions,
            "question_types": question_types
        }
    }

def main():
    print("WorksheetAI Configuration Generator\n")
    
    generator = WorksheetGenerator()
    
    subject = select_subject(generator)
    modules = select_modules(generator, subject)
    topics = select_topics(generator, subject, modules)
    min_difficulty = select_min_difficulty()
    max_difficulty = select_max_difficulty(min_difficulty)
    count = get_question_count()
    
    question_types = select_question_types(generator)
    config = generate_config(subject, topics, min_difficulty, max_difficulty, count, question_types)
    
    # Save output
    output_path = questionary.path("Save configuration to:").ask()
    try:
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to {output_path}")
    except Exception as e:
        print(f"Error saving config: {e}")
        exit(1)

if __name__ == '__main__':
    main()
