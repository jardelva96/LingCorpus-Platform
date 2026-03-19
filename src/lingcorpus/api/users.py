"""Rotas de gerenciamento de usuários e autenticação."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from lingcorpus.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
)
from lingcorpus.database import get_db
from lingcorpus.models import User, UserRole
from lingcorpus.schemas import Token, UserCreate, UserResponse, UserUpdate
from lingcorpus.services.audit_service import log_action

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])
user_router = APIRouter(prefix="/api/users", tags=["Usuários"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Autentica um usuário e retorna o token JWT."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    log_action(db, user.id, "LOGIN", "user", user.id)
    return Token(access_token=token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário na plataforma."""
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe",
        )
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user.id, "REGISTER", "user", user.id)
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna dados do usuário autenticado."""
    return current_user


@user_router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Lista todos os usuários (apenas admin)."""
    return db.query(User).all()


@user_router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Atualiza dados de um usuário (apenas admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if update.full_name is not None:
        user.full_name = update.full_name
    if update.role is not None:
        user.role = update.role
    if update.is_active is not None:
        user.is_active = update.is_active

    db.commit()
    db.refresh(user)

    log_action(
        db, current_user.id, "UPDATE_USER", "user", user_id,
        details=f"Campos atualizados: {update.model_dump(exclude_unset=True)}",
    )
    return user
