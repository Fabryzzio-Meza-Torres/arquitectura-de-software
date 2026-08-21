from __future__ import annotations

import calendar
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlmodel import Session, select

from models.domain import Application, Installment, ScheduleSimulation
from schemas.api import SimulationCreate


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def build_simulation(
    session: Session,
    application: Application,
    payload: SimulationCreate,
) -> ScheduleSimulation:
    existing = session.exec(
        select(ScheduleSimulation).where(ScheduleSimulation.application_id == application.id)
    ).all()
    if len(existing) >= 3:
        raise HTTPException(status_code=409, detail="This application already has the maximum of 3 simulations")
    term = min(application.requested_term_months, application.approved_term_months or application.requested_term_months)
    installment_count = term - payload.grace_months
    if installment_count < 1:
        raise HTTPException(status_code=422, detail="Grace period must leave at least one installment")
    first_due = add_months(date.today(), payload.grace_months + 1)
    if add_months(date.today(), payload.grace_months) > application.expected_settlement_date:
        raise HTTPException(status_code=422, detail="Grace period extends past the project settlement date")
    if payload.frequency == "MILESTONE":
        dates = payload.milestone_dates or []
        if len(dates) != installment_count:
            raise HTTPException(status_code=422, detail=f"MILESTONE frequency requires exactly {installment_count} dates")
        if dates != sorted(dates) or dates[0] < first_due:
            raise HTTPException(status_code=422, detail="Milestone dates must be sorted and cannot precede the post-grace first due date")
        due_dates = dates
    else:
        due_dates = [add_months(date.today(), payload.grace_months + number) for number in range(1, installment_count + 1)]

    principal = money(application.requested_amount)
    annual_rate = Decimal(application.annual_interest_rate or 0)
    monthly_rate = annual_rate / Decimal("1200")
    balloon = money(principal * Decimal(payload.balloon_percent) / Decimal("100"))
    amortizing_principal = principal - balloon
    if monthly_rate == 0:
        regular_payment = money(amortizing_principal / installment_count)
    else:
        factor = (Decimal("1") + monthly_rate) ** installment_count
        regular_payment = money(amortizing_principal * monthly_rate * factor / (factor - Decimal("1")))

    balance = amortizing_principal
    rows: list[tuple[Decimal, Decimal, Decimal]] = []
    for number in range(1, installment_count + 1):
        interest = money(balance * monthly_rate)
        principal_part = money(regular_payment - interest)
        if number == installment_count:
            principal_part = money(balance)
        amount = money(principal_part + interest)
        balance = money(balance - principal_part)
        if number == installment_count:
            principal_part = money(principal_part + balloon)
            amount = money(amount + balloon)
        rows.append((amount, principal_part, interest))

    total_cost = money(sum((row[0] for row in rows), Decimal("0")))
    total_interest = money(total_cost - principal)
    current_period_due = sum((row[0] for row, due in zip(rows, due_dates, strict=True) if due <= date.today()), Decimal("0"))
    simulation = ScheduleSimulation(
        application_id=application.id,
        grace_months=payload.grace_months,
        frequency=payload.frequency,
        balloon_percent=payload.balloon_percent,
        annual_interest_rate=annual_rate,
        total_interest=total_interest,
        total_cost=total_cost,
        capital_outlay_avoided=money(max(Decimal("0"), principal - current_period_due)),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    session.add(simulation)
    session.flush()
    for index, (due, row) in enumerate(zip(due_dates, rows, strict=True), start=1):
        amount, principal_part, interest = row
        session.add(Installment(
            simulation_id=simulation.id,
            number=index,
            due_date=due,
            amount=amount,
            principal=principal_part,
            interest=interest,
            cash_flow_gap_days=(application.expected_settlement_date - due).days,
        ))
    return simulation


def signature_for(session: Session, simulation: ScheduleSimulation, signer: str, signed_at: datetime) -> str:
    installments = session.exec(
        select(Installment).where(Installment.simulation_id == simulation.id).order_by(Installment.number)
    ).all()
    canonical = {
        "simulation_id": simulation.id,
        "signer": signer,
        "signed_at": signed_at.isoformat(),
        "installments": [
            {"number": item.number, "due_date": item.due_date.isoformat(), "amount": str(item.amount)}
            for item in installments
        ],
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
