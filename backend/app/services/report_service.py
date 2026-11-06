"""报告服务。"""
import json

from app.core.exceptions import ReportGenerationError
from app.llm.output_schemas import LLMReport
from app.models.report import AnswerRecord, Report
from app.models.quiz import Question
from app.services.scoring_service import compute_score


class ReportService:
    def __init__(self, report_chain=None):
        if report_chain is None:
            from app.llm.report_chain import build_report_chain

            report_chain = build_report_chain()
        self.chain = report_chain

    def generate(
        self,
        quiz_id: str,
        topic: str,
        questions: list[Question],
        answer_records: list[AnswerRecord],
    ) -> Report:
        # 1. 本地评分（正确率以本地计算为准，不依赖 LLM）
        score = compute_score(questions, answer_records)

        # 2. 调用 LLM 生成复盘报告
        try:
            result = self.chain.invoke(
                {
                    "topic": topic,
                    "quiz_json": json.dumps([q.model_dump() for q in questions], ensure_ascii=False),
                    "answer_records": json.dumps([r.model_dump() for r in answer_records], ensure_ascii=False),
                    "score_summary": json.dumps(score.model_dump(), ensure_ascii=False),
                }
            )
        except Exception as e:
            raise ReportGenerationError() from e

        if not isinstance(result, LLMReport):
            raise ReportGenerationError()

        # 3. 正确率兜底：有题目时以本地计算为准
        accuracy = score.accuracy if score.total else result.accuracy

        return Report(
            accuracy=accuracy,
            mastered_points=result.mastered_points,
            weak_points=result.weak_points,
            three_line_summary=result.three_line_summary,
            advice=result.advice,
            share_quote=result.share_quote,
        )
