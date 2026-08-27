from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from database import get_session
from models.domain import (
    Contract,
    ContractState,
    DelinquencyLevel,
    InboxMessage,
    Installment,
    Payment,
    ReconciliationStatus,
    ResolutionChoice,
    Role,
    User,
)
from schemas.api import (
    CollectionMessageCreate,
    CollectionsSummaryRead,
    DelinquencyBucket,
    PaymentCreate,
    PaymentRead,
    ResolutionCreate,
)
from services.audit import audit
from services.auth import CurrentUser, require_roles
from services.collections import allocate_payment, delinquency_level
from services.schedule import money


router = APIRouter(prefix="/api", tags=["Collections and end-of-contract resolution"])
SessionDep = Annotated[Session, Depends(get_session)]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _contract_for_client(session: Session, contract_id: int, user: User) -> Contract:
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return contract


def _executable_installments(session: Session, contract_id: int) -> list[Installment]:
    return session.exec(
        select(Installment).where(Installment.contract_id == contract_id).order_by(Installment.number)
    ).all()


@router.post("/contracts/{contract_id}/payments", response_model=PaymentRead, summary="Register an idempotent installment payment")
def register_payment(
    contract_id: int,
    payload: PaymentCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.CLIENT))],
):
    """FR-11, AC-4.1/4.2/4.3: idempotent by bank_reference, applied oldest-first, flags a
    mismatch instead of silently accepting a partial or over payment."""
    contract = _contract_for_client(session, contract_id, user)
    if contract.status != ContractState.ACTIVE:
        raise HTTPException(status_code=409, detail="Payments can only be registered on an ACTIVE contract")
    existing = session.exec(
        select(Payment).where(Payment.contract_id == contract.id, Payment.bank_reference == payload.bank_reference)
    ).first()
    if existing:
        return existing

    installments = _executable_installments(session, contract.id)
    unpaid = [item for item in installments if item.paid_amount < item.amount]
    if not unpaid:
        raise HTTPException(status_code=409, detail="Contract has no outstanding installments")
    oldest_due = unpaid[0].amount - unpaid[0].paid_amount
    status = ReconciliationStatus.MATCHED if payload.amount == oldest_due else ReconciliationStatus.RECONCILIATION_MISMATCH

    allocations, _remainder = allocate_payment(installments, payload.amount)
    applied_total = Decimal("0")
    for installment, applied in allocations:
        installment.paid_amount = money(installment.paid_amount + applied)
        applied_total += applied
        session.add(installment)
    contract.outstanding_balance = money(contract.outstanding_balance - applied_total)

    payment = Payment(
        contract_id=contract.id,
        bank_reference=payload.bank_reference,
        amount=payload.amount,
        currency=contract.currency,
        registered_by=user.id,
        reconciliation_status=status,
    )
    try:
        session.add(payment)
        session.flush()
        audit(session, entity_type="contract", entity_id=contract.id, action="PAYMENT_REGISTERED", actor=user, new=f"{payload.bank_reference}:{status.value}")
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = session.exec(
            select(Payment).where(Payment.contract_id == contract.id, Payment.bank_reference == payload.bank_reference)
        ).first()
        if existing:
            return existing
        raise HTTPException(status_code=409, detail="Concurrent payment rejected") from exc
    session.refresh(payment)
    return payment


@router.get("/contracts/{contract_id}/payments", response_model=list[PaymentRead], summary="List payments and reconciliation status for a contract")
def list_payments(contract_id: int, session: SessionDep, user: CurrentUser):
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if user.role == Role.CLIENT and contract.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return session.exec(
        select(Payment).where(Payment.contract_id == contract_id).order_by(Payment.created_at)
    ).all()


