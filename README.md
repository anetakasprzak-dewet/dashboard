# Auto Analytics & Reporting Dashboard

A Streamlit-based dashboard tool that auto-builds key reporting views using your operational and financial data from:

- monday.com (deals / pipeline context)
- Harvest (time tracking)
- Xero (billing and collections)

## What it supports

- Auto-generated dashboard from integrated data sources.
- Team-level target management (revenue, collections, utilization hours, profitability).
- Billing visibility by **month** and **year**.
- Money collected and outstanding amounts.
- Time recorded per team.
- Deal profitability analysis.
- Consolidated team scorecard vs targets.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py