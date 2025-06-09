import streamlit as st
import pandas as pd
import numpy as np
import io
import os

st.set_page_config(layout="wide")
st.title("TriNetX Outcomes Table (Bombproof Absolute Cell Mapping)")

uploaded_files = st.file_uploader(
    "📂 Upload TriNetX outcome files (.csv only for max reliability)",
    type=["csv"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one TriNetX outcome file exported from TriNetX.")
    st.stop()

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

with st.expander("Journal Table Style (click to expand)", expanded=False):
    journal_style = st.radio(
        "Select Table Style (overrides colors below):",
        list(JOURNAL_STYLES.keys()),
        index=0
    )

defaults = JOURNAL_STYLES[journal_style]

with st.expander("Table Colors (click to expand)", expanded=False):
    header_bg = st.color_picker("Header background", defaults['header_bg'])
    header_fg = st.color_picker("Header text", defaults['header_fg'])
    stats_bg = st.color_picker("Statistics row background", defaults['stats_bg'])
    stats_fg = st.color_picker("Statistics row text", defaults['stats_fg'])
    font_family = defaults['font']
    border_style = defaults['border']

with st.expander("Other Table Options (click to expand)", expanded=False):
    bold_headers = st.checkbox("Bold column headers", value=True)
    st.markdown("---")
    st.markdown("#### Rearrangement")
    st.caption("Drag outcome names to set display order below.")

def robust_csv_to_df(uploaded_file):
    # Reads a CSV "as-is", splitting on comma or tab, pads to max width
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

outcome_tables = []
outcome_names = []
for file in uploaded_files:
    # Bombproof CSV loader
    df = robust_csv_to_df(file)

    # Optionally show for validation
    # st.write(f"Preview for file: {file.name}")
    # st.dataframe(df.head(30))

    min_rows = 28
    min_cols = 6
    if df.shape[0] < min_rows:
        df = pd.concat([df, pd.DataFrame([['']*df.shape[1]]*(min_rows-df.shape[0]))], ignore_index=True)
    if df.shape[1] < min_cols:
        df = pd.concat([df, pd.DataFrame([['']*(min_cols-df.shape[1]) for _ in range(df.shape[0]))], axis=1)

    default_name = file.name.rsplit('.', 1)[0]
    with st.expander(f"Customize Outcome Name for '{default_name}'", expanded=False):
        user_outcome = st.text_input("Enter Outcome Name", default_name, key=f"outcome_{default_name}")

    outcome_names.append(user_outcome)

    # --- Absolute mapping per your design ---
    block = [
        [user_outcome, "", "", "", "", ""],  # Outcome name row
        ["Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk", "", ""],
        [get_cell(df,10,1), get_cell(df,10,2), get_cell(df,10,3), get_cell(df,10,4), "", ""],  # B11-E11
        [get_cell(df,11,1), get_cell(df,11,2), get_cell(df,11,3), get_cell(df,11,4), "", ""],  # B12-E12
        ["", "", "", "", "", ""],  # spacer
        ["Risk Difference", "", "Risk Ratio", get_cell(df,21,0), "Odds Ratio", get_cell(df,26,0)],
        [
            get_cell(df,16,0), get_cell(df,16,1),
            "95% CI", f"({get_cell(df,21,1)}, {get_cell(df,21,2)})",
            "95% CI", f"({get_cell(df,26,1)}, {get_cell(df,26,2)})"
        ],
        [
            "95% CI", f"({get_cell(df,16,1)}, {get_cell(df,16,2)})", "", "",
            "p", get_cell(df,16,4)
        ]
    ]
    outcome_tables.append(block)

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

def style_block(block, bold_headers, header_bg, header_fg, stats_bg, stats_fg, font_family, border_style):
    css = f"""
    <style>
    .custom-table {{
        border-collapse:collapse;width:90%;font-family:{font_family};font-size:1em;margin-bottom:2em;
    }}
    .custom-table th, .custom-table td {{
        border:{border_style};
        padding:7px 6px;
        text-align:center;
    }}
    .custom-table tr.header-row th {{
        background:{header_bg};
        color:{header_fg};
        {"font-weight:700;" if bold_headers else ""}
        font-size:1em;
    }}
    .custom-table tr.stats-row td {{
        background:{stats_bg};
        color:{stats_fg};
        font-weight:600;
    }}
    </style>
    """
    html = css + "<table class='custom-table'><tbody>"
    for i, row in enumerate(block):
        row_class = ""
        if i == 1:
            row_class = "header-row"
            tag = "th"
        elif i > 4:
            row_class = "stats-row"
            tag = "td"
        else:
            tag = "td"
        html += f"<tr class='{row_class}'>" + "".join([f"<{tag}>{cell}</{tag}>" for cell in row]) + "</tr>"
    html += "</tbody></table>"
    return html

st.markdown("### Custom Outcomes Table(s)")
for name in st.session_state["order"]:
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

csv_buffer = io.StringIO()
for idx, name in enumerate(st.session_state["order"]):
    pd.DataFrame(outcome_tables[idx]).to_csv(csv_buffer, index=False, header=False)
    csv_buffer.write("\n\n")
st.download_button(
    "Download All Outcomes as CSV",
    csv_buffer.getvalue(),
    "all_outcomes_tables.csv",
    "text/csv"
)
