"""Aplicação FastAPI principal."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lingcorpus.api.analysis import router as analysis_router
from lingcorpus.api.corpus import router as corpus_router
from lingcorpus.api.users import router as auth_router
from lingcorpus.api.users import user_router
from lingcorpus.database import init_db


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa o banco de dados na primeira execução."""
    init_db()
    _create_default_admin()
    yield


app = FastAPI(
    title="LingCorpus Platform",
    description=(
        "Plataforma web para gerenciamento, validação e análise de corpus textual "
        "de pesquisa. Desenvolvida para apoiar projetos em Linguística Computacional, "
        "Linguística de Corpus e Processamento de Língua Natural."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(corpus_router)
app.include_router(analysis_router)


def _create_default_admin():
    """Cria usuário administrador padrão se não existir."""
    from lingcorpus.auth import hash_password
    from lingcorpus.database import SessionLocal
    from lingcorpus.models import User, UserRole

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@lingcorpus.local",
                hashed_password=hash_password("admin123"),
                full_name="Administrador",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/", tags=["Root"])
def root():
    """Página raiz com informações da API."""
    return {
        "name": "LingCorpus Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "description": "Plataforma de gerenciamento e análise de corpus textual",
    }


@app.get("/health", tags=["Root"])
def health():
    """Verificação de saúde da aplicação."""
    return {"status": "ok"}


def main():
    """Ponto de entrada para execução direta."""
    uvicorn.run("lingcorpus.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
