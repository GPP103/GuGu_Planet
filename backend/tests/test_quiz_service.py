"""出题服务测试。"""
import pytest

from app.core.exceptions import InputInvalidError, QuizGenerationError
from app.llm.output_schemas import LLMQuiz
from app.services.quiz_service import QuizService
from app.services.search_service import SearchContext, SearchSource
from helpers import FakeChain, make_llm_quiz


def test_generate_ok():
    service = QuizService(FakeChain(make_llm_quiz()))
    quiz = service.generate("什么是 RAG")
    assert quiz.quiz_id.startswith("quiz_")
    assert quiz.title == "RAG 入门"
    assert quiz.user_input == "什么是 RAG"
    assert len(quiz.questions) == 1
    assert quiz.questions[0].type == "single"
    assert quiz.questions[0].difficulty == "easy"


def test_generate_empty_input():
    service = QuizService(FakeChain(make_llm_quiz()))
    with pytest.raises(InputInvalidError):
        service.generate("   ")


def test_generate_llm_failure():
    service = QuizService(FakeChain(exc=RuntimeError("boom")))
    with pytest.raises(QuizGenerationError):
        service.generate("什么是 RAG")


def test_generate_empty_questions():
    service = QuizService(FakeChain(LLMQuiz(title="t", summary="s", questions=[])))
    with pytest.raises(QuizGenerationError):
        service.generate("什么是 RAG")


def test_generate_normalizes_type():
    quiz = make_llm_quiz()
    quiz.questions[0].type = "单选"
    service = QuizService(FakeChain(quiz))
    result = service.generate("什么是 RAG")
    assert result.questions[0].type == "single"


class FakeSearch:
    def __init__(self, ctx):
        self.ctx = ctx

    def search(self, query):
        return self.ctx


def test_generate_with_search_injects_context_and_sources():
    ctx = SearchContext(
        answer="Harness Engineering 是设计 AI 智能体执行环境的学科",
        sources=[SearchSource(title="来源", url="https://example.com/a", content="正文")],
    )
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, search_service=FakeSearch(ctx))
    quiz = service.generate("Harness Engineering")
    assert quiz.freshness == "fresh"
    assert quiz.sources[0].url == "https://example.com/a"
    assert "AI 智能体执行环境" in chain.last_payload["search_context"]


def test_generate_empty_search_degrades():
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, search_service=FakeSearch(SearchContext()))
    quiz = service.generate("Harness Engineering")
    assert quiz.freshness == "stale"
    assert quiz.sources == []
    assert "未提供联网检索资料" in chain.last_payload["search_context"]
