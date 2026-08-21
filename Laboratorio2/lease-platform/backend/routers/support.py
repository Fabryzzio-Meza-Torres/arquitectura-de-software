from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models.domain import AuditEntry, InboxMessage, Role, User
from schemas.api import AuditRead, InboxRead
from services.auth import CurrentUser, require_roles


router = APIRouter(prefix="/api", tags=["Support and traceability"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/inbox", response_model=list[InboxRead])
def read_inbox(session: SessionDep, user: CurrentUser):
    return session.exec(select(InboxMessage).where(
        InboxMessage.user_id == user.id
    ).order_by(InboxMessage.created_at.desc())).all()


@router.get("/audit", response_model=list[AuditRead], summary="Query append-only audit entries")
def read_audit(
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
    entity_id: str | None = Query(default=None),
    actor_id: int | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
):
    del user
    statement = select(AuditEntry).order_by(AuditEntry.created_at.desc())
    if entity_id:
        statement = statement.where(AuditEntry.entity_id == entity_id)
    if actor_id:
        statement = statement.where(AuditEntry.actor_id == actor_id)
    if date_from:
        statement = statement.where(AuditEntry.created_at >= date_from)
    if date_to:
        statement = statement.where(AuditEntry.created_at <= date_to)
    return session.exec(statement).all()

