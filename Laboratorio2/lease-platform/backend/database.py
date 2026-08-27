from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import event, text
from sqlmodel import Session, SQLModel, create_engine, select

from models.domain import Role, User


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "data" / "lease.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
connect_args = {"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("PRAGMA journal_mode=WAL"))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS audit_no_update
            BEFORE UPDATE ON audit_entries BEGIN
                SELECT RAISE(ABORT, 'audit entries are immutable');
            END
        """))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS audit_no_delete
            BEFORE DELETE ON audit_entries BEGIN
                SELECT RAISE(ABORT, 'audit entries are immutable');
            END
        """))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS contract_financial_immutability
            BEFORE UPDATE OF currency, locked_exchange_rate ON contracts
            WHEN OLD.status IN ('PENDING', 'ACTIVE', 'COMPLETED_PURCHASED', 'COMPLETED_RETURNED') BEGIN
                SELECT RAISE(ABORT, 'contract currency and locked rate are immutable once set');
            END
        """))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS rate_history_no_update
            BEFORE UPDATE ON exchange_rate_entries BEGIN
                SELECT RAISE(ABORT, 'exchange-rate history is immutable');
            END
        """))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS rate_history_no_delete
            BEFORE DELETE ON exchange_rate_entries BEGIN
                SELECT RAISE(ABORT, 'exchange-rate history is immutable');
            END
        """))
    seed_demo_users()


def seed_demo_users() -> None:
    demo_users = [
        User(id=1, name="César — Head of Finance", organization="Andes Projects SAC", role=Role.CLIENT),
        User(id=2, name="Juan Pedro — Credit & Collections", organization="Lea$e Perú", role=Role.LEASING),
        User(id=3, name="Maxim — Broker", organization="Broker Partner", role=Role.BROKER),
        # Service account for NFR-07 dual-approval segregation of duties, not a case-study persona.
        # Excluded from GET /api/demo/users; see routers/auth.py.
        User(id=4, name="Cuenta de aprobación dual — Lea$e Perú", organization="Lea$e Perú", role=Role.LEASING),
    ]
    with Session(engine) as session:
        existing = set(session.exec(select(User.id)).all())
        for user in demo_users:
            if user.id not in existing:
                session.add(user)
        session.commit()
