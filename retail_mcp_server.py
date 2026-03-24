from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

ROOT = Path(__file__).resolve().parent
ORDERS_DIR = ROOT / "data" / "orders"
REFUND_BASE_URL = os.getenv("REFUND_BASE_URL", "http://127.0.0.1:8002")
COMP_SERVICE_BASE_URL = os.getenv("COMP_SERVICE_BASE_URL", REFUND_BASE_URL)
TIMEOUT = 10

mcp = FastMCP("Northwind Retail MCP")


def _load_order(order_id: str) -> dict[str, Any]:
    path = ORDERS_DIR / f"{order_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"order not found: {order_id}")
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def get_order_details(order_id: str) -> dict[str, Any]:
    """Look up a customer order by order_id."""
    return _load_order(order_id)


@mcp.tool()
def request_refund(order_id: str, reason: str) -> dict[str, Any]:
    """Submit a refund request for an order."""
    response = requests.post(
        f"{REFUND_BASE_URL}/refunds",
        json={"order_id": order_id, "reason": reason},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def issue_compensation(order_id: str, amount: int, reason: str) -> dict[str, Any]:
    """Issue additional customer compensation for an order."""
    response = requests.post(
        f"{COMP_SERVICE_BASE_URL}/compensations",
        json={"order_id": order_id, "amount": amount, "reason": reason},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
