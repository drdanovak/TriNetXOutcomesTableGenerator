import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(layout="wide")
st.title("TriNetX Compact Table Generator")

uploaded_files = st.file_uploader(
    "📂 Upload TriNetX outcome files (.csv only for max reliability)",
    type=["csv"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one TriNetX outcome file exported from TriNetX.")
    st.stop()

# ---- Sidebar/Toolbar Options ----
st.sidebar.header("Table Options")

journal_style = st.sidebar.selectbox(
    "Journal Table Style",
    ["AMA", "APA", "NEJM"],
    index=0
)
grayscale = st.sidebar.checkbox("Grayscale style", value=False)
decimals = st.sidebar.number_input("Decimal places", min_value=0, max_value=6, value=3, step=1)
show_percent = st.sidebar.checkbox("Show risk as percent (%)", value=False)
bold_headers = st.sidebar.checkbox("Bold column headers", value=True)

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
    "GRAYSCALE": dict(
        header_bg="#222", header_fg="#fff",
        stats_bg="#eee", stats_fg="#222",
        font="Arial, sans-serif", border="1px solid #555"
    )
}
defaults = JOURNAL_STYLES[journal_style]
if grayscale:
    defaults = JOURNAL_STYLES["GRAYSCALE"]

header_bg = st.sidebar.color_picker("Header background", defaults['header_bg'])
header_fg = st.sidebar.color_picker("Header text", defaults['header_fg'])
stats_bg = st.sidebar.color_picker("Statistics row background", defaults['stats_bg'])
stats_fg = st.sidebar.color_picker("Statistics row text", defaults['stats_fg'])
font_family = defaults['font']
border_style = defaults['border']

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

def fmt_num(val, decimals=3, percent=False):
    try:
        num = float(val)
        if percent:
            num = num * 100
            s = f"{num:.{decimals}f}%"
        else:
            s = f"{num:.{decimals}f}"
        return s
    except Exception:
        return val

def fmt_p(val):
    try:
        num = float(val)
        if num < 0.001:
            return "p<.001"
        else:
            return f"p={num:.3f}"
    except Exception:
        if str(val).strip() == "":
            return ""
        return f"p={val}"
    
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
    for file in uploaded_files:
        default_name = file.name.rsplit('.', 1)[0]
        user_outcome = st.text_input(f"Outcome name for '{default_name}'", default_name, key=f"outcome_{default_name}")
        outcome_name_map[file.name] = user_outcome

    st.markdown("---")
    order = st.multiselect(
        "Display order (drag to rearrange):",
        options=[outcome_name_map[file.name] for file in uploaded_files],
        default=[outcome_name_map[file.name] for file in uploaded_files],
        key="outcome_order"
    )

diagnostics = []
for file in uploaded_files:
    df = robust_csv_to_df(file)
    min_rows = 28
    min_cols = 6
    if df.shape[0] < min_rows:
        df = pd.concat([df, pd.DataFrame([[''] * df.shape[1] for _ in range(min_rows - df.shape[0])])], ignore_index=True)
    if df.shape[1] < min_cols:
        add_cols = min_cols - df.shape[1]
        pad_df = pd.DataFrame([[''] * add_cols for _ in range(df.shape[0])])
        df = pd.concat([df, pad_df], axis=1)

    name = outcome_name_map[file.name]

    cohort_1 = [
        get_cell(df,10,1), get_cell(df,10,2), get_cell(df,10,3), get_cell(df,10,4)
    ]
    cohort_2 = [
        get_cell(df,11,1), get_cell(df,11,2), get_cell(df,11,3), get_cell(df,11,4)
    ]
    # Risk Difference
    risk_diff = fmt_num(get_cell(df,16,0), decimals, show_percent)
    risk_diff_ci = f"({fmt_num(get_cell(df,16,1),decimals,show_percent)}, {fmt_num(get_cell(df,16,2),decimals,show_percent)})"
    risk_diff_p = fmt_p(get_cell(df,16,4))
    # Risk Ratio
    risk_ratio = fmt_num(get_cell(df,21,0), decimals, False)
    risk_ratio_ci = f"({fmt_num(get_cell(df,21,1),decimals,False)}, {fmt_num(get_cell(df,21,2),decimals,False)})"
    # Odds Ratio
    odds_ratio = fmt_num(get_cell(df,26,0), decimals, False)
    odds_ratio_ci = f"({fmt_num(get_cell(df,26,1),decimals,False)}, {fmt_num(get_cell(df,26,2),decimals,False)})"

    block = [
        [f"<b>{name}</b>", "", "", ""],
        ["Cohort", "Patients", "With Outcome", "Risk"],
        [cohort_1[0], fmt_num(cohort_1[1], decimals), fmt_num(cohort_1[2], decimals), fmt_num(cohort_1[3], decimals, show_percent)],
        [cohort_2[0], fmt_num(cohort_2[1], decimals), fmt_num(cohort_2[2], decimals), fmt_num(cohort_2[3], decimals, show_percent)],
        ["Risk Difference", risk_diff, f"95% CI: {risk_diff_ci}", risk_diff_p],
        ["Risk Ratio", risk_ratio, f"95% CI: {risk_ratio_ci}", ""],
        ["Odds Ratio", odds_ratio, f"95% CI: {odds_ratio_ci}", ""],
    ]
    outcome_names.append(name)
    outcome_tables.append(block)

def style_block(block, bold_headers, header_bg, header_fg, stats_bg, stats_fg, font_family, border_style, grayscale=False):
    if grayscale:
        header_bg, header_fg, stats_bg, stats_fg = "#222", "#fff", "#eee", "#222"
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
        border_style=border_style,
        grayscale=grayscale,
    ), unsafe_allow_html=True)

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

# Diagnostics for development/debugging
with st.expander("Show Diagnostics", expanded=False):
    st.write(pd.DataFrame(diagnostics))
