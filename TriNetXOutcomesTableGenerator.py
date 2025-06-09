import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("TriNetX Multi-Outcome Table (Direct Mapping, Journal Styles)")

uploaded_files = st.file_uploader(
    "📂 Upload multiple TriNetX outcome files (.csv, .xls, or .xlsx)",
    type=["csv", "xls", "xlsx"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least two TriNetX outcome files exported from TriNetX.")
    st.stop()

# --- Journal Styles Presets ---
JOURNAL_STYLES = {
    "AMA": dict(
        header_bg="#1b365d", header_fg="#ffffff",
        band1_bg="#f6f7fb", band2_bg="#ffffff",
        stats_bg="#e6ecf2", stats_fg="#243952",
        font="Arial, sans-serif", border="1px solid #b6c5db"
    ),
    "APA": dict(
        header_bg="#002b36", header_fg="#fff",
        band1_bg="#f7fbfa", band2_bg="#e3ece9",
        stats_bg="#e1f0ee", stats_fg="#175c4c",
        font="Times New Roman, Times, serif", border="1px solid #aab8c2"
    ),
    "NEJM": dict(
        header_bg="#d6001c", header_fg="#fff",
        band1_bg="#faf6f5", band2_bg="#fff",
        stats_bg="#fbeaea", stats_fg="#990000",
        font="Georgia, serif", border="1px solid #e2bfc1"
    ),
}

# --- Expander: Journal Style ---
with st.expander("Journal Table Style (click to expand)", expanded=False):
    journal_style = st.radio(
        "Select Table Style (overrides colors below):",
        list(JOURNAL_STYLES.keys()),
        index=0
    )

# --- Defaults from selected style ---
defaults = JOURNAL_STYLES[journal_style]

# --- Expander: Table Colors ---
with st.expander("Table Colors (click to expand)", expanded=False):
    header_bg = st.color_picker("Header background", defaults['header_bg'])
    header_fg = st.color_picker("Header text", defaults['header_fg'])
    band1_bg = st.color_picker("Band 1 background", defaults['band1_bg'])
    band2_bg = st.color_picker("Band 2 background", defaults['band2_bg'])
    stats_bg = st.color_picker("Statistics row background", defaults['stats_bg'])
    stats_fg = st.color_picker("Statistics row text", defaults['stats_fg'])
    font_family = defaults['font']
    border_style = defaults['border']

# --- Expander: Other Options ---
with st.expander("Other Table Options (click to expand)", expanded=False):
    banded = st.checkbox("Banded rows (zebra striping)", value=True)
    bold_headers = st.checkbox("Bold column headers", value=True)
    st.markdown("---")
    st.markdown("#### Rearrangement")
    st.caption("Drag outcome names to set display order below.")

# ---- Utility for safe extraction ----
def safe_row(df, idx):
    # Returns the row if present, else ["", "", "", "", ""]
    if idx < len(df):
        row = df.iloc[idx]
        # Pad row if not enough columns
        row = list(row.values)
        while len(row) < 5:
            row.append("")
        return row
    else:
        return ["", "", "", "", ""]

def extract_outcome_data(file):
    file_ext = os.path.splitext(file.name)[-1].lower()
    if file_ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file, header=None)
    elif file_ext == ".csv":
        file.seek(0)
        try:
            df = pd.read_csv(file, header=None, engine="python", on_bad_lines="skip")
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, header=None, engine="python", error_bad_lines=False)
    else:
        return None

    outcome_name = file.name.rsplit('.', 1)[0]

    # Always map exact rows/columns, fill with blanks if missing
    row_c1 = safe_row(df, 10)        # A11-E11
    row_c2 = safe_row(df, 11)        # A12-E12
    row_riskdiff = safe_row(df, 16)  # A17-E17
    row_riskratio = safe_row(df, 21) # A22-C22 (map up to 3 columns)
    row_oddsratio = safe_row(df, 26) # A27-C27 (map up to 3 columns)

    stats_row = {
        "Outcome": "",
        "Cohort": "<b>Statistics</b>",
        "N": "",
        "Events": "",
        "Risk": f"Risk Diff: {row_riskdiff[0]}<br><span style='font-size:0.93em'>95% CI: ({row_riskdiff[1]}, {row_riskdiff[2]})</span>",
        "Stat": f"Risk Ratio: {row_riskratio[0]}<br><span style='font-size:0.93em'>95% CI: ({row_riskratio[1]}, {row_riskratio[2]})</span>",
        "Odds Ratio": f"Odds Ratio: {row_oddsratio[0]}<br><span style='font-size:0.93em'>95% CI: ({row_oddsratio[1]}, {row_oddsratio[2]})</span>",
        "Z": f"z: {row_riskdiff[3]}",
        "P": f"p: {row_riskdiff[4]}"
    }

    return [
        {
            "Outcome": outcome_name,
            "Cohort": row_c1[0],
            "N": row_c1[2],
            "Events": row_c1[3],
            "Risk": row_c1[4],
            "Stat": "",
            "Odds Ratio": "",
            "Z": "",
            "P": ""
        },
        {
            "Outcome": "",
            "Cohort": row_c2[0],
            "N": row_c2[2],
            "Events": row_c2[3],
            "Risk": row_c2[4],
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

if "order" not in st.session_state or set(st.session_state.get("order", [])) != set(outcome_names):
    st.session_state["order"] = outcome_names.copy()

order = st.multiselect(
    "Drag outcomes below to reorder for display:",
    options=outcome_names,
    default=st.session_state["order"],
    key="outcome_order"
)

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
        stats_fg="#764600",
        font_family="Arial, sans-serif",
        border_style="1px solid #b8cbe9"
    ):
    css = f"""
    <style>
    .stacked-table {{
        border-collapse:collapse;width:100%;font-family:{font_family};font-size:0.97em;
    }}
    .stacked-table th {{
        background:{header_bg};
        color:{header_fg};
        padding:7px 6px;
        font-size:1em;
        border:{border_style};
        {"font-weight:700;" if bold_headers else "font-weight:400;"}
    }}
    .stacked-table td {{
        border:{border_style};
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
    font_family=font_family,
    border_style=border_style
), unsafe_allow_html=True)

st.download_button(
    "Download Stacked Table as CSV",
    stacked_df.to_csv(index=False),
    "stacked_outcomes_table.csv",
    "text/csv"
)
