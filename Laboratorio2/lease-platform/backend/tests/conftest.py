from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from database import create_db_and_tables, engine
from main import app


@pytest.fixture()
def client():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    with TestClient(app) as test_client:
        yield test_client


def token_for(client: TestClient, user_id: int) -> str:
    response = client.post("/api/demo/session", json={"user_id": user_id})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_request(client: TestClient, token: str, *, amount: int = 250000, ruc: str = "20123456789") -> dict:
    response = client.post("/api/requests", headers=auth(token), json={
        "ruc": ruc,
        "machinery_type": "Excavadora hidráulica",
        "requested_term_months": 12,
        "requested_amount": amount,
        "currency": "PEN",
        "expected_settlement_date": "2027-12-20",
    })
    assert response.status_code == 200, response.text
    return response.json()


def complete_dossier(client: TestClient, token: str, application_id: int) -> None:
    for kind in ("BANK_STATEMENTS", "TAX_RETURN", "PROJECT_CONTRACT"):
        response = client.post(
            f"/api/requests/{application_id}/documents",
            headers=auth(token),
            data={"kind": kind},
            files={"file": (f"{kind}.pdf", b"%PDF-1.4 POC document", "application/pdf")},
        )
        assert response.status_code == 200, response.text
    response = client.post(
        f"/api/requests/{application_id}/submit",
        headers=auth(token),
        json={"bureau_scenario": "SUCCESS", "bureau_score": 720},
    )
    assert response.status_code == 200, response.text


def external_approve(client: TestClient, application_id: int, amount: int = 250000) -> dict:
    response = client.post("/api/integrations/risk-outcomes", headers={"X-Integration-Key": "poc-risk-secret"}, json={
        "application_id": application_id,
        "outcome": "APPROVED",
        "reason_code": "EXTERNAL_POLICY_APPROVED",
        "reason_text": "External evaluator confirmed policy compliance.",
        "approved_limit": amount,
        "approved_term_months": 12,
        "annual_interest_rate": 12,
    })
    assert response.status_code == 200, response.text
    return response.json()


def signed_simulation(client: TestClient, token: str, application_id: int) -> dict:
    response = client.post(
        f"/api/requests/{application_id}/simulations",
        headers=auth(token),
        json={"grace_months": 0, "frequency": "MONTHLY", "balloon_percent": 0},
    )
    assert response.status_code == 200, response.text
    simulation = response.json()
    response = client.post(
        f"/api/simulations/{simulation['id']}/accept",
        headers=auth(token),
        json={"signer_confirmation": "César — Head of Finance"},
    )
    assert response.status_code == 200, response.text
    return response.json()

