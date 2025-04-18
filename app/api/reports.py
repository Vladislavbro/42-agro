from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date as date_type

from app.schemas import Report
from app.models import ReportModel
from app.api.messages import get_db  # берём ту же зависимость для сессии

router = APIRouter(tags=["reports"])


@router.get(
    "/reports",
    response_model=List[Report],
    summary="Получить отчёты за конкретную дату",
)
def get_reports(
    report_date: date_type = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    """
    Возвращает все сохранённые отчёты из БД за указанную дату `YYYY-MM-DD`.
    """
    records = (
        db.query(ReportModel)
          .filter(ReportModel.date == report_date)
          .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="Отчётов за эту дату не найдено")
    # автоматически сконвертируется в Pydantic-схему Report
    return records
