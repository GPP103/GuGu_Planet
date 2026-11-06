"""报告接口测试（mock LLM 链）。"""
from app.api.v1.routes import report as report_route
from app.main import app
from app.services.report_service import ReportService
from helpers import FakeChain, make_llm_report, make_question


def _payload():
    return {
        "quiz_id": "quiz_x",
        "topic": "RAG 入门",
        "questions": [
            make_question("q1", "点1").model_dump(),
            make_question("q2", "点2").model_dump(),
        ],
        "answer_records": [
            {"question_id": "q1", "selected_answers": ["A"], "is_correct": True, "duration_ms": 1000},
            {"question_id": "q2", "selected_answers": ["A"], "is_correct": False, "duration_ms": 2000},
        ],
    }


def test_report_endpoint_ok(client):
    app.dependency_overrides[report_route.get_report_service] = lambda: ReportService(FakeChain(make_llm_report()))
    try:
        resp = client.post("/api/v1/report/generate", json=_payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["accuracy"] == 50
        assert body["data"]["share_quote"] == "把知识做成关卡，记忆会更深。"
    finally:
        app.dependency_overrides.clear()
