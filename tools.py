from __future__ import annotations

import contextlib
import contextvars
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

ROOT = Path(__file__).resolve().parent
ORDERS_DIR = ROOT / "data" / "orders"
REFUND_BASE_URL = os.getenv("REFUND_BASE_URL", "http://127.0.0.1:8002")
COMP_SERVICE_BASE_URL = os.getenv("COMP_SERVICE_BASE_URL", REFUND_BASE_URL)
TIMEOUT = 10

_RECORDER: contextvars.ContextVar["Recorder | None"] = contextvars.ContextVar("demo_recorder", default=None)


@dataclass
class Recorder:
    timeline: list[dict[str, Any]] = field(default_factory=list)
    order_details: dict[str, Any] | None = None
    refund_request: dict[str, Any] | None = None
    refund_result: dict[str, Any] | None = None
    compensation_request: dict[str, Any] | None = None
    compensation_result: dict[str, Any] | None = None

    def record(self, entry: dict[str, Any]) -> None:
        self.timeline.append(entry)


@contextlib.contextmanager
def recorder_context(recorder: Recorder) -> Iterator[None]:
    token = _RECORDER.set(recorder)
    try:
        yield
    finally:
        _RECORDER.reset(token)


def _active_recorder() -> Recorder | None:
    return _RECORDER.get()


def _record(entry: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.record(entry)


def _record_order_details(order: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.order_details = order


def _record_refund_request(payload: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.refund_request = payload


def _record_refund_result(result: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.refund_result = result


def _record_compensation_request(payload: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.compensation_request = payload


def _record_compensation_result(result: dict[str, Any]) -> None:
    recorder = _active_recorder()
    if recorder is not None:
        recorder.compensation_result = result


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def get_order_details_impl(order_id: str) -> str:
    _record(
        {
            "step": "tool_call",
            "tool": "get_order_details",
            "status": "started",
            "request": {"order_id": order_id},
        }
    )
    path = ORDERS_DIR / f"{order_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"order not found: {order_id}")
    order = _load_json(path)
    _record_order_details(order)
    _record(
        {
            "step": "tool_result",
            "tool": "get_order_details",
            "status": "ok",
            "response": order,
        }
    )
    return json.dumps(order)


def request_refund_impl(order_id: str, reason: str) -> str:
    payload = {"order_id": order_id, "reason": reason}
    _record_refund_request(payload)
    _record(
        {
            "step": "tool_call",
            "tool": "request_refund",
            "status": "started",
            "request": payload,
        }
    )
    response = requests.post(f"{REFUND_BASE_URL}/refunds", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    text = response.text
    parsed = _parse_json(text)
    if parsed is not None:
        _record_refund_result(parsed)
    _record(
        {
            "step": "tool_result",
            "tool": "request_refund",
            "status": parsed.get("status", "ok") if parsed else "ok",
            "response": parsed or {"raw": text},
        }
    )
    return text


def issue_compensation_impl(order_id: str, amount: int, reason: str) -> str:
    payload = {"order_id": order_id, "amount": amount, "reason": reason}
    _record_compensation_request(payload)
    _record(
        {
            "step": "tool_call",
            "tool": "issue_compensation",
            "status": "started",
            "request": payload,
        }
    )
    response = requests.post(f"{COMP_SERVICE_BASE_URL}/compensations", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    text = response.text
    parsed = _parse_json(text)
    if parsed is not None:
        _record_compensation_result(parsed)
    _record(
        {
            "step": "tool_result",
            "tool": "issue_compensation",
            "status": parsed.get("status", "ok") if parsed else "ok",
            "response": parsed or {"raw": text},
        }
    )
    return text


def build_tools() -> list:
    @tool
    def get_order_details(order_id: str) -> str:
        """Look up a customer order by order_id and return the raw JSON result."""
        return get_order_details_impl(order_id)

    @tool
    def request_refund(order_id: str, reason: str) -> str:
        """Submit a refund request for an order and return the raw JSON result."""
        return request_refund_impl(order_id, reason)

    @tool
    def issue_compensation(order_id: str, amount: int, reason: str) -> str:
        """Issue additional customer compensation for an order and return the raw JSON result."""
        return issue_compensation_impl(order_id, amount, reason)

    return [get_order_details, request_refund, issue_compensation]
