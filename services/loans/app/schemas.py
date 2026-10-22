"""Схемы данных сервиса loans: выдачи книг."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class LoanIn(BaseModel):
    book_id: int
    reader_id: int
    loan_date: date
    due_date: date
    returned: bool = False


class LoanUpdate(BaseModel):
    book_id: Optional[int] = None
    reader_id: Optional[int] = None
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    returned: Optional[bool] = None


class Loan(LoanIn):
    id: int
