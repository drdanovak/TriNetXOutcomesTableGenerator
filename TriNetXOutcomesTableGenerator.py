import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("TriNetX Outcomes Table Generator (Custom Format)")

uploaded_file = st.file_uploader("Upload TriNetX Outcomes CSV (as downloaded)", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file, header=None, dtype=str)

    # Try-catch in case of file structure change
    try:
        cohort1 = df.iloc[5,0].split(",")
        cohort2 = df.iloc[6,0].split(",")
        risk_diff = df.iloc[9,0].split(",")
        risk_ratio = df.iloc[12,0].split(",")
        odds_ratio = df.iloc[15,0].split(",")

        c1_name, c1_n, c1_outcome_n, c1_risk = cohort1[1], cohort1[2], cohort1[3], cohort1[4]
        c2_name, c2_n, c2_outcome_n, c2_risk = cohort2[1], cohort2[2], cohort2[3], cohort2[4]

        risk_diff_val, risk_diff_lo, risk_diff_hi = risk_diff[0], risk_diff[1], risk_diff[2]
        risk_ratio_val, risk_ratio_lo, risk_ratio_hi = risk_ratio[0], risk_ratio[1], risk_ratio[2]
        odds_ratio_val, odds_ratio_lo, odds_ratio_hi = odds_ratio[0], odds_ratio[1], odds_ratio[2]

        p_val = ""  # Not present in your rows, you can add logic if available

        # Build cohort table
        cohort_table = pd.DataFrame([
            [c1_name, c1_n, c1_outcome_n, c1_risk],
            [c2_name, c2_n, c2_outcome_n, c2_risk]
        ], columns=["Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk"])

        st.markdown("### Cohort Results")
        st.dataframe(cohort_table, hide_index=True, use_container_width=True)

        # Build stats table
        stats_table = pd.DataFrame([
            ["Risk Difference", risk_diff_val, f"({risk_diff_lo}, {risk_diff_hi})", ""],
            ["Risk Ratio", risk_ratio_val, f"({risk_ratio_lo}, {risk_ratio_hi})", ""],
            ["Odds Ratio", odds_ratio_val, f"({odds_ratio_lo}, {odds_ratio_hi})", ""],
        ], columns=["Statistic", "Value", "95% CI", "p-value"])

        st.markdown("### Statistics")
        st.dataframe(stats_table, hide_index=True, use_container_width=True)

        # Journal style HTML (copy-paste)
        st.markdown("**Formatted Table (Copy for Manuscript)**")
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
        </style>
        <table class="outcome-table">
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
            <td>{risk_diff_val}</td>
            <td>({risk_diff_lo}, {risk_diff_hi})</td>
            <td></td>
        </tr>
        <tr>
            <td>Risk Ratio</td>
            <td>{risk_ratio_val}</td>
            <td>({risk_ratio_lo}, {risk_ratio_hi})</td>
            <td></td>
        </tr>
        <tr>
            <td>Odds Ratio</td>
            <td>{odds_ratio_val}</td>
            <td>({odds_ratio_lo}, {odds_ratio_hi})</td>
            <td></td>
        </tr>
        </table>
        """
        st.markdown(html_table, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"File structure did not match expected TriNetX export: {e}")

else:
    st.info("Upload a TriNetX outcomes CSV file to get started.")
