import streamlit as st
import pandas as pd
import os
import numpy as np

st.set_page_config(layout="wide")
st.title("TriNetX Outcomes Table (Header-Relative Mapping)")

uploaded_files = st.file_uploader(
    "📂 Upload TriNetX outcome files (.csv, .xls, or .xlsx)",
    type=["csv", "xls", "xlsx"], accept_multiple_files=True
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

def get_cell(df, row, col):
    try:
        val = df.iat[row, col]
        if pd.isna(val):
            return ""
        return str(val)
    except Exception:
        return ""

def find_header_row(df):
    for idx in range(min(len(df), 40)):  # only check the first 40 rows
        row_vals = df.iloc[idx].astype(str).str.lower()
        if any("cohort name" in str(cell).strip().lower() for cell in row_vals):
            return idx
    return None

outcome_tables = []
outcome_names = []
for file in uploaded_files:
    file_ext = os.path.splitext(file.name)[-1].lower()
    if file_ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file, header=None, dtype=str)
    elif file_ext == ".csv":
        file.seek(0)
        try:
            df = pd.read_csv(file, header=None, engine="python", on_bad_lines="skip", dtype=str)
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, header=None, engine="python", error_bad_lines=False, dtype=str)
    else:
        continue

    # Pad for safety
    if df.shape[0] < 40:
        df = pd.concat([df, pd.DataFrame(np.full((40-df.shape[0], df.shape[1]), "", dtype=object))], ignore_index=True)
    if df.shape[1] < 10:
        df = pd.concat([df, pd.DataFrame(np.full((df.shape[0], 10-df.shape[1]), "", dtype=object))], axis=1)

    # --- Robust: find the "Cohort Name" header row ---
    header_row = find_header_row(df)
    if header_row is None:
        st.warning(f"File {file.name}: Could not find 'Cohort Name' header row.")
        continue

    default_name = file.name.rsplit('.', 1)[0]
    with st.expander(f"Customize Outcome Name for '{default_name}'", expanded=False):
        user_outcome = st.text_input("Enter Outcome Name", default_name, key=f"outcome_{default_name}")

    outcome_names.append(user_outcome)

    # Offsets relative to header_row:
    idx_c1 = header_row + 1
    idx_c2 = header_row + 2
    idx_riskdiff = header_row + 7
    idx_riskratio = header_row + 12
    idx_oddsratio = header_row + 17

    # Build table according to your drawing
    block = [
        [user_outcome, "", "", "", "", ""],
        [
            get_cell(df, header_row, 1),  # "Cohort Name"
            get_cell(df, header_row, 2),  # "Patients in Cohort"
            get_cell(df, header_row, 3),  # "Patients with Outcome"
            get_cell(df, header_row, 4),  # "Risk"
            "", ""
        ],
        [get_cell(df, idx_c1, 1), get_cell(df, idx_c1, 2), get_cell(df, idx_c1, 3), get_cell(df, idx_c1, 4), "", ""],
        [get_cell(df, idx_c2, 1), get_cell(df, idx_c2, 2), get_cell(df, idx_c2, 3), get_cell(df, idx_c2, 4), "", ""],
        ["", "", "", "", "", ""],  # spacer
        [
            "Risk Difference", "", "Risk Ratio", get_cell(df, idx_riskratio, 0), "Odds Ratio", get_cell(df, idx_oddsratio, 0)
        ],
        [
            get_cell(df, idx_riskdiff, 0), get_cell(df, idx_riskdiff, 1),
            "95% CI", f"({get_cell(df, idx_riskratio, 1)}, {get_cell(df, idx_riskratio, 2)})",
            "95% CI", f"({get_cell(df, idx_oddsratio, 1)}, {get_cell(df, idx_oddsratio, 2)})"
        ],
        [
            "95% CI", f"({get_cell(df, idx_riskdiff, 1)}, {get_cell(df, idx_riskdiff, 2)})", "", "",
            "p", get_cell(df, idx_riskdiff, 4)
        ]
    ]
    outcome_tables.append(block)

# --- Ordering UI ---
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

# CSV export for all outcomes (one after another)
import io
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
