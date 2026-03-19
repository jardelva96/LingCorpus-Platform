"""Rotas de análise NLP sobre o corpus."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from lingcorpus.auth import get_current_user
from lingcorpus.database import get_db
from lingcorpus.models import Corpus, Document, User, UserRole
from lingcorpus.schemas import ConcordanceLine, NLPAnalysisResponse, TextStatistics, TokenFrequency
from lingcorpus.services.corpus_service import get_corpus_text
from lingcorpus.services.nlp_service import (
    compute_frequencies,
    compute_statistics,
    concordance,
    ngrams,
    tokenize,
)

router = APIRouter(prefix="/api/analysis", tags=["Análise NLP"])


@router.get("/{corpus_id}/statistics", response_model=TextStatistics)
def get_statistics(
    corpus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna estatísticas descritivas do corpus."""
    corpus = _get_corpus(db, corpus_id, current_user)
    text = get_corpus_text(db, corpus_id)
    if not text.strip():
        raise HTTPException(status_code=404, detail="Corpus sem documentos")
    stats = compute_statistics(text, corpus.language)
    return TextStatistics(
        total_tokens=stats.total_tokens,
        total_types=stats.total_types,
        type_token_ratio=stats.type_token_ratio,
        avg_word_length=stats.avg_word_length,
        avg_sentence_length=stats.avg_sentence_length,
        hapax_legomena=stats.hapax_legomena,
        hapax_ratio=stats.hapax_ratio,
    )


@router.get("/{corpus_id}/frequencies", response_model=list[TokenFrequency])
def get_frequencies(
    corpus_id: int,
    top_n: int = Query(default=50, ge=1, le=500),
    remove_stopwords: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna as palavras mais frequentes do corpus."""
    corpus = _get_corpus(db, corpus_id, current_user)
    text = get_corpus_text(db, corpus_id)
    tokens = tokenize(text, corpus.language)
    freqs = compute_frequencies(tokens, remove_stopwords, corpus.language)
    total = sum(f for _, f in freqs)
    return [
        TokenFrequency(token=t, frequency=f, relative_frequency=f / total if total else 0.0)
        for t, f in freqs[:top_n]
    ]


@router.get("/{corpus_id}/concordance", response_model=list[ConcordanceLine])
def get_concordance(
    corpus_id: int,
    keyword: str = Query(min_length=1),
    window: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna linhas de concordância KWIC para uma palavra-chave."""
    corpus = _get_corpus(db, corpus_id, current_user)
    docs = db.query(Document).filter(Document.corpus_id == corpus_id).all()
    results = []
    for doc in docs:
        hits = concordance(doc.content, keyword, window, corpus.language, doc.filename)
        results.extend(
            ConcordanceLine(
                left_context=h.left_context,
                keyword=h.keyword,
                right_context=h.right_context,
                document=h.document,
            )
            for h in hits
        )
    return results


@router.get("/{corpus_id}/ngrams")
def get_ngrams(
    corpus_id: int,
    n: int = Query(default=2, ge=2, le=5),
    top_k: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna os n-gramas mais frequentes do corpus."""
    corpus = _get_corpus(db, corpus_id, current_user)
    text = get_corpus_text(db, corpus_id)
    tokens = tokenize(text, corpus.language)
    grams = ngrams(tokens, n)
    return [{"ngram": g, "frequency": f} for g, f in grams[:top_k]]


@router.get("/{corpus_id}/full", response_model=NLPAnalysisResponse)
def get_full_analysis(
    corpus_id: int,
    top_n: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna análise completa: estatísticas + frequências."""
    corpus = _get_corpus(db, corpus_id, current_user)
    text = get_corpus_text(db, corpus_id)
    if not text.strip():
        raise HTTPException(status_code=404, detail="Corpus sem documentos")

    stats = compute_statistics(text, corpus.language)
    tokens = tokenize(text, corpus.language)
    freqs = compute_frequencies(tokens, remove_stopwords=True, language=corpus.language)
    total = sum(f for _, f in freqs)

    return NLPAnalysisResponse(
        statistics=TextStatistics(
            total_tokens=stats.total_tokens,
            total_types=stats.total_types,
            type_token_ratio=stats.type_token_ratio,
            avg_word_length=stats.avg_word_length,
            avg_sentence_length=stats.avg_sentence_length,
            hapax_legomena=stats.hapax_legomena,
            hapax_ratio=stats.hapax_ratio,
        ),
        top_frequencies=[
            TokenFrequency(token=t, frequency=f, relative_frequency=f / total if total else 0.0)
            for t, f in freqs[:top_n]
        ],
    )


def _get_corpus(db: Session, corpus_id: int, user: User) -> Corpus:
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus não encontrado")
    if user.role != UserRole.ADMIN and corpus.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return corpus
