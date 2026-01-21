from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Action, Insight


def _truncate(value: str, limit: int = 255) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _action_templates(insight: Insight) -> list[tuple[str, str, str]]:
    title = insight.title.lower()
    templates: list[tuple[str, str, str]] = []

    if "runway" in title:
        templates = [
            (
                "Reduce discretionary spend by 10%",
                "Runway is below target and burn must be reduced quickly.",
                "Extend runway by 1-2 months.",
            ),
            (
                "Build a 12-week cash forecast",
                "Short-term cash visibility reduces surprise shortfalls.",
                "Improve liquidity planning and fundraising timing.",
            ),
        ]
    elif "cashflow" in title:
        templates = [
            (
                "Accelerate collections for top customers",
                "Recent cashflow is negative and collections can improve quickly.",
                "Increase near-term cash inflows.",
            ),
            (
                "Review vendor payment terms",
                "Stretching outflows can stabilize cash in the short term.",
                "Reduce monthly cash volatility.",
            ),
        ]
    elif "margin" in title:
        templates = [
            (
                "Audit pricing and discounting",
                "Margin compression suggests pricing leakage.",
                "Recover 2-3 points of gross margin.",
            ),
            (
                "Review COGS drivers by segment",
                "Identifying high-cost segments improves profitability focus.",
                "Improve margin mix over the next quarter.",
            ),
        ]
    elif "expenses" in title:
        templates = [
            (
                "Reassess hiring and discretionary spend",
                "Expense growth is outpacing revenue.",
                "Align burn with revenue trajectory.",
            ),
        ]
    else:
        templates = [
            (
                "Assign an owner to address this insight",
                "Ensure accountability for resolving the insight.",
                "Improve execution velocity.",
            ),
        ]

    if insight.severity == "high":
        templates.append(
            (
                "Schedule executive review within 7 days",
                "High-severity insight needs leadership attention.",
                "Accelerate decision-making.",
            )
        )

    return templates


def generate_actions(db: Session, organization_id: uuid.UUID) -> list[Action]:
    cutoff = datetime.utcnow() - timedelta(days=30)
    insights = (
        db.query(Insight)
        .filter(Insight.organization_id == organization_id, Insight.created_at >= cutoff)
        .order_by(Insight.created_at.desc())
        .all()
    )

    existing_titles = {
        row[0]
        for row in db.query(Action.title)
        .filter(
            Action.organization_id == organization_id,
            Action.created_at >= datetime.utcnow() - timedelta(days=14),
        )
        .all()
    }

    created: list[Action] = []
    now = datetime.utcnow()

    for insight in insights:
        templates = _action_templates(insight)
        for action_title, rationale, impact in templates[:3]:
            title = _truncate(f"{action_title} — Rationale: {rationale} Impact: {impact}")
            if title in existing_titles:
                continue
            due_at = None
            if insight.severity == "high":
                due_at = now + timedelta(days=14)
            elif insight.severity == "medium":
                due_at = now + timedelta(days=30)

            action = Action(
                organization_id=organization_id,
                insight_id=insight.id,
                title=title,
                status="open",
                due_at=due_at,
            )
            created.append(action)
            existing_titles.add(title)

    if created:
        db.add_all(created)
        db.commit()

    return created


def open_actions(db: Session, organization_id: uuid.UUID) -> list[Action]:
    return (
        db.query(Action)
        .filter(Action.organization_id == organization_id, Action.status == "open")
        .order_by(Action.created_at.desc())
        .all()
    )
