from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.security import APIKeyHeader
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from database import get_session
from models.domain import (
    Application,
    ApplicationStatus,
    BrokerAssignment,
    CreditDocument,
    DecisionAttestation,
    DecisionOutcome,
    InboxMessage,
    Role,
    User,
)
from schemas.api import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationSubmit,
    CreditDocumentRead,
    DecisionAttestationRead,
    RiskOutcomeCreate,
)
from services.audit import audit
from services.auth import CurrentUser, require_roles
from services.files import contains_eicar, inspect_upload, persist_upload


router = APIRouter(prefix="/api", tags=["Financing requests"])
SessionDep = Annotated[Session, Depends(get_session)]
integration_key = APIKeyHeader(name="X-Integration-Key", description="POC external risk adapter key")
MANDATORY_DOCUMENTS = {"BANK_STATEMENTS", "TAX_RETURN", "PROJECT_CONTRACT"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _intent(payload: ApplicationCreate) -> str:
    raw = "|".join([
        payload.ruc,
        payload.machinery_type.strip().lower(),
        str(payload.requested_amount),
        str(payload.requested_term_months),
        payload.currency,
    ])
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_application(session: Session, application_id: int) -> Application:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _check_application_access(application: Application, user: User) -> None:
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if user.role == Role.CLIENT and application.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")


def _dual_approval_required(application: Application) -> bool:
    conversion = Decimal(os.getenv("POC_USD_PEN_RATE", "3.75")) if application.currency == "USD" else Decimal("1")
    return application.requested_amount * conversion > Decimal("500000")


def _apply_outcome(session: Session, application: Application) -> None:
    if not application.pending_outcome:
        return
    previous = application.status
    outcome = application.pending_outcome
    application.status = ApplicationStatus(outcome.value)
    application.pending_outcome = None
    application.updated_at = _now()
    owner = session.get(User, application.owner_id)
    if owner:
        session.add(InboxMessage(
            user_id=owner.id,
            subject=f"Financing request {application.id}: {application.status.value}",
            body=f"Outcome received from external evaluator. Reason: {application.decision_reason_code} — {application.decision_reason_text}",
        ))
    audit(
        session,
        entity_type="application",
        entity_id=application.id,
        action="EXTERNAL_OUTCOME_RECORDED",
        actor=None,
        previous=previous.value,
        new=application.status.value,
    )


@router.post("/requests", response_model=ApplicationRead, summary="Create an idempotent financing request")
def create_request(payload: ApplicationCreate, session: SessionDep, user: CurrentUser):
    if user.role != Role.CLIENT:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    intent_key = _intent(payload)
    existing = session.exec(select(Application).where(Application.intent_key == intent_key)).first()
    if existing:
        # Same intent resubmitted at any point (still under review, or already decided):
        # idempotent submit returns the existing application rather than erroring (AC-1.3).
        return existing
    application = Application(owner_id=user.id, intent_key=intent_key, **payload.model_dump())
    try:
        session.add(application)
        session.flush()
        session.add(BrokerAssignment(application_id=application.id, broker_id=3))
        audit(session, entity_type="application", entity_id=application.id, action="CREATED", actor=user, new=application.status.value)
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.exec(select(Application).where(Application.intent_key == intent_key)).first()
        if existing:
            return existing
        raise
    session.refresh(application)
    return application


@router.get("/requests", response_model=list[ApplicationRead], summary="List requests visible to current role")
def list_requests(session: SessionDep, user: CurrentUser):
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    statement = select(Application).order_by(Application.created_at.desc())
    if user.role == Role.CLIENT:
        statement = statement.where(Application.owner_id == user.id)
    return session.exec(statement).all()


@router.get("/requests/{application_id}", response_model=ApplicationRead)
def read_request(application_id: int, session: SessionDep, user: CurrentUser):
    application = _get_application(session, application_id)
    _check_application_access(application, user)
    return application


@router.get("/requests/{application_id}/documents", response_model=list[CreditDocumentRead])
def list_documents(application_id: int, session: SessionDep, user: CurrentUser):
    application = _get_application(session, application_id)
    _check_application_access(application, user)
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return session.exec(select(CreditDocument).where(CreditDocument.application_id == application_id)).all()


@router.post("/requests/{application_id}/documents", response_model=CreditDocumentRead, summary="Upload one mandatory dossier document")
async def upload_document(
    application_id: int,
    session: SessionDep,
    user: CurrentUser,
    kind: Annotated[str, Form(description="BANK_STATEMENTS, TAX_RETURN or PROJECT_CONTRACT")],
    file: Annotated[UploadFile, File()],
):
    application = _get_application(session, application_id)
    if user.role != Role.CLIENT or application.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if application.status != ApplicationStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="Documents can only be uploaded while SUBMITTED")
    kind = kind.upper()
    if kind not in MANDATORY_DOCUMENTS:
        raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(MANDATORY_DOCUMENTS)}")
    data, digest = await inspect_upload(file)
    existing = session.exec(
        select(CreditDocument).where(CreditDocument.application_id == application_id, CreditDocument.kind == kind)
    ).first()
    document = existing or CreditDocument(
        application_id=application_id,
        kind=kind,
        original_name=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
    )
    document.original_name = file.filename or "upload"
    document.mime_type = file.content_type or "application/octet-stream"
    document.size_bytes = len(data)
    if contains_eicar(data):
        document.quarantined = True
        document.stored_name = None
        session.add(InboxMessage(
            user_id=user.id,
            subject="Document rejected by antivirus simulation",
            body=f"{document.original_name} matched the EICAR test signature and was not stored.",
        ))
    else:
        document.quarantined = False
        document.stored_name = persist_upload(data, digest, document.original_name)
    session.add(document)
    session.flush()
    audit(session, entity_type="application", entity_id=application_id, action="DOSSIER_DOCUMENT_PROCESSED", actor=user, new=f"{kind}:{'QUARANTINED' if document.quarantined else 'STORED'}")
    session.commit()
    session.refresh(document)
    return document


