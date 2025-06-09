import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("TriNetX Outcomes Table (Custom Layout)")

uploaded_files = st.file_uploader(
    "📂 Upload TriNetX outcome files (.csv, .xls, or .xlsx)",
    type=["csv", "xls", "xlsx"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one TriNetX outcome file exported from TriNetX.")
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
    stats_bg = st.color_picker("Statistics row background", defaults['stats_bg'])
    stats_fg = st.color_picker("Statistics row text", defaults['stats_fg'])
    font_family = defaults['font']
    border_style = defaults['border']

# --- Expander: Other Options ---
with st.expander("Other Table Options (click to expand)", expanded=False):
    bold_headers = st.checkbox("Bold column headers", value=True)
    st.markdown("---")
    st.markdown("#### Rearrangement")
    st.caption("Drag outcome names to set display order below.")

def safe(df, row, col):
    try:
        return df.iloc[row, col] if row < df.shape[0] and col < df.shape[1] else ""
    except Exception:
        return ""

# --- Build blocks for each outcome file ---
outcome_tables = []
outcome_names = []
for file in uploaded_files:
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
        continue

    default_name = file.name.rsplit('.', 1)[0]
    with st.expander(f"Customize Outcome Name for '{default_name}'", expanded=False):
        user_outcome = st.text_input("Enter Outcome Name", default_name, key=f"outcome_{default_name}")

    outcome_names.append(user_outcome)

    table = [
        [user_outcome, "", "", "", ""],  # Outcome name as first row
        ["Cohort Name", "Patients in Cohort", "Patients with Outcome", "Risk", ""],
        [safe(df, 10, 1), safe(df, 10, 2), safe(df, 10, 3), safe(df, 10, 4), ""],  # B11-E11
        [safe(df, 11, 1), safe(df, 11, 2), safe(df, 11, 3), safe(df, 11, 4), ""],  # B12-E12
        ["", "", "", "", ""],  # spacer row
        ["Risk Difference", "", "Risk Ratio", safe(df, 21, 0), "Odds Ratio", safe(df, 26, 0)],
        [
            safe(df, 16, 0),  # A17
            safe(df, 16, 1),  # B17
            "95% CI", f"({safe(df, 21, 1)}, {safe(df, 21, 2)})",
            "95% CI", f"({safe(df, 26, 1)}, {safe(df, 26, 2)})"
        ],
        [
            "95% CI", f"({safe(df, 16, 1)}, {safe(df, 16, 2)})",
            "", "",
            "p", safe(df, 16, 4)
        ]
    ]
    # Some rows have >5 columns, fix:
    block = []
    for row in table:
        if len(row) < 6:
            row = row + [""] * (6 - len(row))
        block.append(row)
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

# --- Render each table in chosen order ---
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
    .custom-table thead tr th {{
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
        row_class = "stats-row" if i > 4 else ""
        tag = "th" if i == 1 else "td"
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

# Optionally allow user to download as CSV (one block per outcome)
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
