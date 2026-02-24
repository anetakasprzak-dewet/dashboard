 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
new file mode 100644
index 0000000000000000000000000000000000000000..520e7c4672148fac62e57e2e7703f2393b055240
--- /dev/null
+++ b/README.md
@@ -0,0 +1,44 @@
+# Auto Analytics & Reporting Dashboard
+
+A Streamlit-based dashboard tool that auto-builds key reporting views using your operational and financial data from:
+
+- monday.com (deals / pipeline context)
+- Harvest (time tracking)
+- Xero (billing and collections)
+
+## What it supports
+
+- Auto-generated dashboard from integrated data sources.
+- Team-level target management (revenue, collections, utilization hours, profitability).
+- Billing visibility by **month** and **year**.
+- Money collected and outstanding amounts.
+- Time recorded per team.
+- Deal profitability analysis.
+- Consolidated team scorecard vs targets.
+
+## Quick start
+
+```bash
+python -m venv .venv
+source .venv/bin/activate
+pip install -r requirements.txt
+streamlit run app.py
+```
+
+## Credentials (optional)
+
+If credentials are unavailable, the app auto-generates demo data so you can still use and test dashboards.
+
+Set environment variables to use live data:
+
+- `MONDAY_API_TOKEN`
+- `HARVEST_API_TOKEN`
+- `HARVEST_ACCOUNT_ID`
+- `XERO_ACCESS_TOKEN`
+- `XERO_TENANT_ID`
+
+## Notes
+
+- monday.com schema fields vary by board; update IDs/field mapping in `connectors.py`.
+- Xero and Harvest APIs can require pagination for larger datasets.
+- `team_scorecard` estimates collection per team proportionally to team revenue if direct team-invoice linking is unavailable.
 
EOF
)