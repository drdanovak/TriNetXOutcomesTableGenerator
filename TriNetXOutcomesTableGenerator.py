import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("Upload your CSV", type="csv")
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, header=None, dtype=str, engine="python", on_bad_lines='skip')
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()
    
    st.write("First 30 rows, 6 columns:")
    st.dataframe(df.iloc[:30, :6])

    st.write(f"C17 (row 16, col 2): '{df.iat[16, 2] if df.shape[0] > 16 and df.shape[1] > 2 else 'N/A'}'")
    st.write(f"B22 (row 21, col 1): '{df.iat[21, 1] if df.shape[0] > 21 and df.shape[1] > 1 else 'N/A'}'")
    st.write(f"A27 (row 26, col 0): '{df.iat[26, 0] if df.shape[0] > 26 and df.shape[1] > 0 else 'N/A'}'")
