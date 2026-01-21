from __future__ import annotations

import os

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Organization


DEMO_ORG_NAME = os.getenv("DEMO_ORG_NAME", "AION Demo")


def main() -> None:
    with SessionLocal() as session:
        existing = session.execute(
            select(Organization).where(Organization.name == DEMO_ORG_NAME)
        ).scalar_one_or_none()
        if existing:
            print(f"Demo organization '{DEMO_ORG_NAME}' already exists.")
            return

        session.add(Organization(name=DEMO_ORG_NAME))
        session.commit()
        print(f"Created demo organization '{DEMO_ORG_NAME}'.")


if __name__ == "__main__":
    main()
