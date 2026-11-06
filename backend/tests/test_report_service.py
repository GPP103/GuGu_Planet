"""报告服务测试。"""
import pytest

from app.core.exceptions import ReportGenerationError
from app.models.report import AnswerRecord
from app.services.report_service import ReportService
from helpers import FakeChain, make_llm_report, make_question


def _records():
    return [
        AnswerRecord(question_id="q1", selected_answers=["A"], is_correct=True),
        AnswerRecord(question_id="q2", selected_answers=["A"], is_correct=False),
    ]


def test_report_ok():
    service = ReportService(FakeChain(make_llm_report()))
    qs = [make_question("q1", "点1"), make_question("q2", "点2")]
    report = service.generate("quiz_x", "RAG 入门", qs, _records())
    assert report.accuracy == 50
    assert report.share_quote == "把知识做成关卡，记忆会更深。"
    assert len(report.three_line_summary) == 3


def test_report_accuracy_from_local_not_llm():
    # 即使 LLM 编造 99%，正确率也必须以本地计算为准
    fake = make_llm_report()
    fake.accuracy = 99
    service = ReportService(FakeChain(fake))
    qs = [make_question("q1", "点1"), make_question("q2", "点2")]
    report = service.generate("quiz_x", "RAG 入门", qs, _records())
    assert report.accuracy == 50


def test_report_llm_failure():
    service = ReportService(FakeChain(exc=RuntimeError("boom")))
    qs = [make_question("q1", "点1")]
    with pytest.raises(ReportGenerationError):
        service.generate("quiz_x", "RAG 入门", qs, _records())
