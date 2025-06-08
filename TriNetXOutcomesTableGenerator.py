import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("TriNetX Multi-Outcome Table (Stacked Format)")

uploaded_files = st.file_uploader(
    "📂 Upload multiple TriNetX outcome Excel files (.xls or .xlsx)",
    type=["xls", "xlsx"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least two outcome Excel files exported from TriNetX.")
    st.stop()

def extract_outcome_data(file):
    df = pd.read_excel(file, header=None)
    # Find header row
    header_row = None
    for i, row in df.iterrows():
        if any(str(cell).strip().lower().startswith("cohort") for cell in row):
            header_row = i
            break
    if header_row is None:
        return None
    data = df.iloc[header_row:header_row+3]
    data.columns = list(data.iloc[0])
    data = data.iloc[1:].reset_index(drop=True)
    # Get outcome name from filename
    outcome_name = file.name.rsplit('.', 1)[0]
    # Cohort columns
    c1 = data.iloc[0]
    c2 = data.iloc[1]
    # Risk, events, n
    risk_col = [col for col in data.columns if "risk" in str(col).lower()][0]
    n1 = c1.get("Patients in Cohort", "")
    n2 = c2.get("Patients in Cohort", "")
    e1 = c1.get("Patients with Outcome", "")
    e2 = c2.get("Patients with Outcome", "")
    risk1 = c1.get(risk_col, "")
    risk2 = c2.get(risk_col, "")
    cname1 = c1.get("Cohort Name", "")
    cname2 = c2.get("Cohort Name", "")
    # Defaults for summary stats
    risk_diff = ""
    risk_diff_ci = ""
    odds_ratio = ""
    odds_ratio_ci = ""
    z_score = ""
    p_val = ""
    for i in range(header_row+3, min(header_row+8, len(df))):
        txt = " ".join(str(x) for x in df.iloc[i] if pd.notna(x))
        if "risk difference" in txt.lower():
            risk_diff = txt.split(":")[-1].strip()
        if "95% ci" in txt.lower() and "risk" in txt.lower():
            risk_diff_ci = txt.split(":")[-1].strip()
        if "odds ratio" in txt.lower():
            odds_ratio = txt.split(":")[-1].strip()
        if "95% ci" in txt.lower() and "odds" in txt.lower():
            odds_ratio_ci = txt.split(":")[-1].strip()
        if "z=" in txt.lower():
            z_score = txt.lower().split("z=")[-1].split()[0].replace(",", "")
        if "p=" in txt.lower():
            p_val = txt.lower().split("p=")[-1].split()[0].replace(",", "")
    # Compose group columns
    return [
        # First row: Outcome + Cohort 1 data
        {
            "Outcome": outcome_name,
            "Cohort": cname1,
            "N": n1,
            "Events": e1,
            "Risk": risk1,
            "Stat": "",
            "Odds Ratio": "",
            "Z": "",
            "P": ""
        },
        # Second row: (Outcome blank) + Cohort 2 data
        {
            "Outcome": "",
            "Cohort": cname2,
            "N": n2,
            "Events": e2,
            "Risk": risk2,
            "Stat": "",
            "Odds Ratio": "",
            "Z": "",
            "P": ""
        },
        # Third row: (Outcome blank, Cohort = "Statistics") + stats
        {
            "Outcome": "",
            "Cohort": "<b>Statistics</b>",
            "N": "",
            "Events": "",
            "Risk": f"Risk Diff: {risk_diff} <br><span style='font-size:0.93em'>95% CI: {risk_diff_ci}</span>",
            "Stat": f"Odds Ratio: {odds_ratio} <br><span style='font-size:0.93em'>95% CI: {odds_ratio_ci}</span>",
            "Odds Ratio": f"Z: {z_score}",
            "Z": f"P: {p_val}",
            "P": ""
        }
    ]

# Gather all rows, stacking per outcome
all_rows = []
for file in uploaded_files:
    rows = extract_outcome_data(file)
    if rows:
        all_rows.extend(rows)

# Convert to DataFrame
stacked_df = pd.DataFrame(all_rows)

def style_stacked_table(df):
    css = """
    <style>
    .stacked-table {border-collapse:collapse;width:100%;font-family:Segoe UI,Arial,sans-serif;font-size:0.97em;}
    .stacked-table th {background:#17456d;color:#fff;padding:7px 6px;font-size:1em;border:1px solid #b8cbe9;}
    .stacked-table td {border:1px solid #d4e1f2;padding:7px 6px;text-align:center;vertical-align:middle;}
    .stacked-table tbody tr:nth-child(3n+1) {background:#e6f0fa;}
    .stacked-table tbody tr:nth-child(3n+2) {background:#f5faff;}
    .stacked-table tbody tr:nth-child(3n)   {background:#f9eab3;font-weight:600;}
    .stacked-table td b {color:#764600;}
    .stacked-table td span {color:#444;}
    </style>
    """
    html = css + "<table class='stacked-table'><thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</tbody></table>"
    return html

st.markdown("### Stacked Outcomes Table")
st.markdown(style_stacked_table(stacked_df), unsafe_allow_html=True)

st.download_button(
    "Download Stacked Table as CSV",
    stacked_df.to_csv(index=False),
    "stacked_outcomes_table.csv",
    "text/csv"
)
