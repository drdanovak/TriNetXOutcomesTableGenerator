import streamlit as st

# --- Robust TriNetX text parser ---
def get_next_data_line(lines, start):
    """Find the next line after 'start' that looks like a CSV (data, not header or blank)."""
    for i in range(start, len(lines)):
        line = lines[i].strip()
        if line and line != '" "' and not line.startswith("Risk") and ',' in line:
            return line
    return None

def parse_trinetx_outcomes(lines):
    # Find cohort section
    cohort1, cohort2 = None, None
    for i, line in enumerate(lines):
        if line.strip().startswith("Cohort,Cohort Name"):
            cohort1 = lines[i+1].strip().split(",")
            cohort2 = lines[i+2].strip().split(",")
            break
    # Find stats
    def find_stat(stat_name):
        idx_list = [i for i, l in enumerate(lines) if stat_name in l]
        return get_next_data_line(lines, idx_list[0]+1) if idx_list else None

    risk_diff_line = find_stat("Risk Difference")
    risk_diff = risk_diff_line.split(",") if risk_diff_line else ["", "", ""]

    risk_ratio_line = find_stat("Risk Ratio")
    risk_ratio = risk_ratio_line.split(",") if risk_ratio_line else ["", "", ""]

    odds_ratio_line = find_stat("Odds Ratio")
    odds_ratio = odds_ratio_line.split(",") if odds_ratio_line else ["", "", ""]

    # Map cohort data (with fallback to blanks)
    c1 = cohort1 if cohort1 else [""]*5
    c2 = cohort2 if cohort2 else [""]*5

    c1_name, c1_n, c1_outcome_n, c1_risk = c1[1:5]
    c2_name, c2_n, c2_outcome_n, c2_risk = c2[1:5]

    # Map stats
    risk_diff_val, risk_diff_lo, risk_diff_hi = (risk_diff + ["", "", ""])[:3]
    risk_ratio_val, risk_ratio_lo, risk_ratio_hi = (risk_ratio + ["", "", ""])[:3]
    odds_ratio_val, odds_ratio_lo, odds_ratio_hi = (odds_ratio + ["", "", ""])[:3]

    return {
        "c1_name": c1_name, "c1_n": c1_n, "c1_outcome_n": c1_outcome_n, "c1_risk": c1_risk,
        "c2_name": c2_name, "c2_n": c2_n, "c2_outcome_n": c2_outcome_n, "c2_risk": c2_risk,
        "risk_diff_val": risk_diff_val, "risk_diff_lo": risk_diff_lo, "risk_diff_hi": risk_diff_hi,
        "risk_ratio_val": risk_ratio_val, "risk_ratio_lo": risk_ratio_lo, "risk_ratio_hi": risk_ratio_hi,
        "odds_ratio_val": odds_ratio_val, "odds_ratio_lo": odds_ratio_lo, "odds_ratio_hi": odds_ratio_hi
    }

st.set_page_config(layout="wide")
st.title("🧮 TriNetX Outcomes Table Generator (Robust)")

uploaded_file = st.file_uploader("Upload TriNetX Outcomes CSV (exported as-is from TriNetX)", type="csv")
if uploaded_file:
    # Decode and split into lines
    lines = uploaded_file.getvalue().decode("utf-8").splitlines()
    outcome = parse_trinetx_outcomes(lines)

    # Outcome name (editable)
    outcome_name = st.text_input("Outcome Name (edit if desired):", value="Outcome")

    # Display table (pretty, journal-ready)
    st.markdown(f"### {outcome_name} Outcome Table")

    # Cohort results (pretty table)
    st.markdown(
        f"""
        <table style="font-size:16px; border-collapse:collapse; width:100%; margin-bottom:16px;">
          <tr style="background:#f7f7f7;">
            <th>Cohort Name</th><th>Patients in Cohort</th><th>Patients with Outcome</th><th>Risk</th>
          </tr>
          <tr>
            <td>{outcome['c1_name']}</td><td>{outcome['c1_n']}</td><td>{outcome['c1_outcome_n']}</td><td>{outcome['c1_risk']}</td>
          </tr>
          <tr>
            <td>{outcome['c2_name']}</td><td>{outcome['c2_n']}</td><td>{outcome['c2_outcome_n']}</td><td>{outcome['c2_risk']}</td>
          </tr>
        </table>
        """,
        unsafe_allow_html=True
    )

    # Summary statistics
    st.markdown(
        f"""
        <table style="font-size:16px; border-collapse:collapse; width:100%;">
          <tr style="background:#f7f7f7;">
            <th>Statistic</th><th>Value</th><th>95% CI</th>
          </tr>
          <tr>
            <td>Risk Difference</td>
            <td>{outcome['risk_diff_val']}</td>
            <td>({outcome['risk_diff_lo']}, {outcome['risk_diff_hi']})</td>
          </tr>
          <tr>
            <td>Risk Ratio</td>
            <td>{outcome['risk_ratio_val']}</td>
            <td>({outcome['risk_ratio_lo']}, {outcome['risk_ratio_hi']})</td>
          </tr>
          <tr>
            <td>Odds Ratio</td>
            <td>{outcome['odds_ratio_val']}</td>
            <td>({outcome['odds_ratio_lo']}, {outcome['odds_ratio_hi']})</td>
          </tr>
        </table>
        """,
        unsafe_allow_html=True
    )

    st.info("Copy the above table for your manuscript or poster. If a statistic is missing, check your TriNetX export file for that section.")

else:
    st.info("Upload a TriNetX CSV export to generate your formatted outcome table.")

