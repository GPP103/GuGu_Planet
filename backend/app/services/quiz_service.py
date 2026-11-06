"""出题服务。"""
from app.core.exceptions import InputInvalidError, QuizGenerationError
from app.llm.output_schemas import LLMQuiz
from app.models.quiz import Option, Question, Quiz
from app.utils.content_filter import validate_input
from app.utils.id_generator import gen_quiz_id
from app.utils.normalize import normalize_difficulty, normalize_type
from app.utils.text_cleaner import clean_text


class QuizService:
    def __init__(self, quiz_chain=None):
        if quiz_chain is None:
            from app.llm.quiz_chain import build_quiz_chain

            quiz_chain = build_quiz_chain()
        self.chain = quiz_chain

    def generate(self, user_input: str, question_count: int = 5, difficulty: str = "mixed") -> Quiz:
        # 1. 校验与清洗
        try:
            cleaned = validate_input(user_input)
        except ValueError as e:
            raise InputInvalidError(str(e)) from e
        cleaned = clean_text(cleaned)

        # 2. 调用 LLM 生成结构化题库
        try:
            result = self.chain.invoke({"user_input": cleaned})
        except Exception as e:
            raise QuizGenerationError() from e

        if not isinstance(result, LLMQuiz) or not result.questions:
            raise QuizGenerationError()

        # 3. 归一化并组装领域模型（对 LLM 输出做字段兜底）
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
            questions=questions,
        )
