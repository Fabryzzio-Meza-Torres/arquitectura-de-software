from __future__ import annotations

from datetime import date
from decimal import Decimal

from models.domain import DelinquencyLevel, Installment


def delinquency_level(installments: list[Installment], today: date) -> DelinquencyLevel:
    """FR-19 / KPD-9: classify by days elapsed since the oldest missed due date.
    0 -> GREEN, 1-30 -> YELLOW, 31-60 -> ORANGE, 61+ -> RED.

    # ponytail: computed on read, not a daily ACID-guarded recompute (NFR-17). Fine at
    # Phase 1 volume; upgrade to a per-contract transactional daily job when payments and
    # concurrent recompute actually collide (Phase 2).
    """
    oldest_unpaid = min(
        (installment.due_date for installment in installments
         if installment.paid_amount < installment.amount and installment.due_date < today),
        default=None,
    )
    if oldest_unpaid is None:
        return DelinquencyLevel.GREEN
    days_late = (today - oldest_unpaid).days
    if days_late <= 30:
        return DelinquencyLevel.YELLOW
    if days_late <= 60:
        return DelinquencyLevel.ORANGE
    return DelinquencyLevel.RED


def allocate_payment(installments: list[Installment], amount: Decimal) -> tuple[list[tuple[Installment, Decimal]], Decimal]:
    """FR-11: apply `amount` oldest-first across unpaid installments.
    Returns (allocations, remainder) without mutating the installments; the caller commits."""
    remaining = amount
    allocations: list[tuple[Installment, Decimal]] = []
    unpaid = sorted(
        (installment for installment in installments if installment.paid_amount < installment.amount),
        key=lambda installment: (installment.due_date, installment.number),
    )
    for installment in unpaid:
        if remaining <= 0:
            break
        due = installment.amount - installment.paid_amount
        applied = min(due, remaining)
        allocations.append((installment, applied))
        remaining -= applied
    return allocations, remaining
