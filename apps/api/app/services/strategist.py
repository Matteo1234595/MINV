from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import HealthScore, Insight, KpiSnapshot, StrategyBrief


def _format_currency(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _latest_kpis(db: Session, organization_id: uuid.UUID) -> tuple[datetime, dict[str, float]]:
    latest_snapshot = (
        db.query(KpiSnapshot.snapshot_at)
        .filter(KpiSnapshot.organization_id == organization_id)
        .order_by(KpiSnapshot.snapshot_at.desc())
        .first()
    )
    if latest_snapshot is None:
        raise ValueError("No KPI snapshots available")

    snapshot_at = latest_snapshot[0]
    rows = (
        db.query(KpiSnapshot)
        .filter(
            KpiSnapshot.organization_id == organization_id,
            KpiSnapshot.snapshot_at == snapshot_at,
        )
        .all()
    )
    metrics = {row.metric: float(row.value) for row in rows}
    return snapshot_at, metrics


def _latest_health_score(db: Session, organization_id: uuid.UUID) -> HealthScore | None:
    return (
        db.query(HealthScore)
        .filter(HealthScore.organization_id == organization_id)
        .order_by(HealthScore.computed_at.desc())
        .first()
    )


def generate_strategy_brief(db: Session, organization_id: uuid.UUID) -> StrategyBrief:
    snapshot_at, metrics = _latest_kpis(db, organization_id)
    health_score = _latest_health_score(db, organization_id)

    insights = (
        db.query(Insight)
        .filter(
            Insight.organization_id == organization_id,
            Insight.created_at >= datetime.utcnow() - timedelta(days=30),
        )
        .order_by(Insight.created_at.desc())
        .all()
    )

    revenue = metrics.get("revenue")
    expenses = metrics.get("expenses")
    cashflow = metrics.get("cashflow")
    burn_rate = metrics.get("burn_rate")
    runway = metrics.get("runway")
    gross_margin = metrics.get("gross_margin")

    risks = [insight for insight in insights if insight.severity in {"high", "medium"}]
    opportunities = [insight for insight in insights if insight.severity == "info"]

    risks_section = "\n".join(f"- {insight.title}" for insight in risks[:3]) or "- No major risks flagged."
    opportunities_section = (
        "\n".join(f"- {insight.title}" for insight in opportunities[:3])
        or "- No standout opportunities flagged."
    )

    plan_30 = "Stabilize cash discipline and validate near-term revenue drivers."
    plan_60 = "Double down on highest ROI growth channels and pricing optimization."
    plan_90 = "Expand operating runway via sustained margin improvements."

    if runway is not None and runway < 6:
        plan_30 = "Cut non-essential spend and tighten collections to extend runway."
        plan_60 = "Prepare fundraising or credit options while aligning burn to revenue."
        plan_90 = "Rebuild cash buffer through revenue acceleration and cost controls."

    content = "\n".join(
        [
            "AION Strategic Brief",
            "",
            "Current situation:",
            f"- Snapshot month: {snapshot_at.date()}",
            f"- Health score: {health_score.score if health_score else 'n/a'} / 100",
            f"- Revenue: {_format_currency(revenue)}",
            f"- Expenses: {_format_currency(expenses)}",
            f"- Cashflow: {_format_currency(cashflow)}",
            f"- Burn rate: {_format_currency(burn_rate)}",
            f"- Runway (months): {runway if runway is not None else 'n/a'}",
            f"- Gross margin: {_format_percent(gross_margin)}",
            "",
            "Top risks:",
            risks_section,
            "",
            "Top opportunities:",
            opportunities_section,
            "",
            "30/60/90-day plan:",
            f"- 30 days: {plan_30}",
            f"- 60 days: {plan_60}",
            f"- 90 days: {plan_90}",
            "",
            "Citations:",
            f"- KPIs: revenue {_format_currency(revenue)}, expenses {_format_currency(expenses)}, "
            f"cashflow {_format_currency(cashflow)}, burn {_format_currency(burn_rate)}, "
            f"runway {runway if runway is not None else 'n/a'}, gross margin {_format_percent(gross_margin)}.",
            f"- Insights: {', '.join(insight.title for insight in insights[:5]) or 'n/a'}.",
        ]
    )

    context = {
        "snapshot_at": snapshot_at.isoformat(),
        "metrics": metrics,
        "health_score_id": str(health_score.id) if health_score else None,
        "insight_ids": [str(insight.id) for insight in insights],
    }

    brief = StrategyBrief(
        organization_id=organization_id,
        content=content,
        context=context,
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return brief


def latest_strategy_brief(db: Session, organization_id: uuid.UUID) -> StrategyBrief | None:
    return (
        db.query(StrategyBrief)
        .filter(StrategyBrief.organization_id == organization_id)
        .order_by(StrategyBrief.created_at.desc())
        .first()
    )
