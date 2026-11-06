"""出题服务（含题目库关键字缓存）。"""
import json

from sqlalchemy.orm import Session

from app.core.exceptions import InputInvalidError, QuizGenerationError
from app.llm.output_schemas import LLMQuiz
from app.models.question_bank import QuestionBank
from app.models.quiz import Option, Question, Quiz
from app.utils.content_filter import validate_input
from app.utils.id_generator import gen_quiz_id
from app.utils.normalize import normalize_difficulty, normalize_type
from app.utils.text_cleaner import clean_text


class QuizService:
    def __init__(self, quiz_chain=None, db: Session | None = None):
        if quiz_chain is None:
            from app.llm.quiz_chain import build_quiz_chain

            quiz_chain = build_quiz_chain()
        self.chain = quiz_chain
        self.db = db

    def generate(self, user_input: str, question_count: int = 5, difficulty: str = "mixed") -> Quiz:
        try:
            cleaned = validate_input(user_input)
        except ValueError as e:
            raise InputInvalidError(str(e)) from e
        cleaned = clean_text(cleaned)

        # 1. 关键字缓存命中：输入包含任一关键字即返回，省 token、提速
        if self.db is not None:
            cached = self._find_by_keyword(cleaned)
            if cached is not None:
                return cached

        # 2. LLM 生成
        quiz = self._generate_via_llm(cleaned)

        # 3. 写缓存
        if self.db is not None:
            self._save_cache(quiz)

        return quiz

    def _generate_via_llm(self, cleaned: str) -> Quiz:
        try:
            result = self.chain.invoke({"user_input": cleaned})
        except Exception as e:
            raise QuizGenerationError() from e

        if not isinstance(result, LLMQuiz) or not result.questions:
            raise QuizGenerationError()

        questions: list[Question] = []
        for q in result.questions:
            questions.append(
                Question(
                    id=q.id,
                    type=normalize_type(q.type),
                    stem=q.stem,
                    options=[Option(key=o.key, text=o.text) for o in q.options],
                    answer=q.answer,
                    explanation=q.explanation,
                    knowledge_point=q.knowledge_point,
                    difficulty=normalize_difficulty(q.difficulty),
                )
            )

        return Quiz(
            quiz_id=gen_quiz_id(),
            title=result.title,
            summary=result.summary,
            user_input=cleaned,
            keywords=list(result.keywords or []),
            questions=questions,
        )

    def _find_by_keyword(self, text: str) -> Quiz | None:
        text_lower = text.lower()
        rows = self.db.query(QuestionBank).all()
        for row in rows:
            try:
                keywords = json.loads(row.keywords or "[]")
            except Exception:
                continue
            for kw in keywords:
                if kw and kw.lower() in text_lower:
                    row.hit_count += 1
                    self.db.commit()
                    return self._row_to_quiz(row, text)
        return None

    def _row_to_quiz(self, row: QuestionBank, text: str) -> Quiz | None:
        try:
            questions = [Question(**q) for q in json.loads(row.questions)]
        except Exception:
            return None
        return Quiz(
            quiz_id=gen_quiz_id(),
            title=row.title,
            summary=row.summary,
            user_input=text,
            keywords=json.loads(row.keywords or "[]"),
            questions=questions,
        )

    def _save_cache(self, quiz: Quiz) -> None:
        # 相同标题视为已缓存，避免重复入库
        exists = self.db.query(QuestionBank).filter(QuestionBank.title == quiz.title).first()
        if exists is not None:
            return
        row = QuestionBank(
            title=quiz.title,
            keywords=json.dumps(quiz.keywords, ensure_ascii=False),
            summary=quiz.summary,
            question_count=len(quiz.questions),
            questions=json.dumps([q.model_dump() for q in quiz.questions], ensure_ascii=False),
        )
        self.db.add(row)
        self.db.commit()
