#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 23:00:22 2026

@author: ravneetkaursaini
"""


import pandas as pd

def load_financial_xls(path):
    # Load sheets
    bs = pd.read_excel(path, sheet_name="Balance Sheet", engine="openpyxl")
    is_ = pd.read_excel(path, sheet_name="Income Statement")
    cf = pd.read_excel(path, sheet_name="Cash Flow")

    # Drop empty rows
    bs = bs.dropna(how="all")
    is_ = is_.dropna(how="all")
    cf = cf.dropna(how="all")

    # Set metric name as index
    bs = bs.set_index(bs.columns[0])
    is_ = is_.set_index(is_.columns[0])
    cf = cf.set_index(cf.columns[0])

    # Years
    years = is_.columns.astype(int)
    n_years = len(years)
    df = pd.DataFrame({"year": years})

    # Helper: always return exactly n_years values
    def find_row(sheet, labels):
        for label in labels:
            if label in sheet.index:
                row = sheet.loc[label].values

                # Clean commas
                row = [str(x).replace(",", "") for x in row]

                # Convert to numeric
                row = pd.to_numeric(row, errors="coerce")

                # Pad or trim
                if len(row) < n_years:
                    row = list(row) + [None] * (n_years - len(row))
                if len(row) > n_years:
                    row = row[:n_years]

                return row

        return [None] * n_years

    # ============================
    # INCOME STATEMENT
    # ============================

    df["revenue"] = find_row(is_, ["Revenue"])
    df["cogs"] = find_row(is_, ["Cost of Goods Sold (COGS) incl. D&A"])

    # OPEX = SG&A + R&D
    sga = find_row(is_, ["SG&A Expense"])
    rnd = find_row(is_, ["Research & Development"])
    df["opex"] = (pd.Series(sga) + pd.Series(rnd)).values

    df["ebit"] = find_row(is_, ["EBIT"])
    df["net_income"] = find_row(is_, ["Net Income", "Consolidated Net Income"])
    df["interest_expense"] = find_row(is_, ["Interest Expense"])
    df["ebitda"] = find_row(is_, ["EBITDA"])

    # ============================
    # CASH FLOW STATEMENT
    # ============================

    df["cfo"] = find_row(cf, ["Net Operating Cash Flow"])
    df["cfi"] = find_row(cf, ["Net Investing Cash Flow"])
    df["cff"] = find_row(cf, ["Net Financing Cash Flow"])

    # ============================
    # BALANCE SHEET
    # ============================

    df["cash"] = find_row(bs, ["Cash & Short Term Investments"])
    df["ar"] = find_row(bs, ["Accounts Receivables, Net"])
    df["ap"] = find_row(bs, ["Accounts Payable"])
    df["inventory"] = find_row(bs, ["Inventories"])
    df["total_assets"] = find_row(bs, ["Total Assets"])
    df["equity"] = find_row(bs, ["Total Shareholders' Equity"])

    short_debt = find_row(bs, ["ST Debt & Current Portion LT Debt"])
    long_debt = find_row(bs, ["Long-Term Debt"])
    df["total_debt"] = (pd.Series(short_debt) + pd.Series(long_debt)).values

    # ============================
    # CONVERT TO MILLIONS
    # ============================

    for col in df.columns:
        if col != "year":
            df[col] = pd.to_numeric(df[col], errors="coerce") / 1_000

    return df




