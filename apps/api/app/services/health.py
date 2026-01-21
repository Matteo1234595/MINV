from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import HealthScore, Insight, KpiSnapshot


@dataclass(frozen=True)
class HealthScoreResult:
    score: int
    components: dict[str, float | dict[str, float | None]]
    computed_at: datetime
    snapshot_at: datetime


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))


def _latest_snapshot_at(db: Session, organization_id: uuid.UUID) -> datetime | None:
    latest = (
        db.query(KpiSnapshot.snapshot_at)
        .filter(KpiSnapshot.organization_id == organization_id)
        .order_by(KpiSnapshot.snapshot_at.desc())
        .first()
    )
    return latest[0] if latest else None


def _latest_metrics(db: Session, organization_id: uuid.UUID, snapshot_at: datetime) -> dict[str, float]:
    rows = (
        db.query(KpiSnapshot)
        .filter(
            KpiSnapshot.organization_id == organization_id,
            KpiSnapshot.snapshot_at == snapshot_at,
        )
        .all()
    )
    return {row.metric: float(row.value) for row in rows}


def _metric_series(
    db: Session, organization_id: uuid.UUID, metric: str, limit: int = 3
) -> list[float]:
    rows = (
        db.query(KpiSnapshot.value)
        .filter(KpiSnapshot.organization_id == organization_id, KpiSnapshot.metric == metric)
        .order_by(KpiSnapshot.snapshot_at.desc())
        .limit(limit)
        .all()
    )
    return [float(row[0]) for row in reversed(rows)]


def compute_health_score(db: Session, organization_id: uuid.UUID) -> HealthScoreResult | None:
    snapshot_at = _latest_snapshot_at(db, organization_id)
    if snapshot_at is None:
        return None

    metrics = _latest_metrics(db, organization_id, snapshot_at)
    runway_months = metrics.get("runway")
    burn_rate = metrics.get("burn_rate")
    gross_margin = metrics.get("gross_margin")
    revenue = metrics.get("revenue")

    # Scoring formula (deterministic):
    # - runway score: 3 months => 20, 18+ months => 100, linear in-between; missing => 50.
    # - burn rate score: penalize burn as % of revenue (0% => 100, 100% => 50, 200% => 0).
    # - gross margin score: margin percentage scaled to 0-100; missing => 50.
    # - revenue trend score (3m): 50 +/- 50 * growth rate over 3 months (capped).
    # - cashflow volatility score (3m): 100 - 50 * coefficient of variation (capped).
    if runway_months is None:
        runway_score = 50.0
    elif runway_months <= 3:
        runway_score = 20.0
    elif runway_months >= 18:
        runway_score = 100.0
    else:
        runway_score = 20.0 + (runway_months - 3) * (80.0 / 15.0)

    if revenue and revenue > 0 and burn_rate is not None:
        burn_ratio = burn_rate / revenue
        burn_rate_score = _clamp(100.0 - burn_ratio * 50.0)
    else:
        burn_rate_score = 50.0

    if gross_margin is None:
        gross_margin_score = 50.0
    else:
        gross_margin_score = _clamp(gross_margin * 100.0)

    revenue_series = _metric_series(db, organization_id, "revenue")
    if len(revenue_series) >= 2:
        oldest, latest = revenue_series[0], revenue_series[-1]
        if oldest > 0:
            revenue_trend = (latest - oldest) / oldest
        elif latest > 0:
            revenue_trend = 1.0
        else:
            revenue_trend = 0.0
        revenue_trend_score = _clamp(50.0 + revenue_trend * 50.0)
    else:
        revenue_trend = 0.0
        revenue_trend_score = 50.0

    cashflow_series = _metric_series(db, organization_id, "cashflow")
    if len(cashflow_series) >= 2:
        mean = statistics.fmean(cashflow_series)
        stdev = statistics.pstdev(cashflow_series)
        volatility = stdev / max(abs(mean), 1.0)
        cashflow_volatility_score = _clamp(100.0 - volatility * 50.0)
    else:
        volatility = 0.0
        cashflow_volatility_score = 50.0

    component_scores = [
        runway_score,
        burn_rate_score,
        gross_margin_score,
        revenue_trend_score,
        cashflow_volatility_score,
    ]
    overall = int(round(_clamp(sum(component_scores) / len(component_scores))))
    computed_at = datetime.utcnow()

    components: dict[str, float | dict[str, float | None]] = {
        "runway_months": {"value": runway_months, "score": runway_score},
        "burn_rate": {"value": burn_rate, "score": burn_rate_score},
        "gross_margin": {"value": gross_margin, "score": gross_margin_score},
        "revenue_trend_3m": {"value": revenue_trend, "score": revenue_trend_score},
        "cashflow_volatility_3m": {"value": volatility, "score": cashflow_volatility_score},
    }

    return HealthScoreResult(
        score=overall,
        components=components,
        computed_at=computed_at,
        snapshot_at=snapshot_at,
    )


