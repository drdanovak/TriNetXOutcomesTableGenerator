import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("📈 TriNetX Outcomes Table Maker (Multi-File Journal Formatter)")

st.markdown("""
Upload multiple CSV files containing your outcomes data. The app will automatically combine them into a single, clean, journal-ready table.
You can adjust formatting and column selection to match your publication’s requirements.
""")

# --- Robust CSV Loader ---
def robust_read_csv(uploaded_file):
    # Try TriNetX-style file (skip 9 header rows)
    uploaded_file.seek(0)
    try:
        df = pd.read_csv(uploaded_file, header=None, skiprows=9)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        return df
    except Exception:
        pass
    # Try as regular CSV
    uploaded_file.seek(0)
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        raise e

# --- 1. File Upload Section ---
uploaded_files = st.file_uploader(
    "📂 Upload one or more Outcomes CSV files", type="csv", accept_multiple_files=True
)

if not uploaded_files or len(uploaded_files) == 0:
    st.info("Please upload at least one CSV file.")
    st.stop()

# --- 2. Data Loading and Merging ---
dfs = []
for file in uploaded_files:
    try:
        df = robust_read_csv(file)
        dfs.append(df)
    except Exception as e:
        st.warning(f"Could not read {file.name}: {e}")

if not dfs:
    st.error("No valid files loaded.")
    st.stop()

# Align columns across all files (union of all columns, fill missing with empty string)
all_columns = []
for df in dfs:
    all_columns += list(df.columns)
all_columns = list(dict.fromkeys(all_columns))  # Remove duplicates, keep order

merged_df = pd.concat(
    [df.reindex(columns=all_columns, fill_value="") for df in dfs],
    axis=0,
    ignore_index=True
)

# Clean up column names, trim whitespace
merged_df.columns = [str(c).strip() for c in merged_df.columns]

# --- 3. Sidebar Formatting and Selection ---
with st.sidebar.expander("🛠️ Table Formatting & Columns", expanded=True):
    font_size = st.slider("Font Size (pt)", 7, 18, 11)
    h_align = st.selectbox("Text Align", ["left", "center", "right"], index=1)
    v_align = st.selectbox("Vertical Align", ["top", "middle", "bottom"], index=1)
    round_decimals = st.slider("Round numerical values to", 0, 5, 2)
    # Column selection
    selected_columns = st.multiselect(
        "Columns to display (drag to re-order):",
        merged_df.columns,
        default=merged_df.columns
    )
    # Column renaming
    rename_dict = {}
    for col in selected_columns:
        new_name = st.text_input(f"Rename column '{col}'", col, key=f"rename_{col}")
        rename_dict[col] = new_name

# Filter and rename columns
display_df = merged_df[selected_columns].rename(columns=rename_dict)

# Try rounding numerics
for col in display_df.columns:
    try:
        display_df[col] = pd.to_numeric(display_df[col]).round(round_decimals)
    except Exception:
        pass

# --- 4. Generate HTML Table with Journal Formatting ---
def make_html_table(df, font_size, h_align, v_align):
    # Table CSS
    css = f"""
    <style>
    table.outcomes-table {{
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: {font_size}pt;
    }}
    th, td {{
        border: 1px solid #888;
        padding: 6px 10px;
        text-align: {h_align};
        vertical-align: {v_align};
    }}
    th {{
        background: #f7f7f7;
        font-weight: bold;
    }}
    </style>
    """
    # Table HTML
    html = css + "<table class='outcomes-table'>"
    # Header
    html += "<tr>" + "".join([f"<th>{c}</th>" for c in df.columns]) + "</tr>"
    # Data rows
    for _, row in df.iterrows():
        html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

st.markdown("### 🧾 Journal-Ready Outcomes Table")
table_html = make_html_table(display_df, font_size, h_align, v_align)
st.markdown(table_html, unsafe_allow_html=True)

# --- 5. Download / Copy Options ---
st.markdown("---")
csv_buffer = io.StringIO()
display_df.to_csv(csv_buffer, index=False)
st.download_button(
    "Download as CSV",
    csv_buffer.getvalue(),
    file_name="Combined_Outcomes_Table.csv",
    mime="text/csv"
)

# Copy-to-clipboard HTML table (JS workaround)
copy_button_html = """
<button onclick="navigator.clipboard.writeText(document.getElementById('final_table').outerHTML);"
style="padding:8px 18px;font-size:1rem;border-radius:6px;border:1px solid #888;background:#fafbfc;">
📋 Copy Table HTML to Clipboard
</button>
"""
st.markdown(f'<div id="final_table">{table_html}</div>', unsafe_allow_html=True)
st.markdown(copy_button_html, unsafe_allow_html=True)
