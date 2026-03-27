"""
BEACON agent — LangGraph workflow with Claude tool use.

Graph:
  START → fetch_data → generate_brief → END
  (optional second flow: notes_input → extract_tasks → END)
"""

from __future__ import annotations
from typing import Any, TypedDict
from anthropic import Anthropic
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from tools import (
    get_stock_info,
    get_market_news,
    format_stock_for_claude,
    format_news_for_claude,
)
from prompts import BEACON_SYSTEM_PROMPT, TASK_EXTRACTION_PROMPT

load_dotenv()

# ---------------------------------------------------------------------------
# Claude tool definitions
# ---------------------------------------------------------------------------

TOOL_GET_STOCK_INFO = {
    "name": "get_stock_info",
    "description": (
        "Get live stock price, analyst target, P/E ratio, market cap, "
        "and company overview for a given ticker symbol."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol e.g. AAPL, MSFT, JPM",
            }
        },
        "required": ["ticker"],
    },
}

TOOL_GET_MARKET_NEWS = {
    "name": "get_market_news",
    "description": "Get recent news headlines for a given stock ticker.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol e.g. AAPL, MSFT, JPM",
            }
        },
        "required": ["ticker"],
    },
}

ALL_TOOLS = [TOOL_GET_STOCK_INFO, TOOL_GET_MARKET_NEWS]


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class BeaconState(TypedDict):
    # Inputs
    client_name: str
    meeting_type: str
    tickers: list[str]
    notes: str

    # Intermediate
    fetched_data: str
    steps: list[str]

    # Outputs
    brief: str
    tasks: str


# ---------------------------------------------------------------------------
# Helper: run Claude tool use loop
# ---------------------------------------------------------------------------

def _run_tool_call(tool_use) -> str:
    tool_name = getattr(tool_use, "name", None)
    tool_input = getattr(tool_use, "input", {})
    ticker = (tool_input.get("ticker") or "").strip().upper()

    if tool_name == "get_stock_info":
        info = get_stock_info(ticker)
        return format_stock_for_claude(info)
    elif tool_name == "get_market_news":
        news = get_market_news(ticker)
        return format_news_for_claude(ticker, news)
    return f"Unknown tool: {tool_name}"


def _block_to_dict(b) -> dict:
    btype = getattr(b, "type", None)
    if btype == "text":
        return {"type": "text", "text": getattr(b, "text", "")}
    elif btype == "tool_use":
        return {
            "type": "tool_use",
            "id": getattr(b, "id", None),
            "name": getattr(b, "name", None),
            "input": getattr(b, "input", {}),
        }
    return {"type": btype}


# ---------------------------------------------------------------------------
# Node 1: fetch_data
# Prompt Claude to call tools for each ticker, collect all data
# ---------------------------------------------------------------------------

def fetch_data(state: BeaconState) -> BeaconState:
    client = Anthropic()
    steps = list(state.get("steps") or [])

    tickers = state.get("tickers") or []
    client_name = state.get("client_name", "the client")
    meeting_type = state.get("meeting_type", "Annual Review")

    user_message = (
        f"I have a {meeting_type} meeting with {client_name}. "
        f"Their portfolio includes: {', '.join(tickers)}. "
        f"Please fetch the current stock info AND recent news for each ticker "
        f"so we can prepare a comprehensive meeting brief."
    )

    messages = [{"role": "user", "content": user_message}]
    all_fetched = []

    # Agentic loop — keep calling tools until Claude stops
    while True:
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            tools=ALL_TOOLS,
            messages=messages,
            system=BEACON_SYSTEM_PROMPT,
        )

        blocks = list(resp.content or [])
        tool_uses = [b for b in blocks if getattr(b, "type", None) == "tool_use"]

        if not tool_uses:
            break

        # Execute all tool calls
        tool_results = []
        for tool_use in tool_uses:
            result = _run_tool_call(tool_use)
            all_fetched.append(result)
            tool_name = getattr(tool_use, "name", "")
            ticker = (getattr(tool_use, "input", {}).get("ticker") or "").upper()
            steps.append(f"📊 Fetched **{tool_name}** for **{ticker}**")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": getattr(tool_use, "id", None),
                "content": result,
            })

        messages.append({"role": "assistant", "content": [_block_to_dict(b) for b in blocks]})
        messages.append({"role": "user", "content": tool_results})

        if resp.stop_reason == "end_turn":
            break

    steps.append("✅ All market data fetched")
    return {**state, "fetched_data": "\n\n".join(all_fetched), "steps": steps}


# ---------------------------------------------------------------------------
# Node 2: generate_brief
# Use fetched data to generate structured meeting brief
# ---------------------------------------------------------------------------

def generate_brief(state: BeaconState) -> BeaconState:
    client = Anthropic()
    steps = list(state.get("steps") or [])

    client_name = state.get("client_name", "the client")
    meeting_type = state.get("meeting_type", "Annual Review")
    fetched_data = state.get("fetched_data", "")

    steps.append("✍️ Generating meeting brief...")

    prompt = (
        f"Using the following live market data, generate a complete meeting brief "
        f"for my {meeting_type} with {client_name}.\n\n"
        f"LIVE MARKET DATA:\n{fetched_data}\n\n"
        f"Generate the full structured brief now."
    )

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
        system=BEACON_SYSTEM_PROMPT,
    )

    brief = "".join(
        getattr(b, "text", "") for b in resp.content
        if getattr(b, "type", None) == "text"
    ).strip()

    steps.append("✅ Meeting brief ready")
    return {**state, "brief": brief, "steps": steps}


# ---------------------------------------------------------------------------
# Node 3: extract_tasks (optional — triggered by meeting notes input)
# ---------------------------------------------------------------------------

def extract_tasks(state: BeaconState) -> BeaconState:
    client = Anthropic()
    steps = list(state.get("steps") or [])
    notes = state.get("notes", "")

    if not notes.strip():
        return {**state, "tasks": "", "steps": steps}

    steps.append("📋 Extracting follow-up tasks from notes...")

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"Meeting notes:\n\n{notes}"}],
        system=TASK_EXTRACTION_PROMPT,
    )

    tasks = "".join(
        getattr(b, "text", "") for b in resp.content
        if getattr(b, "type", None) == "text"
    ).strip()

    steps.append("✅ Follow-up tasks extracted")
    return {**state, "tasks": tasks, "steps": steps}


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(BeaconState)

    graph.add_node("fetch_data", fetch_data)
    graph.add_node("generate_brief", generate_brief)
    graph.add_node("extract_tasks", extract_tasks)

    graph.set_entry_point("fetch_data")
    graph.add_edge("fetch_data", "generate_brief")
    graph.add_edge("generate_brief", "extract_tasks")
    graph.add_edge("extract_tasks", END)

    return graph.compile()


BEACON_GRAPH = build_graph()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_beacon(
    client_name: str,
    meeting_type: str,
    tickers: list[str],
    notes: str = "",
) -> dict[str, Any]:
    """
    Run the full BEACON workflow.
    Returns brief, tasks, and steps for the UI.
    """
    initial_state: BeaconState = {
        "client_name": client_name,
        "meeting_type": meeting_type,
        "tickers": tickers,
        "notes": notes,
        "fetched_data": "",
        "steps": [],
        "brief": "",
        "tasks": "",
    }

    result = BEACON_GRAPH.invoke(initial_state)

    return {
        "brief": result.get("brief", ""),
        "tasks": result.get("tasks", ""),
        "steps": result.get("steps", []),
    }


__all__ = ["run_beacon"]