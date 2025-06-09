import streamlit as st
import pandas as pd
import numpy as np

def get_cell(df, cell):
    """Get the value from Excel-like coordinates (A1, B2, etc.)."""
    col = ord(cell[0].upper()) - ord('A')
    row = int(cell[1:]) - 1  # zero-based index
    return df.iloc[row, col]

st.set_page_config(layout="wide")
st.title("TriNetX Outcomes Journal Table Generator")

uploaded_file = st.file_uploader("Upload TriNetX Outcomes CSV/Excel", type=["csv", "xlsx"])
if uploaded_file:
    # Auto-detect file type
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, header=None)
    else:
        df = pd.read_excel(uploaded_file, header=None)

    # Editable outcome name
    outcome_name = st.text_input("Outcome Name (edit as needed):", value="Outcome Name")

    # Extract cohort and statistics values by coordinates
    c1_name = get_cell(df, "B11")
    c1_n = get_cell(df, "C11")
    c1_outcome_n = get_cell(df, "D11")
    c1_risk = get_cell(df, "E11")

    c2_name = get_cell(df, "B12")
    c2_n = get_cell(df, "C12")
    c2_outcome_n = get_cell(df, "D12")
    c2_risk = get_cell(df, "E12")

    risk_diff = get_cell(df, "A17")
    risk_diff_ci = f"({get_cell(df, 'B17')}, {get_cell(df, 'C17')})"
    risk_ratio = get_cell(df, "A22")
    risk_ratio_ci = f"({get_cell(df, 'B22')}, {get_cell(df, 'C22')})"
    odds_ratio = get_cell(df, "A27")
    odds_ratio_ci = f"({get_cell(df, 'B27')}, {get_cell(df, 'C27')})"
    pval = get_cell(df, "E17")

    # Build display table
    table_data = [
        [c1_name, c1_n, c1_outcome_n, c1_risk],
        [c2_name, c2_n, c2_outcome_n, c2_risk],
    ]
    stat_data = [
        ["Risk Difference", risk_diff, risk_diff_ci, ""],
        ["Risk Ratio", risk_ratio, risk_ratio_ci, ""],
        ["Odds Ratio", odds_ratio, odds_ratio_ci, ""],
        ["p-value", pval, "", ""],
    ]

    st.markdown(f"### {outcome_name}")
    st.markdown("**Cohort Results**")
    df_cohort = pd.DataFrame(table_data, columns=[
        "Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk"
    ])
    st.dataframe(df_cohort, hide_index=True, use_container_width=True)

    st.markdown("**Statistics**")
    df_stats = pd.DataFrame(stat_data, columns=[
        "Statistic", "Value", "95% CI", ""
    ])
    st.dataframe(df_stats, hide_index=True, use_container_width=True)

    # Fancy HTML Table (for journal submission)
    st.markdown("**Formatted Table (Copy-Paste for Manuscript)**")
    html_table = f"""
    <style>
    .outcome-table {{
        font-size: 16px; border-collapse: collapse; width: 100%;
    }}
    .outcome-table th, .outcome-table td {{
        border: 1px solid #999; padding: 6px 12px; text-align: center;
    }}
    .outcome-table th {{
        background: #f7f7f7;
    }}
    .outcome-table caption {{
        text-align: left; font-weight: bold; margin-bottom: 4px;
    }}
    </style>
    <table class="outcome-table">
    <caption>{outcome_name}</caption>
    <tr>
        <th>Cohort Name</th>
        <th>Patients in Cohort</th>
        <th>Patients with Outcome</th>
        <th>Risk</th>
    </tr>
    <tr>
        <td>{c1_name}</td>
        <td>{c1_n}</td>
        <td>{c1_outcome_n}</td>
        <td>{c1_risk}</td>
    </tr>
    <tr>
        <td>{c2_name}</td>
        <td>{c2_n}</td>
        <td>{c2_outcome_n}</td>
        <td>{c2_risk}</td>
    </tr>
    <tr><td colspan="4" style="background:#efefef;"></td></tr>
    <tr>
        <th>Statistic</th>
        <th>Value</th>
        <th>95% CI</th>
        <th>p-value</th>
    </tr>
    <tr>
        <td>Risk Difference</td>
        <td>{risk_diff}</td>
        <td>{risk_diff_ci}</td>
        <td></td>
    </tr>
    <tr>
        <td>Risk Ratio</td>
        <td>{risk_ratio}</td>
        <td>{risk_ratio_ci}</td>
        <td></td>
    </tr>
    <tr>
        <td>Odds Ratio</td>
        <td>{odds_ratio}</td>
        <td>{odds_ratio_ci}</td>
        <td></td>
    </tr>
    <tr>
        <td>p-value</td>
        <td>{pval}</td>
        <td></td>
        <td></td>
    </tr>
    </table>
    """
    st.markdown(html_table, unsafe_allow_html=True)

else:
    st.info("Upload a TriNetX outcomes CSV or Excel file to get started.")

