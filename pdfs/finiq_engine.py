#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 13:03:57 2026

@author: ravneetkaursaini
"""



"""
FinIQ - Finance Intelligence Quotient
CFO-grade financial intelligence engine:
- CSV ingestion (user-uploaded + Apple sample)
- SQLite storage
- Full financial model (IS/BS/CF)
- Ratios, EQ score, WC engine, scenarios, risk
- CEO/CFO/Analyst/Investor narratives
- Optional peer comparison (second upload)

You will wrap this in Streamlit:
- Upload: CSV for Company A (+ optional Company B)
- Demo: Apple sample CSV
- Tabs: Executive, Health, Ratios, WC, Narratives, Scenario, Risk, Peer
"""


import io
import re
import sqlite3
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# =========================================================
# CONFIG
# =========================================================

DB_PATH = "finiq.db"

APPLE_SAMPLE_XLS = "apple_financials.xls"  # you’ll create this from Apple 10-K

# =========================================================
# UTILS
# =========================================================

def safe_div(a, b):
    return np.where(b == 0, np.nan, a / b)

def format_pct(x):
    if pd.isna(x):
        return "n/a"
    return f"{x:.1f}%"

def format_num(x):
    if pd.isna(x):
        return "n/a"
    return f"${x/1_000_000:.1f}M"

def trend_arrow(series: pd.Series) -> str:
    series = series.dropna()
    if len(series) < 2:
        return "stable"
    last, prev = series.iloc[-1], series.iloc[-2]
    if last > prev * 1.02:
        return "improving"
    elif last < prev * 0.98:
        return "deteriorating"
    else:
        return "stable"

# =========================================================
# SQL LAYER — SQLite (Option A)
# =========================================================

def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ticker TEXT,
        sector TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        revenue REAL,
        cogs REAL,
        opex REAL,
        ebitda REAL,
        net_income REAL,
        cfo REAL,
        cfi REAL,
        cff REAL,
        cash REAL,
        total_debt REAL,
        equity REAL,
        ar REAL,
        ap REAL,
        inventory REAL,
        interest_expense REAL,
        total_assets REAL,
        UNIQUE(company_id, year),
        FOREIGN KEY(company_id) REFERENCES companies(id)
    );
    """)

    conn.commit()
    conn.close()

def upsert_company(name: str, ticker: Optional[str] = None, sector: Optional[str] = None,
                   db_path: str = DB_PATH) -> int:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM companies WHERE name = ? AND IFNULL(ticker,'') = IFNULL(?, '')",
                (name, ticker))
    row = cur.fetchone()
    if row:
        company_id = row[0]
    else:
        cur.execute("INSERT INTO companies (name, ticker, sector) VALUES (?, ?, ?)",
                    (name, ticker, sector))
        company_id = cur.lastrowid
    conn.commit()
    conn.close()
    return company_id

