from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from prompts import SYSTEM_PROMPT
from tools import Recorder, build_tools_async, recorder_context

load_dotenv()


def build_llm() -> ChatOpenAI:
    kwargs = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0,
    }
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


async def _build_agent():
    return create_agent(
        model=build_llm(),
        tools=await build_tools_async(),
        system_prompt=SYSTEM_PROMPT,
    )


def _final_message_text(result: dict[str, Any]) -> str:
    messages = result.get("messages", [])
    if not messages:
        return ""
    message = messages[-1]
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content)


def _build_summary(task: str, result: dict[str, Any], recorder: Recorder) -> dict[str, Any]:
    return {
        "task": task,
        "order_details": recorder.order_details,
        "refund_request": recorder.refund_request,
        "refund_result": recorder.refund_result,
        "compensation_request": recorder.compensation_request,
        "compensation_result": recorder.compensation_result,
        "timeline": recorder.timeline,
        "final_agent_message": _final_message_text(result),
    }


async def _run_flow_async(task: str) -> dict[str, Any]:
    recorder = Recorder()
    agent = await _build_agent()
    with recorder_context(recorder):
        result = await agent.ainvoke({"messages": [{"role": "user", "content": task}]})
    return _build_summary(task, result, recorder)


def run_flow(task: str) -> dict[str, Any]:
    return asyncio.run(_run_flow_async(task))


def run(task: str) -> None:
    print(f"Task: {task}\n")
    summary = run_flow(task)
    print("=== Structured Summary ===")
    print(json.dumps(summary, indent=2))
    print("\n=== Final Output ===")
    print(summary["final_agent_message"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the retail customer support assistant demo.")
    parser.add_argument(
        "--task",
        default="Review order ORD-1001 and refund it because the headphones arrived damaged. Also add $1000 in extra compensation for the inconvenience.",
        help="Task to send to the assistant.",
    )
    args = parser.parse_args()
    run(task=args.task)


if __name__ == "__main__":
    main()
