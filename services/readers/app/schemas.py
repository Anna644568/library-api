"""Схемы данных сервиса readers: читатели."""
from typing import Optional

from pydantic import BaseModel, Field

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class ReaderIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=EMAIL)
    phone: Optional[str] = None


class ReaderUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, pattern=EMAIL)
    phone: Optional[str] = None


class Reader(ReaderIn):
    id: int
