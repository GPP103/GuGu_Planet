"""出题链。"""
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.llm.langchain_factory import create_chat_model
from app.llm.output_schemas import LLMQuiz
from app.prompts.quiz_prompt import QUIZ_SYSTEM_PROMPT, QUIZ_USER_TEMPLATE


def build_quiz_chain():
    llm = create_chat_model(settings.quiz_temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QUIZ_SYSTEM_PROMPT),
            ("human", QUIZ_USER_TEMPLATE),
        ]
    )
    return prompt | llm.with_structured_output(LLMQuiz, method="function_calling")
