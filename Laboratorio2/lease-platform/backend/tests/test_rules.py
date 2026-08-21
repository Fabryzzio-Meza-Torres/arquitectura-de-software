from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text

from conftest import auth, complete_dossier, create_request, external_approve, signed_simulation, token_for
from database import engine


def test_validation_dossier_and_eicar(client):
    token = token_for(client, 1)
    response = client.post("/api/requests", headers=auth(token), json={
        "ruc": "ABC",
        "machinery_type": "X",
        "requested_term_months": 0,
        "requested_amount": 0,
        "currency": "EUR",
        "expected_settlement_date": "2027-10-10",
    })
    assert response.status_code == 422
    application = create_request(client, token)
    response = client.post(
        f"/api/requests/{application['id']}/documents",
        headers=auth(token),
        data={"kind": "BANK_STATEMENTS"},
        files={"file": ("infected.pdf", b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["quarantined"] is True
    response = client.post(
        f"/api/requests/{application['id']}/submit",
        headers=auth(token),
        json={"bureau_scenario": "SUCCESS", "bureau_score": 720},
    )
    assert response.status_code == 409
    assert "BANK_STATEMENTS" in response.text


def test_timeout_routes_to_manual_queue(client):
    token = token_for(client, 1)
    leasing = token_for(client, 2)
    application = create_request(client, token)
    for kind in ("BANK_STATEMENTS", "TAX_RETURN", "PROJECT_CONTRACT"):
        client.post(
            f"/api/requests/{application['id']}/documents", headers=auth(token), data={"kind": kind},
            files={"file": ("d.pdf", b"%PDF dossier", "application/pdf")},
        )
    response = client.post(
        f"/api/requests/{application['id']}/submit",
        headers=auth(token), json={"bureau_scenario": "TIMEOUT"},
    )
    assert response.json()["status"] == "SCORING_UNAVAILABLE"
    queue = client.get("/api/review-queue", headers=auth(leasing)).json()
    assert [item["id"] for item in queue] == [application["id"]]


def test_high_value_requires_two_distinct_attestations(client):
    client_token = token_for(client, 1)
    jp_token = token_for(client, 2)
    ana_token = token_for(client, 4)
    application = create_request(client, client_token, amount=600000)
    complete_dossier(client, client_token, application["id"])
    outcome = external_approve(client, application["id"], amount=600000)
    assert outcome["status"] == "IN_REVIEW"
    first = client.post(f"/api/requests/{application['id']}/decision-attestations", headers=auth(jp_token))
    assert first.status_code == 200
    assert client.post(f"/api/requests/{application['id']}/decision-attestations", headers=auth(jp_token)).status_code == 409
    second = client.post(f"/api/requests/{application['id']}/decision-attestations", headers=auth(ana_token))
    assert second.status_code == 200
    final = client.get(f"/api/requests/{application['id']}", headers=auth(client_token)).json()
    assert final["status"] == "APPROVED"


def test_three_simulation_limit_and_financial_immutability(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    application = create_request(client, client_token)
    complete_dossier(client, client_token, application["id"])
    external_approve(client, application["id"])
    simulations = []
    for grace in range(3):
        response = client.post(
            f"/api/requests/{application['id']}/simulations", headers=auth(client_token),
            json={"grace_months": grace, "frequency": "MONTHLY", "balloon_percent": 0},
        )
        assert response.status_code == 200
        simulations.append(response.json())
    assert client.post(
        f"/api/requests/{application['id']}/simulations", headers=auth(client_token),
        json={"grace_months": 3, "frequency": "MONTHLY", "balloon_percent": 0},
    ).status_code == 409
    client.post(
        f"/api/simulations/{simulations[0]['id']}/accept", headers=auth(client_token),
        json={"signer_confirmation": "César"},
    )
    contract = client.post(
        f"/api/requests/{application['id']}/activate", headers=auth(leasing_token), json={"exchange_rate": 1},
    ).json()
    with engine.begin() as connection:
        try:
            connection.execute(text("UPDATE contracts SET currency='USD' WHERE id=:id"), {"id": contract["id"]})
            raised = False
        except Exception as error:  # SQLite surfaces trigger as an integrity/database error.
            raised = "immutable" in str(error)
    assert raised


def test_concurrent_activation_creates_exactly_one_contract(client):
    client_token = token_for(client, 1)
    leasing_token = token_for(client, 2)
    application = create_request(client, client_token)
    complete_dossier(client, client_token, application["id"])
    external_approve(client, application["id"])
    signed_simulation(client, client_token, application["id"])

    def activate(_):
        response = client.post(
            f"/api/requests/{application['id']}/activate",
            headers=auth(leasing_token), json={"exchange_rate": 1},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=25) as executor:
        statuses = list(executor.map(activate, range(100)))
    assert statuses.count(200) == 1
    assert statuses.count(409) == 99
    contracts = client.get("/api/contracts", headers=auth(leasing_token)).json()
    assert len(contracts) == 1
