import streamlit as st
import pandas as pd
import numpy as np
import io

# Import Sortable for drag-and-drop, make sure to install 'streamlit-sortables'
from streamlit_sortables import sort_items

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

with st.sidebar.expander("Color and Style Options", expanded=False):
    journal_style = st.selectbox(
        "Journal Table Style",
        ["AMA", "APA", "NEJM"],
        index=0
    )
    grayscale = st.checkbox("Grayscale style", value=False)
    font_family = st.selectbox("Font", ["Arial, sans-serif", "Times New Roman, Times, serif", "Georgia, serif"], index=0)
    border_style = st.selectbox("Border Style", ["1px solid #b6c5db", "1px solid #aab8c2", "1px solid #e2bfc1", "1px solid #555"], index=0)
    spacing = st.slider("Cell vertical spacing (px)", 4, 20, 8, 1)

    horizontal_align = st.selectbox("Horizontal Align", ["center", "left", "right"], index=0)
    vertical_align = st.selectbox("Vertical Align", ["middle", "top", "bottom"], index=0)

    JOURNAL_STYLES = {
        "AMA": dict(
            header_bg="#1b365d", header_fg="#ffffff",
            stats_bg="#e6ecf2", stats_fg="#243952",
        ),
        "APA": dict(
            header_bg="#002b36", header_fg="#fff",
            stats_bg="#e1f0ee", stats_fg="#175c4c",
        ),
        "NEJM": dict(
            header_bg="#d6001c", header_fg="#fff",
            stats_bg="#fbeaea", stats_fg="#990000",
        ),
        "GRAYSCALE": dict(
            header_bg="#646464", header_fg="#fff",
            stats_bg="#eee", stats_fg="#222",
        )
    }
    defaults = JOURNAL_STYLES[journal_style]
    if grayscale:
        color_override = JOURNAL_STYLES["GRAYSCALE"]
        header_bg = st.color_picker("Header background", color_override['header_bg'])
        header_fg = st.color_picker("Header text", color_override['header_fg'])
        stats_bg = st.color_picker("Statistics row background", color_override['stats_bg'])
        stats_fg = st.color_picker("Statistics row text", color_override['stats_fg'])
    else:
        header_bg = st.color_picker("Header background", defaults['header_bg'])
        header_fg = st.color_picker("Header text", defaults['header_fg'])
        stats_bg = st.color_picker("Statistics row background", defaults['stats_bg'])
        stats_fg = st.color_picker("Statistics row text", defaults['stats_fg'])

    bold_headers = st.checkbox("Bold column headers", value=True)

decimals = st.sidebar.number_input("Decimal places for risks/ratios", min_value=0, max_value=6, value=3, step=1)
show_percent = st.sidebar.checkbox("Show risk as percent (%)", value=False)

# ---- File and Table Adjustments ----
with st.sidebar.expander("File and Table Adjustments", expanded=False):
    outcome_name_map = {}
    for file in uploaded_files:
        default_name = file.name.rsplit('.', 1)[0]
        user_outcome = st.text_input(f"Outcome name for '{default_name}'", default_name, key=f"outcome_{default_name}")
        outcome_name_map[file.name] = user_outcome

    st.markdown("---")
    # Drag-and-drop ordering using streamlit-sortables
    item_labels = [outcome_name_map[file.name] for file in uploaded_files]
    sorted_items = sort_items(item_labels, direction="vertical", label="Drag to reorder outcome tables")
    st.session_state["order"] = sorted_items

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

def fmt_num(val, decimals=3, percent=False, integer=False):
    try:
        if integer:
            return f"{int(float(val)):,}"
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

outcome_names = []
outcome_tables = []
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
        get_cell(df,10,1), 
        fmt_num(get_cell(df,10,2), integer=True),
        fmt_num(get_cell(df,10,3), integer=True),
        fmt_num(get_cell(df,10,4), decimals, show_percent)
    ]
    cohort_2 = [
        get_cell(df,11,1), 
        fmt_num(get_cell(df,11,2), integer=True),
        fmt_num(get_cell(df,11,3), integer=True),
        fmt_num(get_cell(df,11,4), decimals, show_percent)
    ]
    risk_diff = fmt_num(get_cell(df,16,0), decimals, show_percent)
    risk_diff_ci = f"({fmt_num(get_cell(df,16,1),decimals,show_percent)}, {fmt_num(get_cell(df,16,2),decimals,show_percent)})"
    risk_diff_p = fmt_p(get_cell(df,16,4))
    risk_ratio = fmt_num(get_cell(df,21,0), decimals, False)
    risk_ratio_ci = f"({fmt_num(get_cell(df,21,1),decimals,False)}, {fmt_num(get_cell(df,21,2),decimals,False)})"
    odds_ratio = fmt_num(get_cell(df,26,0), decimals, False)
    odds_ratio_ci = f"({fmt_num(get_cell(df,26,1),decimals,False)}, {fmt_num(get_cell(df,26,2),decimals,False)})"

    block = [
        [f"<b>{name}</b>", "", "", ""],
        ["Cohort", "Patients", "Patients with Outcome", "Risk"],
        cohort_1,
        cohort_2,
        ["Risk Difference", risk_diff, f"95% CI: {risk_diff_ci}", risk_diff_p],
        ["Risk Ratio", risk_ratio, f"95% CI: {risk_ratio_ci}", ""],
        ["Odds Ratio", odds_ratio, f"95% CI: {odds_ratio_ci}", ""],
    ]
    outcome_names.append(name)
    outcome_tables.append(block)

def style_block(block, bold_headers, header_bg, header_fg, stats_bg, stats_fg, font_family, border_style, spacing, h_align, v_align):
    css = f"""
    <style>
    .compact-table {{
        border-collapse:collapse;width:70%;font-family:{font_family};font-size:1.04em;margin-bottom:2em;
    }}
    .compact-table th, .compact-table td {{
        border:{border_style};
        padding:{spacing}px 8px;
        text-align:{h_align};
        vertical-align:{v_align};
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

# Use drag-and-drop sort order if available, else preserve upload order
order = st.session_state.get("order", outcome_names)

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
        spacing=spacing,
        h_align=horizontal_align,
        v_align=vertical_align,
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

# Diagnostics (optional)
with st.expander("Show Diagnostics", expanded=False):
    st.write(outcome_names)
    st.write(st.session_state.get("order"))
