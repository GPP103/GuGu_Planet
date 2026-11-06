"""评分服务测试。"""
from app.models.report import AnswerRecord
from app.services.scoring_service import compute_score
from helpers import make_question


def test_score_basic():
    qs = [make_question("q1", "知识点1"), make_question("q2", "知识点2")]
    recs = [
        AnswerRecord(question_id="q1", selected_answers=["A"], is_correct=True),
        AnswerRecord(question_id="q2", selected_answers=["A"], is_correct=False),
    ]
    s = compute_score(qs, recs)
    assert s.total == 2
    assert s.correct == 1
    assert s.accuracy == 50
    assert s.correct_points == ["知识点1"]
    assert s.wrong_points == ["知识点2"]


def test_score_dedupe_points():
    qs = [make_question("q1", "重复点"), make_question("q2", "重复点")]
    recs = [
        AnswerRecord(question_id="q1", selected_answers=["A"], is_correct=True),
        AnswerRecord(question_id="q2", selected_answers=["A"], is_correct=True),
    ]
    s = compute_score(qs, recs)
    assert s.correct_points == ["重复点"]
    assert s.wrong_points == []


def test_score_empty_questions():
    s = compute_score([], [])
    assert s.total == 0
    assert s.accuracy == 0


def test_score_all_correct():
    qs = [make_question("q1", "点"), make_question("q2", "点2"), make_question("q3", "点3"), make_question("q4", "点4")]
    recs = [AnswerRecord(question_id=f"q{i}", selected_answers=["A"], is_correct=True) for i in range(1, 5)]
    s = compute_score(qs, recs)
    assert s.accuracy == 100
