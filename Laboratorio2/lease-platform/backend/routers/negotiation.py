from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from database import get_session
from models.domain import (
    Application,
    BrokerAssignment,
    DealProposal,
    GuidanceMessage,
    Meeting,
    MeetingState,
    Negotiation,
    NegotiationDocument,
    NegotiationState,
    Role,
    User,
)
from schemas.api import (
    DealProposalCreate,
    DealProposalRead,
    GuidanceMessageCreate,
    GuidanceMessageRead,
    MeetingCreate,
    MeetingRead,
    MeetingResponseCreate,
    NegotiationDocumentRead,
    NegotiationRead,
    BrokerAssignmentRead,
)
from services.audit import audit
from services.auth import CurrentUser, require_roles
from services.files import UPLOAD_DIR, inspect_upload, persist_upload


router = APIRouter(prefix="/api", tags=["Broker negotiation"])
SessionDep = Annotated[Session, Depends(get_session)]


def _now():
    return datetime.now(timezone.utc)


def _get_negotiation(session: Session, negotiation_id: int) -> Negotiation:
    negotiation = session.get(Negotiation, negotiation_id)
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return negotiation


def _check_access(session: Session, negotiation: Negotiation, user: User) -> None:
    application = session.get(Application, negotiation.application_id)
    allowed = user.role == Role.LEASING or user.id == negotiation.broker_id or (application and user.id == application.owner_id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Unauthorized access")


def _read_full(session: Session, negotiation: Negotiation) -> NegotiationRead:
    return NegotiationRead(
        **NegotiationRead.model_validate(negotiation).model_dump(exclude={"meetings", "proposals", "messages", "documents"}),
        meetings=session.exec(select(Meeting).where(Meeting.negotiation_id == negotiation.id).order_by(Meeting.created_at)).all(),
        proposals=session.exec(select(DealProposal).where(DealProposal.negotiation_id == negotiation.id).order_by(DealProposal.created_at)).all(),
        messages=session.exec(select(GuidanceMessage).where(GuidanceMessage.negotiation_id == negotiation.id).order_by(GuidanceMessage.created_at)).all(),
        documents=session.exec(select(NegotiationDocument).where(NegotiationDocument.negotiation_id == negotiation.id).order_by(NegotiationDocument.created_at)).all(),
    )


@router.post("/requests/{application_id}/negotiation", response_model=NegotiationRead, summary="Open a documented negotiation")
def create_negotiation(
    application_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.BROKER))],
):
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    assignment = session.exec(select(BrokerAssignment).where(
        BrokerAssignment.application_id == application_id,
        BrokerAssignment.broker_id == user.id,
    )).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    existing = session.exec(select(Negotiation).where(Negotiation.application_id == application_id)).first()
    if existing:
        if existing.broker_id != user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        return _read_full(session, existing)
    negotiation = Negotiation(application_id=application_id, broker_id=user.id)
    session.add(negotiation)
    session.flush()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="OPENED", actor=user, new=negotiation.state.value)
    session.commit()
    session.refresh(negotiation)
    return _read_full(session, negotiation)


@router.get("/broker/assignments", response_model=list[BrokerAssignmentRead], summary="List minimal application references assigned to current Broker")
def list_broker_assignments(
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.BROKER))],
):
    assignments = session.exec(
        select(BrokerAssignment).where(BrokerAssignment.broker_id == user.id).order_by(BrokerAssignment.created_at.desc())
    ).all()
    result = []
    for assignment in assignments:
        application = session.get(Application, assignment.application_id)
        if not application:
            continue
        negotiation = session.exec(select(Negotiation).where(Negotiation.application_id == application.id)).first()
        result.append(BrokerAssignmentRead(
            application_id=application.id,
            machinery_type=application.machinery_type,
            currency=application.currency,
            negotiation_id=negotiation.id if negotiation else None,
        ))
    return result


@router.get("/requests/{application_id}/negotiation", response_model=NegotiationRead)
def read_request_negotiation(application_id: int, session: SessionDep, user: CurrentUser):
    negotiation = session.exec(select(Negotiation).where(Negotiation.application_id == application_id)).first()
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    _check_access(session, negotiation, user)
    return _read_full(session, negotiation)


@router.get("/negotiations", response_model=list[NegotiationRead])
def list_negotiations(session: SessionDep, user: CurrentUser):
    statement = select(Negotiation).order_by(Negotiation.updated_at.desc())
    if user.role == Role.BROKER:
        statement = statement.where(Negotiation.broker_id == user.id)
    negotiations = session.exec(statement).all()
    visible = []
    for negotiation in negotiations:
        try:
            _check_access(session, negotiation, user)
            visible.append(_read_full(session, negotiation))
        except HTTPException:
            continue
    return visible


