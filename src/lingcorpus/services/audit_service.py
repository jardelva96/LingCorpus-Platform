"""Serviço de auditoria para rastreamento de ações na plataforma."""

from __future__ import annotations

from sqlalchemy.orm import Session

from lingcorpus.models import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str = "",
    ip_address: str = "",
) -> AuditLog:
    """Registra uma ação no log de auditoria."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_recent_logs(
    db: Session,
    limit: int = 50,
    user_id: int | None = None,
    entity_type: str | None = None,
) -> list[AuditLog]:
    """Retorna os logs de auditoria mais recentes, com filtros opcionais."""
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def count_actions_by_user(db: Session) -> list[tuple[int, str, int]]:
    """Conta ações agrupadas por usuário."""
    from sqlalchemy import func

    from lingcorpus.models import User

    results = (
        db.query(User.id, User.username, func.count(AuditLog.id))
        .join(AuditLog, User.id == AuditLog.user_id)
        .group_by(User.id, User.username)
        .all()
    )
    return results


def count_actions_by_type(db: Session) -> list[tuple[str, int]]:
    """Conta ações agrupadas por tipo."""
    from sqlalchemy import func

    results = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .all()
    )
    return results
