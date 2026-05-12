import streamlit as st
import pandas as pd
import openpyxl
import urllib.parse
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Marine Spares & PMS Monitor", 
    page_icon="🚢", 
    layout="wide"
)

# 2. CORE FUNCTIONS
def process_excel_with_hyperlinks(file):
    """
    Reads the raw Excel file using openpyxl, bypasses broken local links, 
    decodes URLs, and rebuilds the absolute company network path.
    """
    try:
        # Reset the file pointer (crucial for Streamlit Cloud)
        file.seek(0)
        
        # Load the workbook (data_only=True ignores formulas)
        wb = openpyxl.load_workbook(file, data_only=True)
        
        # Locate the 'SPARES' sheet (case-insensitive check)
        sheet_name = next((s for s in wb.sheetnames if 'SPARES' in s.upper()), wb.sheetnames[0])
        ws = wb[sheet_name]
        
        # Dynamically find the header row
        header_row_idx = None
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True)):
            if row and ("TA REF" in row or "DESCRIPTION" in row):
                header_row_idx = i + 1 # openpyxl uses 1-based indexing
                break
                
        if not header_row_idx:
            st.error("Could not locate the header row. Please ensure a column named 'TA REF' exists.")
            return pd.DataFrame()

        # Extract headers
        headers = [str(cell.value).strip() if cell.value else f"Col_{idx}" for idx, cell in enumerate(ws[header_row_idx])]
        
        data = []
        
        # The known base path for the company network drive
        base_path = r"Z:\Marine_Dept\Alexis\Spares\Hyperlinks 2026"
        
        # Iterate through rows below the header
        for row in ws.iter_rows(min_row=header_row_idx + 1):
            row_data = {}
            has_data = False
            for idx, cell in enumerate(row):
                if idx < len(headers):
                    col_name = headers[idx]
                    row_data[col_name] = cell.value
                    
                    if cell.value is not None:
                        has_data = True
                    
                    # EXTRACT AND REBUILD HYPERLINK TARGETS 
                    if cell.hyperlink and cell.hyperlink.target:
                        raw_link = str(cell.hyperlink.target)
                        
                        # Clean up URL encoding (turns %20 into spaces)
                        clean_link = urllib.parse.unquote(raw_link)
                        
                        # Rebuild the absolute path if it's a relative link
                        if clean_link.startswith("..\\..\\") and "MODION" in clean_link:
                            tail_end = clean_link.split("MODION")[1]
                            rebuilt_link = f"{base_path}\\MODION{tail_end}"
                            # Convert Windows backslashes to forward slashes for universal web linking
                            rebuilt_link = rebuilt_link.replace("\\", "/")
                            row_data[f"{col_name}_URL"] = f"file:///{rebuilt_link}"
                        else:
                            row_data[f"{col_name}_URL"] = clean_link
                        
            # Only append if the row has actual data
            if has_data and row_data.get("TA REF"):
                data.append(row_data)
                
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Error reading the Excel file: {str(e)}")
        return pd.DataFrame()

def calculate_status(df):
    """
    Calculates the current status of each requisition based on PMS milestones.
    """
    today = pd.to_datetime('today')
    
    # Standardize date columns safely
    date_cols = ['DATE', 'ORDER DATE', 'EST. READINESS', 'RCVD']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    statuses = []
    for _, row in df.iterrows():
        if pd.notnull(row.get('RCVD')):
            statuses.append("🟢 Received / Completed")
        elif pd.notnull(row.get('EST. READINESS')):
            if row['EST. READINESS'] < today:
                statuses.append("🔴 LAGGING: Overdue for Delivery")
            else:
                statuses.append("🟡 In Transit / Awaiting Delivery")
        elif pd.notnull(row.get('ORDER DATE')):
            statuses.append("🟠 Ordered: Awaiting Readiness Date")
        elif pd.notnull(row.get('DATE')):
            if (today - row['DATE']).days > 14:
                statuses.append("🔴 LAGGING: Overdue for Purchasing")
            else:
                statuses.append("🔵 Pending Office Approval")
        else:
            statuses.append("⚪ Unknown Status")
            
    df['STATUS'] = statuses
    
    # Reorder columns to put STATUS up front for visibility
    cols = df.columns.tolist()
    if 'STATUS' in cols:
        cols.insert(0, cols.pop(cols.index('STATUS')))
        df = df[cols]
        
    return df

# 3. UI LAYOUT
st.title("🚢 Marine Spares & PMS Monitor")
st.markdown("Upload your **Excel (.xlsx)** file to extract hidden component links and track moving/lagging parts securely.")

# File Uploader
uploaded_file = st.file_uploader("Upload Spares Excel File", type=["xlsx"])

if uploaded_file is not None:
    with st.spinner("Extracting raw data and rebuilding network links..."):
        # Process Data
        df = process_excel_with_hyperlinks(uploaded_file)
        
        if not df.empty:
            df = calculate_status(df)
            
            # --- DASHBOARD METRICS ---
            st.subheader("📊 Fleet Requisition Overview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Requisitions", len(df))
            col2.metric("Received 🟢", len(df[df['STATUS'].str.contains("Received", na=False)]))
            col3.metric("In Progress 🟡", len(df[df['STATUS'].str.contains("Transit|Ordered|Pending", na=False)]))
            
            lagging_count = len(df[df['STATUS'].str.contains("LAGGING", na=False)])
            col4.metric("Lagging / Overdue 🔴", lagging_count, delta_color="inverse")
            
            st.divider()
            
            # --- LAGGING ALERTS ---
            if lagging_count > 0:
                st.error(f"⚠️ Action Required: {lagging_count} component(s) are lagging behind schedule.")
                lagging_df = df[df['STATUS'].str.contains("LAGGING", na=False)]
                
                alert_cols = [c for c in ['STATUS', 'TA REF', 'TA REF_URL', 'EQUIPMENT', 'DESCRIPTION', 'DATE', 'EST. READINESS'] if c in lagging_df.columns]
                st.dataframe(
                    lagging_df[alert_cols], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "TA REF_URL": st.column_config.LinkColumn("Component Document")
                    }
                )
            else:
                st.success("✅ All systems go! No components are currently lagging.")
            
            st.divider()
            
            # --- MAIN DATA EXPLORER ---
            st.subheader("🔍 Full Component Explorer")
            
            # Filters
            filter_cols = st.columns(2)
            with filter_cols[0]:
                status_options = df['STATUS'].unique().tolist()
                status_filter = st.multiselect("Filter by Status:", options=status_options, default=status_options)
            with filter_cols[1]:
                if 'EQUIPMENT' in df.columns:
                    equip_options = df['EQUIPMENT'].dropna().unique().tolist()
                    equip_filter = st.multiselect("Filter by Equipment:", options=equip_options)
                else:
                    equip_filter = []
            
            # Apply Filters
            filtered_df = df[df['STATUS'].isin(status_filter)]
            if 'EQUIPMENT' in df.columns and equip_filter:
                filtered_df = filtered_df[filtered_df['EQUIPMENT'].isin(equip_filter)]
            
            # Show Data table with clickable links
            st.dataframe(
                filtered_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "TA REF_URL": st.column_config.LinkColumn("Component Document")
                }
            )
        else:
            st.warning("No data found or sheet is empty. Please ensure the 'SPARES' sheet is formatted correctly.")
