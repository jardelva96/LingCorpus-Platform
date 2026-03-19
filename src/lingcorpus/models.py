"""Modelos SQLAlchemy para o banco de dados."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from lingcorpus.database import Base


class UserRole(str, enum.Enum):
    """Níveis de acesso do usuário."""

    ADMIN = "admin"
    PESQUISADOR = "pesquisador"
    VISITANTE = "visitante"


class ValidationStatus(str, enum.Enum):
    """Status de validação de um registro."""

    PENDENTE = "pendente"
    VALIDADO = "validado"
    REJEITADO = "rejeitado"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Usuário da plataforma com controle de acesso baseado em papel."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VISITANTE, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    corpora = relationship("Corpus", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


class Corpus(Base):
    """Coleção de textos enviados por um pesquisador."""

    __tablename__ = "corpora"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    language = Column(String(10), default="pt")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    owner = relationship("User", back_populates="corpora")
    documents = relationship("Document", back_populates="corpus", cascade="all, delete-orphan")


class Document(Base):
    """Documento textual pertencente a um corpus."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_encoding = Column(String(50), default="utf-8")
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    type_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    validation_status = Column(
        Enum(ValidationStatus), default=ValidationStatus.PENDENTE, nullable=False
    )
    validation_notes = Column(Text, default="")
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    corpus_id = Column(Integer, ForeignKey("corpora.id"), nullable=False)
    uploaded_at = Column(DateTime, default=_utcnow, nullable=False)

    corpus = relationship("Corpus", back_populates="documents")


class AuditLog(Base):
    """Registro de auditoria para rastrear ações na plataforma."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, default="")
    ip_address = Column(String(45), default="")
    timestamp = Column(DateTime, default=_utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


class FrequencyCache(Base):
    """Cache de análise de frequência por documento."""

    __tablename__ = "frequency_cache"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    token = Column(String(255), nullable=False, index=True)
    frequency = Column(Integer, nullable=False)
    relative_frequency = Column(Float, nullable=False)
