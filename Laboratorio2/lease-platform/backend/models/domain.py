from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(StrEnum):
    CLIENT = "CLIENT"
    LEASING = "LEASING"
    BROKER = "BROKER"


class ApplicationStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    SCORING_UNAVAILABLE = "SCORING_UNAVAILABLE"
    APPROVED = "APPROVED"
    CONDITIONED = "CONDITIONED"
    REJECTED = "REJECTED"


class DecisionOutcome(StrEnum):
    APPROVED = "APPROVED"
    CONDITIONED = "CONDITIONED"
    REJECTED = "REJECTED"


class NegotiationState(StrEnum):
    OPEN = "OPEN"
    PROPOSED = "PROPOSED"
    STALLED = "STALLED"
    CLOSED = "CLOSED"


class MeetingState(StrEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RESCHEDULED = "RESCHEDULED"


class ContractState(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED_PURCHASED = "COMPLETED_PURCHASED"
    COMPLETED_RETURNED = "COMPLETED_RETURNED"


class DelinquencyLevel(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


class ResolutionChoice(StrEnum):
    PURCHASE = "PURCHASE"
    RETURN = "RETURN"


class ReconciliationStatus(StrEnum):
    MATCHED = "MATCHED"
    RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"


class ReceptionState(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    organization: str
    role: Role


class DemoSession(SQLModel, table=True):
    __tablename__ = "demo_sessions"
    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class Application(SQLModel, table=True):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("intent_key", name="uq_application_intent"),)
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    ruc: str = Field(index=True, min_length=11, max_length=11)
    machinery_type: str
    requested_term_months: int
    requested_amount: Decimal = Field(max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    expected_settlement_date: date
    intent_key: str = Field(index=True)
    status: ApplicationStatus = Field(default=ApplicationStatus.SUBMITTED, index=True)
    bureau_score: int | None = None
    bureau_attempts: int = 0
    pending_outcome: DecisionOutcome | None = None
    approved_limit: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    approved_term_months: int | None = None
    annual_interest_rate: Decimal | None = Field(default=None, max_digits=7, decimal_places=4)
    decision_reason_code: str | None = None
    decision_reason_text: str | None = None
    decision_received_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CreditDocument(SQLModel, table=True):
    __tablename__ = "credit_documents"
    __table_args__ = (UniqueConstraint("application_id", "kind", name="uq_credit_document_kind"),)
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    kind: str
    original_name: str
    stored_name: str | None = None
    mime_type: str
    size_bytes: int
    quarantined: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class BrokerAssignment(SQLModel, table=True):
    __tablename__ = "broker_assignments"
    __table_args__ = (UniqueConstraint("application_id", name="uq_broker_assignment_application"),)
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    broker_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class DecisionAttestation(SQLModel, table=True):
    __tablename__ = "decision_attestations"
    __table_args__ = (UniqueConstraint("application_id", "user_id", name="uq_decision_attestation"),)
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class AuditEntry(SQLModel, table=True):
    __tablename__ = "audit_entries"
    id: int | None = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True)
    entity_id: str = Field(index=True)
    actor_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    organization: str
    action: str
    previous_value: str | None = None
    new_value: str | None = None
    created_at: datetime = Field(default_factory=utcnow, index=True)


class InboxMessage(SQLModel, table=True):
    __tablename__ = "inbox_messages"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    subject: str
    body: str
    delivery_status: str = "DELIVERED_IN_APP"
    created_at: datetime = Field(default_factory=utcnow)


class Negotiation(SQLModel, table=True):
    __tablename__ = "negotiations"
    __table_args__ = (UniqueConstraint("application_id", name="uq_negotiation_application"),)
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    broker_id: int = Field(foreign_key="users.id", index=True)
    state: NegotiationState = Field(default=NegotiationState.OPEN, index=True)
    proposed_dates_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Meeting(SQLModel, table=True):
    __tablename__ = "meetings"
    id: int | None = Field(default=None, primary_key=True)
    negotiation_id: int = Field(foreign_key="negotiations.id", index=True)
    proposed_by: int = Field(foreign_key="users.id")
    scheduled_for: datetime
    state: MeetingState = Field(default=MeetingState.PROPOSED)
    response_by: int | None = Field(default=None, foreign_key="users.id")
    response_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class DealProposal(SQLModel, table=True):
    __tablename__ = "deal_proposals"
    id: int | None = Field(default=None, primary_key=True)
    negotiation_id: int = Field(foreign_key="negotiations.id", index=True)
    author_id: int = Field(foreign_key="users.id")
    text: str
    created_at: datetime = Field(default_factory=utcnow)


class GuidanceMessage(SQLModel, table=True):
    __tablename__ = "guidance_messages"
    id: int | None = Field(default=None, primary_key=True)
    negotiation_id: int = Field(foreign_key="negotiations.id", index=True)
    author_id: int = Field(foreign_key="users.id")
    recipients: str
    body: str
    delivery_status: str = "DELIVERED_IN_APP"
    created_at: datetime = Field(default_factory=utcnow)


class NegotiationDocument(SQLModel, table=True):
    __tablename__ = "negotiation_documents"
    id: int | None = Field(default=None, primary_key=True)
    negotiation_id: int = Field(foreign_key="negotiations.id", index=True)
    uploaded_by: int = Field(foreign_key="users.id")
    original_name: str
    stored_name: str
    mime_type: str
    size_bytes: int
    summary: str
    structured_details: str
    created_at: datetime = Field(default_factory=utcnow)


class ScheduleSimulation(SQLModel, table=True):
    __tablename__ = "schedule_simulations"
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    grace_months: int = 0
    frequency: str = "MONTHLY"
    balloon_percent: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    annual_interest_rate: Decimal = Field(max_digits=7, decimal_places=4)
    total_interest: Decimal = Field(max_digits=14, decimal_places=2)
    total_cost: Decimal = Field(max_digits=14, decimal_places=2)
    capital_outlay_avoided: Decimal = Field(max_digits=14, decimal_places=2)
    accepted: bool = False
    signed_by: int | None = Field(default=None, foreign_key="users.id")
    signed_at: datetime | None = None
    signature_hash: str | None = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)


class Installment(SQLModel, table=True):
    __tablename__ = "installments"
    __table_args__ = (UniqueConstraint("simulation_id", "contract_id", "number", name="uq_installment_number"),)
    id: int | None = Field(default=None, primary_key=True)
    simulation_id: int = Field(foreign_key="schedule_simulations.id", index=True)
    contract_id: int | None = Field(default=None, foreign_key="contracts.id", index=True)
    number: int
    due_date: date
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    principal: Decimal = Field(max_digits=14, decimal_places=2)
    interest: Decimal = Field(max_digits=14, decimal_places=2)
    cash_flow_gap_days: int
    paid_amount: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)


class Contract(SQLModel, table=True):
    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_contract_application"),
        UniqueConstraint("simulation_id", name="uq_contract_simulation"),
    )
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    simulation_id: int = Field(foreign_key="schedule_simulations.id")
    owner_id: int = Field(foreign_key="users.id", index=True)
    status: ContractState = Field(default=ContractState.PENDING, index=True)
    currency: str
    locked_exchange_rate: Decimal = Field(max_digits=12, decimal_places=6)
    outstanding_balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    reception_status: ReceptionState = Field(default=ReceptionState.PENDING)
    reception_note: str | None = None
    resolution_choice: ResolutionChoice | None = None
    resolved_at: datetime | None = None
    activated_at: datetime = Field(default_factory=utcnow)


class ExchangeRateEntry(SQLModel, table=True):
    __tablename__ = "exchange_rate_entries"
    id: int | None = Field(default=None, primary_key=True)
    contract_id: int = Field(foreign_key="contracts.id", index=True)
    rate: Decimal = Field(max_digits=12, decimal_places=6)
    effective_at: datetime = Field(default_factory=utcnow)
    reason: str = "Initial contract activation"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("contract_id", "bank_reference", name="uq_payment_contract_bank_reference"),)
    id: int | None = Field(default=None, primary_key=True)
    contract_id: int = Field(foreign_key="contracts.id", index=True)
    bank_reference: str = Field(index=True)
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    currency: str
    registered_by: int = Field(foreign_key="users.id")
    reconciliation_status: ReconciliationStatus = Field(default=ReconciliationStatus.MATCHED)
    created_at: datetime = Field(default_factory=utcnow)
