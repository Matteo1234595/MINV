from __future__ import annotations

import calendar
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from app.models import BankTransaction, Invoice, KpiSnapshot

METRICS = (
    "cashflow",
    "revenue",
    "expenses",
    "burn_rate",
    "runway",
    "gross_margin",
)


@dataclass(frozen=True)
class KpiResult:
    snapshot_at: datetime
    metric: str
    value: float


def _month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_end(value: datetime) -> datetime:
    last_day = calendar.monthrange(value.year, value.month)[1]
    return value.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)


def _iter_month_starts(start: datetime, end: datetime) -> Iterable[datetime]:
    current = _month_start(start)
    end_month = _month_start(end)
    while current <= end_month:
        yield current
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


def _coerce_amount(value: float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def compute_monthly_kpis(
    db: Session,
    organization_id: uuid.UUID,
    start_month: datetime | None = None,
    end_month: datetime | None = None,
) -> list[KpiResult]:
    min_txn, max_txn = db.execute(
        select(func.min(BankTransaction.occurred_at), func.max(BankTransaction.occurred_at)).where(
            BankTransaction.organization_id == organization_id
        )
    ).one()
    min_invoice, max_invoice = db.execute(
        select(func.min(Invoice.issued_at), func.max(Invoice.issued_at)).where(
            Invoice.organization_id == organization_id
        )
    ).one()

    candidates = [value for value in (min_txn, max_txn, min_invoice, max_invoice) if value]
    if not candidates:
        return []

    range_start = _month_start(start_month or min(candidates))
    range_end = _month_start(end_month or max(candidates))

    results: list[KpiResult] = []

    for month_start in _iter_month_starts(range_start, range_end):
        month_end = _month_end(month_start)

        revenue = _coerce_amount(
            db.execute(
                select(func.sum(Invoice.amount)).where(
                    Invoice.organization_id == organization_id,
                    Invoice.issued_at >= month_start,
                    Invoice.issued_at <= month_end,
                )
            ).scalar()
        )

        expenses = _coerce_amount(
            db.execute(
                select(
                    func.sum(
                        case(
                            (BankTransaction.amount < 0, -BankTransaction.amount),
                            else_=0,
                        )
                    )
                ).where(
                    BankTransaction.organization_id == organization_id,
                    BankTransaction.occurred_at >= month_start,
                    BankTransaction.occurred_at <= month_end,
                )
            ).scalar()
        )

        cashflow = _coerce_amount(
            db.execute(
                select(func.sum(BankTransaction.amount)).where(
                    BankTransaction.organization_id == organization_id,
                    BankTransaction.occurred_at >= month_start,
                    BankTransaction.occurred_at <= month_end,
                )
            ).scalar()
        )

        cash_balance = _coerce_amount(
            db.execute(
                select(func.sum(BankTransaction.amount)).where(
                    BankTransaction.organization_id == organization_id,
                    BankTransaction.occurred_at <= month_end,
                )
            ).scalar()
        )

        burn_rate = expenses
        runway = cash_balance / burn_rate if burn_rate > 0 else 0.0
        gross_margin = (revenue - expenses) / revenue if revenue > 0 else 0.0

        results.extend(
            [
                KpiResult(snapshot_at=month_start, metric="cashflow", value=cashflow),
                KpiResult(snapshot_at=month_start, metric="revenue", value=revenue),
                KpiResult(snapshot_at=month_start, metric="expenses", value=expenses),
                KpiResult(snapshot_at=month_start, metric="burn_rate", value=burn_rate),
            ]
        )
        results.append(KpiResult(snapshot_at=month_start, metric="runway", value=runway))
        results.append(KpiResult(snapshot_at=month_start, metric="gross_margin", value=gross_margin))

    return results


def persist_kpis(
    db: Session,
    organization_id: uuid.UUID,
    results: list[KpiResult],
    start_month: datetime,
    end_month: datetime,
) -> int:
    db.execute(
        delete(KpiSnapshot).where(
            KpiSnapshot.organization_id == organization_id,
            KpiSnapshot.snapshot_at >= start_month,
            KpiSnapshot.snapshot_at <= end_month,
        )
    )

    snapshots = [
        KpiSnapshot(
            organization_id=organization_id,
            snapshot_at=result.snapshot_at,
            metric=result.metric,
            value=result.value,
        )
        for result in results
    ]
    db.add_all(snapshots)
    db.commit()
    return len(snapshots)
