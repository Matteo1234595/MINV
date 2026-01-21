from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

import httpx
from sqlalchemy.orm import Session

from app.models import Action, Insight, KpiSnapshot, StrategyBrief


@dataclass(frozen=True)
class ChatResult:
    content: str
    model: str
    tool_calls: list[dict[str, Any]]


class OpenAIClient:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def responses(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/responses",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    def chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()


def _env_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _load_context(db: Session, organization_id: uuid.UUID) -> dict[str, Any]:
    latest_snapshot = (
        db.query(KpiSnapshot.snapshot_at)
        .filter(KpiSnapshot.organization_id == organization_id)
        .order_by(KpiSnapshot.snapshot_at.desc())
        .first()
    )
    metrics: dict[str, float] = {}
    snapshot_at = None
    if latest_snapshot:
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

    insights = (
        db.query(Insight)
        .filter(
            Insight.organization_id == organization_id,
            Insight.created_at >= datetime.utcnow() - timedelta(days=30),
        )
        .order_by(Insight.created_at.desc())
        .all()
    )

    actions = (
        db.query(Action)
        .filter(Action.organization_id == organization_id, Action.status == "open")
        .order_by(Action.created_at.desc())
        .all()
    )

    brief = (
        db.query(StrategyBrief)
        .filter(StrategyBrief.organization_id == organization_id)
        .order_by(StrategyBrief.created_at.desc())
        .first()
    )

    return {
        "snapshot_at": snapshot_at.isoformat() if snapshot_at else None,
        "kpis": metrics,
        "insights": [
            {"id": str(insight.id), "title": insight.title, "severity": insight.severity}
            for insight in insights
        ],
        "actions": [
            {"id": str(action.id), "title": action.title, "status": action.status}
            for action in actions
        ],
        "strategy_brief": brief.content if brief else None,
    }


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_latest_kpis",
                "description": "Fetch latest KPI metrics for the organization.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_recent_insights",
                "description": "Fetch recent insights for the organization.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_open_actions",
                "description": "Fetch open actions for the organization.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_latest_strategy_brief",
                "description": "Fetch the latest strategy brief content.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]


def _tool_impls(
    db: Session, organization_id: uuid.UUID
) -> dict[str, Callable[[], dict[str, Any]]]:
    context = _load_context(db, organization_id)

    return {
        "get_latest_kpis": lambda: {"snapshot_at": context["snapshot_at"], "kpis": context["kpis"]},
        "get_recent_insights": lambda: {"insights": context["insights"]},
        "get_open_actions": lambda: {"actions": context["actions"]},
        "get_latest_strategy_brief": lambda: {"strategy_brief": context["strategy_brief"]},
    }


def _extract_response_message(response: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    output = response.get("output", [])
    tool_calls: list[dict[str, Any]] = []
    content = ""
    for item in output:
        if item.get("type") == "tool_call":
            tool_calls.append(item)
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    content += part.get("text", "")
    return content or response.get("output_text", ""), tool_calls


def _extract_chat_message(response: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    choices = response.get("choices", [])
    if not choices:
        return "", []
    message = choices[0].get("message", {})
    content = message.get("content", "") or ""
    tool_calls = message.get("tool_calls", []) or []
    return content, tool_calls


def chat_with_tools(
    db: Session,
    organization_id: uuid.UUID,
    user_message: str,
    client: OpenAIClient,
) -> ChatResult:
    context = _load_context(db, organization_id)
    tools = _tool_definitions()
    system_prompt = (
        "You are AION Copilot. Use the provided organization context and tools. "
        "Cite KPI numbers and insight titles when relevant."
    )
    model = _env_model()

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Organization context: {context}\nUser: {user_message}",
            },
        ],
        "tools": tools,
    }

    try:
        response = client.responses(payload)
        content, tool_calls = _extract_response_message(response)
    except httpx.HTTPStatusError:
        chat_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Organization context: {context}\nUser: {user_message}"},
            ],
            "tools": tools,
        }
        response = client.chat_completions(chat_payload)
        content, tool_calls = _extract_chat_message(response)

    if tool_calls:
        tool_impls = _tool_impls(db, organization_id)
        tool_outputs = []
        for call in tool_calls:
            tool_name = call.get("name") or call.get("function", {}).get("name")
            if tool_name in tool_impls:
                tool_outputs.append(
                    {
                        "type": "tool_output",
                        "call_id": call.get("call_id"),
                        "output": tool_impls[tool_name](),
                    }
                )

        follow_up = {
            "model": model,
            "input": payload["input"] + tool_outputs,
            "tools": tools,
        }
        try:
            response = client.responses(follow_up)
            content, _ = _extract_response_message(response)
        except httpx.HTTPStatusError:
            chat_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Organization context: {context}\nUser: {user_message}"},
                    {"role": "assistant", "content": content},
                ],
                "tools": tools,
            }
            response = client.chat_completions(chat_payload)
            content, _ = _extract_chat_message(response)

    return ChatResult(content=content, model=model, tool_calls=tool_calls)
