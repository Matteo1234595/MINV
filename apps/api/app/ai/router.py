from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.service import ChatResult, OpenAIClient, chat_with_tools
from app.db import get_db

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    organization_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    content: str
    model: str
    tool_calls: list[dict[str, object]]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    client = OpenAIClient(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL"))
    result: ChatResult = chat_with_tools(db, payload.organization_id, payload.message, client)
    return ChatResponse(content=result.content, model=result.model, tool_calls=result.tool_calls)
