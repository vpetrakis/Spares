# 🚢 Marine Spares & PMS Monitor

A local, secure dashboard designed to track marine spare parts pipelines, calculate delivery bottlenecks, and bypass broken Excel relative links.

## 🚀 Features
* **Link Extraction:** Uses `openpyxl` to extract raw URLs/paths from Excel hyperlinks, allowing you to access component numbers even if the file is moved off the company network.
* **Automated Triage:** Calculates lagging components based on order dates vs. estimated readiness dates.
* **Secure Setup:** Runs entirely locally via Streamlit. No data is sent to external servers.

## 🛠️ Installation & Usage
1. Clone this repository to your local machine.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
