from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.auth import get_current_user
from app.services.auth import has_org_access


def require_org_access(org_id: uuid.UUID):
    def _dependency(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        if not has_org_access(db, current_user.id, org_id):
            raise HTTPException(status_code=403, detail="Access denied")
        return current_user

    return _dependency
