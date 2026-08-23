from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from conftest import activated_pending_contract, auth, complete_dossier, confirm_reception, create_request, external_approve, token_for
from services.collections import allocate_payment, delinquency_level


class _Installment:
    def __init__(self, due_date, amount, paid_amount=Decimal("0")):
        self.due_date = due_date
        self.amount = amount
        self.paid_amount = paid_amount
        self.number = 1


def test_delinquency_level_boundaries():
    today = date(2027, 3, 1)
    assert delinquency_level([_Installment(today, Decimal("100"))], today) == "GREEN"
    assert delinquency_level([_Installment(today - timedelta(days=1), Decimal("100"))], today) == "YELLOW"
    assert delinquency_level([_Installment(today - timedelta(days=30), Decimal("100"))], today) == "YELLOW"
    assert delinquency_level([_Installment(today - timedelta(days=31), Decimal("100"))], today) == "ORANGE"
    assert delinquency_level([_Installment(today - timedelta(days=60), Decimal("100"))], today) == "ORANGE"
    assert delinquency_level([_Installment(today - timedelta(days=61), Decimal("100"))], today) == "RED"
    paid = _Installment(today - timedelta(days=90), Decimal("100"), paid_amount=Decimal("100"))
    assert delinquency_level([paid], today) == "GREEN"


def test_allocate_payment_applies_oldest_first():
    older = _Installment(date(2027, 1, 1), Decimal("100"))
    newer = _Installment(date(2027, 2, 1), Decimal("100"))
    newer.number = 2
    allocations, remainder = allocate_payment([newer, older], Decimal("150"))
    assert allocations[0][0] is older
    assert allocations[0][1] == Decimal("100")
    assert allocations[1][0] is newer
    assert allocations[1][1] == Decimal("50")
    assert remainder == Decimal("0")


def test_broker_cannot_read_collections_summary(client):
    broker_token = token_for(client, 3)
    response = client.get("/api/collections/summary", headers=auth(broker_token))
    assert response.status_code == 403


def test_collections_summary_excludes_closed_contracts(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    application = create_request(client, client_token)
    complete_dossier(client, client_token, application["id"])
    external_approve(client, application["id"])
    contract = activated_pending_contract(client, client_token, leasing_token, application["id"])
    contract = confirm_reception(client, client_token, contract["id"])

    summary = client.get("/api/collections/summary", headers=auth(leasing_token)).json()
    assert sum(bucket["count"] for bucket in summary["delinquency_buckets"]) == 1

    for index, installment in enumerate(contract["installments"]):
        client.post(
            f"/api/contracts/{contract['id']}/payments",
            headers=auth(client_token),
            json={"bank_reference": f"REF-CLOSE-{index}", "amount": installment["amount"]},
        )
    client.post(f"/api/contracts/{contract['id']}/resolution", headers=auth(client_token), json={"choice": "PURCHASE"})
    client.post(f"/api/contracts/{contract['id']}/resolution/process", headers=auth(leasing_token))

    summary_after = client.get("/api/collections/summary", headers=auth(leasing_token)).json()
    assert sum(bucket["count"] for bucket in summary_after["delinquency_buckets"]) == 0
