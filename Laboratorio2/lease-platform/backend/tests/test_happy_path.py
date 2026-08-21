from __future__ import annotations

from decimal import Decimal

from conftest import auth, complete_dossier, create_request, external_approve, signed_simulation, token_for


def test_phase_one_happy_path(client):
    client_token = token_for(client, 1)
    broker_token = token_for(client, 3)
    leasing_token = token_for(client, 2)

    application = create_request(client, client_token)
    duplicate = create_request(client, client_token)
    assert duplicate["id"] == application["id"]
    complete_dossier(client, client_token, application["id"])

    response = client.post(f"/api/requests/{application['id']}/negotiation", headers=auth(broker_token))
    assert response.status_code == 200
    negotiation = response.json()
    response = client.post(
        f"/api/negotiations/{negotiation['id']}/meetings",
        headers=auth(broker_token),
        json={"scheduled_for": "2027-01-15T15:00:00Z"},
    )
    meeting = response.json()
    assert meeting["state"] == "PROPOSED"
    response = client.post(
        f"/api/negotiations/{negotiation['id']}/meetings/{meeting['id']}/response",
        headers=auth(client_token),
        json={"action": "ACCEPTED", "note": "Explicit client response"},
    )
    assert response.json()["state"] == "ACCEPTED"
    response = client.post(
        f"/api/negotiations/{negotiation['id']}/documents",
        headers=auth(broker_token),
        data={"summary": "Complete shared leasing contract", "structured_details": '{"term":12}'},
        files={"file": ("contract.pdf", b"%PDF-1.4 contract", "application/pdf")},
    )
    assert response.status_code == 200
    shared_document = response.json()
    response = client.get(
        f"/api/negotiations/{negotiation['id']}/documents/{shared_document['id']}/download",
        headers=auth(client_token),
    )
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 contract"

    outcome = external_approve(client, application["id"])
    assert outcome["status"] == "APPROVED"
    simulation = signed_simulation(client, client_token, application["id"])
    assert simulation["accepted"] is True
    assert len(simulation["signature_hash"]) == 64
    assert sum(Decimal(item["principal"]) for item in simulation["installments"]) == Decimal(application["requested_amount"])

    response = client.post(
        f"/api/requests/{application['id']}/activate",
        headers=auth(leasing_token),
        json={"exchange_rate": 1},
    )
    assert response.status_code == 200, response.text
    contract = response.json()
    assert contract["status"] == "ACTIVE"
    assert contract["currency"] == "PEN"
    assert contract["schedule"]["signature_hash"] == simulation["signature_hash"]

    response = client.post(
        f"/api/contracts/{contract['id']}/reception-status",
        headers=auth(client_token),
        json={"status": "CONFIRMED", "note": "Status only"},
    )
    assert response.json()["reception_status"] == "CONFIRMED"

    schema = client.get("/openapi.json").json()
    assert "/docs" not in schema["paths"]
    paths = " ".join(schema["paths"])
    assert all(term not in paths for term in ("provider", "procurement", "catalog", "logistics"))
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_broker_cannot_record_outcome_or_read_contracts(client):
    broker_token = token_for(client, 3)
    assert client.get("/api/requests", headers=auth(broker_token)).status_code == 403
    assert client.get("/api/contracts", headers=auth(broker_token)).status_code == 403
    assert client.post(
        "/api/integrations/risk-outcomes",
        headers=auth(broker_token),
        json={},
    ).status_code in {401, 422}
    audit_token = token_for(client, 2)
    entries = client.get("/api/audit", headers=auth(audit_token)).json()
    assert any(entry["action"] == "UNAUTHORIZED_ACCESS_DENIED" for entry in entries)
