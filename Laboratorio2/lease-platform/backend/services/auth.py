from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from database import get_session
from models.domain import DemoSession, Role, User


bearer_scheme = HTTPBearer(
    description="Use the access_token returned by POST /api/demo/session. This is a role selector for the POC, not production authentication."
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    demo_session = session.get(DemoSession, credentials.credentials)
    if not demo_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired demo token")
    user = session.get(User, demo_session.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demo user no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable:
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")
        return user
    return dependency


def leasing_users(session: Session) -> list[User]:
    return list(session.exec(select(User).where(User.role == Role.LEASING)).all())

