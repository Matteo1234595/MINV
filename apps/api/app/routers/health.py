from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Insight
from app.services.health import (
    compute_health_score,
    generate_insights,
    latest_health_score,
    persist_health_score,
)
from app.services.kpis import compute_monthly_kpis, persist_kpis

router = APIRouter(tags=["health", "insights"])


class HealthScoreResponse(BaseModel):
    organization_id: uuid.UUID
    score: int
    components: dict[str, float | dict[str, float | None]]
    computed_at: datetime


class InsightsRecomputeResponse(BaseModel):
    organization_id: uuid.UUID
    health_score: int
    computed_at: datetime
    insights_created: int


class InsightResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    severity: str
    created_at: datetime


class InsightsLatestResponse(BaseModel):
    organization_id: uuid.UUID
    insights: list[InsightResponse]


@router.get("/health/latest", response_model=HealthScoreResponse)
def latest_health(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    score = latest_health_score(db, organization_id)
    if score is None:
        raise HTTPException(status_code=404, detail="No health score found")

    return HealthScoreResponse(
        organization_id=organization_id,
        score=score.score,
        components=score.components,
        computed_at=score.computed_at,
    )


@router.post("/insights/recompute", response_model=InsightsRecomputeResponse)
def recompute_insights(
    organization_id: uuid.UUID = Query(...),
    recompute_kpis: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    if recompute_kpis:
        results = compute_monthly_kpis(db, organization_id)
        if not results:
            raise HTTPException(status_code=404, detail="No KPI data available")
        persist_kpis(db, organization_id, results, results[0].snapshot_at, results[-1].snapshot_at)

    health_result = compute_health_score(db, organization_id)
    if health_result is None:
        raise HTTPException(status_code=404, detail="No KPI snapshots available for scoring")

    score = persist_health_score(db, organization_id, health_result)
    insights = generate_insights(db, organization_id, health_result)

    return InsightsRecomputeResponse(
        organization_id=organization_id,
        health_score=score.score,
        computed_at=score.computed_at,
        insights_created=len(insights),
    )


@router.get("/insights/latest", response_model=InsightsLatestResponse)
def latest_insights(
    organization_id: uuid.UUID,
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Insight)
        .filter(Insight.organization_id == organization_id)
        .order_by(Insight.created_at.desc())
        .limit(limit)
        .all()
    )

    return InsightsLatestResponse(
        organization_id=organization_id,
        insights=[
            InsightResponse(
                id=row.id,
                title=row.title,
                body=row.body,
                severity=row.severity,
                created_at=row.created_at,
            )
            for row in rows
        ],
    )
