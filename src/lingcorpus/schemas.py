"""Schemas Pydantic para validação de entrada/saída da API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from lingcorpus.models import UserRole, ValidationStatus

# ── Usuários ──────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole = UserRole.VISITANTE


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: int | None = None


# ── Autenticação ──────────────────────────────────────────────────────────


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


# ── Corpus ────────────────────────────────────────────────────────────────


class CorpusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    language: str = Field(default="pt", max_length=10)


class CorpusResponse(BaseModel):
    id: int
    name: str
    description: str
    language: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class CorpusUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    language: str | None = None


# ── Documentos ────────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_encoding: str
    token_count: int
    type_count: int
    char_count: int
    sentence_count: int
    validation_status: ValidationStatus
    validation_notes: str
    corpus_id: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentValidation(BaseModel):
    status: ValidationStatus
    notes: str = ""


# ── Análise NLP ───────────────────────────────────────────────────────────


class TokenFrequency(BaseModel):
    token: str
    frequency: int
    relative_frequency: float


class ConcordanceLine(BaseModel):
    left_context: str
    keyword: str
    right_context: str
    document: str


class TextStatistics(BaseModel):
    total_tokens: int
    total_types: int
    type_token_ratio: float
    avg_word_length: float
    avg_sentence_length: float
    hapax_legomena: int
    hapax_ratio: float


class NLPAnalysisResponse(BaseModel):
    statistics: TextStatistics
    top_frequencies: list[TokenFrequency]


# ── Auditoria ─────────────────────────────────────────────────────────────


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: int | None
    details: str
    timestamp: datetime

    model_config = {"from_attributes": True}
