"""答题记录与错题本服务。"""
import hashlib
import json

from sqlalchemy.orm import Session

from app.core.exceptions import InputInvalidError
from app.models.quiz_record import QuizRecord, WrongQuestion
from app.models.record_schemas import HistoryItem, RecordSubmitResponse, WrongItem
from app.models.user import User
from app.utils.cache_key import normalize_cache_input


def _question_hash(stem: str) -> str:
    return hashlib.sha256(normalize_cache_input(stem).encode("utf-8")).hexdigest()


class RecordService:
    def __init__(self, db: Session):
        self.db = db

    def submit(
        self,
        user: User,
        topic: str,
        questions: list[dict],
        records: list[dict],
    ) -> RecordSubmitResponse:
        if not questions:
            raise InputInvalidError("题目不能为空")

        answered = len(records)
        correct = sum(1 for r in records if r.get("is_correct"))

        # 1. 更新统计（只算实际作答数，区分「未作答」与「答错」）
        from app.services.user_service import UserService

        stats = UserService(self.db).submit_study_record(user, answered, correct)

        # 2. 组装每道题作答详情
        qmap = {q.get("id"): q for q in questions}
        items = []
        for r in records:
            q = qmap.get(r.get("question_id"))
            if not q:
                continue
            items.append(
                {
                    "type": q.get("type", "single"),
                    "stem": q.get("stem", ""),
                    "options": q.get("options", []),
                    "answer": q.get("answer", []),
                    "user_answer": r.get("selected_answers", []),
                    "is_correct": r.get("is_correct", False),
                    "explanation": q.get("explanation", ""),
                    "knowledge_point": q.get("knowledge_point", ""),
                }
            )

        # 3. 写答题历史（含题目级详情）
        accuracy = round(correct / answered * 100) if answered > 0 else 0
        record = QuizRecord(
            user_id=user.id,
            topic=topic,
            question_count=len(questions),
            answered_count=answered,
            correct_count=correct,
            accuracy=accuracy,
            items=json.dumps(items, ensure_ascii=False),
        )
        self.db.add(record)

        # 4. 写错题本（按题干去重，重复答错更新时间与答案）
        for r in records:
            if r.get("is_correct"):
                continue
            q = qmap.get(r.get("question_id"))
            if not q:
                continue
            self._upsert_wrong(user.id, topic, q, r)

        self.db.commit()
        return RecordSubmitResponse(
            record_id=record.id,
            total_answered=stats.total_answered,
            total_correct=stats.total_correct,
            current_streak=stats.current_streak,
            accuracy=stats.accuracy,
        )

    def _upsert_wrong(self, user_id: int, topic: str, q: dict, r: dict) -> None:
        h = _question_hash(q.get("stem", ""))
        row = (
            self.db.query(WrongQuestion)
            .filter(WrongQuestion.user_id == user_id, WrongQuestion.question_hash == h)
            .first()
        )
        data = dict(
            topic=topic,
            type=q.get("type", "single"),
            stem=q.get("stem", ""),
            options=json.dumps(q.get("options", []), ensure_ascii=False),
            answer=json.dumps(q.get("answer", []), ensure_ascii=False),
            explanation=q.get("explanation", ""),
            knowledge_point=q.get("knowledge_point", ""),
            user_answer=json.dumps(r.get("selected_answers", []), ensure_ascii=False),
        )
        if row is not None:
            for k, v in data.items():
                setattr(row, k, v)
        else:
            self.db.add(WrongQuestion(user_id=user_id, question_hash=h, **data))

    def history(self, user: User, limit: int = 50) -> list[HistoryItem]:
        rows = (
            self.db.query(QuizRecord)
            .filter(QuizRecord.user_id == user.id)
            .order_by(QuizRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            HistoryItem(
                id=r.id,
                topic=r.topic,
                question_count=r.question_count,
                answered_count=r.answered_count,
                correct_count=r.correct_count,
                accuracy=r.accuracy,
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M"),
                items=json.loads(r.items or "[]"),
            )
            for r in rows
        ]

    def wrong_list(self, user: User) -> list[WrongItem]:
        rows = (
            self.db.query(WrongQuestion)
            .filter(WrongQuestion.user_id == user.id)
            .order_by(WrongQuestion.updated_at.desc())
            .all()
        )
        return [
            WrongItem(
                id=w.id,
                topic=w.topic,
                type=w.type,
                stem=w.stem,
                options=json.loads(w.options or "[]"),
                answer=json.loads(w.answer or "[]"),
                explanation=w.explanation,
                knowledge_point=w.knowledge_point,
                user_answer=json.loads(w.user_answer or "[]"),
            )
            for w in rows
        ]

    def remove_wrong(self, user: User, wrong_id: int) -> bool:
        row = (
            self.db.query(WrongQuestion)
            .filter(WrongQuestion.id == wrong_id, WrongQuestion.user_id == user.id)
            .first()
        )
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
