"""复盘报告接口。"""
from fastapi import APIRouter, Depends

from app.models.common import ApiResponse
from app.models.report import Report, ReportGenerateRequest
from app.services.report_service import ReportService

router = APIRouter()

_report_service: ReportService | None = None


def get_report_service() -> ReportService:
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service


@router.post("/report/generate")
def generate_report(
    req: ReportGenerateRequest,
    service: ReportService = Depends(get_report_service),
) -> ApiResponse[Report]:
    report = service.generate(req.quiz_id, req.topic, req.questions, req.answer_records)
    return ApiResponse(data=report)
