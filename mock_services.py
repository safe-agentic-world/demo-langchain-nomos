from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
ORDERS_DIR = ROOT / "data" / "orders"


def load_order(order_id: str) -> dict[str, Any]:
    path = ORDERS_DIR / f"{order_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="order not found")
    return json.loads(path.read_text(encoding="utf-8"))


support_app = FastAPI(title="Mock Support Service")


class RefundRequest(BaseModel):
    order_id: str
    reason: str


class CompensationRequest(BaseModel):
    order_id: str
    amount: int
    reason: str


@support_app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@support_app.post("/refunds")
def create_refund(req: RefundRequest) -> dict[str, Any]:
    order = load_order(req.order_id)
    if not order.get("refund_eligible", False):
        raise HTTPException(status_code=409, detail="order is not eligible for refund")
    return {
        "refund_id": f"rfd_{req.order_id.lower()}",
        "status": "accepted",
        "order_id": order["order_id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "reason": req.reason,
        "customer": order["customer"],
    }


@support_app.post("/compensations")
def create_compensation(req: CompensationRequest) -> dict[str, Any]:
    order = load_order(req.order_id)
    return {
        "compensation_id": f"cmp_{req.order_id.lower()}",
        "status": "approved",
        "order_id": order["order_id"],
        "amount": req.amount,
        "currency": order["currency"],
        "reason": req.reason,
        "customer": order["customer"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the mock support service.")
    parser.add_argument("service", choices=["refund"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    uvicorn.run(support_app, host=args.host, port=args.port or 8002, log_level="info")


if __name__ == "__main__":
    main()
