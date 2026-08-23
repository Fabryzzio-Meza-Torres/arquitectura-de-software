from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from database import create_db_and_tables, engine
from models.domain import AuditEntry, DemoSession, User
from routers import auth, collections, contracts, financing, negotiation, support


TAGS = [
    {"name": "Demo session", "description": "POC identity selector. Tokens prove RBAC behavior but are not production authentication."},
    {"name": "Financing requests", "description": "Client requests, dossier, external scoring orchestration and decision attestations."},
    {"name": "External integrations", "description": "Callbacks that record external outcomes. Lea$e never computes credit decisions."},
    {"name": "Broker negotiation", "description": "Explicit user-authored dates, responses, proposals, messages and shared PDF records. No automatic negotiation."},
    {"name": "Schedules and contracts", "description": "Simulations, signature, atomic activation, locked currency/rate and reception status."},
    {"name": "Collections and end-of-contract resolution", "description": "Idempotent payments, reconciliation, 4-color delinquency, pronosticated income and the purchase/return branches."},
    {"name": "Support and traceability", "description": "In-app inbox and immutable audit trail."},
]


DESCRIPTION = """
# Lea$e Phase 1 POC

Happy Path: financing request → documented Broker negotiation → **externally supplied** credit outcome → signed schedule → active contract.

## Scope guard

Lea$e records explicit user actions and external outcomes. It does **not** calculate credit decisions, negotiate automatically, select providers or machinery, procure equipment, coordinate delivery logistics, or expose a Provider actor. Equipment reception is only a contract status.

## Swagger authorization

1. Call `POST /api/demo/session` with user `1` (César, CLIENT), `2` (Juan Pedro, LEASING) or
   `3` (Maxim, BROKER). User `4` is the NFR-07 dual-approval service account, not a persona —
   it is omitted from `GET /api/demo/users` but can still open a session directly for testing
   the >PEN 500,000 dual-attestation rule.
2. Copy `access_token`.
3. Click **Authorize** and paste the token.

External risk callbacks use `X-Integration-Key: poc-risk-secret`.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Lea$e POC API",
    version="0.1.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_denied_access(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 403:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            with Session(engine) as session:
                demo_session = session.get(DemoSession, token)
                user = session.get(User, demo_session.user_id) if demo_session else None
                session.add(AuditEntry(
                    entity_type="access",
                    entity_id=request.url.path,
                    actor_id=user.id if user else None,
                    organization=user.organization if user else "UNKNOWN",
                    action="UNAUTHORIZED_ACCESS_DENIED",
                    previous_value=None,
                    new_value=request.method,
                ))
                session.commit()
    return response

app.include_router(auth.router)
app.include_router(financing.router)
app.include_router(negotiation.router)
app.include_router(contracts.router)
app.include_router(collections.router)
app.include_router(support.router)


@app.get("/health", tags=["Support and traceability"], summary="Liveness and POC scope marker")
def health():
    return {"status": "ok", "service": "lease-poc", "credit_decision_engine": False, "provider_actor": False}
