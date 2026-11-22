"""Weekly Status Report Agent: turns rough team updates into a clean report.

Built by Kavita at Zero to Live, Future Proof India.
"""
import os

import pandas as pd
import streamlit as st

from agent import run, to_markdown
from demo import SECTIONS
from prompts import SYSTEM_PROMPT

st.set_page_config(page_title="Weekly Status Report Agent", page_icon="📊", layout="wide")


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default)).strip()


API_KEY = setting("AI_API_KEY")
BASE_URL = setting("AI_BASE_URL", "https://api.openai.com/v1")
MODEL = setting("AI_MODEL", "gpt-4o-mini")

STATUS_COLOUR = {"Green": "#16a34a", "Amber": "#d97706", "Red": "#dc2626"}
SECTION_ICON = {"Highlights": "🌟", "Progress": "✅", "Risks": "⚠️", "Blockers": "⛔", "Next week": "📅"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; max-width: 1180px;}
      .hero {background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #fff; padding: 22px 26px;
             border-radius: 14px; margin-bottom: 16px;}
      .hero h1 {font-size: 1.75rem; margin: 0 0 6px 0; color: #ffffff;}
      .hero p {margin: 0; font-size: 1rem; opacity: 0.9;}
      .card {background: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.05);}
      .card h4 {margin: 0 0 8px 0; font-size: 1.02rem; color: #0f172a;}
      .item {padding: 7px 0; border-top: 1px dashed #e2e8f0; font-size: 0.93rem; line-height: 1.4;}
      .item:first-of-type {border-top: none;}
      .tag {display: inline-block; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3;
             margin-left: 6px;}
      .status {display: inline-block; color: #fff; font-weight: 700; padding: 6px 14px; border-radius: 999px; font-size: 0.95rem;}
      .step {color: #0f172a; padding: 8px 12px; border-left: 4px solid #16a34a; background: #f8fafc; margin-bottom: 8px; border-radius: 6px;}
      .step.bad {border-left-color: #d97706;}
      .footer {color: #64748b; font-size: 0.82rem; text-align: center; margin-top: 36px; padding: 12px 0; border-top: 1px solid #e2e8f0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Header: Clear title and one-line explainer
st.markdown(
    '<div class="hero">'
    "<h1>📊 Weekly Status Report Agent</h1>"
    "<p>Turn rough team updates into a clean, executive-ready weekly status report in seconds.</p>"
    "</div>",
    unsafe_allow_html=True,
)

if API_KEY:
    st.success(f"✅ Using a real AI model ({MODEL}).")
else:
    st.info("ℹ️ Demo mode: no AI key added yet, so the agent uses simple rules. Add your key in secrets to use a real model.")

SAMPLES = {
    "Sample 1: Normal fintech sprint": "samples/sample1.txt",
    "Sample 2: Normal platform sprint": "samples/sample2.txt",
    "Sample 3: Messy with typos": "samples/sample3.txt",
    "Sample 4: Very short updates": "samples/sample4.txt",
    "Sample 5: Missing key info": "samples/sample5.txt",
    "Banking portal (default)": "sample_updates.txt",
    "Cloud migration": "samples/cloud_migration.txt",
    "Telecom billing": "samples/telecom_billing.txt",
}


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


if "updates" not in st.session_state:
    st.session_state.updates = ""

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Team Notes")
    pick = st.selectbox("Choose a sample input", list(SAMPLES))
    c1, c2 = st.columns(2)
    if c1.button("Load sample", use_container_width=True):
        st.session_state.updates = read(SAMPLES[pick])
    up = c2.file_uploader("or upload a file", type=["txt", "md", "csv"], label_visibility="collapsed")
    if up is not None and st.session_state.get("_uploaded") != up.name:
        st.session_state.updates = up.read().decode("utf-8", errors="ignore")
        st.session_state._uploaded = up.name

    updates = st.text_area(
        "Paste weekly notes below:",
        key="updates",
        height=320,
        placeholder="Paste stand-up notes, Jira lines, or quick team emails...",
    )
    go = st.button("Write my report", type="primary", use_container_width=True)

with right:
    st.subheader("Generated Report")
    if go:
        if not updates.strip():
            st.warning("Please paste some notes first, or click 'Load sample'.")
        else:
            with st.spinner("Analyzing updates, checking for blockers, and drafting report..."):
                try:
                    result, steps = run(updates, SYSTEM_PROMPT, API_KEY, BASE_URL, MODEL)
                except Exception as err:
                    st.error(f"The AI model could not answer. Check your key and model name, then try again. Details: {err}")
                    st.stop()
            st.session_state.result, st.session_state.steps = result, steps

    result = st.session_state.get("result")
    steps = st.session_state.get("steps", [])

    if not result:
        st.markdown(
            '<div class="card"><h4>How it works</h4>'
            '<div class="item">1. Paste rough updates on the left, or click <b>Load sample</b>.</div>'
            '<div class="item">2. Click <b>Write my report</b>.</div>'
            '<div class="item">3. The agent categorizes items, assesses overall RAG status, checks its work, and highlights actions.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        items = result.get("items", [])
        count = lambda s: len([i for i in items if i.get("section") == s])
        colour = STATUS_COLOUR.get(result.get("status", ""), "#6b7280")

        # Status and Reason
        st.markdown(
            f'<div style="margin-bottom: 10px;">'
            f'<span class="status" style="background:{colour}">Status: {result.get("status", "Unknown")}</span>'
            f'&nbsp;&nbsp;<span style="color:#334155; font-weight: 500;">{result.get("status_reason", "")}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        # Headline
        if result.get("headline"):
            st.markdown(
                f'<div class="card" style="border-left: 5px solid {colour};">'
                f'<h4>What Matters Most This Week</h4>'
                f'<div style="font-size: 1.05rem; font-weight: 500;">{result["headline"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Executive Summary
        st.markdown(f"**Executive Summary:** {result.get('summary', 'Not enough information.')}")

        # Metrics row
        st.write("")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Highlights", count("Highlights"))
        k2.metric("Risks", count("Risks"))
        k3.metric("Blockers", count("Blockers"))
        k4.metric("Questions", len(result.get("questions", [])))

        # Clearly separated sections in tabs
        tab_report, tab_register, tab_actions, tab_email, tab_questions, tab_steps = st.tabs(
            ["Report", "Risks & Blockers", "Actions & Decisions", "Email to Sponsor", "Questions for Team", "Agent Steps"]
        )

        with tab_report:
            for s in SECTIONS:
                rows = [i for i in items if i.get("section") == s]
                body = "".join(
                    f'<div class="item">{i.get("text", "")}'
                    + (f'<span class="tag">👤 {i["owner"]}</span>' if i.get("owner") else "")
                    + (f'<span class="tag">📅 {i["due"]}</span>' if i.get("due") else "")
                    + "</div>"
                    for i in rows
                ) or '<div class="item" style="color:#94a3b8;">Nothing to report.</div>'
                st.markdown(f'<div class="card"><h4>{SECTION_ICON[s]} {s}</h4>{body}</div>', unsafe_allow_html=True)

        with tab_register:
            reg = [i for i in items if i.get("section") in ("Risks", "Blockers")]
            if reg:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Type": i["section"][:-1],
                                "Impact": i.get("impact") or "Not known",
                                "Owner": i.get("owner") or "Not known",
                                "Due": i.get("due") or "Not known",
                                "Item": i.get("text", ""),
                            }
                            for i in reg
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No risks or blockers recorded this week.")

        with tab_actions:
            st.markdown("#### Top Actions This Week")
            for n, a in enumerate(result.get("actions", []) or [], 1):
                st.markdown(
                    f'<div class="step"><b>{n}. {a.get("action", "")}</b><br>'
                    f'<span style="color:#475569">Owner: {a.get("owner") or "Not assigned"} · Why: {a.get("why", "")}</span></div>',
                    unsafe_allow_html=True,
                )
            if not result.get("actions"):
                st.write("No immediate actions logged.")

            st.markdown("#### Decisions Needed")
            for dcs in result.get("decisions", []) or ["No pending decisions."]:
                st.markdown(f"- {dcs}")

        with tab_email:
            st.markdown("#### Ready-to-Send Sponsor Email")
            st.text_area("Copy and paste to email:", result.get("email", "") or "No email draft available.", height=240)

        with tab_questions:
            st.markdown("#### Questions to Clarify with the Team")
            for q in result.get("questions", []) or ["All required information is complete."]:
                st.markdown(f"- {q}")

        with tab_steps:
            st.markdown("#### Self-Verification & Execution Log")
            for n, s in enumerate(steps, 1):
                st.markdown(
                    f'<div class="step {"" if s["ok"] else "bad"}"><b>{n}. {s["name"]}</b> {"✓" if s["ok"] else "!"}<br>'
                    f'<span style="color:#475569">{s["detail"]}</span></div>',
                    unsafe_allow_html=True,
                )

        st.write("")
        st.download_button(
            "Download Markdown Report",
            to_markdown(result),
            file_name="weekly-status-report.md",
            use_container_width=True,
        )
        st.caption("Factual report generated using strict source notes verification.")

# Footer
st.markdown('<div class="footer">Built by Kavita at Zero to Live, Future Proof India</div>', unsafe_allow_html=True)
