import streamlit as st
from agent import run_beacon

st.set_page_config(
    page_title="BEACON — Advisor Meeting Prep",
    page_icon="🔦",
    layout="wide",
)


def _init_state() -> None:
    st.session_state.setdefault("brief", "")
    st.session_state.setdefault("tasks", "")
    st.session_state.setdefault("steps", [])
    st.session_state.setdefault("ran", False)


def _reset() -> None:
    st.session_state["brief"] = ""
    st.session_state["tasks"] = ""
    st.session_state["steps"] = []
    st.session_state["ran"] = False


_init_state()

# ---------------------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔦 BEACON")
    st.caption("Advisor Intelligence & Meeting Prep Agent")
    st.divider()

    client_name = st.text_input("Client Name", placeholder="e.g. Sarah Johnson")

    meeting_type = st.selectbox(
        "Meeting Type",
        ["Annual Review", "Quarterly Check-in", "Onboarding", "Financial Planning", "Tax Planning"],
    )

    tickers_input = st.text_input(
        "Portfolio Tickers (comma-separated)",
        placeholder="e.g. AAPL, MSFT, JPM",
    )

    st.divider()

    st.markdown("**Try a sample client:**")
    if st.button("Load Sarah Johnson", use_container_width=True):
        st.session_state["sample"] = {
            "client_name": "Sarah Johnson",
            "meeting_type": "Annual Review",
            "tickers": "AAPL, MSFT, JNJ",
        }
        st.rerun()

    if st.button("Load David Chen", use_container_width=True):
        st.session_state["sample"] = {
            "client_name": "David Chen",
            "meeting_type": "Quarterly Check-in",
            "tickers": "GOOGL, AMZN, NVDA",
        }
        st.rerun()

    st.divider()
    if st.button("New Session", use_container_width=True, type="secondary"):
        _reset()
        st.session_state.pop("sample", None)
        st.rerun()

# Apply sample if selected
if "sample" in st.session_state:
    sample = st.session_state.pop("sample")
    client_name = sample["client_name"]
    meeting_type = sample["meeting_type"]
    tickers_input = sample["tickers"]
    st.session_state["client_name_display"] = client_name

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown("## 🔦 BEACON")
st.caption("Advisor Intelligence & Meeting Prep Agent — Powered by Claude + LangGraph + Live Market Data")
st.divider()

if not st.session_state["ran"]:
    # Input form
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Prepare a Meeting Brief")
        st.markdown(
            "Enter your client's name, meeting type, and portfolio tickers. "
            "BEACON will fetch live market data and generate a structured brief in seconds."
        )

    generate = st.button(
        "Generate Meeting Brief",
        type="primary",
        use_container_width=True,
        disabled=not (client_name and tickers_input),
    )

    if generate:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if not tickers:
            st.error("Please enter at least one ticker.")
        else:
            with st.spinner("Fetching live market data and generating brief..."):
                result = run_beacon(
                    client_name=st.session_state.get("client_name_display") or client_name or "Client",
                    meeting_type=meeting_type,
                    tickers=tickers,
                )
            st.session_state["brief"] = result.get("brief", "")
            st.session_state["tasks"] = result.get("tasks", "")
            st.session_state["steps"] = result.get("steps", [])
            st.session_state["ran"] = True
            st.rerun()

else:
    # Results view
    st.markdown(f"### 📋 Meeting Brief — {st.session_state.get('client_name_display', client_name)}")

    # Transparency expander
    steps = st.session_state.get("steps", [])
    if steps:
        with st.expander("🔎 How BEACON prepared this brief"):
            for step in steps:
                st.markdown(step)

    # Brief
    st.markdown(st.session_state["brief"].replace("$", "\\$"))

    st.divider()

    # Meeting notes → task extraction
    st.markdown("### 📝 Meeting Notes")
    st.caption("Paste your meeting notes below and BEACON will extract follow-up tasks.")

    notes = st.text_area(
        "Meeting Notes",
        height=200,
        placeholder="e.g. Client wants to increase bond allocation, concerned about tech concentration, asked about estate planning options...",
        label_visibility="collapsed",
    )

    if st.button("Extract Follow-up Tasks", type="primary", disabled=not notes.strip()):
        with st.spinner("Extracting tasks..."):
            result = run_beacon(
                client_name=client_name or "Client",
                meeting_type=meeting_type or "Meeting",
                tickers=[],
                notes=notes,
            )
        st.session_state["tasks"] = result.get("tasks", "")

    if st.session_state.get("tasks"):
        st.markdown("### ✅ Follow-up Tasks")
        st.markdown(st.session_state["tasks"])
