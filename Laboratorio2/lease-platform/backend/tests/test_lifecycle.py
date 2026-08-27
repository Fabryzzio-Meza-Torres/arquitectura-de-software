from __future__ import annotations

from conftest import (
    activated_pending_contract,
    auth,
    complete_dossier,
    confirm_reception,
    create_request,
    external_approve,
    token_for,
)


def _ready_contract(client, client_token, leasing_token):
    application = create_request(client, client_token)
    complete_dossier(client, client_token, application["id"])
    external_approve(client, application["id"])
    return activated_pending_contract(client, client_token, leasing_token, application["id"])


def test_contract_starts_pending_and_activates_on_confirmed_reception(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    contract = _ready_contract(client, client_token, leasing_token)
    assert contract["status"] == "PENDING"
    assert contract["installments"] == []

    activated = confirm_reception(client, client_token, contract["id"])
    assert activated["status"] == "ACTIVE"
    assert len(activated["installments"]) > 0
    assert float(activated["outstanding_balance"]) > 0


def test_rejected_reception_stays_pending_and_notifies_leasing(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    contract = _ready_contract(client, client_token, leasing_token)

    response = client.post(
        f"/api/contracts/{contract['id']}/reception-status",
        headers=auth(client_token),
        json={"status": "REJECTED", "note": "Maquinaria dañada en tránsito"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["reception_status"] == "REJECTED"
    assert body["installments"] == []

    inbox = client.get("/api/inbox", headers=auth(leasing_token)).json()
    assert any("recepción rechazada" in item["subject"] for item in inbox)


def test_payment_is_idempotent_and_flags_mismatch(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    contract = _ready_contract(client, client_token, leasing_token)
    contract = confirm_reception(client, client_token, contract["id"])
    first_due = contract["installments"][0]

    mismatch = client.post(
        f"/api/contracts/{contract['id']}/payments",
        headers=auth(client_token),
        json={"bank_reference": "REF-1", "amount": float(first_due["amount"]) - 1},
    )
    assert mismatch.status_code == 200
    assert mismatch.json()["reconciliation_status"] == "RECONCILIATION_MISMATCH"

    replay = client.post(
        f"/api/contracts/{contract['id']}/payments",
        headers=auth(client_token),
        json={"bank_reference": "REF-1", "amount": float(first_due["amount"]) - 1},
    )
    assert replay.json()["id"] == mismatch.json()["id"]


def test_purchase_requires_zero_balance_and_branches_are_mutually_exclusive(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    contract = _ready_contract(client, client_token, leasing_token)
    contract = confirm_reception(client, client_token, contract["id"])

    denied = client.post(
        f"/api/contracts/{contract['id']}/resolution",
        headers=auth(client_token),
        json={"choice": "PURCHASE"},
    )
    assert denied.status_code == 409

    for index, installment in enumerate(contract["installments"]):
        client.post(
            f"/api/contracts/{contract['id']}/payments",
            headers=auth(client_token),
            json={"bank_reference": f"REF-PAYOFF-{index}", "amount": installment["amount"]},
        )

    chosen = client.post(
        f"/api/contracts/{contract['id']}/resolution",
        headers=auth(client_token),
        json={"choice": "PURCHASE"},
    )
    assert chosen.status_code == 200

    second_choice = client.post(
        f"/api/contracts/{contract['id']}/resolution",
        headers=auth(client_token),
        json={"choice": "RETURN"},
    )
    assert second_choice.status_code == 409

    processed = client.post(f"/api/contracts/{contract['id']}/resolution/process", headers=auth(leasing_token))
    assert processed.status_code == 200
    assert processed.json()["status"] == "COMPLETED_PURCHASED"
