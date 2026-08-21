from __future__ import annotations

from sqlmodel import Session

from models.domain import AuditEntry, User


def audit(
    session: Session,
    *,
    entity_type: str,
    entity_id: int | str,
    action: str,
    actor: User | None,
    previous: str | None = None,
    new: str | None = None,
    organization: str | None = None,
) -> None:
    session.add(AuditEntry(
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor_id=actor.id if actor else None,
        organization=organization or (actor.organization if actor else "EXTERNAL_INTEGRATION"),
        action=action,
        previous_value=previous,
        new_value=new,
    ))

