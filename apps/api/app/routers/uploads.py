from __future__ import annotations

import csv
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BankTransaction, Invoice, Upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

BANK_TRANSACTION_REQUIRED_COLUMNS = {"occurred_at", "amount"}
INVOICE_REQUIRED_COLUMNS = {"issued_at", "amount"}


class CSVValidationError(ValueError):
    pass


def _parse_datetime(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise CSVValidationError(f"Invalid {field}: '{value}'. Use ISO-8601 format.") from exc


def _parse_decimal(value: str, field: str) -> Decimal:
    try:
        return Decimal(value)
    except Exception as exc:  # noqa: BLE001
        raise CSVValidationError(f"Invalid {field}: '{value}'. Use a numeric value.") from exc


def _normalize_headers(reader: csv.DictReader[str]) -> dict[str, str]:
    if reader.fieldnames is None:
        raise CSVValidationError("CSV file is missing a header row.")
    return {name.strip().lower(): name for name in reader.fieldnames}


def _validate_headers(field_map: dict[str, str], required: set[str]) -> None:
    missing = sorted(required - set(field_map.keys()))
    if missing:
        raise CSVValidationError(f"Missing required columns: {', '.join(missing)}")


def _row_hash(values: list[str]) -> str:
    normalized = "|".join(value.strip().lower() for value in values)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _read_upload_file(upload_file: UploadFile) -> csv.DictReader[str]:
    content = upload_file.file.read()
    if isinstance(content, bytes):
        text = content.decode("utf-8")
    else:
        text = str(content)
    return csv.DictReader(StringIO(text))


def _create_upload(db: Session, organization_id: uuid.UUID, filename: str) -> Upload:
    upload = Upload(organization_id=organization_id, filename=filename, status="processing")
    db.add(upload)
    db.flush()
    return upload


def _parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}.") from exc


def _finalize_upload(db: Session, upload: Upload, status: str) -> None:
    upload.status = status
    db.add(upload)


def _prepare_transaction_rows(
    reader: csv.DictReader[str],
    field_map: dict[str, str],
    upload_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> tuple[list[BankTransaction], int]:
    seen_hashes: set[str] = set()
    records: list[BankTransaction] = []
    duplicates = 0

    for row in reader:
        try:
            occurred_at = _parse_datetime(row[field_map["occurred_at"]].strip(), "occurred_at")
            amount = _parse_decimal(row[field_map["amount"]].strip(), "amount")
        except KeyError as exc:
            raise CSVValidationError("CSV row is missing required columns.") from exc
        currency = row.get(field_map.get("currency", ""), "").strip() or "USD"
        description = row.get(field_map.get("description", ""), "").strip() or None

        row_signature = _row_hash(
            [
                occurred_at.isoformat(),
                str(amount),
                currency,
                description or "",
            ]
        )
        if row_signature in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(row_signature)

        records.append(
            BankTransaction(
                organization_id=organization_id,
                upload_id=upload_id,
                occurred_at=occurred_at,
                amount=amount,
                currency=currency,
                description=description,
            )
        )

    return records, duplicates


def _prepare_invoice_rows(
    reader: csv.DictReader[str],
    field_map: dict[str, str],
    upload_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> tuple[list[Invoice], int]:
    seen_hashes: set[str] = set()
    records: list[Invoice] = []
    duplicates = 0

    for row in reader:
        try:
            issued_at = _parse_datetime(row[field_map["issued_at"]].strip(), "issued_at")
            amount = _parse_decimal(row[field_map["amount"]].strip(), "amount")
        except KeyError as exc:
            raise CSVValidationError("CSV row is missing required columns.") from exc
        due_at_value = row.get(field_map.get("due_at", ""), "").strip()
        due_at = _parse_datetime(due_at_value, "due_at") if due_at_value else None
        currency = row.get(field_map.get("currency", ""), "").strip() or "USD"
        status = row.get(field_map.get("status", ""), "").strip() or "open"

        row_signature = _row_hash(
            [
                issued_at.isoformat(),
                str(amount),
                currency,
                status,
                due_at.isoformat() if due_at else "",
            ]
        )
        if row_signature in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(row_signature)

        records.append(
            Invoice(
                organization_id=organization_id,
                upload_id=upload_id,
                issued_at=issued_at,
                due_at=due_at,
                amount=amount,
                currency=currency,
                status=status,
            )
        )

    return records, duplicates


def _handle_validation_error(upload: Upload, db: Session, error: Exception) -> None:
    _finalize_upload(db, upload, "failed")
    db.commit()
    raise HTTPException(status_code=400, detail=str(error)) from error


def _response_payload(upload: Upload, inserted: int, duplicates: int) -> dict[str, Any]:
    return {
        "upload_id": str(upload.id),
        "status": upload.status,
        "inserted": inserted,
        "duplicates": duplicates,
    }


@router.post("/bank-transactions")
def upload_bank_transactions(
    organization_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    organization_id = _parse_uuid(organization_id, "organization_id")
    upload = _create_upload(db, organization_id, file.filename or "bank_transactions.csv")
    try:
        reader = _read_upload_file(file)
        field_map = _normalize_headers(reader)
        _validate_headers(field_map, BANK_TRANSACTION_REQUIRED_COLUMNS)
        records, duplicates = _prepare_transaction_rows(reader, field_map, upload.id, organization_id)
    except (CSVValidationError, UnicodeDecodeError) as exc:
        _handle_validation_error(upload, db, exc)

    db.add_all(records)
    _finalize_upload(db, upload, "complete")
    db.commit()

    return _response_payload(upload, inserted=len(records), duplicates=duplicates)


@router.post("/invoices")
def upload_invoices(
    organization_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    organization_id = _parse_uuid(organization_id, "organization_id")
    upload = _create_upload(db, organization_id, file.filename or "invoices.csv")
    try:
        reader = _read_upload_file(file)
        field_map = _normalize_headers(reader)
        _validate_headers(field_map, INVOICE_REQUIRED_COLUMNS)
        records, duplicates = _prepare_invoice_rows(reader, field_map, upload.id, organization_id)
    except (CSVValidationError, UnicodeDecodeError) as exc:
        _handle_validation_error(upload, db, exc)

    db.add_all(records)
    _finalize_upload(db, upload, "complete")
    db.commit()

    return _response_payload(upload, inserted=len(records), duplicates=duplicates)
