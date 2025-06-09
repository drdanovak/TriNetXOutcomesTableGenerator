import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(layout="wide")
st.title("TriNetX Compact Outcomes Table")

uploaded_files = st.file_uploader(
    "📂 Upload TriNetX outcome files (.csv only for max reliability)",
    type=["csv"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one TriNetX outcome file exported from TriNetX.")
    st.stop()

# ---- Toolbar/Sidebar Options ----
st.sidebar.header("Table Options")
journal_style = st.sidebar.selectbox(
    "Journal Table Style",
    ["AMA", "APA", "NEJM"],
    index=0
)
JOURNAL_STYLES = {
    "AMA": dict(
        header_bg="#1b365d", header_fg="#ffffff",
        stats_bg="#e6ecf2", stats_fg="#243952",
        font="Arial, sans-serif", border="1px solid #b6c5db"
    ),
    "APA": dict(
        header_bg="#002b36", header_fg="#fff",
        stats_bg="#e1f0ee", stats_fg="#175c4c",
        font="Times New Roman, Times, serif", border="1px solid #aab8c2"
    ),
    "NEJM": dict(
        header_bg="#d6001c", header_fg="#fff",
        stats_bg="#fbeaea", stats_fg="#990000",
        font="Georgia, serif", border="1px solid #e2bfc1"
    ),
}
defaults = JOURNAL_STYLES[journal_style]

header_bg = st.sidebar.color_picker("Header background", defaults['header_bg'])
header_fg = st.sidebar.color_picker("Header text", defaults['header_fg'])
stats_bg = st.sidebar.color_picker("Statistics row background", defaults['stats_bg'])
stats_fg = st.sidebar.color_picker("Statistics row text", defaults['stats_fg'])
font_family = defaults['font']
border_style = defaults['border']
bold_headers = st.sidebar.checkbox("Bold column headers", value=True)

outcome_names = []
outcome_tables = []
outcome_name_map = {}

def robust_csv_to_df(uploaded_file):
    raw = uploaded_file.read().decode('utf-8').splitlines()
    rows = []
    max_cols = 0
    for line in raw:
        comma_split = line.split(',')
        tab_split = line.split('\t')
        row = comma_split if len(comma_split) >= len(tab_split) else tab_split
        rows.append(row)
        if len(row) > max_cols:
            max_cols = len(row)
    rows = [r + [''] * (max_cols - len(r)) for r in rows]
    df = pd.DataFrame(rows)
    return df

def get_cell(df, row, col):
    try:
        val = df.iat[row, col]
        if pd.isna(val):
            return ""
        return str(val)
    except Exception:
        return ""

# ---- Sidebar: File Adjustment and Order ----
with st.sidebar.expander("File & Table Adjustments", expanded=True):
    name_inputs = {}
    for file in uploaded_files:
        default_name = file.name.rsplit('.', 1)[0]
        user_outcome = st.text_input(f"Outcome name for '{default_name}'", default_name, key=f"outcome_{default_name}")
        outcome_name_map[file.name] = user_outcome

    st.markdown("---")
    # You can't reorder file_uploader files directly, but you can let users specify the outcome order
    order = st.multiselect(
        "Display order (drag to rearrange):",
        options=[outcome_name_map[file.name] for file in uploaded_files],
        default=[outcome_name_map[file.name] for file in uploaded_files],
        key="outcome_order"
    )

# ---- Process and Display Each Table ----
diagnostics = []
for file in uploaded_files:
    df = robust_csv_to_df(file)
    # Padding to avoid index errors
    min_rows = 28
    min_cols = 6
    if df.shape[0] < min_rows:
        df = pd.concat([df, pd.DataFrame([[''] * df.shape[1] for _ in range(min_rows - df.shape[0])])], ignore_index=True)
    if df.shape[1] < min_cols:
        add_cols = min_cols - df.shape[1]
        pad_df = pd.DataFrame([[''] * add_cols for _ in range(df.shape[0])])
        df = pd.concat([df, pad_df], axis=1)

    name = outcome_name_map[file.name]

    # --- Extract values with full diagnostic printout ---
    diagnostics.append({
        "file": file.name,
        "Cohort 1 Name (B11)": get_cell(df,10,1),
        "Cohort 1 Patients (C11)": get_cell(df,10,2),
        "Cohort 1 With Outcome (D11)": get_cell(df,10,3),
        "Cohort 1 Risk (E11)": get_cell(df,10,4),
        "Cohort 2 Name (B12)": get_cell(df,11,1),
        "Cohort 2 Patients (C12)": get_cell(df,11,2),
        "Cohort 2 With Outcome (D12)": get_cell(df,11,3),
        "Cohort 2 Risk (E12)": get_cell(df,11,4),
        "Risk Diff (A17)": get_cell(df,16,0),
        "Risk Diff Lower (B17)": get_cell(df,16,1),
        "Risk Diff Upper (C17)": get_cell(df,16,2),
        "Risk Diff p (E17)": get_cell(df,16,4),
        "Risk Ratio (A22)": get_cell(df,21,0),
        "Risk Ratio Lower (B22)": get_cell(df,21,1),
        "Risk Ratio Upper (C22)": get_cell(df,21,2),
        "Odds Ratio (A27)": get_cell(df,26,0),
        "Odds Ratio Lower (B27)": get_cell(df,26,1),
        "Odds Ratio Upper (C27)": get_cell(df,26,2),
    })

    block = [
        [f"<b>Outcome:</b> {name}", "", "", ""],
        ["<b>Cohort</b>", "<b>Patients</b>", "<b>With Outcome</b>", "<b>Risk</b>"],
        [get_cell(df,10,1), get_cell(df,10,2), get_cell(df,10,3), get_cell(df,10,4)],
        [get_cell(df,11,1), get_cell(df,11,2), get_cell(df,11,3), get_cell(df,11,4)],
        ["<b>Risk Difference</b>", get_cell(df,16,0), f"95% CI: ({get_cell(df,16,1)}, {get_cell(df,16,2)})", f"p: {get_cell(df,16,4)}"],
        ["<b>Risk Ratio</b>", get_cell(df,21,0), f"95% CI: ({get_cell(df,21,1)}, {get_cell(df,21,2)})", ""],
        ["<b>Odds Ratio</b>", get_cell(df,26,0), f"95% CI: ({get_cell(df,26,1)}, {get_cell(df,26,2)})", ""],
    ]
    outcome_names.append(name)
    outcome_tables.append(block)

def style_block(block, bold_headers, header_bg, header_fg, stats_bg, stats_fg, font_family, border_style):
    css = f"""
    <style>
    .compact-table {{
        border-collapse:collapse;width:70%;font-family:{font_family};font-size:1.04em;margin-bottom:2em;
    }}
    .compact-table th, .compact-table td {{
        border:{border_style};
        padding:5px 6px;
        text-align:center;
        vertical-align:middle;
    }}
    .compact-table tr:nth-child(1) td {{
        background:{header_bg};
        color:{header_fg};
        {"font-weight:700;" if bold_headers else ""}
        font-size:1.08em;
        text-align:left;
    }}
    .compact-table tr:nth-child(2) td {{
        background:{header_bg};
        color:{header_fg};
        {"font-weight:700;" if bold_headers else ""}
    }}
    .compact-table tr:nth-child(n+5) td {{
        background:{stats_bg};
        color:{stats_fg};
        font-weight:600;
    }}
    </style>
    """
    html = css + "<table class='compact-table'>"
    for i, row in enumerate(block):
        html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

st.markdown("### Compact Outcomes Table(s)")
# Only show selected order
for name in order:
    idx = outcome_names.index(name)
    block = outcome_tables[idx]
    st.markdown(style_block(
        block,
        bold_headers=bold_headers,
        header_bg=header_bg,
        header_fg=header_fg,
        stats_bg=stats_bg,
        stats_fg=stats_fg,
        font_family=font_family,
        border_style=border_style
    ), unsafe_allow_html=True)

# Optional: Download CSV
csv_buffer = io.StringIO()
for idx, name in enumerate(order):
    pd.DataFrame(outcome_tables[outcome_names.index(name)]).to_csv(csv_buffer, index=False, header=False)
    csv_buffer.write("\n\n")
st.download_button(
    "Download All Outcomes as CSV",
    csv_buffer.getvalue(),
    "all_outcomes_tables.csv",
    "text/csv"
)

# ---- Diagnostics Table (For Debugging, remove/comment for final) ----
with st.expander("Show Diagnostics", expanded=False):
    st.write(pd.DataFrame(diagnostics))
