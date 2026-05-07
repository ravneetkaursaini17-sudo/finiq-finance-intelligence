#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 20:35:40 2026

@author: ravneetkaursaini
"""

# app.py


import streamlit as st
import pandas as pd
import numpy as np

from io import BytesIO


import importlib
import load_financials_csv
importlib.reload(load_financials_csv)


from finiq_engine import (
    load_financial_csv,
    load_apple_sample,
    FinancialModel,
    executive_brief_narrative,
    lens_narrative,
    why_cash_not_profit_narrative,
    scenario_judgment_narrative,
    peer_comparison_summary,
    plot_financial_trends,
    plot_waterfall_income,
)




# =========================
# PAGE CONFIG & STYLE
# =========================

st.set_page_config(
    page_title="FinIQ - Finance Intelligence Quotient",
    layout="wide",
    page_icon="💼",
)


# =========================
# COLORS
# =========================

PRIMARY_NAVY = "#0A1A2F"
GOLD = "#D4AF37"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F5F7FA"
TEAL = "#1ABC9C"
RED = "#E74C3C"



# =========================
# GLOBAL CSS / STYLE
# =========================


st.markdown(
    f"""
    <style>
    /* GLOBAL BACKGROUND */
    body {{
        background-color: {PRIMARY_NAVY};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}

    /* HEADER */
    .finiq-header {{
        background: linear-gradient(90deg, {PRIMARY_NAVY}, #12243A);
        padding: 18px 24px;
        border-radius: 10px;
        color: {WHITE};
        margin-bottom: 18px;
        border-bottom: 3px solid {GOLD};
    }}

    /* MAIN TITLE */
    .finiq-title {{
        font-family: 'Montserrat', sans-serif;
        font-size: 32px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: {WHITE};
        margin-bottom: 6px;
    }}

    /* SUBTITLE */
    .finiq-subtitle {{
        font-size: 16px;
        opacity: 0.85;
        color: {WHITE};
    }}

    /* SECTION TITLES */
    .finiq-section-title {{
        font-family: 'Montserrat', sans-serif;
        font-size: 22px;
        font-weight: 700;
        text-transform: uppercase;
        color: {WHITE};
        margin-top: 28px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }}

    /* CARDS */
    .finiq-card {{
        background-color: #1B2A41;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        margin-bottom: 12px;
        color: {WHITE};
    }}

    /* KPI VALUE */
    .finiq-kpi-value {{
        font-family: 'Roboto Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        color: {WHITE};
    }}

    /* KPI LABEL */
    .finiq-kpi-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: rgba(255,255,255,0.55);
    }}

    /* BADGES */
    .finiq-badge-green {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background-color: rgba(26,188,156,0.25);
        color: #1ABC9C;
        font-size: 11px;
        font-weight: 600;
    }}

    .finiq-badge-red {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background-color: rgba(231,76,60,0.25);
        color: #E74C3C;
        font-size: 11px;
        font-weight: 600;
    }}

    .finiq-badge-amber {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background-color: rgba(241,196,15,0.25);
        color: #F1C40F;
        font-size: 11px;
        font-weight: 600;
    }}

    /* NARRATIVE TEXT */
    .finiq-narrative {{
        font-size: 14px;
        line-height: 1.55;
        color: rgba(255,255,255,0.85);
    }}

    .finiq-narrative-title {{
        font-size: 14px;
        font-weight: 700;
        color: {WHITE};
        margin-bottom: 4px;
    }}

    .finiq-signal-dot {{
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# HEADER
# =========================

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50; margin-bottom: 10px;'>
        FINIQ — Finance Intelligence Dashboard
    </h1>
    <p style='text-align: center; color: #CCCCCC; font-size: 16px; margin-top: -10px;'>
        CFO‑Grade Financial Insights & Scenario Modeling
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# SIDEBAR INPUTS
# =========================
st.sidebar.title("⚙️ Configuration")

mode = st.sidebar.selectbox(
    "Mode",
    ["Demo (Apple sample)", "Upload your own file"],
)

uploaded_file = None
peer_file = None

if mode == "Upload your own file":
    uploaded_file = st.sidebar.file_uploader(
        "Upload main financials file (Excel)",
        type=["xlsx", "xls"],
    )

peer_file = st.sidebar.file_uploader(
    "Optional: Upload peer company file (CSV)",
    type=["csv"],
    )





# =========================
# DATA LOADING (DEMO + CUSTOM)
# =========================

col_mode, col_upload, col_peer, col_pdf = st.columns([1.2, 2.2, 2.0, 1.6])

with col_mode:
    mode = st.radio(
        "Mode",
        ["Demo (Apple sample)", "Upload File"],
        index=0,
        help="Demo uses Apple sample XLS so the dashboard is never blank.",
    )

uploaded_file = None
peer_file = None

with col_upload:
    if mode == "Upload File":
        uploaded_file = st.file_uploader(
    "Upload company file",
    type=["csv", "xls", "xlsx"],
            help="CSV must contain: year, revenue, cogs, opex, net_income, cfo, cfi, cff, cash, total_debt, equity, ar, ap, inventory, interest_expense, total_assets",
        )

with st.sidebar:
    st.markdown(
        "<div style='font-size:14px; font-weight:600; color:white; margin-bottom:6px;'>Peer File (Optional)</div>",
        unsafe_allow_html=True
    )

    peer_file = st.file_uploader(
        "Upload peer file",
        type=["csv", "xls", "xlsx"],
        label_visibility="collapsed"
    )



# =========================
# LOAD DATAFRAME
# =========================

from load_financials_csv import load_financial_xls

if mode == "Demo (Apple sample)":
    df = load_financial_xls("apple_financials.xlsx")
else:
    if uploaded_file is not None:
        df = load_financial_xls(uploaded_file)
    else:
        df = pd.DataFrame()

model = FinancialModel(df)

peer_model = None
if peer_file is not None:
    try:
        df_peer = load_financial_csv(peer_file)
        peer_model = FinancialModel(df_peer)
    except Exception as e:
        st.error(f"Peer file error: {e}")
                 
        
        


# =========================
# EXECUTIVE SUMMARY
# =========================

brief = executive_brief_narrative(model)
eq_score = brief["eq_score"]
subscores = brief["subscores"]

# Determine company name
if mode == "Demo (Apple sample)":
    company_name = "Apple"
else:
    if uploaded_file is not None:
        company_name = uploaded_file.name.split(".")[0]
    else:
        company_name = "Company"

st.markdown(f'<div class="finiq-section-title">Executive Summary — {company_name}</div>', unsafe_allow_html=True)

left, right = st.columns([3, 2])  # 60/40 split

with left:
    # EQ score + subscores + strengths/risks
    with st.container():
        st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
        st.markdown("**EQ Score (Financial Quality)**")
        st.markdown(
            f"<span class='finiq-kpi-value'>{eq_score:.0f}</span> / 100",
            unsafe_allow_html=True,
        )

        # Subscores
        sub_cols = st.columns(4)
        labels = ["Profitability", "Cash Flow", "Leverage", "Working Capital"]
        keys = ["profitability", "cash_flow_quality", "leverage", "working_capital"]
        for c, label, key in zip(sub_cols, labels, keys):
            with c:
                st.markdown(
                    f"<div class='finiq-kpi-label'>{label}</div>"
                    f"<div class='finiq-kpi-value' style='font-size:16px;'>{subscores[key]:.0f}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Strengths & risks
        st.markdown("**Strengths**")
        if brief["strengths"]:
            for s in brief["strengths"]:
                st.markdown(
                    f"<span class='finiq-signal-dot' style='background-color:{TEAL};'></span>{s}",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("_No major strengths flagged above benchmark thresholds._")

        st.markdown("**Risks**")
        if brief["risks"]:
            for r in brief["risks"]:
                st.markdown(
                    f"<span class='finiq-signal-dot' style='background-color:{RED};'></span>{r}",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("_No acute financial risks flagged versus typical thresholds._")

        st.markdown("</div>", unsafe_allow_html=True)

with right:
    # CEO lens narrative + key KPIs
    ceo_view = lens_narrative(model, "CEO")
    latest = model.df.iloc[-1]
    prev = model.df.iloc[-2] if len(model.df) > 1 else None

    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("<div class='finiq-narrative-title'>CEO Lens</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='finiq-narrative'>{ceo_view['text']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Key Momentum KPIs**")

    k1, k2 = st.columns(2)
    with k1:
        rev = latest["revenue"]
        rev_yoy = (
            (rev - prev["revenue"]) / prev["revenue"] * 100 if prev is not None and prev["revenue"] != 0 else np.nan
        )
        st.markdown("<div class='finiq-kpi-label'>Revenue (latest)</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='finiq-kpi-value'>{rev:.1f}M</div>",
            unsafe_allow_html=True,
            )

        if not np.isnan(rev_yoy):
            color = TEAL if rev_yoy >= 0 else RED
            st.markdown(
                f"<span style='color:{color}; font-size:12px;'>YoY: {rev_yoy:+.1f}%</span>",
                unsafe_allow_html=True,
            )

    with k2:
        op_margin = latest["operating_margin"]
        st.markdown("<div class='finiq-kpi-label'>Operating Margin</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='finiq-kpi-value'>{op_margin:.1f}%</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FINANCIAL HEALTH
# =========================

st.markdown('<div class="finiq-section-title">Financial Health</div>', unsafe_allow_html=True)
fh_left, fh_right = st.columns([3, 2])

with fh_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Revenue, EBITDA, Net Income, FCF**")
    fig1 = plot_financial_trends(model)
    st.pyplot(fig1)
    st.markdown("</div>", unsafe_allow_html=True)

with fh_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Revenue to Net Income Waterfall (Latest Year)**")
    fig2 = plot_waterfall_income(model)
    st.pyplot(fig2)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RATIOS
# =========================

st.markdown('<div class="finiq-section-title">Ratios & Metrics</div>', unsafe_allow_html=True)
rat_left, rat_right = st.columns([3, 2])

latest = model.df.iloc[-1]

def ratio_row(label, value, unit="%", good_high=True):
    if pd.isna(value):
        return "n/a"   # <-- IMPORTANT: return ONLY n/a
    color = TEAL if (value >= 0 and good_high) or (value <= 0 and not good_high) else RED
    return f"<span style='color:{color}; font-weight:600;'>{value:.1f}{unit}</span>"


with rat_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Profitability & Liquidity**")
    st.markdown(
        f"""
        - Gross margin: {ratio_row("Gross margin", latest["gross_margin"])}
        - Operating margin: {ratio_row("Operating margin", latest["operating_margin"])}
        - Net margin: {ratio_row("Net margin", latest["net_margin"])}
        - ROE: {ratio_row("ROE", latest["roe"])}
        - Current ratio: {ratio_row("Current ratio", latest["current_ratio"], unit="x")}
        - Quick ratio: {ratio_row("Quick ratio", latest["quick_ratio"], unit="x")}
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with rat_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Leverage & Efficiency**")
    st.markdown(
        f"""
        - Debt to equity: {ratio_row("Debt to equity", latest["debt_to_equity"], unit="x", good_high=False)}
        - Net leverage: {ratio_row("Net leverage", latest["net_leverage"], unit="x", good_high=False)}
        - Interest coverage: {ratio_row(None, latest["interest_coverage"], unit="x") if not pd.isna(latest["interest_coverage"]) else "n/a"}
        - AR days: {ratio_row("AR days", latest["ar_days"], unit="d", good_high=False)}
        - Inventory days: {ratio_row("Inventory days", latest["inventory_days"], unit="d", good_high=False)}
        - AP days: {ratio_row("AP days", latest["ap_days"], unit="d")}
        - Cash conversion cycle: {ratio_row("CCC", latest["ccc"], unit="d", good_high=False)}
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# WORKING CAPITAL
# =========================

st.markdown('<div class="finiq-section-title">Working Capital & Cash vs Profit</div>', unsafe_allow_html=True)
wc_left, wc_right = st.columns([3, 2])

with wc_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Working Capital Drivers**")
    st.markdown(
        f"""
        - AR days: **{latest['ar_days']:.1f} days**
        - Inventory days: **{latest['inventory_days']:.1f} days**
        - AP days: **{latest['ap_days']:.1f} days**
        - Cash conversion cycle: **{latest['ccc']:.1f} days**
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with wc_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("<div class='finiq-narrative-title'>Why Cash ≠ Profit</div>", unsafe_allow_html=True)
    wc_text = why_cash_not_profit_narrative(model)
    st.markdown(f"<div class='finiq-narrative'>{wc_text}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# NARRATIVES (CEO / CFO / ANALYST / INVESTOR)
# =========================

st.markdown('<div class="finiq-section-title">Strategic Narratives</div>', unsafe_allow_html=True)
n_left, n_right = st.columns([3, 2])

with n_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("<div class='finiq-narrative-title'>CEO Narrative</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='finiq-narrative'>{lens_narrative(model, 'CEO')['text']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='finiq-narrative-title' style='margin-top:10px;'>CFO Narrative</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='finiq-narrative'>{lens_narrative(model, 'CFO')['text']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with n_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("<div class='finiq-narrative-title'>Analyst Narrative</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='finiq-narrative'>{lens_narrative(model, 'ANALYST')['text']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='finiq-narrative-title' style='margin-top:10px;'>Investor Narrative</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='finiq-narrative'>{lens_narrative(model, 'INVESTOR')['text']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SCENARIO ENGINE
# =========================

st.markdown('<div class="finiq-section-title">Scenario Engine</div>', unsafe_allow_html=True)
sc_left, sc_right = st.columns([3, 2])

with sc_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Adjust Assumptions**")
    rev_delta = st.slider("Revenue change (%)", -20.0, 20.0, 0.0, 1.0)
    margin_delta = st.slider("Operating margin change (pts)", -5.0, 5.0, 0.0, 0.5)
    wc_delta = st.slider("Working capital days change", -30.0, 30.0, 0.0, 1.0)
    st.markdown("</div>", unsafe_allow_html=True)

scenario = model.run_scenario(rev_delta_pct=rev_delta, margin_delta_pct=margin_delta, wc_days_delta=wc_delta)
scenario_text = scenario_judgment_narrative(model, scenario, rev_delta, margin_delta, wc_delta)

with sc_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("<div class='finiq-narrative-title'>Scenario Judgment</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='finiq-narrative'>{scenario_text}</div>", unsafe_allow_html=True)
    st.markdown("---", unsafe_allow_html=True)
    st.markdown(
        f"**Base FCF vs Scenario FCF**  \n"
        f"- Base FCF: **${model.df.iloc[-1]['fcf']:.1f}M**  \n"
        f"- Scenario FCF: **${scenario['new_fcf']:.1f}M**",

        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RISK & COVENANTS
# =========================

st.markdown('<div class="finiq-section-title">Risk & Covenants</div>', unsafe_allow_html=True)
rk_left, rk_right = st.columns([3, 2])

risk = model.risk_covenant_summary()

def badge_for_value(val, good_high=True):
    if val is None:
        return "<span class='finiq-badge-amber'>n/a</span>"
    if good_high:
        if val >= 0:
            return "<span class='finiq-badge-green'>Comfortable</span>"
        else:
            return "<span class='finiq-badge-red'>Tight</span>"
    else:
        if val <= 0:
            return "<span class='finiq-badge-green'>Comfortable</span>"
        else:
            return "<span class='finiq-badge-red'>Elevated</span>"

with rk_left:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Covenant Headroom**")
    st.markdown(
        f"""
        - Net leverage: **{risk['net_leverage'] if risk['net_leverage'] is not None else 'n/a'}x**  
        Headroom vs limit: **{risk['leverage_headroom'] if risk['leverage_headroom'] is not None else 'n/a'}x** {badge_for_value(risk['leverage_headroom'], good_high=True)}

        - Interest coverage: **{f"{risk['interest_coverage']:.1f}x" if risk['interest_coverage'] is not None else "n/a"}**  
        Headroom vs limit: **{f"{risk['coverage_headroom']:.1f}x" if risk['coverage_headroom'] is not None else "n/a"}** {badge_for_value(risk['coverage_headroom'], good_high=True)}

        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with rk_right:
    st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
    st.markdown("**Risk Summary**")
    if risk["risks"]:
        for r in risk["risks"]:
            st.markdown(
                f"<span class='finiq-signal-dot' style='background-color:{RED};'></span>{r}",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("_No acute risk flags based on leverage, coverage, FCF, and cash._")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# PEER COMPARISON (OPTIONAL)
# =========================

if peer_model is not None:
    st.markdown('<div class="finiq-section-title">Peer Comparison</div>', unsafe_allow_html=True)
    pc_left, pc_right = st.columns([3, 2])

    summary = peer_comparison_summary(model, peer_model)

    with pc_left:
        st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
        st.markdown("**Key Metrics (Latest Year)**")
        for metric, vals in summary.items():
            a = vals["A"]
            b = vals["B"]
            if a is None or b is None:
                continue
            if metric in ["revenue", "fcf"]:
                a_disp = f"${a/1_000_000:.1f}M"
                b_disp = f"${b/1_000_000:.1f}M"
            elif metric in ["ccc"]:
                a_disp = f"{a:.1f}d"
                b_disp = f"{b:.1f}d"
            else:
                a_disp = f"{a:.1f}"
                b_disp = f"{b:.1f}"

            if metric in ["ccc", "net_leverage"]:
                winner = "A" if a < b else "B"
            else:
                winner = "A" if a > b else "B"

            winner_badge = (
                "<span class='finiq-badge-green'>Lead</span>" if winner == "A" else "<span class='finiq-badge-amber'>Peer Lead</span>"
            )

            st.markdown(
                f"- **{metric.replace('_', ' ').title()}**  \n"
                f"  - Company A: {a_disp}  \n"
                f"  - Company B: {b_disp}  \n"
                f"  {winner_badge}",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with pc_right:
        st.markdown('<div class="finiq-card">', unsafe_allow_html=True)
        st.markdown(
        "<div class='finiq-narrative-title'>Peer Interpretation</div>",
        unsafe_allow_html=True,
        )
        st.markdown(
        "<div class='finiq-narrative'>The peer comparison highlights where the company leads on scale, margins, "
        "cash conversion, and balance sheet resilience versus a chosen benchmark. Persistent gaps in CCC, "
        "net leverage, or interest coverage often signal where execution or capital structure needs attention.</div>",
        unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
