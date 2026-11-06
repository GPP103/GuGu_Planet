"""报告链。"""
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.llm.langchain_factory import create_chat_model
from app.llm.output_schemas import LLMReport
from app.prompts.report_prompt import REPORT_SYSTEM_PROMPT, REPORT_USER_TEMPLATE


def build_report_chain():
    llm = create_chat_model(settings.report_temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REPORT_SYSTEM_PROMPT),
            ("human", REPORT_USER_TEMPLATE),
        ]
    )
    return prompt | llm.with_structured_output(LLMReport, method="function_calling")
