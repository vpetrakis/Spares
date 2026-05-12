import streamlit as st
import pandas as pd
import openpyxl
import urllib.parse
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & PREMIUM UI INJECTIONS
# ==========================================
st.set_page_config(page_title="Marine Spares Control Tower", page_icon="🚢", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    .metric-critical {
        background: linear-gradient(135deg, #2b0000 0%, #4a0000 100%);
        border: 1px solid #ff4b4b;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        animation: pulse 2s infinite;
    }
    .metric-card {
        background: #1E2329;
        border: 1px solid #2B303A;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    @keyframes pulse {
        0% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
        50% { box-shadow: 0 0 20px rgba(255, 75, 75, 0.8); }
        100% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BULLETPROOF DATA EXTRACTION ENGINE
# ==========================================
@st.cache_data(show_spinner=False)
def extract_and_clean_data(file_bytes):
    try:
        import io
        file_obj = io.BytesIO(file_bytes)
        wb = openpyxl.load_workbook(file_obj, data_only=True)
        sheet_name = next((s for s in wb.sheetnames if 'SPARES' in s.upper()), wb.sheetnames[0])
        ws = wb[sheet_name]
        
        header_row_idx = next((i + 1 for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True)) if row and "TA REF" in row), None)
        if not header_row_idx: return pd.DataFrame(), "CRITICAL ERROR: Header row not found."

        headers = [str(cell.value).strip() if cell.value else f"Col_{idx}" for idx, cell in enumerate(ws[header_row_idx])]
        data = []
        base_path = r"Z:\Marine_Dept\Alexis\Spares\Hyperlinks 2026"
        
        for row in ws.iter_rows(min_row=header_row_idx + 1):
            row_data = {}
            if not row[headers.index('TA REF') if 'TA REF' in headers else 1].value: continue
                
            for idx, cell in enumerate(row):
                if idx < len(headers):
                    col_name = headers[idx]
                    row_data[col_name] = cell.value
                    
                    if cell.hyperlink and cell.hyperlink.target:
                        raw_link = urllib.parse.unquote(str(cell.hyperlink.target))
                        if raw_link.startswith("..\\..\\") and "MODION" in raw_link:
                            tail = raw_link.split("MODION")[1].replace("\\", "/")
                            row_data[f"{col_name}_URL"] = f"file:///{base_path.replace(chr(92), '/')}/MODION{tail}"
                        else:
                            row_data[f"{col_name}_URL"] = raw_link
            data.append(row_data)
            
        df = pd.DataFrame(data)
        if 'SENT TO FINANCE' not in df.columns: df['SENT TO FINANCE'] = pd.NaT
        if 'PRIORITY' not in df.columns: df['PRIORITY'] = "STANDARD"
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ==========================================
# 3. STATE MACHINE & SLA CALCULATOR
# ==========================================
def process_pipeline_state(df):
    today = pd.to_datetime('today')
    date_cols = ['DATE', 'SENT TO FINANCE', 'ORDER DATE', 'EST. READINESS', 'RCVD']
    for col in date_cols: df[col] = pd.to_datetime(df[col], errors='coerce')
        
    SLA_SUPPLY = 7
    SLA_FINANCE = 5
    
    statuses, flags = [], []
    for _, row in df.iterrows():
        is_critical = str(row.get('PRIORITY')).upper().strip() == 'CRITICAL'
        
        if pd.notnull(row['RCVD']):
            state, flag = "🟢 Completed", "OK"
        elif pd.notnull(row['EST. READINESS']):
            state, flag = ("🔴 Logistics Lag (Overdue)", "DELAYED") if row['EST. READINESS'] < today else ("🟡 In Transit", "OK")
        elif pd.notnull(row['ORDER DATE']):
            state, flag = "🟠 Ordered (Awaiting Delivery Date)", "OK"
        elif pd.notnull(row['SENT TO FINANCE']):
            state, flag = ("🔴 Finance Lag (Overdue)", "DELAYED") if (today - row['SENT TO FINANCE']).days > SLA_FINANCE else ("🟣 Pending Finance", "OK")
        elif pd.notnull(row['DATE']):
            state, flag = ("🔴 Supply Lag (Overdue)", "DELAYED") if (today - row['DATE']).days > SLA_SUPPLY else ("🔵 Pending Supply", "OK")
        else:
            state, flag = "⚪ Unknown", "ERROR"
            
        if is_critical and flag == "DELAYED": state = "🔥 CRITICAL FAILURE: " + state
        statuses.append(state); flags.append(flag)
        
    df['STATUS'] = statuses; df['FLAG'] = flags
    cols = df.columns.tolist()
    for c in reversed([c for c in ['PRIORITY', 'STATUS', 'TA REF'] if c in cols]): cols.insert(0, cols.pop(cols.index(c)))
    return df

# ==========================================
# 4. FRONTEND DASHBOARD RENDERING
# ==========================================
st.title("🚢 Marine Spares Control Tower")

uploaded_file = st.file_uploader("Drop Master Spares File (.xlsx) Here", type=["xlsx"])

if uploaded_file:
    with st.spinner("Executing Data Extraction & Path Resolution..."):
        raw_df, error = extract_and_clean_data(uploaded_file.getvalue())
        
    if error: st.error(f"System Integrity Fault: {error}")
    elif not raw_df.empty:
        df = process_pipeline_state(raw_df)
        
        # --- METRICS ---
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><h3>{len(df)}</h3><p>Total Pipeline Requisitions</p></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>{len(df[df['STATUS'] == '🟢 Completed'])}</h3><p>Completed / Onboard</p></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>{len(df[df['FLAG'] == 'DELAYED']) - len(df[df['STATUS'].str.contains('CRITICAL FAILURE')])}</h3><p>Standard Delays</p></div>", unsafe_allow_html=True)
        
        crit_alerts = len(df[df['STATUS'].str.contains("CRITICAL FAILURE")])
        if crit_alerts > 0: c4.markdown(f"<div class='metric-critical'><h3 style='color:white;'>{crit_alerts}</h3><p style='color:white; font-weight:bold;'>CRITICAL OVERDUE</p></div>", unsafe_allow_html=True)
        else: c4.markdown(f"<div class='metric-card'><h3>0</h3><p>Critical Overdue</p></div>", unsafe_allow_html=True)

        st.markdown("<hr style='border:1px solid #2B303A'>", unsafe_allow_html=True)
        
        # --- NATIVE STREAMLIT BOTTLENECK ANALYSIS (No Plotly Required) ---
        st.subheader("📊 Pipeline Bottleneck Analysis")
        active_df = df[df['STATUS'] != '🟢 Completed']
        
        if not active_df.empty:
            col_chart, col_triage = st.columns([1.5, 2])
            with col_chart:
                status_counts = active_df['STATUS'].value_counts()
                st.bar_chart(status_counts) # Native Streamlit Chart
                
            with col_triage:
                st.markdown("### 🔥 Priority Triage Zone")
                critical_df = df[df['STATUS'].str.contains("CRITICAL FAILURE")]
                if not critical_df.empty:
                    st.error("Immediate Action Required on the following items:")
                    display_cols = [c for c in ['TA REF', 'EQUIPMENT', 'STATUS', 'DATE', 'SENT TO FINANCE'] if c in critical_df.columns]
                    st.dataframe(critical_df[display_cols], hide_index=True, use_container_width=True)
                else:
                    st.success("No critical overdue items. Fleet equipment is secure.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- INTERACTIVE DATA GRID ---
        st.subheader("🔍 Full Fleet Control Grid")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1: stat_filt = st.multiselect("Filter Status:", options=df['STATUS'].unique(), default=df['STATUS'].unique())
        with f_col2: equip_filt = st.multiselect("Filter Equipment:", options=df['EQUIPMENT'].dropna().unique())
        with f_col3: pri_filt = st.multiselect("Priority:", options=df['PRIORITY'].unique(), default=df['PRIORITY'].unique())
            
        filtered = df[df['STATUS'].isin(stat_filt) & df['PRIORITY'].isin(pri_filt)]
        if equip_filt: filtered = filtered[filtered['EQUIPMENT'].isin(equip_filt)]
            
        st.dataframe(
            filtered, use_container_width=True, hide_index=True,
            column_config={
                "TA REF_URL": st.column_config.LinkColumn("Document Link", display_text="Open File"),
                "COST": st.column_config.NumberColumn("Cost ($)", format="$%.2f"),
                "DATE": st.column_config.DateColumn("Requested", format="DD MMM YYYY"),
                "SENT TO FINANCE": st.column_config.DateColumn("To Finance", format="DD MMM YYYY"),
                "ORDER DATE": st.column_config.DateColumn("PO Placed", format="DD MMM YYYY")
            }
        )