@router.post("/requests/{application_id}/submit", response_model=ApplicationRead, summary="Complete dossier and enter external review")
def submit_request(application_id: int, payload: ApplicationSubmit, session: SessionDep, user: CurrentUser):
    application = _get_application(session, application_id)
    if user.role != Role.CLIENT or application.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if application.status != ApplicationStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="Only SUBMITTED applications can enter review")
    documents = session.exec(select(CreditDocument).where(CreditDocument.application_id == application_id)).all()
    valid_kinds = {document.kind for document in documents if not document.quarantined and document.stored_name}
    missing = sorted(MANDATORY_DOCUMENTS - valid_kinds)
    if missing:
        raise HTTPException(status_code=409, detail={"message": "Mandatory dossier is incomplete", "missing": missing})
    previous = application.status
    application.bureau_attempts = 3 if payload.bureau_scenario == "TIMEOUT" else 1
    if payload.bureau_scenario == "TIMEOUT":
        application.status = ApplicationStatus.SCORING_UNAVAILABLE
        application.bureau_score = None
    else:
        application.status = ApplicationStatus.IN_REVIEW
        application.bureau_score = payload.bureau_score
    application.updated_at = _now()
    audit(session, entity_type="application", entity_id=application.id, action="SUBMITTED_TO_EXTERNAL_REVIEW", actor=user, previous=previous.value, new=application.status.value)
    session.commit()
    session.refresh(application)
    return application


@router.post("/integrations/risk-outcomes", response_model=ApplicationRead, tags=["External integrations"], summary="Receive—not compute—an external credit outcome")
def receive_risk_outcome(
    payload: RiskOutcomeCreate,
    session: SessionDep,
    key: Annotated[str, Depends(integration_key)],
):
    if key != os.getenv("POC_RISK_INTEGRATION_KEY", "poc-risk-secret"):
        raise HTTPException(status_code=401, detail="Invalid integration key")
    application = _get_application(session, payload.application_id)
    if application.status not in {ApplicationStatus.IN_REVIEW, ApplicationStatus.SCORING_UNAVAILABLE}:
        raise HTTPException(status_code=409, detail="Application is not awaiting an external outcome")
    application.pending_outcome = payload.outcome
    application.approved_limit = payload.approved_limit
    application.approved_term_months = payload.approved_term_months
    application.annual_interest_rate = payload.annual_interest_rate
    application.decision_reason_code = payload.reason_code
    application.decision_reason_text = payload.reason_text
    application.decision_received_at = _now()
    if not _dual_approval_required(application):
        _apply_outcome(session, application)
    else:
        audit(session, entity_type="application", entity_id=application.id, action="EXTERNAL_OUTCOME_PENDING_DUAL_ATTESTATION", actor=None, new=payload.outcome.value)
    session.commit()
    session.refresh(application)
    return application


@router.post("/requests/{application_id}/decision-attestations", response_model=DecisionAttestationRead, summary="Attest an externally received high-value decision")
def attest_decision(
    application_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    application = _get_application(session, application_id)
    if not application.pending_outcome:
        raise HTTPException(status_code=409, detail="No external outcome is awaiting attestation")
    existing = session.exec(select(DecisionAttestation).where(
        DecisionAttestation.application_id == application_id,
        DecisionAttestation.user_id == user.id,
    )).first()
    if existing:
        raise HTTPException(status_code=409, detail="This leasing account already attested the outcome")
    attestation = DecisionAttestation(application_id=application_id, user_id=user.id)
    session.add(attestation)
    session.flush()
    audit(session, entity_type="application", entity_id=application_id, action="DECISION_ATTESTED", actor=user, new=str(user.id))
    count = len(session.exec(select(DecisionAttestation).where(DecisionAttestation.application_id == application_id)).all())
    if not _dual_approval_required(application) or count >= 2:
        _apply_outcome(session, application)
    session.commit()
    session.refresh(attestation)
    return attestation


@router.get("/review-queue", response_model=list[ApplicationRead], summary="Read the leasing review/recording queue")
def review_queue(
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    del user
    return session.exec(select(Application).where(
        Application.status.in_([ApplicationStatus.IN_REVIEW, ApplicationStatus.SCORING_UNAVAILABLE])
    ).order_by(Application.created_at)).all()
