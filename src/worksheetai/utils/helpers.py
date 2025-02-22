from typing import List, Dict, Generator, Type, TypeVar
from pydantic import BaseModel, Field
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

T = TypeVar("T", bound=BaseModel)
from worksheetai.models import WorksheetConfig, Question, ComplexQuestion, Topic
from worksheetai.services.ai import generate_question_prompt, get_llama_index_openai_client

# Settings.llm = OpenAI()

class QuestionResponse(BaseModel):
    markdown_content: List[str] = Field(description="List of markdown strings for the question")

def generate_response_from_config(
        worksheet_config: WorksheetConfig,
        response_model: Type[T],
        base_prompt: str = None) -> Generator[T, None, None]:
    """
    Generates responses iteratively based on the worksheet config.
    Yields an instance of the provided pydantic model type.
    """
    openai_client = get_llama_index_openai_client()
    sllm = openai_client.as_structured_llm(output_cls=response_model)

    print("Base Prompt:\n", base_prompt)

    # Initialize conversation history as empty list.
    conversation_history: List[ChatMessage] = []

    for i, question_config in enumerate(worksheet_config.questions):
        question = Question(**question_config.model_dump())
        question_prompt = generate_question_prompt(
            question_config=question.model_dump(),
            base_prompt=base_prompt
        )
        print("\nQuestion Prompt:\n", question_prompt)
        
        # Create a ChatMessage for the user question and add to history.
        user_msg = ChatMessage.from_str(question_prompt)
        conversation_history.append(user_msg)
        
        # Pass the full conversation history (user and previous assistant messages) to the chat call.
        response = sllm.chat(conversation_history)
        
        try:
            model_response = response.raw
            # Create and add the assistant's response to the conversation history.
            assistant_msg = ChatMessage(role="assistant", content=str(model_response))
            conversation_history.append(assistant_msg)
            yield model_response
        except Exception as e:
            print(f"Error validating response: {e}")
            print("Raw response content:\n", response.raw)
            yield response_model.construct()

def generate_complex_questions(worksheet_config: WorksheetConfig) -> List[ComplexQuestion]:
    """Generate complex questions for the worksheet."""
    complex_questions = []
    openai_client = get_llama_index_openai_client()
    sllm = openai_client.as_structured_llm(output_cls=ComplexQuestion)

    topics = worksheet_config.topics
    student_level = worksheet_config.student_level
    difficulty = worksheet_config.difficulty
    num_of_questions = len(worksheet_config.questions)
    flavour = worksheet_config.flavour

    subtopics = [subtopic.dict() for topic in topics for subtopic in topic.subtopics]

    base_prompt = f"""
    From the following subtopics, pick 2-3 subtopics to generate a complex question.
    A complex question is a question with multiple subtopics and has a special creative flair to it.

    Subtopics:
    {subtopics}

    """

    rules = """
    Rules:
    - Do not repeat question descriptions, be creative
    - Be creative but keep it relevant to the subtopics
    - Subtopics should not be repeated in the same question
    """

    # Initialize conversation history for complex questions.
    conversation_history: List[ChatMessage] = []

    for _ in range(num_of_questions):
        prompt = f"""
        {base_prompt if _ == 0 else ''}
        {rules}

        Student Level: {student_level}

        Difficulty: {difficulty}

        Flavour: {flavour}
        """

        user_msg = ChatMessage.from_str(prompt)
        conversation_history.append(user_msg)
        response = sllm.chat(conversation_history)

        try:
            model_response = response.raw
            complex_questions.append(model_response)
            conversation_history.append(ChatMessage(role="assistant", content=str(model_response)))
        except Exception as e:
            print(f"Error validating response: {e}")
            print("Raw response content:\n", response.raw)
 
    return complex_questions

def generate_response_from_complex_questions_config(
        worksheet_config: WorksheetConfig,
        response_model: Type[T],
        base_prompt: str = None) -> Generator[T, None, None]:
    """
    Generates responses iteratively based on the worksheet config.
    Yields an instance of the provided pydantic model type.
    """
    openai_client = get_llama_index_openai_client()
    sllm = openai_client.as_structured_llm(output_cls=response_model)

    complex_questions = generate_complex_questions(
        worksheet_config
    )

    print("Base Prompt:\n", base_prompt)

    # Initialize conversation history for complex questions.
    conversation_history: List[ChatMessage] = []

    for i, complex_question_config in enumerate(complex_questions):
        question = ComplexQuestion(**complex_question_config.model_dump())
        if i == 0:
            question_prompt = generate_question_prompt(
                question_config=question.model_dump(),
                base_prompt=base_prompt
            )
        else:
            question_prompt = generate_question_prompt(
                question_config=question.model_dump(),
                base_prompt=""
            )
        print("\nQuestion Prompt:\n", question_prompt)
        
        # Append the user's complex question to the history.
        user_msg = ChatMessage.from_str(question_prompt)
        conversation_history.append(user_msg)
        
        # Use the full conversation history in the chat call.
        response = sllm.chat(conversation_history)
        
        try:
            model_response = response.raw
            # Append the assistant's reply to the conversation history.
            assistant_msg = ChatMessage(role="assistant", content=str(model_response))
            conversation_history.append(assistant_msg)
            yield model_response
        except Exception as e:
            print(f"Error validating response: {e}")
            print("Raw response content:\n", response.raw)
            yield response_model.construct()
