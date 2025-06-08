import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Outcomes Table (Polished Publication Style)")

uploaded_file = st.file_uploader(
    "📂 Upload your Outcomes Table (.csv, .xls, .xlsx)",
    type=["csv", "xls", "xlsx"]
)
if not uploaded_file:
    st.info("Please upload your outcomes table file.")
    st.stop()

filename = uploaded_file.name.lower()

# --- Robust load, skip TriNetX headers if present ---
if filename.endswith(".csv"):
    uploaded_file.seek(0)
    try:
        df = pd.read_csv(uploaded_file, header=None, skiprows=9)
        if not str(df.iloc[0,1]).lower().startswith("cohort"):
            raise Exception("Header not found after skipping 9 rows.")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=None)
elif filename.endswith((".xls", ".xlsx")):
    df = pd.read_excel(uploaded_file, header=None)
else:
    st.error("Unsupported file type. Please upload a .csv, .xls, or .xlsx file.")
    st.stop()

# --- Format data (assumes header, then two cohort rows, then stats below or added) ---
columns = [
    "Cohort", "Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk Percentage"
]
df.columns = columns
df = df.iloc[1:3].reset_index(drop=True)
df["Cohort"] = [1, 2]
df["Patients in Cohort"] = df["Patients in Cohort"].astype(int)
df["Patients with Outcome"] = df["Patients with Outcome"].astype(int)
df["Risk Percentage"] = pd.to_numeric(df["Risk Percentage"], errors='coerce').map("{:.9f}".format)

# --- Summary statistics (can be made editable if you wish) ---
stats = {
    "risk_diff": "5%",
    "risk_diff_ci": "(2%, 8%)",
    "risk_ratio": "1.42",
    "risk_ratio_ci": "(1.10, 1.85)",
    "odds_ratio": "1.42",
    "odds_ratio_ci": "(1.08, 1.85)",
    "z": "2.8",
    "p": "0.005"
}

def nice_outcomes_table(df, stats):
    # Custom HTML with distinct header, zebra striping, bold stat box
    html = """
    <style>
    .nice-table {border-collapse:collapse;width:100%;font-family:Segoe UI,Arial,sans-serif;margin-top:24px;}
    .nice-table th {background:#1d3557;color:#fff;padding:10px 8px;font-size:1.1em;border:1px solid #7da0c7;}
    .nice-table td {border:1px solid #c4d2e7;padding:10px 8px;}
    .nice-table tbody tr:nth-child(odd) {background:#f6fafd;}
    .nice-table tbody tr:nth-child(even) {background:#e3ecf6;}
    .stats-footer-row td {
        background: #f9eab3 !important;
        color: #353535;
        font-weight: bold;
        border-top: 2px solid #b49d4d;
        font-size: 1.08em;
        text-align: left;
        padding-top:18px;
    }
    .stats-footer-row2 td {
        background: #f9eab3 !important;
        color: #353535;
        font-size: 1.03em;
        font-style: italic;
        text-align: left;
    }
    </style>
    <table class="nice-table">
      <thead>
        <tr>
          <th>Cohort</th>
          <th>Cohort Name</th>
          <th>Patients in Cohort</th>
          <th>Patients with Outcome</th>
          <th>Risk Percentage</th>
        </tr>
      </thead>
      <tbody>
    """
    for i, row in df.iterrows():
        html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"

    # Stats row 1: Risk diff, Odds Ratio, Z
    html += f"""
      <tr class="stats-footer-row">
        <td colspan="2">Risk Difference: {stats['risk_diff']}</td>
        <td>Odds Ratio: {stats['odds_ratio']}</td>
        <td>Z={stats['z']}</td>
        <td></td>
      </tr>
    """
    # Stats row 2: CI for each stat, P-value
    html += f"""
      <tr class="stats-footer-row2">
        <td colspan="2">95% CI: {stats['risk_diff_ci']}</td>
        <td>95% CI: {stats['odds_ratio_ci']}</td>
        <td>P={stats['p']}</td>
        <td></td>
      </tr>
    """

    html += "</tbody></table>"
    return html

st.markdown("### Polished Journal-Style Outcomes Table")
st.markdown(nice_outcomes_table(df, stats), unsafe_allow_html=True)
