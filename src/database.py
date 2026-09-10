"""Database access and employee data initialization."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'travel_assistant.db'}"
load_dotenv(PROJECT_ROOT / ".env")


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(primary_key=True)
    country: Mapped[str]
    employee_type: Mapped[str]
    status: Mapped[str]
    manager_approval: Mapped[bool]
    created_at: Mapped[datetime]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "country": self.country,
            "employee_type": self.employee_type,
            "eligibility_status": self.status,
            "is_eligible": self.manager_approval,
            "created_at": self.created_at.isoformat(),
        }


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine():
    return create_engine(
        get_database_url(),
        future=True,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def initialize_database(csv_path: str | Path | None = None) -> None:
    """Create tables and seed employees from CSV when the table is empty."""
    if get_database_url().startswith(("postgresql://", "postgresql+psycopg2://")):
        # Hosted PostgreSQL schemas are managed externally, for example in Supabase.
        return
    csv_file = Path(csv_path or PROJECT_ROOT / "data" / "employees.csv")
    engine = get_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        if session.scalar(select(Employee.employee_id).limit(1)) is not None:
            return
        with csv_file.open(newline="", encoding="utf-8") as file:
            employees = []
            for row in csv.DictReader(file):
                row["manager_approval"] = row["manager_approval"].lower() == "true"
                row["created_at"] = datetime.fromisoformat(row["created_at"])
                employees.append(Employee(**row))
            session.add_all(employees)
        session.commit()


def find_employee(employee_id: str) -> Dict[str, Any] | None:
    initialize_database()
    with Session(get_engine()) as session:
        employee = session.get(Employee, employee_id.strip().upper())
        return employee.as_dict() if employee else None