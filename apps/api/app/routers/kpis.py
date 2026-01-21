from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import KpiSnapshot
from app.services.kpis import METRICS, compute_monthly_kpis, persist_kpis

router = APIRouter(prefix="/kpis", tags=["kpis"])


class KpiRecomputeRequest(BaseModel):
    organization_id: uuid.UUID
    start_month: datetime | None = Field(
        default=None, description="Month start (YYYY-MM-01) to recompute from"
    )
    end_month: datetime | None = Field(
        default=None, description="Month start (YYYY-MM-01) to recompute through"
    )


class KpiRecomputeResponse(BaseModel):
    organization_id: uuid.UUID
    start_month: datetime
    end_month: datetime
    inserted: int


class KpiSnapshotResponse(BaseModel):
    organization_id: uuid.UUID
    snapshot_at: datetime
    metric: str
    value: float


class KpiLatestResponse(BaseModel):
    organization_id: uuid.UUID
    snapshot_at: datetime
    metrics: dict[str, float]


def _to_month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@router.post("/recompute", response_model=KpiRecomputeResponse)
def recompute_kpis(payload: KpiRecomputeRequest, db: Session = Depends(get_db)):
    results = compute_monthly_kpis(
        db,
        payload.organization_id,
        start_month=payload.start_month,
        end_month=payload.end_month,
    )

    if not results:
        raise HTTPException(status_code=404, detail="No data available for KPI computation")

    start_month = _to_month_start(payload.start_month or results[0].snapshot_at)
    end_month = _to_month_start(payload.end_month or results[-1].snapshot_at)
    inserted = persist_kpis(db, payload.organization_id, results, start_month, end_month)

    return KpiRecomputeResponse(
        organization_id=payload.organization_id,
        start_month=start_month,
        end_month=end_month,
        inserted=inserted,
    )


@router.get("/latest", response_model=KpiLatestResponse)
def latest_kpis(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    latest_snapshot = db.query(KpiSnapshot.snapshot_at).filter(
        KpiSnapshot.organization_id == organization_id
    ).order_by(KpiSnapshot.snapshot_at.desc()).first()

    if latest_snapshot is None:
        raise HTTPException(status_code=404, detail="No KPI snapshots found")

    snapshot_at = latest_snapshot[0]
    rows = (
        db.query(KpiSnapshot)
        .filter(
            KpiSnapshot.organization_id == organization_id,
            KpiSnapshot.snapshot_at == snapshot_at,
            KpiSnapshot.metric.in_(METRICS),
        )
        .all()
    )

    metrics = {row.metric: float(row.value) for row in rows}

    return KpiLatestResponse(
        organization_id=organization_id,
        snapshot_at=snapshot_at,
        metrics=metrics,
    )