def upsert_statements(company_id: int, df: pd.DataFrame, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for _, r in df.iterrows():
        cur.execute("""
        INSERT OR REPLACE INTO statements (
            company_id, year, revenue, cogs, opex, ebitda, net_income,
            cfo, cfi, cff, cash, total_debt, equity, ar, ap, inventory,
            interest_expense, total_assets
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            int(r["year"]),
            r.get("revenue"),
            r.get("cogs"),
            r.get("opex"),
            r.get("ebitda"),
            r.get("net_income"),
            r.get("cfo"),
            r.get("cfi"),
            r.get("cff"),
            r.get("cash"),
            r.get("total_debt"),
            r.get("equity"),
            r.get("ar"),
            r.get("ap"),
            r.get("inventory"),
            r.get("interest_expense"),
            r.get("total_assets"),
        ))
    conn.commit()
    conn.close()

def load_company_statements(company_id: int, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT year, revenue, cogs, opex, ebitda, net_income, cfo, cfi, cff, cash, "
        "total_debt, equity, ar, ap, inventory, interest_expense, total_assets "
        "FROM statements WHERE company_id = ? ORDER BY year",
        conn,
        params=(company_id,),
    )
    conn.close()
    return df

# =========================================================
# INGESTION — CSV ONLY (CUSTOM MODE + DUMMY MODE)
# =========================================================



REQUIRED_COLUMNS = [
    "year","revenue","cogs","opex","net_income","cfo","cfi","cff",
    "cash","total_debt","equity","ar","ap","inventory",
    "interest_expense","total_assets"
]

def load_financial_csv(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xls") or file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type. Upload CSV, XLS, or XLSX.")


    # 1. Validate required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # 2. Clean numeric columns
    for col in REQUIRED_COLUMNS:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("(", "-", regex=False)
            .str.replace(")", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Sort by year
    df = df.sort_values("year").reset_index(drop=True)

    return df

    

# =========================================================
# FINANCIAL MODEL
# =========================================================

@dataclass
class IndustryBenchmarks:
    profitability: Dict[str, float]
    liquidity: Dict[str, float]
    leverage: Dict[str, float]
    efficiency: Dict[str, float]

def default_benchmarks() -> IndustryBenchmarks:
    return IndustryBenchmarks(
        profitability={"gross_margin": 40, "operating_margin": 15, "roe": 12},
        liquidity={"current_ratio": 1.5, "quick_ratio": 1.2, "cash_ratio": 0.3},
        leverage={"debt_to_equity": 0.8, "interest_coverage": 4.0, "net_leverage": 2.5},
        efficiency={"ar_days": 45, "inventory_days": 60, "ap_days": 40, "ccc": 65},
    )

class FinancialModel:
    def __init__(self, df: pd.DataFrame, benchmarks: Optional[IndustryBenchmarks] = None):
        self.df = df.sort_values("year").reset_index(drop=True)
        self.benchmarks = benchmarks or default_benchmarks()
        self._compute_derived_fields()

    def _compute_derived_fields(self):
        df = self.df

        df["gross_profit"] = df["revenue"] - df["cogs"]
        df["operating_income"] = df["gross_profit"] - df["opex"]
        df["fcf"] = df["cfo"] + df["cfi"] + df["cff"]

        df["gross_margin"] = safe_div(df["gross_profit"], df["revenue"]) * 100
        df["operating_margin"] = safe_div(df["operating_income"], df["revenue"]) * 100
        df["net_margin"] = safe_div(df["net_income"], df["revenue"]) * 100

        df["roe"] = safe_div(df["net_income"], df["equity"]) * 100
        df["roa"] = safe_div(df["net_income"], (df["equity"] + df["total_debt"])) * 100

        df["current_ratio"] = safe_div(
            df["ar"] + df["inventory"] + df["cash"], df["ap"] + df["total_debt"]
        )
        df["quick_ratio"] = safe_div(
            df["ar"] + df["cash"], df["ap"] + df["total_debt"]
        )
        df["cash_ratio"] = safe_div(df["cash"], df["ap"] + df["total_debt"])

        df["debt_to_equity"] = safe_div(df["total_debt"], df["equity"])
        df["net_debt"] = df["total_debt"] - df["cash"]
        df["net_leverage"] = safe_div(df["net_debt"], df["ebitda"])
        df["interest_coverage"] = safe_div(df["operating_income"], df["interest_expense"])

        df["ar_days"] = safe_div(df["ar"], df["revenue"]) * 365
        df["inventory_days"] = safe_div(df["inventory"], df["cogs"]) * 365
        df["ap_days"] = safe_div(df["ap"], df["cogs"]) * 365
        df["ccc"] = df["ar_days"] + df["inventory_days"] - df["ap_days"]

        df["accrual_ratio"] = safe_div(df["net_income"] - df["cfo"], df["total_assets"])

        self.df = df

    # EQ score & badges

    def compute_eq_score(self) -> Tuple[float, Dict[str, float]]:
        df = self.df
        latest = df.iloc[-1]

        prof = np.nanmean([
            latest["gross_margin"],
            latest["operating_margin"],
            latest["roe"],
        ])
        prof_score = np.interp(prof, [0, 40], [20, 100])

        accrual = latest["accrual_ratio"]
        if pd.isna(accrual):
            cfq_score = 60
        else:
            cfq_score = np.interp(-accrual, [-0.2, 0.2], [20, 100])

        lev = latest["net_leverage"]
        if pd.isna(lev):
            lev_score = 60
        else:
            lev_score = np.interp(-lev, [-5, 0], [20, 100])

        ccc = latest["ccc"]
        if pd.isna(ccc):
            wc_score = 60
        else:
            wc_score = np.interp(-ccc, [-150, 0], [20, 100])

        subscores = {
            "profitability": float(prof_score),
            "cash_flow_quality": float(cfq_score),
            "leverage": float(lev_score),
            "working_capital": float(wc_score),
        }
        eq_score = float(np.mean(list(subscores.values())))
        return eq_score, subscores

    def fcf_quality_badge(self) -> str:
        df = self.df
        latest = df.iloc[-1]
        ni, cfo = latest["net_income"], latest["cfo"]
        if pd.isna(ni) or pd.isna(cfo) or ni == 0:
            return "Medium"
        ratio = cfo / ni
        if ratio >= 1.0:
            return "High"
        elif ratio >= 0.6:
            return "Medium"
        else:
            return "Low"

    def working_capital_health(self) -> str:
        df = self.df
        latest = df.iloc[-1]
        ccc = latest["ccc"]
        if pd.isna(ccc):
            return "Neutral"
        if ccc < 60:
            return "Efficient"
        elif ccc < 90:
            return "Neutral"
        else:
            return "Strained"

    # Scenario engine

    def run_scenario(self, rev_delta_pct=0.0, margin_delta_pct=0.0, wc_days_delta=0.0) -> Dict[str, float]:
        base = self.df.iloc[-1].copy()

        new_revenue = base["revenue"] * (1 + rev_delta_pct / 100)
        base_op_margin = base["operating_margin"]
        new_op_margin = base_op_margin + margin_delta_pct
        new_operating_income = new_revenue * new_op_margin / 100

        ebitda_margin = safe_div(base["ebitda"], base["revenue"])
        new_ebitda = new_revenue * ebitda_margin

        new_ar_days = base["ar_days"] + wc_days_delta
        new_inventory_days = base["inventory_days"] + wc_days_delta
        new_ap_days = base["ap_days"] + wc_days_delta
        new_ccc = new_ar_days + new_inventory_days - new_ap_days

        base_ccc = base["ccc"]
        delta_ccc = new_ccc - base_ccc
        wc_impact = (delta_ccc / 365) * (new_revenue / 4)

        base_cfo = base["cfo"]
        new_cfo = base_cfo - wc_impact
        new_fcf = new_cfo + base["cfi"] + base["cff"]
        new_cash = base["cash"] + new_fcf

        return {
            "new_revenue": float(new_revenue),
            "new_operating_income": float(new_operating_income),
            "new_ebitda": float(new_ebitda),
            "new_ccc": float(new_ccc),
            "wc_impact": float(wc_impact),
            "new_cfo": float(new_cfo),
            "new_fcf": float(new_fcf),
            "new_cash": float(new_cash),
        }

    # Risk & covenant

    def risk_covenant_summary(self, leverage_limit=3.5, coverage_limit=3.0) -> Dict:
        df = self.df
        latest = df.iloc[-1]

        net_leverage = latest["net_leverage"]
        interest_cov = latest["interest_coverage"]
        cash = latest["cash"]
        fcf = latest["fcf"]

        lev_headroom = leverage_limit - net_leverage if not pd.isna(net_leverage) else np.nan
        cov_headroom = interest_cov - coverage_limit if not pd.isna(interest_cov) else np.nan

        risks = []
        if not pd.isna(net_leverage) and net_leverage > leverage_limit:
            risks.append("Leverage is above typical covenant comfort levels.")
        if not pd.isna(interest_cov) and interest_cov < coverage_limit:
            risks.append("Interest coverage is thin; earnings may not comfortably cover interest.")
        if not pd.isna(fcf) and fcf < 0:
            risks.append("Free cash flow is negative; the business is consuming cash.")
        if not pd.isna(cash) and cash < 0.1 * df["revenue"].iloc[-1]:
            risks.append("Cash balance is low relative to revenue scale.")

        return {
            "net_leverage": float(net_leverage) if not pd.isna(net_leverage) else None,
            "interest_coverage": float(interest_cov) if not pd.isna(interest_cov) else None,
            "cash": float(cash) if not pd.isna(cash) else None,
            "fcf": float(fcf) if not pd.isna(fcf) else None,
            "leverage_headroom": float(lev_headroom) if not pd.isna(lev_headroom) else None,
            "coverage_headroom": float(cov_headroom) if not pd.isna(cov_headroom) else None,
            "risks": risks,
        }

# =========================================================
# NARRATIVES — CEO-STYLE, DATA-DRIVEN
# =========================================================

def format_num(x):
    if pd.isna(x):
        return "$0.0M"
    return f"${x:.1f}M"   # values already in millions



def executive_brief_narrative(model: FinancialModel) -> Dict:
    df = model.df
    latest = df.iloc[-1]
    eq_score, subscores = model.compute_eq_score()
    wc_health = model.working_capital_health()
    fcf_badge = model.fcf_quality_badge()
    risk_summary = model.risk_covenant_summary()

    strengths, risks = [], []

    if latest["operating_margin"] > model.benchmarks.profitability["operating_margin"]:
        strengths.append("Operating margins are running ahead of typical industry comfort levels.")
    if fcf_badge == "High":
        strengths.append("Earnings are consistently converting into cash.")
    if risk_summary["net_leverage"] is not None and risk_summary["net_leverage"] < 2.0:
        strengths.append("Leverage is moderate and the capital structure is manageable.")

    if wc_health == "Strained":
        risks.append("Working capital is tying up cash and extending the cash conversion cycle.")
    if fcf_badge == "Low":
        risks.append("Profitability is not translating into free cash flow, which pressures liquidity.")
    risks.extend(risk_summary["risks"])

    strengths = strengths[:3]
    risks = risks[:3]

    if eq_score >= 75:
        core_narrative = "This is a financially resilient business with room to invest and absorb volatility."
    elif eq_score >= 55:
        core_narrative = "The business is fundamentally sound but carrying emerging financial pressure that leadership should address early."
    else:
        core_narrative = "The financial profile is fragile; leadership needs to prioritize cash, simplify the balance sheet, and protect runway."

    if wc_health == "Strained" or fcf_badge == "Low":
        action = "Tighten working capital discipline, protect free cash flow, and revisit capital allocation until cash generation stabilizes."
    else:
        action = "Continue disciplined investment in the highest-return areas while preserving balance sheet flexibility."

    return {
        "eq_score": eq_score,
        "subscores": subscores,
        "strengths": strengths,
        "risks": risks,
        "core_narrative": core_narrative,
        "recommended_action": action,
    }

def lens_narrative(model: FinancialModel, lens: str = "CEO") -> Dict:
    df = model.df
    latest = df.iloc[-1]
    eq_score, _ = model.compute_eq_score()
    wc_health = model.working_capital_health()
    fcf_badge = model.fcf_quality_badge()

    lens = lens.upper()

    if lens == "CEO":
        text = (
            f"This business is generating {format_num(latest['revenue'])} in annual revenue with an operating margin of "
            f"{format_pct(latest['operating_margin'])}. The overall financial quality score sits at {eq_score:.0f}, "
            "which signals a platform that can support growth but still demands disciplined execution. "
            f"Free cash flow quality is {fcf_badge.lower()}, and working capital is currently {wc_health.lower()}, "
            "which means cash generation will either amplify or constrain strategic choices over the next 12–24 months."
        )
        questions = [
            "Where is growth creating durable value versus just adding complexity?",
            "What would it take to improve cash conversion by 10–15 days?",
            "Which investments are truly strategic versus simply habitual?",
        ]
    elif lens == "CFO":
        text = (
            f"From a finance lens, the company’s operating margin of {format_pct(latest['operating_margin'])} and "
            f"net margin of {format_pct(latest['net_margin'])} provide a solid earnings base, but the real story sits in cash. "
            f"Free cash flow quality is rated {fcf_badge.lower()}, and working capital is {wc_health.lower()}, which directly "
            "influences liquidity and covenant headroom. Net leverage and interest coverage need to be monitored against "
            "internal thresholds, especially if growth requires incremental capex or restructuring."
        )
        questions = [
            "Where are we losing the most days in the cash conversion cycle?",
            "How much covenant headroom do we have under a downside scenario?",
            "Which cost lines can be structurally reset without damaging the franchise?",
        ]
    elif lens == "ANALYST":
        text = (
            "The financial profile shows a clear set of drivers that explain recent performance. Revenue growth, margin evolution, "
            "and working capital movements together determine the trajectory of free cash flow. The divergence between net income "
            "and operating cash flow, combined with changes in AR, inventory, and AP days, highlights where operational execution "
            "is either supporting or undermining the P&L story."
        )
        questions = [
            "What portion of margin change is driven by mix versus pure pricing?",
            "How much of working capital movement is structural versus timing-related?",
            "Which segments are diluting returns?",
        ]
    else:  # INVESTOR
        text = (
            "Viewed through an investor lens, the company’s appeal rests on the durability of its cash flows, the efficiency of its "
            "capital allocation, and the resilience of its balance sheet. Profitability levels, return on equity, and free cash flow "
            "conversion indicate how effectively management turns revenue into distributable value."
        )
        questions = [
            "Is free cash flow growth keeping pace with revenue growth?",
            "Does leverage enhance returns or simply increase fragility?",
            "Are capital allocation decisions compounding value over time?",
        ]

    return {"lens": lens, "text": text, "questions": questions}

def why_cash_not_profit_narrative(model: FinancialModel) -> str:
    df = model.df
    latest = df.iloc[-1]
    return (
        f"On paper, the business reports net income of {format_num(latest['net_income'])}, but cash tells a more nuanced story. "
        f"Operating cash flow of {format_num(latest['cfo'])} reflects the real pace at which earnings convert into liquidity. "
        f"A cash conversion cycle of {latest['ccc']:.0f} days explains why cash may lag profit: receivables, inventory, and payables "
        "either pull cash forward or push it out. The leadership imperative is to treat working capital as a strategic lever, not an afterthought."
    )

def scenario_judgment_narrative(model: FinancialModel, scenario: Dict, rev_delta_pct, margin_delta_pct, wc_days_delta) -> str:
    df = model.df
    latest = df.iloc[-1]
    base_fcf = latest["fcf"]
    new_fcf = scenario["new_fcf"]
    delta_fcf = new_fcf - base_fcf

    if new_fcf < 0 and base_fcf >= 0:
        verdict = "Under this scenario, the business flips from generating cash to consuming it, compressing strategic flexibility."
    elif new_fcf < base_fcf:
        verdict = "This scenario erodes free cash flow, narrowing the margin for error and tightening capital allocation choices."
    else:
        verdict = "Even under this scenario, free cash flow remains positive, giving leadership room to invest and absorb volatility."

    return (
        f"With revenue adjusted by {rev_delta_pct:+.1f}% and operating margin shifted by {margin_delta_pct:+.1f} points, "
        f"free cash flow moves by {format_num(delta_fcf)} versus the base case. Changes in working capital days of "
        f"{wc_days_delta:+.1f} drive an incremental cash impact of {format_num(scenario['wc_impact'])}. {verdict}"
    )

# =========================================================
# VISUALS
# =========================================================

def plot_financial_trends(model: FinancialModel):
    df = model.df
    years = df["year"]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(years, df["revenue"], color="#1f77b4", marker="o", label="Revenue")
    ax1.plot(years, df["ebitda"], color="#2ca02c", marker="o", label="EBITDA")
    ax1.plot(years, df["net_income"], color="#ff7f0e", marker="o", label="Net Income")
    ax1.plot(years, df["fcf"], color="#d62728", marker="o", label="Free Cash Flow")

    ax1.set_xlabel("Year")
    ax1.set_ylabel("Amount (USD)")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${x:.0f}M"))
    ax1.set_title("Financial Health: Revenue, EBITDA, Net Income, FCF")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(years, df["gross_margin"], color="#9467bd", linestyle="--", marker="x", label="Gross Margin")
    ax2.plot(years, df["operating_margin"], color="#8c564b", linestyle="--", marker="x", label="Operating Margin")
    ax2.plot(years, df["net_margin"], color="#e377c2", linestyle="--", marker="x", label="Net Margin")
    ax2.set_ylabel("Margin (%)")
    ax2.legend(loc="lower right")

    plt.tight_layout()
    return fig

def plot_waterfall_income(model: FinancialModel):
    df = model.df
    latest = df.iloc[-1]

    labels = ["Revenue", "COGS", "Opex", "Other", "Net Income"]
    revenue = latest["revenue"]
    cogs = -latest["cogs"]
    opex = -latest["opex"]
    other = latest["operating_income"] - latest["net_income"]
    net_income = latest["net_income"]

    values = [revenue, cogs, opex, other, net_income]

    fig, ax = plt.subplots(figsize=(8, 5))

    cum_values = [0]
    for v in values[:-1]:
        cum_values.append(cum_values[-1] + v)

    colors = ["#1f77b4", "#d62728", "#d62728", "#7f7f7f", "#2ca02c"]

    for i, (label, v) in enumerate(zip(labels, values)):
        if i == 0:
            ax.bar(i, v, color=colors[i])
        elif i == len(labels) - 1:
            ax.bar(i, v, bottom=cum_values[i], color=colors[i])
        else:
            ax.bar(i, v, bottom=cum_values[i], color=colors[i])

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Amount (USD)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${x:.0f}M"))
    ax.set_title("Revenue to Net Income Waterfall")
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    return fig

# =========================================================
# PEER COMPARISON (OPTIONAL SECOND UPLOAD)
# =========================================================

def peer_comparison_summary(model_a: FinancialModel, model_b: FinancialModel) -> Dict:
    a = model_a.df.iloc[-1]
    b = model_b.df.iloc[-1]

    def pick(series_name):
        return {
            "A": float(a[series_name]) if not pd.isna(a[series_name]) else None,
            "B": float(b[series_name]) if not pd.isna(b[series_name]) else None,
        }

    return {
        "revenue": pick("revenue"),
        "operating_margin": pick("operating_margin"),
        "net_margin": pick("net_margin"),
        "ccc": pick("ccc"),
        "net_leverage": pick("net_leverage"),
        "interest_coverage": pick("interest_coverage"),
        "fcf": pick("fcf"),
    }

# =========================================================
# APPLE SAMPLE LOADER (for demo mode)
# =========================================================

def load_apple_sample(path=APPLE_SAMPLE_XLS):
    return pd.read_excel(path)

# =========================================================
# LOCAL TEST (you’ll replace with Streamlit UI)
# =========================================================

if __name__ == "__main__":
    init_db()

    # DEMO MODE: load Apple sample CSV so dashboard is never blank
    df = load_apple_sample()  # reads APPLE_SAMPLE_CSV

    company_id = upsert_company("Apple Inc.", "AAPL")
    upsert_statements(company_id, df)
    df_loaded = load_company_statements(company_id)

    model = FinancialModel(df_loaded)
    brief = executive_brief_narrative(model)
    ceo_view = lens_narrative(model, "CEO")
    wc_text = why_cash_not_profit_narrative(model)

    scenario = model.run_scenario(rev_delta_pct=-5, margin_delta_pct=-1, wc_days_delta=5)
    scenario_text = scenario_judgment_narrative(model, scenario, -5, -1, 5)

    risk = model.risk_covenant_summary()

    print("=== Executive Brief ===")
    print(brief)
    print("\n=== CEO Lens ===")
    print(ceo_view)
    print("\n=== Why Cash ≠ Profit ===")
    print(wc_text)
    print("\n=== Scenario Judgment ===")
    print(scenario_text)
    print("\n=== Risk & Covenant Summary ===")
    print(risk)

    fig1 = plot_financial_trends(model)
    fig2 = plot_waterfall_income(model)
    plt.show()
