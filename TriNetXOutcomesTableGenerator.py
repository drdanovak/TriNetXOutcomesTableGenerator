import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Outcomes Table Formatter (Journal Style)")

uploaded_file = st.file_uploader("📂 Upload your Outcomes Table (.csv, .xls, .xlsx)", type=["csv", "xls", "xlsx"])
if not uploaded_file:
    st.info("Please upload your outcomes table file.")
    st.stop()

filename = uploaded_file.name.lower()
if filename.endswith(".csv"):
    df = pd.read_csv(uploaded_file, header=None)
elif filename.endswith((".xls", ".xlsx")):
    df = pd.read_excel(uploaded_file, header=None)
else:
    st.error("Unsupported file type. Please upload a .csv, .xls, or .xlsx file.")
    st.stop()

# Basic assumption: first row is header, next two are cohort rows, optional: stat row(s)
header = list(df.iloc[0])
cohort1 = list(df.iloc[1])
cohort2 = list(df.iloc[2])

# (Optional) Manually input summary stats or extract/calculate as needed
# Replace these with correct column indexes or automate extraction if preferred
stats = {
    "risk_diff": "5%",
    "risk_diff_ci": "(2%, 8%)",
    "risk_ratio": "1.33",
    "risk_ratio_ci": "(1.10, 1.61)",
    "odds_ratio": "1.42",
    "odds_ratio_ci": "(1.08, 1.85)",
    "z": "2.8",
    "p": "0.005"
}

def render_outcomes_summary_table(header, cohort1, cohort2, stats):
    html = f"""
    <style>
    .summary-table {{border-collapse:collapse;width:100%;font-family:Arial,sans-serif;}}
    .summary-table th, .summary-table td {{border:1px solid #2b4367;padding:8px;text-align:center;}}
    .summary-table th {{background:#3d62a8;color:#fff;}}
    .summary-table tr.cohort-row {{background:#e9edf6;}}
    .summary-table tr.stat-row td {{background:#f6f8fa;font-size:0.95em;text-align:left;}}
    </style>
    <table class="summary-table">
      <tr>
        <th>{header[0]}</th>
        <th>{header[1]}</th>
        <th>{header[2]}</th>
        <th>{header[3]}</th>
      </tr>
      <tr class="cohort-row">
        <td>{cohort1[0]}</td>
        <td>{cohort1[1]}</td>
        <td>{cohort1[2]}</td>
        <td>{cohort1[3]}</td>
      </tr>
      <tr class="cohort-row">
        <td>{cohort2[0]}</td>
        <td>{cohort2[1]}</td>
        <td>{cohort2[2]}</td>
        <td>{cohort2[3]}</td>
      </tr>
      <tr class="stat-row">
        <td colspan="2">
          <b>Risk Difference:</b> {stats["risk_diff"]}<br>
          <b>95% CI:</b> {stats["risk_diff_ci"]}<br>
          <b>Risk Ratio:</b> {stats["risk_ratio"]}<br>
          <b>95% CI:</b> {stats["risk_ratio_ci"]}
        </td>
        <td>
          <b>Odds Ratio:</b> {stats["odds_ratio"]}<br>
          <b>95% CI:</b> {stats["odds_ratio_ci"]}
        </td>
        <td>
          <b>Z=</b>{stats["z"]}<br>
          <b>P=</b>{stats["p"]}
        </td>
      </tr>
    </table>
    """
    return html

st.markdown("### Journal-Style Outcomes Table")
st.markdown(render_outcomes_summary_table(header, cohort1, cohort2, stats), unsafe_allow_html=True)