@router.post("/contracts/{contract_id}/collection-message", summary="Send a formal message to a delinquent client (VG3)")
def send_collection_message(
    contract_id: int,
    payload: CollectionMessageCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    installments = _executable_installments(session, contract.id)
    level = delinquency_level(installments, date.today())
    if level == DelinquencyLevel.GREEN:
        raise HTTPException(status_code=409, detail="Contract is current; no collection message needed")
    session.add(InboxMessage(
        user_id=contract.owner_id,
        subject=f"Contrato #{contract.id}: pago pendiente ({level.value})",
        body=payload.note or f"Su contrato tiene cuotas vencidas y está clasificado como {level.value}. Regularice a la brevedad.",
    ))
    audit(session, entity_type="contract", entity_id=contract.id, action="COLLECTION_MESSAGE_SENT", actor=user, new=level.value)
    session.commit()
    return {"level": level.value, "sent": True}


@router.get("/collections/summary", response_model=CollectionsSummaryRead, summary="Pronosticated income and 4-color delinquency buckets (VG3, FR-20, FR-27)")
def collections_summary(
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    today = date.today()
    contracts = session.exec(
        select(Contract).where(Contract.status == ContractState.ACTIVE)
    ).all()

    pronosticated_income: dict[str, Decimal] = {}
    receivable: dict[str, Decimal] = {}
    bucket_totals: dict[DelinquencyLevel, tuple[int, Decimal]] = {level: (0, Decimal("0")) for level in DelinquencyLevel}

    for contract in contracts:
        installments = _executable_installments(session, contract.id)
        due_this_month = sum(
            (item.amount for item in installments if item.due_date.year == today.year and item.due_date.month == today.month),
            Decimal("0"),
        )
        pronosticated_income[contract.currency] = money(pronosticated_income.get(contract.currency, Decimal("0")) + due_this_month)
        receivable[contract.currency] = money(receivable.get(contract.currency, Decimal("0")) + contract.outstanding_balance)
        level = delinquency_level(installments, today)
        count, total = bucket_totals[level]
        bucket_totals[level] = (count + 1, money(total + contract.outstanding_balance))

    return CollectionsSummaryRead(
        computed_at=_now(),
        pronosticated_income_by_currency=pronosticated_income,
        receivable_by_currency=receivable,
        delinquency_buckets=[
            DelinquencyBucket(level=level, count=count, outstanding_total=total)
            for level, (count, total) in bucket_totals.items()
        ],
    )


@router.post("/contracts/{contract_id}/resolution", summary="Client chooses the end-of-contract branch")
def choose_resolution(
    contract_id: int,
    payload: ResolutionCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.CLIENT))],
):
    """FR-21, AC-6.1/6.4: exactly one of two mutually exclusive branches; PURCHASE requires
    the outstanding balance to be fully settled."""
    contract = _contract_for_client(session, contract_id, user)
    if contract.status != ContractState.ACTIVE:
        raise HTTPException(status_code=409, detail="Only an ACTIVE contract can be resolved")
    if contract.resolution_choice:
        raise HTTPException(status_code=409, detail="A resolution branch was already chosen for this contract")
    if payload.choice == ResolutionChoice.PURCHASE and contract.outstanding_balance != Decimal("0"):
        raise HTTPException(status_code=409, detail="All remaining installments must be paid before exercising the purchase option")
    contract.resolution_choice = payload.choice
    audit(session, entity_type="contract", entity_id=contract.id, action="RESOLUTION_CHOSEN", actor=user, new=payload.choice.value)
    session.commit()
    session.refresh(contract)
    return {"contract_id": contract.id, "choice": contract.resolution_choice.value}


@router.post("/contracts/{contract_id}/resolution/process", summary="Leasing company processes the chosen branch, closing the contract (VG4)")
def process_resolution(
    contract_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != ContractState.ACTIVE:
        raise HTTPException(status_code=409, detail="Only an ACTIVE contract can be closed")
    if not contract.resolution_choice:
        raise HTTPException(status_code=409, detail="The client has not chosen a resolution branch yet")
    previous = contract.status
    contract.status = (
        ContractState.COMPLETED_PURCHASED if contract.resolution_choice == ResolutionChoice.PURCHASE
        else ContractState.COMPLETED_RETURNED
    )
    contract.resolved_at = _now()
    audit(session, entity_type="contract", entity_id=contract.id, action="RESOLUTION_PROCESSED", actor=user, previous=previous.value, new=contract.status.value)
    session.commit()
    session.refresh(contract)
    return {"contract_id": contract.id, "status": contract.status.value}
