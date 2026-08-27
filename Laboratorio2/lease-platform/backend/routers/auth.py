from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models.domain import DemoSession, User
from schemas.api import DemoSessionCreate, DemoSessionRead, DemoUserRead
from services.auth import CurrentUser


router = APIRouter(prefix="/api", tags=["Demo session"])
SessionDep = Annotated[Session, Depends(get_session)]


DUAL_APPROVAL_SERVICE_ACCOUNT_ID = 4


@router.get(
    "/demo/users",
    response_model=list[DemoUserRead],
    summary="List seeded demo identities (case-study personas only)",
)
def list_demo_users(session: SessionDep):
    """Excludes the NFR-07 dual-approval service account (id 4): it is a second
    authorized leasing-company account for segregation of duties, not a fourth persona."""
    return session.exec(
        select(User).where(User.id != DUAL_APPROVAL_SERVICE_ACCOUNT_ID).order_by(User.id)
    ).all()


@router.post("/demo/session", response_model=DemoSessionRead, summary="Select a POC identity")
def create_demo_session(payload: DemoSessionCreate, session: SessionDep):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Demo user not found")
    token = secrets.token_urlsafe(32)
    session.add(DemoSession(token=token, user_id=user.id))
    session.commit()
    return DemoSessionRead(access_token=token, user=DemoUserRead.model_validate(user))


@router.get("/me", response_model=DemoUserRead, summary="Read current demo identity")
def read_me(user: CurrentUser):
    return user

