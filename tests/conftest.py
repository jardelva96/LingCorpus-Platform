"""Fixtures compartilhadas para os testes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lingcorpus.app import app
from lingcorpus.auth import hash_password
from lingcorpus.database import Base, get_db
from lingcorpus.models import User, UserRole

TEST_DB_URL = "sqlite:///./test_lingcorpus.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_db():
    """Cria e limpa o banco de dados de teste."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Fornece uma sessão de banco de dados de teste."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """Fornece um cliente HTTP de teste."""
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    """Cria um usuário administrador de teste."""
    user = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def researcher_user(db):
    """Cria um usuário pesquisador de teste."""
    user = User(
        username="researcher",
        email="researcher@test.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Researcher",
        role=UserRole.PESQUISADOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Obtém token de autenticação do admin."""
    r = client.post("/api/auth/login",
                    data={"username": "testadmin", "password": "testpass123"})
    return r.json()["access_token"]


@pytest.fixture
def researcher_token(client, researcher_user):
    """Obtém token de autenticação do pesquisador."""
    r = client.post("/api/auth/login",
                    data={"username": "researcher", "password": "testpass123"})
    return r.json()["access_token"]
