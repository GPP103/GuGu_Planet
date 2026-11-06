"""答题记录相关请求 / 响应模型。"""
from pydantic import BaseModel, Field

from app.models.quiz import Option


class QuestionIn(BaseModel):
    id: str
    type: str = "single"
    stem: str
    options: list[Option] = []
    answer: list[str] = []
    explanation: str = ""
    knowledge_point: str = ""
    difficulty: str = "medium"


class AnswerRecordIn(BaseModel):
    question_id: str
    selected_answers: list[str] = []
    is_correct: bool = False


class RecordSubmitRequest(BaseModel):
    topic: str = Field(default="", max_length=128)
    questions: list[QuestionIn]
    records: list[AnswerRecordIn]


class RecordSubmitResponse(BaseModel):
    record_id: int
    total_answered: int
    total_correct: int
    current_streak: int
    accuracy: int


class RecordItem(BaseModel):
    type: str = "single"
    stem: str = ""
    options: list[Option] = []
    answer: list[str] = []
    user_answer: list[str] = []
    is_correct: bool = False
    explanation: str = ""
    knowledge_point: str = ""


class HistoryItem(BaseModel):
    id: int
    topic: str
    question_count: int
    answered_count: int
    correct_count: int
    accuracy: int
    created_at: str
    items: list[RecordItem] = []


class WrongItem(BaseModel):
    id: int
    topic: str
    type: str
    stem: str
    options: list[Option]
    answer: list[str]
    explanation: str
    knowledge_point: str
    user_answer: list[str]
