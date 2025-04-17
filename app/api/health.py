from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", summary="Проверка статуса сервера")
async def health():
    """
    Простой эндпоинт для проверки работоспособности API.
    Возвращает {"status":"ok"} если сервер поднят.
    """
    return {"status": "ok"}
