"""Pydantic-схемы: что API принимает на вход и что отдаёт."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Авторы ----------
class AuthorIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    country: Optional[str] = None
    birth_year: Optional[int] = Field(default=None, ge=0, le=2100)


class AuthorUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    country: Optional[str] = None
    birth_year: Optional[int] = Field(default=None, ge=0, le=2100)


class Author(AuthorIn):
    id: int


# ---------- Жанры ----------
class GenreIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class GenreUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None


class Genre(GenreIn):
    id: int


# ---------- Книги ----------
class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    year: Optional[int] = Field(default=None, ge=0, le=2100)
    isbn: Optional[str] = None
    copies: int = Field(default=1, ge=0)
    author_id: int
    genre_id: Optional[int] = None


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    year: Optional[int] = Field(default=None, ge=0, le=2100)
    isbn: Optional[str] = None
    copies: Optional[int] = Field(default=None, ge=0)
    author_id: Optional[int] = None
    genre_id: Optional[int] = None


class Book(BookIn):
    id: int


# ---------- Читатели ----------
class ReaderIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = None


class ReaderUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = None


class Reader(ReaderIn):
    id: int
