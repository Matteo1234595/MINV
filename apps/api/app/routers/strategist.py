from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.action_engine import generate_actions, open_actions
from app.services.strategist import generate_strategy_brief, latest_strategy_brief

router = APIRouter(tags=["strategist", "actions"])


class StrategyBriefResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    content: str
    context: dict[str, object]
    created_at: datetime


class ActionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    insight_id: uuid.UUID | None
    title: str
    status: str
    due_at: datetime | None
    created_at: datetime


class ActionsResponse(BaseModel):
    organization_id: uuid.UUID
    actions: list[ActionResponse]


@router.post("/strategist/brief", response_model=StrategyBriefResponse)
def create_brief(organization_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    try:
        brief = generate_strategy_brief(db, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StrategyBriefResponse(
        id=brief.id,
        organization_id=brief.organization_id,
        content=brief.content,
        context=brief.context,
        created_at=brief.created_at,
    )


@router.get("/strategist/latest", response_model=StrategyBriefResponse)
def get_latest_brief(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    brief = latest_strategy_brief(db, organization_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="No strategy brief found")
    return StrategyBriefResponse(
        id=brief.id,
        organization_id=brief.organization_id,
        content=brief.content,
        context=brief.context,
        created_at=brief.created_at,
    )


@router.post("/actions/generate", response_model=ActionsResponse)
def create_actions(organization_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    actions = generate_actions(db, organization_id)
    return ActionsResponse(
        organization_id=organization_id,
        actions=[
            ActionResponse(
                id=action.id,
                organization_id=action.organization_id,
                insight_id=action.insight_id,
                title=action.title,
                status=action.status,
                due_at=action.due_at,
                created_at=action.created_at,
            )
            for action in actions
        ],
    )


@router.get("/actions/open", response_model=ActionsResponse)
def get_open_actions(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    actions = open_actions(db, organization_id)
    return ActionsResponse(
        organization_id=organization_id,
        actions=[
            ActionResponse(
                id=action.id,
                organization_id=action.organization_id,
                insight_id=action.insight_id,
                title=action.title,
                status=action.status,
                due_at=action.due_at,
                created_at=action.created_at,
            )
            for action in actions
        ],
    )
