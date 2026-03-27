---
title: BEACON Advisor Agent
emoji: 🔦
colorFrom: blue
colorTo: yellow
sdk: streamlit
sdk_version: "1.32.0"
app_file: app.py
pinned: false
---

# BEACON — Advisor Intelligence & Meeting Prep Agent

An agentic meeting preparation assistant for independent financial advisors. Enter a client name, meeting type, and portfolio tickers — BEACON fetches live market data and generates a structured, data-grounded meeting brief in seconds.

## What it does

BEACON uses a LangGraph workflow with Claude tool use to automate advisor meeting prep:

- **Fetches live market data** — current price, 52-week range, P/E ratio, analyst targets, dividend yield, and recommendations for each portfolio holding via Yahoo Finance
- **Fetches recent news** — latest headlines for key holdings
- **Generates a structured meeting brief** — client snapshot, portfolio overview, data-backed talking points, market context, suggested agenda, and follow-up tasks
- **Extracts follow-up tasks** — paste meeting notes after the session and BEACON converts them into a prioritized task list

## Tech stack

- Claude (claude-sonnet-4-5) with native tool use
- LangGraph — stateful multi-node workflow orchestration
- yfinance — live market data (no API key required)
- Python + Streamlit

## LangGraph workflow

```
START
  ↓
fetch_data      ← Claude tool use loop (get_stock_info + get_market_news per ticker)
  ↓
generate_brief  ← Claude synthesizes live data into structured meeting brief
  ↓
extract_tasks   ← Claude extracts follow-up tasks from meeting notes (optional)
  ↓
END
```

## Example use cases

- Annual review prep for a client with AAPL, MSFT, JNJ holdings
- Quarterly check-in with talking points grounded in live P/E and analyst targets
- Onboarding brief for a new client with a tech-heavy portfolio
- Post-meeting task extraction from raw notes

## Setup

```bash
pip install -r requirements.txt
# Add ANTHROPIC_API_KEY to .env
streamlit run app.py
```

## Note

For demonstration purposes only. Not financial advice. All data sourced from Yahoo Finance and should be verified before use in client-facing contexts.
```
