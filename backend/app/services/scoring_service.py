"""评分服务：根据答题记录计算统计结果。"""
from pydantic import BaseModel

from app.models.quiz import Question
from app.models.report import AnswerRecord


class ScoreSummary(BaseModel):
    total: int
    correct: int
    accuracy: int
    correct_points: list[str]
    wrong_points: list[str]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def compute_score(questions: list[Question], answer_records: list[AnswerRecord]) -> ScoreSummary:
    id_to_q = {q.id: q for q in questions}
    total = len(questions)
    correct = 0
    correct_points: list[str] = []
    wrong_points: list[str] = []

    for rec in answer_records:
        q = id_to_q.get(rec.question_id)
        if rec.is_correct:
            correct += 1
            if q:
                correct_points.append(q.knowledge_point)
        else:
            if q:
                wrong_points.append(q.knowledge_point)

    accuracy = round(correct / total * 100) if total else 0
    return ScoreSummary(
        total=total,
        correct=correct,
        accuracy=accuracy,
        correct_points=_dedupe(correct_points),
        wrong_points=_dedupe(wrong_points),
    )
