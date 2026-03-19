"""Serviço de gerenciamento de corpus e documentos."""

from __future__ import annotations

import chardet
from sqlalchemy.orm import Session

from lingcorpus.config import settings
from lingcorpus.models import AuditLog, Corpus, Document, ValidationStatus
from lingcorpus.services.nlp_service import compute_statistics


def detect_encoding(raw_bytes: bytes) -> str:
    """Detecta a codificação de um arquivo usando chardet."""
    result = chardet.detect(raw_bytes)
    return result.get("encoding", "utf-8") or "utf-8"


def create_corpus(
    db: Session, name: str, description: str, language: str, owner_id: int,
) -> Corpus:
    """Cria um novo corpus no banco de dados."""
    corpus = Corpus(
        name=name,
        description=description,
        language=language,
        owner_id=owner_id,
    )
    db.add(corpus)
    db.commit()
    db.refresh(corpus)

    db.add(AuditLog(
        user_id=owner_id,
        action="CREATE",
        entity_type="corpus",
        entity_id=corpus.id,
        details=f"Corpus '{name}' criado",
    ))
    db.commit()
    return corpus


def upload_document(
    db: Session,
    corpus_id: int,
    filename: str,
    raw_content: bytes,
    user_id: int,
    language: str = "pt",
) -> Document:
    """Processa e armazena um novo documento no corpus."""
    encoding = detect_encoding(raw_content)
    text = raw_content.decode(encoding, errors="replace")

    # Calcula estatísticas
    stats = compute_statistics(text, language)

    # Salva arquivo original
    dest = settings.upload_dir / f"corpus_{corpus_id}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / filename).write_bytes(raw_content)

    document = Document(
        filename=filename,
        original_encoding=encoding,
        content=text,
        token_count=stats.total_tokens,
        type_count=stats.total_types,
        char_count=len(text),
        sentence_count=int(stats.avg_sentence_length) if stats.total_tokens else 0,
        corpus_id=corpus_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    db.add(AuditLog(
        user_id=user_id,
        action="UPLOAD",
        entity_type="document",
        entity_id=document.id,
        details=f"Documento '{filename}' enviado ({encoding}, {stats.total_tokens} tokens)",
    ))
    db.commit()
    return document


def validate_document(
    db: Session,
    document_id: int,
    status: ValidationStatus,
    notes: str,
    validator_id: int,
) -> Document:
    """Valida ou rejeita um documento."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        msg = f"Documento {document_id} não encontrado"
        raise ValueError(msg)

    doc.validation_status = status
    doc.validation_notes = notes
    doc.validated_by = validator_id
    db.commit()
    db.refresh(doc)

    db.add(AuditLog(
        user_id=validator_id,
        action="VALIDATE",
        entity_type="document",
        entity_id=document_id,
        details=f"Status: {status.value} | {notes}",
    ))
    db.commit()
    return doc


def get_corpus_text(db: Session, corpus_id: int) -> str:
    """Retorna todo o texto concatenado de um corpus."""
    docs = db.query(Document).filter(Document.corpus_id == corpus_id).all()
    return "\n\n".join(doc.content for doc in docs)


def get_corpus_documents(db: Session, corpus_id: int) -> list[Document]:
    """Retorna todos os documentos de um corpus."""
    return db.query(Document).filter(Document.corpus_id == corpus_id).all()


def export_corpus_csv(db: Session, corpus_id: int) -> str:
    """Exporta metadados dos documentos de um corpus em formato CSV."""
    docs = get_corpus_documents(db, corpus_id)
    lines = ["filename,encoding,tokens,types,chars,status"]
    lines.extend(
        f"{doc.filename},{doc.original_encoding},{doc.token_count},"
        f"{doc.type_count},{doc.char_count},{doc.validation_status.value}"
        for doc in docs
    )
    return "\n".join(lines)
