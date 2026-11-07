"""题库领域模型。"""
from typing import Literal

from pydantic import BaseModel, Field


class Option(BaseModel):
    key: str
    text: str


class Question(BaseModel):
    id: str
    type: Literal["single", "multiple", "judge"]
    stem: str
    options: list[Option]
    answer: list[str]
    explanation: str
    knowledge_point: str
    difficulty: Literal["easy", "medium", "hard"]


class Source(BaseModel):
    title: str
    url: str


class Quiz(BaseModel):
    quiz_id: str
    title: str
    summary: str
    source_type: str = "text"
    user_input: str
    keywords: list[str] = []
    questions: list[Question]
    sources: list[Source] = []
    freshness: Literal["fresh", "stale"] = "stale"


class QuizGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    question_count: int = Field(default=5, ge=1, le=10)
    difficulty: str = "mixed"
