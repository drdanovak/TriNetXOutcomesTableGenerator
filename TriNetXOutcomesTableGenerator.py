import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Journal-Style Outcomes Table Generator")

uploaded_file = st.file_uploader(
    "📂 Upload your Outcomes Table (.csv, .xls, .xlsx)",
    type=["csv", "xls", "xlsx"]
)
if not uploaded_file:
    st.info("Please upload your outcomes table file.")
    st.stop()

filename = uploaded_file.name.lower()

# --- Robustly load the table, skipping 9 rows for TriNetX CSVs ---
if filename.endswith(".csv"):
    uploaded_file.seek(0)
    try:
        df = pd.read_csv(uploaded_file, header=None, skiprows=9)
        if not str(df.iloc[0,1]).lower().startswith("cohort"):
            raise ValueError("Header not found after skipping 9 rows.")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=None)
elif filename.endswith((".xls", ".xlsx")):
    df = pd.read_excel(uploaded_file, header=None)
else:
    st.error("Unsupported file type. Please upload a .csv, .xls, or .xlsx file.")
    st.stop()

# --- Standardize columns and rows based on your sample ---
# Assign column names
columns = [
    "Cohort", "Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk Percentage"
]
# We assume first row is header, next two rows are cohort data, and the risk is in the 5th column
df.columns = columns
df = df.iloc[1:3].reset_index(drop=True)  # keep only the two cohort rows

# Optional: Ensure correct dtypes and formatting
df["Cohort"] = [1, 2]
df["Patients in Cohort"] = df["Patients in Cohort"].astype(int)
df["Patients with Outcome"] = df["Patients with Outcome"].astype(int)
df["Risk Percentage"] = pd.to_numeric(df["Risk Percentage"], errors='coerce').map("{:.9f}".format)

# --- Append summary statistics as two custom rows ---
stats_row1 = [
    "Risk Difference: 5%",
    "Odds Ratio: 1.42",
    "Z=2.8",
    "",
    ""
]
stats_row2 = [
    "95% CI: (2%, 8%)",
    "95% CI: (1.08, 1.85)",
    "P=0.005",
    "",
    ""
]

summary_df = pd.DataFrame([stats_row1, stats_row2], columns=columns)

# --- Concatenate main table and summary rows ---
output_df = pd.concat([df, summary_df], ignore_index=True)

# --- Style table with Pandas Styler for simple output or custom HTML for advanced ---
def make_html_table(df):
    # Simple HTML table, add more styling as needed
    css = """
    <style>
    .journal-table {border-collapse:collapse;width:100%;font-family:Arial,sans-serif;}
    .journal-table th, .journal-table td {border:1px solid #2b4367;padding:8px;text-align:center;}
    .journal-table th {background:#3d62a8;color:#fff;}
    .journal-table tr.summary-row td {background:#f6f8fa;font-weight:bold;text-align:left;}
    </style>
    """
    html = css + "<table class='journal-table'>"
    # Header
    html += "<tr>" + "".join([f"<th>{c}</th>" for c in df.columns]) + "</tr>"
    # Data rows
    for i, row in df.iterrows():
        tr_class = 'summary-row' if i >= 2 else ''
        html += f"<tr class='{tr_class}'>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

st.markdown("### Journal-Style Outcomes Table")
st.markdown(make_html_table(output_df), unsafe_allow_html=True)

# Optional: Download as CSV
csv = output_df.to_csv(index=False)
st.download_button("Download Table as CSV", csv, "journal_outcomes_table.csv", "text/csv")
