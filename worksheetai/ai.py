from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
from worksheetai.models import Worksheet, Question
from typing import List, Dict, Any
import json

class WorksheetGenerator:
    def __init__(self, llm_model: str = "gpt-4"):
        """Initialize AI agent with flexible question generation capabilities"""
        self.llm = Settings.llm
        self.system_prompt = """You are an expert educational content creator. Generate worksheets with:
        1. Diverse question types (coding, multiple_choice, essay)
        2. Clear difficulty progression
        3. Topic-specific examples
        4. Structured JSON output matching the Worksheet model"""

    async def generate_worksheet(
        self,
        topics: List[str],
        num_questions: int = 5,
        difficulty_distribution: Dict[str, float] = None
    ) -> Worksheet:
        """Generate a worksheet with configurable parameters"""
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.system_prompt),
            ChatMessage(role=MessageRole.USER, content=json.dumps({
                "topics": topics,
                "num_questions": num_questions,
                "difficulty_distribution": difficulty_distribution or {"easy": 0.2, "medium": 0.5, "hard": 0.3}
            }))
        ]
        
        response = await self.llm.achat(messages)
        return self._parse_response(response.content)

    def _parse_response(self, raw_response: str) -> Worksheet:
        """Validate and parse the LLM response into Worksheet model"""
        try:
            # Attempt to extract JSON from markdown code block
            json_str = raw_response.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_str)
            return Worksheet.model_validate(data)
        except (IndexError, json.JSONDecodeError, KeyError):
            # Fallback to direct JSON parsing
            try:
                return Worksheet.model_validate_json(raw_response)
            except Exception as e:
                return self._create_error_worksheet(f"Parsing failed: {str(e)}")

    def _create_error_worksheet(self, error_msg: str) -> Worksheet:
        """Generate error worksheet for failed generations"""
        return Worksheet(
            title="Generation Error",
            description="Failed to generate worksheet",
            questions=[
                Question(
                    topic="System Error",
                    difficulty="hard",
                    description=error_msg,
                    question_type="essay"
                )
            ]
        )