def persist_health_score(
    db: Session, organization_id: uuid.UUID, result: HealthScoreResult
) -> HealthScore:
    score = HealthScore(
        organization_id=organization_id,
        score=result.score,
        components=result.components,
        computed_at=result.computed_at,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def latest_health_score(db: Session, organization_id: uuid.UUID) -> HealthScore | None:
    return (
        db.query(HealthScore)
        .filter(HealthScore.organization_id == organization_id)
        .order_by(HealthScore.computed_at.desc())
        .first()
    )


def generate_insights(
    db: Session, organization_id: uuid.UUID, health_score: HealthScoreResult
) -> list[Insight]:
    now = datetime.utcnow()
    recent_titles = {
        row[0]
        for row in db.query(Insight.title)
        .filter(
            Insight.organization_id == organization_id,
            Insight.created_at >= now - timedelta(days=7),
        )
        .all()
    }

    metrics = _latest_metrics(db, organization_id, health_score.snapshot_at)
    runway = metrics.get("runway")
    revenue = metrics.get("revenue", 0.0)
    expenses = metrics.get("expenses", 0.0)
    burn_rate = metrics.get("burn_rate", 0.0)

    insights: list[tuple[str, str, str]] = []

    if runway is not None and runway < 6:
        insights.append(
            (
                "Runway below 6 months",
                "Current runway is under 6 months. Consider raising capital or reducing burn.",
                "high",
            )
        )

    gross_margin_series = _metric_series(db, organization_id, "gross_margin")
    if len(gross_margin_series) >= 3 and gross_margin_series[-3] > gross_margin_series[-2] > gross_margin_series[-1]:
        insights.append(
            (
                "Gross margin declining for 3 months",
                "Gross margin has decreased for three consecutive months. Review pricing and cost structure.",
                "medium",
            )
        )

    revenue_series = _metric_series(db, organization_id, "revenue")
    expenses_series = _metric_series(db, organization_id, "expenses")
    if len(revenue_series) >= 2 and len(expenses_series) >= 2:
        revenue_growth = (
            (revenue_series[-1] - revenue_series[0]) / revenue_series[0]
            if revenue_series[0] > 0
            else 0.0
        )
        expenses_growth = (
            (expenses_series[-1] - expenses_series[0]) / expenses_series[0]
            if expenses_series[0] > 0
            else 0.0
        )
        if expenses_growth > revenue_growth + 0.1:
            insights.append(
                (
                    "Expenses rising faster than revenue",
                    "Expense growth is outpacing revenue growth. Reassess hiring and discretionary spend.",
                    "high",
                )
            )

    cashflow_series = _metric_series(db, organization_id, "cashflow")
    if len(cashflow_series) >= 2 and cashflow_series[-1] < 0 and cashflow_series[-2] < 0:
        insights.append(
            (
                "Negative cashflow for two months",
                "Cashflow has been negative for two consecutive months. Prioritize cash collections.",
                "high",
            )
        )

    if revenue > 0 and burn_rate > revenue:
        insights.append(
            (
                "Burn rate exceeds revenue",
                "Burn rate is higher than revenue. Tighten expense controls or accelerate growth.",
                "medium",
            )
        )

    if revenue_series and len(revenue_series) >= 2:
        revenue_growth = (
            (revenue_series[-1] - revenue_series[0]) / revenue_series[0]
            if revenue_series[0] > 0
            else 0.0
        )
        if revenue_growth >= 0.2:
            insights.append(
                (
                    "Revenue growth accelerating",
                    "Revenue has grown at least 20% over the last three months. Lean into acquisition channels.",
                    "info",
                )
            )

    if health_score.score < 50:
        insights.append(
            (
                "Overall financial health below 50",
                "The composite health score is below 50. Focus on improving margin and burn discipline.",
                "high",
            )
        )

    if len(insights) < 3:
        insights.append(
            (
                "KPI coverage limited",
                "Limited KPI history available. Add more months of data to improve trend detection.",
                "info",
            )
        )

    if expenses > revenue and revenue > 0:
        insights.append(
            (
                "Expenses exceed revenue",
                "Current expenses are higher than revenue. Evaluate cost structure for quick wins.",
                "medium",
            )
        )

    filtered = [insight for insight in insights if insight[0] not in recent_titles][:8]
    created: list[Insight] = []

    for title, body, severity in filtered:
        created.append(
            Insight(
                organization_id=organization_id,
                title=title,
                body=body,
                severity=severity,
            )
        )

    if created:
        db.add_all(created)
        db.commit()

    return created
