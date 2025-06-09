import streamlit as st
import pandas as pd
import io

uploaded_file = st.file_uploader("Upload your CSV", type="csv")
if uploaded_file:
    # Read all rows as raw text lines
    raw = uploaded_file.read().decode('utf-8').splitlines()
    rows = []
    max_cols = 0
    for line in raw:
        # Split on comma or tab, whichever yields more columns
        comma_split = line.split(',')
        tab_split = line.split('\t')
        row = comma_split if len(comma_split) >= len(tab_split) else tab_split
        rows.append(row)
        if len(row) > max_cols:
            max_cols = len(row)
    # Pad all rows to the same width
    rows = [r + [''] * (max_cols - len(r)) for r in rows]
    df = pd.DataFrame(rows)

    st.write("First 30 rows, first 8 columns:")
    st.dataframe(df.iloc[:30, :8])

    st.write(f"C17 (row 16, col 2): '{df.iat[16, 2] if df.shape[0] > 16 and df.shape[1] > 2 else 'N/A'}'")
    st.write(f"B22 (row 21, col 1): '{df.iat[21, 1] if df.shape[0] > 21 and df.shape[1] > 1 else 'N/A'}'")
    st.write(f"A27 (row 26, col 0): '{df.iat[26, 0] if df.shape[0] > 26 and df.shape[1] > 0 else 'N/A'}'")
