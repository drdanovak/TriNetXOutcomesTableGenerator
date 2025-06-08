import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("TriNetX Multi-Outcome Table (Fully Customizable)")

uploaded_files = st.file_uploader(
    "📂 Upload multiple TriNetX outcome files (.csv, .xls, or .xlsx)",
    type=["csv", "xls", "xlsx"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least two TriNetX outcome files exported from TriNetX.")
    st.stop()

# --- UI: Formatting Options ---
with st.sidebar:
    st.header("Table Colors")
    header_bg = st.color_picker("Header background", "#17456d")
    header_fg = st.color_picker("Header text", "#ffffff")
    band1_bg = st.color_picker("Band 1 background", "#e6f0fa")
    band2_bg = st.color_picker("Band 2 background", "#f5faff")
    stats_bg = st.color_picker("Statistics row background", "#f9eab3")
    stats_fg = st.color_picker("Statistics row text", "#764600")
    st.header("Other Options")
    banded = st.checkbox("Banded rows (zebra striping)", value=True)
    bold_headers = st.checkbox("Bold column headers", value=True)
    st.markdown("---")
    st.markdown("#### Rearrangement")
    st.caption("Drag outcome names to set display order below.")

def extract_outcome_data(file):
    file_ext = os.path.splitext(file.name)[-1].lower()
    # Read according to extension
    if file_ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file, header=None)
    elif file_ext == ".csv":
        file.seek(0)
        try:
            df = pd.read_csv(file, header=None, skiprows=9)
            if not any(str(cell).strip().lower().startswith("cohort") for cell in df.iloc[0]):
                raise Exception("Header row not found after skipping 9 rows.")
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, header=None)
    else:
        return None  # skip unsupported file

    # --- Find header row with "Cohort" ---
    header_row = None
    for i, row in df.iterrows():
        if any(str(cell).strip().lower().startswith("cohort") for cell in row):
            header_row = i
            break
    if header_row is None:
        return None

    # --- Grab the cohort data ---
    data = df.iloc[header_row:header_row+3].copy()
    data.columns = list(data.iloc[0])
    data = data.iloc[1:].reset_index(drop=True)
    outcome_name = file.name.rsplit('.', 1)[0]
    c1 = data.iloc[0]
    c2 = data.iloc[1]
    risk_col = [col for col in data.columns if "risk" in str(col).lower()][0]
    n1 = c1.get("Patients in Cohort", "")
    n2 = c2.get("Patients in Cohort", "")
    e1 = c1.get("Patients with Outcome", "")
    e2 = c2.get("Patients with Outcome", "")
    risk1 = c1.get(risk_col, "")
    risk2 = c2.get(risk_col, "")
    cname1 = c1.get("Cohort Name", "")
    cname2 = c2.get("Cohort Name", "")

    # Try to get summary stats as columns in the next row(s)
    stats_row_idx = header_row + 3
    stats_row = None
    if stats_row_idx < len(df):
        possible_row = df.iloc[stats_row_idx]
        if any(str(col).lower().strip() in [
            "risk difference", "odds ratio", "z", "p", "95 % ci lower", "95 % ci upper"
        ] for col in possible_row):
            # This is a header row for stats
            stats_row = pd.Series({str(k): v for k, v in zip(possible_row, df.iloc[stats_row_idx+1])})

    # Extract values for stats, trying both column and row parsing
    def get_stat_val(keys, fallback=""):
        # Try as column in stats_row first
        if stats_row is not None:
            for k in keys:
                v = stats_row.get(k, "")
                if pd.notna(v) and str(v).strip() not in ["", "nan"]:
                    return v
        # Fallback: parse as text in post-cohort lines (row-based)
        for i in range(header_row+3, min(header_row+10, len(df))):
            txt = " ".join(str(x) for x in df.iloc[i] if pd.notna(x))
            for k in keys:
                if k.lower() in txt.lower():
                    # Try to extract value after ":"
                    after = txt.lower().split(k.lower()+":")[-1].strip()
                    if after:
                        # stop at next space or parenthesis
                        return after.split()[0].replace("(", "").replace(")", "")
        return fallback

    # Build CI string for risk diff and odds ratio
    risk_diff = get_stat_val(["Risk Difference"])
    risk_diff_ci_lower = get_stat_val(["95 % CI Lower", "Risk Difference Lower"])
    risk_diff_ci_upper = get_stat_val(["95 % CI Upper", "Risk Difference Upper"])
    risk_diff_ci = ""
    if risk_diff_ci_lower or risk_diff_ci_upper:
        risk_diff_ci = f"({risk_diff_ci_lower}, {risk_diff_ci_upper})"
    odds_ratio = get_stat_val(["Odds Ratio"])
    odds_ratio_ci_lower = get_stat_val(["Odds Ratio Lower", "95 % CI Lower"])
    odds_ratio_ci_upper = get_stat_val(["Odds Ratio Upper", "95 % CI Upper"])
    odds_ratio_ci = ""
    if odds_ratio_ci_lower or odds_ratio_ci_upper:
        odds_ratio_ci = f"({odds_ratio_ci_lower}, {odds_ratio_ci_upper})"
    z_score = get_stat_val(["z", "Z"])
    p_val = get_stat_val(["p", "P"])

    stats_row = {
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
    return [
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
        stats_row
    ]

# --- Extract and build all outcome blocks ---
outcome_blocks = []
outcome_names = []
for file in uploaded_files:
    block = extract_outcome_data(file)
    if block:
        outcome_blocks.append(block)
        outcome_names.append(block[0]["Outcome"])

# --- Outcome Reordering with Multiselect ---
if "order" not in st.session_state or set(st.session_state.get("order", [])) != set(outcome_names):
    st.session_state["order"] = outcome_names.copy()

order = st.sidebar.multiselect(
    "Drag outcomes below to reorder for display:",
    options=outcome_names,
    default=st.session_state["order"],
    key="outcome_order"
)

# Update the current session's order if changed via UI
if order != st.session_state.get("order", []):
    st.session_state["order"] = order

# --- Build stacked table in chosen order ---
all_rows = []
for outcome_name in st.session_state["order"]:
    idx = outcome_names.index(outcome_name)
    all_rows.extend(outcome_blocks[idx])

stacked_df = pd.DataFrame(all_rows)

def style_stacked_table(
        df,
        banded=True,
        bold_headers=True,
        header_bg="#17456d",
        header_fg="#fff",
        band1_bg="#e6f0fa",
        band2_bg="#f5faff",
        stats_bg="#f9eab3",
        stats_fg="#764600"
    ):
    css = f"""
    <style>
    .stacked-table {{
        border-collapse:collapse;width:100%;font-family:Segoe UI,Arial,sans-serif;font-size:0.97em;
    }}
    .stacked-table th {{
        background:{header_bg};
        color:{header_fg};
        padding:7px 6px;
        font-size:1em;
        border:1px solid #b8cbe9;
        {"font-weight:700;" if bold_headers else "font-weight:400;"}
    }}
    .stacked-table td {{
        border:1px solid #d4e1f2;
        padding:7px 6px;
        text-align:center;
        vertical-align:middle;
    }}
    """
    if banded:
        css += f"""
        .stacked-table tbody tr.banded1 {{background:{band1_bg};}}
        .stacked-table tbody tr.banded2 {{background:{band2_bg};}}
        """
    else:
        css += ".stacked-table tbody tr {background:#fff;}"
    css += f"""
    .stacked-table tbody tr.stats-row {{
        background: {stats_bg};
        font-weight:600;
    }}
    .stacked-table td b, .stacked-table td span, .stacked-table td div {{
        color:{stats_fg};
    }}
    </style>
    """
    html = css + "<table class='stacked-table'><thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, row in df.iterrows():
        # Choose row class
        if (i % 3) == 2:
            row_class = 'stats-row'
        elif (i % 3) == 0:
            row_class = 'banded1' if banded else ''
        else:
            row_class = 'banded2' if banded else ''
        html += f"<tr class='{row_class}'>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</tbody></table>"
    return html

st.markdown("### Stacked Outcomes Table")
st.markdown(style_stacked_table(
    stacked_df,
    banded=banded,
    bold_headers=bold_headers,
    header_bg=header_bg,
    header_fg=header_fg,
    band1_bg=band1_bg,
    band2_bg=band2_bg,
    stats_bg=stats_bg,
    stats_fg=stats_fg,
), unsafe_allow_html=True)

st.download_button(
    "Download Stacked Table as CSV",
    stacked_df.to_csv(index=False),
    "stacked_outcomes_table.csv",
    "text/csv"
)
