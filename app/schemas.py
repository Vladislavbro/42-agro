from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class RawMessagesIn(BaseModel):
    messages: List[str]

class Report(BaseModel):
    date: date
    department: Optional[str]
    operation: Optional[str]
    crop: Optional[str]
    area_day: Optional[float]
    area_total: Optional[float]
    yield_day: Optional[float]
    yield_total: Optional[float]
