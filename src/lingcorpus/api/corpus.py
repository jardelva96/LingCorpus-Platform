"""Rotas de gerenciamento de corpus e documentos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from lingcorpus.auth import get_current_user, require_role
from lingcorpus.config import settings
from lingcorpus.database import get_db
from lingcorpus.models import Corpus, Document, User, UserRole
from lingcorpus.schemas import (
    CorpusCreate,
    CorpusResponse,
    CorpusUpdate,
    DocumentResponse,
    DocumentValidation,
)
from lingcorpus.services.audit_service import log_action
from lingcorpus.services.corpus_service import (
    create_corpus,
    export_corpus_csv,
    get_corpus_documents,
    upload_document,
    validate_document,
)

router = APIRouter(prefix="/api/corpus", tags=["Corpus"])


@router.post("/", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: CorpusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PESQUISADOR)),
):
    """Cria um novo corpus."""
    corpus = create_corpus(db, data.name, data.description, data.language, current_user.id)
    return _corpus_with_count(corpus, db)


@router.get("/", response_model=list[CorpusResponse])
def list_corpora(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos os corpora acessíveis ao usuário."""
    if current_user.role == UserRole.ADMIN:
        corpora = db.query(Corpus).all()
    else:
        corpora = db.query(Corpus).filter(Corpus.owner_id == current_user.id).all()
    return [_corpus_with_count(c, db) for c in corpora]


@router.get("/{corpus_id}", response_model=CorpusResponse)
def get_corpus(
    corpus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna detalhes de um corpus."""
    corpus = _get_corpus_or_404(db, corpus_id, current_user)
    return _corpus_with_count(corpus, db)


@router.patch("/{corpus_id}", response_model=CorpusResponse)
def update_corpus(
    corpus_id: int,
    update: CorpusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PESQUISADOR)),
):
    """Atualiza metadados de um corpus."""
    corpus = _get_corpus_or_404(db, corpus_id, current_user)
    if update.name is not None:
        corpus.name = update.name
    if update.description is not None:
        corpus.description = update.description
    if update.language is not None:
        corpus.language = update.language
    db.commit()
    db.refresh(corpus)
    log_action(db, current_user.id, "UPDATE", "corpus", corpus_id)
    return _corpus_with_count(corpus, db)


@router.delete("/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus(
    corpus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Remove um corpus e todos os seus documentos."""
    corpus = _get_corpus_or_404(db, corpus_id, current_user)
    log_action(db, current_user.id, "DELETE", "corpus", corpus_id, details=corpus.name)
    db.delete(corpus)
    db.commit()


# ── Documentos ────────────────────────────────────────────────────────────


@router.post("/{corpus_id}/documents", response_model=DocumentResponse)
async def upload(
    corpus_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PESQUISADOR)),
):
    """Envia um documento para o corpus."""
    _get_corpus_or_404(db, corpus_id, current_user)

    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Arquivo muito grande ({size_mb:.1f} MB). "
                f"Máximo: {settings.max_upload_size_mb} MB"
            ),
        )

    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    doc = upload_document(db, corpus_id, file.filename or "unnamed.txt", raw, current_user.id,
                          language=corpus.language)
    return doc


@router.get("/{corpus_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    corpus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista documentos de um corpus."""
    _get_corpus_or_404(db, corpus_id, current_user)
    return get_corpus_documents(db, corpus_id)


@router.patch("/{corpus_id}/documents/{doc_id}/validate", response_model=DocumentResponse)
def validate_doc(
    corpus_id: int,
    doc_id: int,
    validation: DocumentValidation,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PESQUISADOR)),
):
    """Valida ou rejeita um documento."""
    _get_corpus_or_404(db, corpus_id, current_user)
    return validate_document(db, doc_id, validation.status, validation.notes, current_user.id)


@router.get("/{corpus_id}/export")
def export(
    corpus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exporta metadados do corpus em CSV."""
    _get_corpus_or_404(db, corpus_id, current_user)
    from fastapi.responses import PlainTextResponse
    csv_content = export_corpus_csv(db, corpus_id)
    return PlainTextResponse(content=csv_content, media_type="text/csv")


# ── Helpers ───────────────────────────────────────────────────────────────


def _get_corpus_or_404(db: Session, corpus_id: int, user: User) -> Corpus:
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus não encontrado")
    if user.role != UserRole.ADMIN and corpus.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a este corpus")
    return corpus


def _corpus_with_count(corpus: Corpus, db: Session) -> dict:
    doc_count = db.query(Document).filter(Document.corpus_id == corpus.id).count()
    return {
        "id": corpus.id,
        "name": corpus.name,
        "description": corpus.description,
        "language": corpus.language,
        "owner_id": corpus.owner_id,
        "created_at": corpus.created_at,
        "updated_at": corpus.updated_at,
        "document_count": doc_count,
    }
