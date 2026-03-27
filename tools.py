"""
BEACON financial data tools using yfinance.
No API key required.
"""

import yfinance as yf
from typing import Any


def get_stock_info(ticker: str) -> dict[str, Any]:
    """
    Get current stock price, company overview, and key metrics for a ticker.
    """
    ticker = ticker.upper().strip()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "company_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice", "N/A"),
            "previous_close": info.get("previousClose", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "analyst_target_price": info.get("targetMeanPrice", "N/A"),
            "recommendation": info.get("recommendationKey", "N/A"),
            "business_summary": (info.get("longBusinessSummary") or "")[:300] + "..."
                if len(info.get("longBusinessSummary") or "") > 300
                else info.get("longBusinessSummary", "N/A"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_portfolio_summary(tickers: list[str]) -> list[dict[str, Any]]:
    """
    Get stock info for a list of tickers (client portfolio).
    """
    return [get_stock_info(t) for t in tickers if t.strip()]


def get_market_news(ticker: str) -> list[dict[str, Any]]:
    """
    Get recent news headlines for a ticker.
    """
    ticker = ticker.upper().strip()
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []
        results = []
        for item in news[:5]:
            results.append({
                "title": item.get("title", "N/A"),
                "publisher": item.get("publisher", "N/A"),
                "link": item.get("link", ""),
                "published": item.get("providerPublishTime", "N/A"),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def format_stock_for_claude(info: dict) -> str:
    """Format stock info dict into readable string for Claude."""
    if "error" in info:
        return f"[{info.get('ticker')}] Error: {info['error']}"

    return (
        f"[{info['ticker']}] {info['company_name']}\n"
        f"  Sector: {info['sector']} | Industry: {info['industry']}\n"
        f"  Price: ${info['current_price']} | Prev Close: ${info['previous_close']}\n"
        f"  52W High: ${info['52_week_high']} | 52W Low: ${info['52_week_low']}\n"
        f"  Market Cap: {info['market_cap']} | P/E: {info['pe_ratio']}\n"
        f"  Dividend Yield: {info['dividend_yield']}\n"
        f"  Analyst Target: ${info['analyst_target_price']} | Recommendation: {info['recommendation']}\n"
        f"  Summary: {info['business_summary']}\n"
    )


def format_news_for_claude(ticker: str, news: list[dict]) -> str:
    """Format news list into readable string for Claude."""
    if not news or "error" in news[0]:
        return f"No recent news found for {ticker}."

    lines = [f"Recent news for {ticker}:"]
    for i, item in enumerate(news, 1):
        lines.append(f"  {i}. {item['title']} ({item['publisher']})")
    return "\n".join(lines)


__all__ = [
    "get_stock_info",
    "get_portfolio_summary",
    "get_market_news",
    "format_stock_for_claude",
    "format_news_for_claude",
]
