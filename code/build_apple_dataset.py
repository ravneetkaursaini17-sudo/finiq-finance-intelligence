#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 15:57:42 2026

@author: ravneetkaursaini
"""

import os
import pandas as pd
from finiq_engine import parse_financials_from_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "..", "pdfs")

outputs = []

for fname in os.listdir(PDF_DIR):
    if fname.lower().endswith(".pdf"):
        pdf_path = os.path.join(PDF_DIR, fname)
        print(f"Parsing {pdf_path}...")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        df, flags = parse_financials_from_pdf(pdf_bytes)
        print("Flags:", flags)
        outputs.append(df)

if not outputs:
    raise ValueError("No PDFs found in pdfs folder.")

apple_all = pd.concat(outputs).sort_values("year").reset_index(drop=True)

out_path = os.path.join(BASE_DIR, "apple_financials.csv")
apple_all.to_csv(out_path, index=False)
print("Saved:", out_path)

