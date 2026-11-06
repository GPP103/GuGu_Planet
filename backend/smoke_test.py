"""真实 DeepSeek 调用冒烟测试（需 .env 配置 API Key）。"""
import json
import sys

sys.path.insert(0, ".")

from app.models.report import AnswerRecord
from app.services.quiz_service import QuizService
from app.services.report_service import ReportService


def main():
    print("=== 1. 出题链 ===")
    svc = QuizService()
    quiz = svc.generate("什么是 RAG，它和传统搜索有什么区别")
    print(f"quiz_id={quiz.quiz_id} title={quiz.title}")
    print(f"题目数={len(quiz.questions)}")
    for q in quiz.questions:
        print(f"  {q.id} [{q.type}/{q.difficulty}] {q.stem}")
        print(f"    选项={[o.key for o in q.options]} 答案={q.answer} 知识点={q.knowledge_point}")

    print("\n=== 2. 报告链 ===")
    records = []
    for i, q in enumerate(quiz.questions):
        correct = i == 0
        records.append(
            AnswerRecord(
                question_id=q.id,
                selected_answers=q.answer if correct else [],
                is_correct=correct,
                duration_ms=2000,
            )
        )
    rsvc = ReportService()
    report = rsvc.generate(quiz.quiz_id, quiz.title, quiz.questions, records)
    print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