@router.post("/negotiations/{negotiation_id}/meetings", response_model=MeetingRead, summary="Record an explicit meeting-date proposal")
def propose_meeting(negotiation_id: int, payload: MeetingCreate, session: SessionDep, user: CurrentUser):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    if negotiation.state in {NegotiationState.CLOSED, NegotiationState.STALLED}:
        raise HTTPException(status_code=409, detail=f"Negotiation is {negotiation.state.value}")
    if negotiation.proposed_dates_count >= 5:
        negotiation.state = NegotiationState.STALLED
        negotiation.updated_at = _now()
        audit(session, entity_type="negotiation", entity_id=negotiation.id, action="STALLED_AFTER_DATE_LIMIT", actor=user, previous="PROPOSED", new="STALLED")
        session.commit()
        raise HTTPException(status_code=409, detail="Negotiation reached the 5 proposed-date limit and is now STALLED")
    meeting = Meeting(negotiation_id=negotiation.id, proposed_by=user.id, scheduled_for=payload.scheduled_for)
    negotiation.proposed_dates_count += 1
    negotiation.state = NegotiationState.PROPOSED
    negotiation.updated_at = _now()
    session.add(meeting)
    session.flush()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="MEETING_DATE_PROPOSED", actor=user, new=payload.scheduled_for.isoformat())
    session.commit()
    session.refresh(meeting)
    return meeting


@router.post("/negotiations/{negotiation_id}/meetings/{meeting_id}/response", response_model=MeetingRead, summary="Record a company's explicit response")
def respond_meeting(
    negotiation_id: int,
    meeting_id: int,
    payload: MeetingResponseCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.CLIENT, Role.LEASING))],
):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    meeting = session.get(Meeting, meeting_id)
    if not meeting or meeting.negotiation_id != negotiation_id:
        raise HTTPException(status_code=404, detail="Meeting proposal not found")
    previous = meeting.state
    meeting.state = MeetingState(payload.action)
    meeting.response_by = user.id
    meeting.response_note = payload.note
    if payload.new_date:
        meeting.scheduled_for = payload.new_date
    negotiation.updated_at = _now()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="MEETING_RESPONSE_RECORDED", actor=user, previous=previous.value, new=meeting.state.value)
    session.commit()
    session.refresh(meeting)
    return meeting


@router.post("/negotiations/{negotiation_id}/proposals", response_model=DealProposalRead, summary="Record a non-binding Broker proposal")
def create_proposal(
    negotiation_id: int,
    payload: DealProposalCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.BROKER))],
):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    if negotiation.state == NegotiationState.CLOSED:
        raise HTTPException(status_code=409, detail="Cannot add a proposal to a CLOSED negotiation")
    proposal = DealProposal(negotiation_id=negotiation.id, author_id=user.id, text=payload.text)
    negotiation.updated_at = _now()
    session.add(proposal)
    session.flush()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="NON_BINDING_PROPOSAL_RECORDED", actor=user)
    session.commit()
    session.refresh(proposal)
    return proposal


@router.post("/negotiations/{negotiation_id}/messages", response_model=GuidanceMessageRead, summary="Record Broker guidance without changing business state")
def create_message(
    negotiation_id: int,
    payload: GuidanceMessageCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.BROKER))],
):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    message = GuidanceMessage(
        negotiation_id=negotiation.id,
        author_id=user.id,
        recipients=payload.recipients,
        body=payload.body,
        delivery_status="DELIVERY_FAILED" if payload.simulate_delivery_failure else "DELIVERED_IN_APP",
    )
    negotiation.updated_at = _now()
    session.add(message)
    session.flush()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="GUIDANCE_MESSAGE_RECORDED", actor=user, new=message.delivery_status)
    session.commit()
    session.refresh(message)
    return message


@router.post("/negotiations/{negotiation_id}/documents", response_model=NegotiationDocumentRead, summary="Upload shared contract documentation")
async def upload_contract_document(
    negotiation_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.BROKER))],
    summary: Annotated[str, Form(min_length=10)],
    structured_details: Annotated[str, Form(min_length=2)],
    file: Annotated[UploadFile, File()],
):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    data, digest = await inspect_upload(file, pdf_only=True)
    stored_name = persist_upload(data, digest, file.filename or "contract.pdf")
    document = NegotiationDocument(
        negotiation_id=negotiation.id,
        uploaded_by=user.id,
        original_name=file.filename or "contract.pdf",
        stored_name=stored_name,
        mime_type=file.content_type or "application/pdf",
        size_bytes=len(data),
        summary=summary,
        structured_details=structured_details,
    )
    negotiation.updated_at = _now()
    session.add(document)
    session.flush()
    audit(session, entity_type="negotiation", entity_id=negotiation.id, action="CONTRACT_DOCUMENT_SHARED", actor=user, new=document.original_name)
    session.commit()
    session.refresh(document)
    return document


@router.get("/negotiations/{negotiation_id}/documents/{document_id}/download", response_class=FileResponse, summary="Download the same authenticated PDF shared with both companies")
def download_contract_document(negotiation_id: int, document_id: int, session: SessionDep, user: CurrentUser):
    negotiation = _get_negotiation(session, negotiation_id)
    _check_access(session, negotiation, user)
    document = session.get(NegotiationDocument, document_id)
    if not document or document.negotiation_id != negotiation_id:
        raise HTTPException(status_code=404, detail="Document not found")
    target = UPLOAD_DIR / document.stored_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Stored document not found")
    return FileResponse(target, media_type="application/pdf", filename=document.original_name)
