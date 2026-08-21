from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.domain import (
    ApplicationStatus,
    ContractState,
    DecisionOutcome,
    MeetingState,
    NegotiationState,
    ReceptionState,
    Role,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DemoUserRead(ORMModel):
    id: int
    name: str
    organization: str
    role: Role


class DemoSessionCreate(BaseModel):
    user_id: int = Field(examples=[1])


class DemoSessionRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: DemoUserRead


class ApplicationCreate(BaseModel):
    ruc: str = Field(min_length=11, max_length=11, examples=["20123456789"])
    machinery_type: str = Field(min_length=2, max_length=120, examples=["Excavadora hidráulica"])
    requested_term_months: int = Field(ge=1, le=120, examples=[12])
    requested_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2, examples=[250000])
    currency: Literal["PEN", "USD"] = Field(examples=["PEN"])
    expected_settlement_date: date

    @field_validator("ruc")
    @classmethod
    def valid_ruc(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("RUC must contain exactly 11 digits")
        return value


class ApplicationRead(ORMModel):
    id: int
    owner_id: int
    ruc: str
    machinery_type: str
    requested_term_months: int
    requested_amount: Decimal
    currency: str
    expected_settlement_date: date
    status: ApplicationStatus
    bureau_score: int | None
    bureau_attempts: int
    pending_outcome: DecisionOutcome | None
    approved_limit: Decimal | None
    approved_term_months: int | None
    annual_interest_rate: Decimal | None
    decision_reason_code: str | None
    decision_reason_text: str | None
    decision_received_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationSubmit(BaseModel):
    bureau_scenario: Literal["SUCCESS", "TIMEOUT"] = "SUCCESS"
    bureau_score: int | None = Field(default=720, ge=0, le=999)


class CreditDocumentRead(ORMModel):
    id: int
    application_id: int
    kind: str
    original_name: str
    mime_type: str
    size_bytes: int
    quarantined: bool
    created_at: datetime


class RiskOutcomeCreate(BaseModel):
    application_id: int
    outcome: DecisionOutcome
    reason_code: str = Field(min_length=2, max_length=80, examples=["POLICY_APPROVED"])
    reason_text: str = Field(min_length=3, max_length=500)
    approved_limit: Decimal | None = Field(default=None, gt=0)
    approved_term_months: int | None = Field(default=None, ge=1, le=120)
    annual_interest_rate: Decimal | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_outcome_fields(self):
        if self.outcome == DecisionOutcome.APPROVED:
            missing = [
                name for name, value in (
                    ("approved_limit", self.approved_limit),
                    ("approved_term_months", self.approved_term_months),
                    ("annual_interest_rate", self.annual_interest_rate),
                ) if value is None
            ]
            if missing:
                raise ValueError(f"Approved outcome requires: {', '.join(missing)}")
        if self.outcome in {DecisionOutcome.REJECTED, DecisionOutcome.CONDITIONED} and len(self.reason_text.strip()) < 20:
            raise ValueError("Conditioned or rejected outcomes require at least 20 characters of justification")
        return self


class DecisionAttestationRead(ORMModel):
    id: int
    application_id: int
    user_id: int
    created_at: datetime


class BrokerAssignmentRead(BaseModel):
    application_id: int
    machinery_type: str
    currency: str
    negotiation_id: int | None = None


class NegotiationCreate(BaseModel):
    application_id: int


class MeetingCreate(BaseModel):
    scheduled_for: datetime


class MeetingResponseCreate(BaseModel):
    action: Literal["ACCEPTED", "REJECTED", "RESCHEDULED"]
    note: str | None = Field(default=None, max_length=500)
    new_date: datetime | None = None

    @model_validator(mode="after")
    def reschedule_requires_date(self):
        if self.action == "RESCHEDULED" and self.new_date is None:
            raise ValueError("new_date is required when action is RESCHEDULED")
        return self


class DealProposalCreate(BaseModel):
    text: str = Field(min_length=10, max_length=2000)


class GuidanceMessageCreate(BaseModel):
    recipients: Literal["CLIENT", "LEASING", "BOTH"]
    body: str = Field(min_length=2, max_length=2000)
    simulate_delivery_failure: bool = False


class MeetingRead(ORMModel):
    id: int
    negotiation_id: int
    proposed_by: int
    scheduled_for: datetime
    state: MeetingState
    response_by: int | None
    response_note: str | None
    created_at: datetime


class DealProposalRead(ORMModel):
    id: int
    negotiation_id: int
    author_id: int
    text: str
    created_at: datetime


class GuidanceMessageRead(ORMModel):
    id: int
    negotiation_id: int
    author_id: int
    recipients: str
    body: str
    delivery_status: str
    created_at: datetime


class NegotiationDocumentRead(ORMModel):
    id: int
    negotiation_id: int
    uploaded_by: int
    original_name: str
    mime_type: str
    size_bytes: int
    summary: str
    structured_details: str
    created_at: datetime


class NegotiationRead(ORMModel):
    id: int
    application_id: int
    broker_id: int
    state: NegotiationState
    proposed_dates_count: int
    created_at: datetime
    updated_at: datetime
    meetings: list[MeetingRead] = []
    proposals: list[DealProposalRead] = []
    messages: list[GuidanceMessageRead] = []
    documents: list[NegotiationDocumentRead] = []


class SimulationCreate(BaseModel):
    grace_months: int = Field(default=0, ge=0, le=6)
    frequency: Literal["MONTHLY", "MILESTONE"] = "MONTHLY"
    balloon_percent: Decimal = Field(default=Decimal("0"), ge=0, le=40)
    milestone_dates: list[date] | None = None

    @model_validator(mode="after")
    def milestones_required(self):
        if self.frequency == "MILESTONE" and not self.milestone_dates:
            raise ValueError("milestone_dates are required for MILESTONE frequency")
        return self


class InstallmentRead(ORMModel):
    id: int
    number: int
    due_date: date
    amount: Decimal
    principal: Decimal
    interest: Decimal
    cash_flow_gap_days: int


class SimulationRead(ORMModel):
    id: int
    application_id: int
    grace_months: int
    frequency: str
    balloon_percent: Decimal
    annual_interest_rate: Decimal
    total_interest: Decimal
    total_cost: Decimal
    capital_outlay_avoided: Decimal
    accepted: bool
    signed_by: int | None
    signed_at: datetime | None
    signature_hash: str | None
    expires_at: datetime
    created_at: datetime
    installments: list[InstallmentRead] = []


class SimulationAccept(BaseModel):
    signer_confirmation: str = Field(min_length=3, max_length=120, examples=["César — Head of Finance"])


class ContractActivate(BaseModel):
    exchange_rate: Decimal = Field(gt=0, max_digits=12, decimal_places=6, examples=[3.75])


class ReceptionUpdate(BaseModel):
    status: Literal["CONFIRMED", "REJECTED"]
    note: str | None = Field(default=None, max_length=500)


class ContractRead(ORMModel):
    id: int
    application_id: int
    simulation_id: int
    owner_id: int
    status: ContractState
    currency: str
    locked_exchange_rate: Decimal
    outstanding_balance: Decimal
    reception_status: ReceptionState
    activated_at: datetime
    schedule: SimulationRead | None = None


class InboxRead(ORMModel):
    id: int
    subject: str
    body: str
    delivery_status: str
    created_at: datetime


class AuditRead(ORMModel):
    id: int
    entity_type: str
    entity_id: str
    actor_id: int | None
    organization: str
    action: str
    previous_value: str | None
    new_value: str | None
    created_at: datetime
