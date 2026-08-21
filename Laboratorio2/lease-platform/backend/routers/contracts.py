from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, select

from database import get_session
from models.domain import (
    Application,
    ApplicationStatus,
    Contract,
    ContractState,
    ExchangeRateEntry,
    Installment,
    ReceptionState,
    Role,
    ScheduleSimulation,
    User,
)
from schemas.api import (
    ContractActivate,
    ContractRead,
    InstallmentRead,
    ReceptionUpdate,
    SimulationAccept,
    SimulationCreate,
    SimulationRead,
)
from services.audit import audit
from services.auth import CurrentUser, require_roles
from services.schedule import build_simulation, signature_for


router = APIRouter(prefix="/api", tags=["Schedules and contracts"])
SessionDep = Annotated[Session, Depends(get_session)]


def _simulation_read(session: Session, simulation: ScheduleSimulation) -> SimulationRead:
    installments = session.exec(
        select(Installment).where(Installment.simulation_id == simulation.id).order_by(Installment.number)
    ).all()
    return SimulationRead(**SimulationRead.model_validate(simulation).model_dump(exclude={"installments"}), installments=installments)


def _contract_read(session: Session, contract: Contract) -> ContractRead:
    simulation = session.get(ScheduleSimulation, contract.simulation_id)
    return ContractRead(
        **ContractRead.model_validate(contract).model_dump(exclude={"schedule"}),
        schedule=_simulation_read(session, simulation) if simulation else None,
    )


def _application_for_user(session: Session, application_id: int, user: User) -> Application:
    application = session.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == Role.CLIENT and application.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return application


@router.post("/requests/{application_id}/simulations", response_model=SimulationRead, summary="Generate one of up to three schedule simulations")
def create_simulation(application_id: int, payload: SimulationCreate, session: SessionDep, user: CurrentUser):
    application = _application_for_user(session, application_id, user)
    if user.role != Role.CLIENT:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if application.status != ApplicationStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Only APPROVED applications can be simulated")
    simulation = build_simulation(session, application, payload)
    session.flush()
    audit(session, entity_type="schedule_simulation", entity_id=simulation.id, action="GENERATED", actor=user, new=simulation.frequency)
    session.commit()
    session.refresh(simulation)
    return _simulation_read(session, simulation)


@router.get("/requests/{application_id}/simulations", response_model=list[SimulationRead])
def list_simulations(application_id: int, session: SessionDep, user: CurrentUser):
    _application_for_user(session, application_id, user)
    simulations = session.exec(select(ScheduleSimulation).where(
        ScheduleSimulation.application_id == application_id
    ).order_by(ScheduleSimulation.created_at)).all()
    return [_simulation_read(session, item) for item in simulations]


@router.post("/simulations/{simulation_id}/accept", response_model=SimulationRead, summary="Accept and sign a simulation snapshot")
def accept_simulation(simulation_id: int, payload: SimulationAccept, session: SessionDep, user: CurrentUser):
    if user.role != Role.CLIENT:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    simulation = session.get(ScheduleSimulation, simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    application = session.get(Application, simulation.application_id)
    if not application or application.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if simulation.accepted:
        return _simulation_read(session, simulation)
    other = session.exec(select(ScheduleSimulation).where(
        ScheduleSimulation.application_id == application.id,
        ScheduleSimulation.accepted == True,  # noqa: E712
    )).first()
    if other:
        raise HTTPException(status_code=409, detail="Another simulation is already accepted")
    signed_at = datetime.now(timezone.utc)
    simulation.accepted = True
    simulation.signed_by = user.id
    simulation.signed_at = signed_at
    simulation.signature_hash = signature_for(session, simulation, payload.signer_confirmation, signed_at)
    audit(session, entity_type="schedule_simulation", entity_id=simulation.id, action="DIGITALLY_SIGNED", actor=user, new=simulation.signature_hash)
    session.commit()
    session.refresh(simulation)
    return _simulation_read(session, simulation)


@router.post("/requests/{application_id}/activate", response_model=ContractRead, summary="Atomically activate one signed contract")
def activate_contract(
    application_id: int,
    payload: ContractActivate,
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(Role.LEASING))],
):
    application = _application_for_user(session, application_id, user)
    if application.status != ApplicationStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Application must be APPROVED by the external evaluator")
    if application.currency == "PEN" and payload.exchange_rate != Decimal("1"):
        raise HTTPException(status_code=422, detail="PEN contracts use exchange rate 1.000000")
    simulation = session.exec(select(ScheduleSimulation).where(
        ScheduleSimulation.application_id == application_id,
        ScheduleSimulation.accepted == True,  # noqa: E712
    )).first()
    if not simulation or not simulation.signature_hash:
        raise HTTPException(status_code=409, detail="An accepted and digitally signed schedule is required")
    existing = session.exec(select(Contract).where(Contract.application_id == application_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Contract and schedule already activated for this application")
    contract = Contract(
        application_id=application.id,
        simulation_id=simulation.id,
        owner_id=application.owner_id,
        status=ContractState.ACTIVE,
        currency=application.currency,
        locked_exchange_rate=payload.exchange_rate,
        outstanding_balance=simulation.total_cost,
    )
    try:
        session.add(contract)
        session.flush()
        session.add(ExchangeRateEntry(contract_id=contract.id, rate=payload.exchange_rate))
        audit(session, entity_type="contract", entity_id=contract.id, action="ACTIVATED", actor=user, new=f"{contract.currency}@{contract.locked_exchange_rate}")
        session.commit()
    except (IntegrityError, OperationalError) as exc:
        session.rollback()
        existing = session.exec(select(Contract).where(Contract.application_id == application_id)).first()
        if existing:
            raise HTTPException(status_code=409, detail="Concurrent activation rejected; contract already exists") from exc
        raise HTTPException(status_code=409, detail="Activation could not preserve serializable consistency") from exc
    session.refresh(contract)
    return _contract_read(session, contract)


@router.get("/contracts", response_model=list[ContractRead], summary="List visible active contracts")
def list_contracts(session: SessionDep, user: CurrentUser):
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    statement = select(Contract).order_by(Contract.activated_at.desc())
    if user.role == Role.CLIENT:
        statement = statement.where(Contract.owner_id == user.id)
    return [_contract_read(session, contract) for contract in session.exec(statement).all()]


@router.get("/contracts/{contract_id}", response_model=ContractRead)
def read_contract(contract_id: int, session: SessionDep, user: CurrentUser):
    if user.role == Role.BROKER:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if user.role == Role.CLIENT and contract.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return _contract_read(session, contract)


@router.post("/contracts/{contract_id}/reception-status", response_model=ContractRead, summary="Record reception as a status only")
def update_reception(contract_id: int, payload: ReceptionUpdate, session: SessionDep, user: CurrentUser):
    if user.role != Role.CLIENT:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    previous = contract.reception_status
    contract.reception_status = ReceptionState(payload.status)
    audit(session, entity_type="contract", entity_id=contract.id, action="RECEPTION_STATUS_RECORDED", actor=user, previous=previous.value, new=contract.reception_status.value)
    session.commit()
    session.refresh(contract)
    return _contract_read(session, contract)

