from __future__ import annotations

import asyncio
import contextlib
import contextvars
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

ROOT = Path(__file__).resolve().parent
DEFAULT_MCP_CONFIG_PATH = ROOT / ".mcp.json"

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


def _parse_json_maybe(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _record_structured_result(tool_name: str, request: dict[str, Any], result: dict[str, Any] | None) -> None:
    if result is None:
        return
    recorder = _active_recorder()
    if recorder is None:
        return
    if tool_name == "get_order_details":
        recorder.order_details = result
        return
    if tool_name == "request_refund":
        recorder.refund_request = request
        recorder.refund_result = result
        return
    if tool_name == "issue_compensation":
        recorder.compensation_request = request
        recorder.compensation_result = result


def _normalize_tool_result(result: Any) -> tuple[str, dict[str, Any] | None]:
    if isinstance(result, str):
        return result, _parse_json_maybe(result)
    if isinstance(result, dict):
        return json.dumps(result), result
    if isinstance(result, list):
        joined = "".join(part.get("text", "") for part in result if isinstance(part, dict))
        return joined, _parse_json_maybe(joined)
    if hasattr(result, "content"):
        content = getattr(result, "content")
        if isinstance(content, str):
            return content, _parse_json_maybe(content)
        if isinstance(content, list):
            joined = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            return joined, _parse_json_maybe(joined)
    text = str(result)
    return text, _parse_json_maybe(text)


def _mcp_config_path() -> Path:
    return Path(os.getenv("MCP_CONFIG_PATH", str(DEFAULT_MCP_CONFIG_PATH))).resolve()


def _load_mcp_server_config() -> dict[str, Any]:
    config_path = _mcp_config_path()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if "mcpServers" in data:
        servers = data["mcpServers"]
    else:
        servers = data
    if not isinstance(servers, dict) or not servers:
        raise ValueError(f"invalid MCP server config: {config_path}")
    return servers


async def _load_wrapped_tools() -> list[StructuredTool]:
    client = MultiServerMCPClient(_load_mcp_server_config())
    mcp_tools = await client.get_tools()
    wrapped: list[StructuredTool] = []
    for tool in mcp_tools:
        wrapped.append(_wrap_mcp_tool(tool))
    return wrapped


def _wrap_mcp_tool(mcp_tool: Any) -> StructuredTool:
    tool_name = str(mcp_tool.name)
    description = str(getattr(mcp_tool, "description", "") or "")
    args_schema = getattr(mcp_tool, "args_schema", None)

    async def _invoke(**kwargs: Any) -> str:
        _record(
            {
                "step": "tool_call",
                "tool": tool_name,
                "status": "started",
                "request": kwargs,
            }
        )
        result = await mcp_tool.ainvoke(kwargs)
        text, parsed = _normalize_tool_result(result)
        _record_structured_result(tool_name, kwargs, parsed)
        _record(
            {
                "step": "tool_result",
                "tool": tool_name,
                "status": parsed.get("status", "ok") if parsed else "ok",
                "response": parsed or {"raw": text},
            }
        )
        return text

    return StructuredTool.from_function(
        coroutine=_invoke,
        name=tool_name,
        description=description,
        args_schema=args_schema,
        infer_schema=args_schema is None,
    )


async def build_tools_async() -> list[StructuredTool]:
    return await _load_wrapped_tools()


def build_tools() -> list[StructuredTool]:
    return asyncio.run(_load_wrapped_tools())
