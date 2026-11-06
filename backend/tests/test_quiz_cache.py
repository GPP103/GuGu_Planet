"""题目库关键字缓存测试。"""
from app.models.question_bank import QuestionBank
from app.services.quiz_service import QuizService
from helpers import FakeChain, make_llm_quiz


def test_generate_caches_then_hits_by_keyword(db_session):
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, db=db_session)

    quiz1 = service.generate("什么是 RAG")
    assert chain.last_payload is not None  # 首次调用 LLM
    assert db_session.query(QuestionBank).count() == 1

    # 输入包含关键字 "RAG"，命中缓存
    chain.last_payload = None
    quiz2 = service.generate("RAG 是什么")
    assert chain.last_payload is None
    assert quiz2.title == quiz1.title
    assert len(quiz2.questions) == len(quiz1.questions)
    assert quiz2.quiz_id != quiz1.quiz_id


def test_keyword_match_different_phrasing(db_session):
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, db=db_session)

    service.generate("RAG 入门")
    chain.last_payload = None
    # 换一种说法但含关键字「检索增强生成」
    service.generate("检索增强生成的原理是什么")
    assert chain.last_payload is None  # 命中缓存


def test_no_keyword_match_goes_to_llm(db_session):
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, db=db_session)

    service.generate("RAG 入门")
    chain.last_payload = None
    # 不含任何关键字，应重新走 LLM
    service.generate("英语单词速记")
    assert chain.last_payload is not None


def test_hit_count_increments(db_session):
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, db=db_session)
    service.generate("RAG 入门")
    service.generate("RAG 是什么")
    row = db_session.query(QuestionBank).first()
    assert row.hit_count == 1  # 首次生成不计数，第二次命中 +1


def test_no_db_skips_cache():
    chain = FakeChain(make_llm_quiz())
    service = QuizService(chain, db=None)
    service.generate("什么是 RAG")
    assert chain.last_payload is not None
