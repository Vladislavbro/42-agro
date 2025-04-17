from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import RawMessagesIn, Report
from app.models import Message as MessageModel, ReportModel
from app.core.database import SessionLocal
from app.message_processing.processor import process_single_message_async

router = APIRouter(tags=["messages"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/incoming/raw-messages",
    response_model=list[Report],
    summary="Приём и обработка сырых сообщений",
)
async def incoming_messages(
    data: RawMessagesIn,
    db: Session = Depends(get_db),
):
    # 1) Сохраняем каждое сообщение в БД
    saved = []
    for text in data.messages:
        msg = MessageModel(text=text)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        saved.append(msg)

    # 2) Для каждого запущенного сообщения вызываем процессор
    all_reports = []
    for msg in saved:
        try:
            extracted: list[dict] = process_single_message_async(msg.text)
        except Exception as e:
            # Превращаем любые ошибки в HTTP 500
            raise HTTPException(status_code=500, detail=str(e))

        # Если нечего извлекать — пропускаем
        if not extracted:
            continue

        # 3) Сохраняем каждый отчёт в БД
        for item in extracted:
            # Маппинг полей из результата процессора в поля модели
            report = ReportModel(
                message_id=msg.id,
                date=item.get("Дата"),
                department=item.get("Подразделение"),
                operation=item.get("Операция"),
                crop=item.get("Культура"),
                area_day=item.get("За день, га"),
                area_total=item.get("С начала операции, га"),
                yield_day=item.get("Вал за день, ц"),
                yield_total=item.get("Вал с начала, ц"),
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            # Преобразуем в Pydantic‑схему для ответа
            all_reports.append(report)

    return all_reports
