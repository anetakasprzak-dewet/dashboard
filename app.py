from __future__ import annotations

import plotly.express as px
import streamlit as st

from connectors import DataConnector
from dashboard_builder import TeamTargets, deal_profitability, monthly_billing, team_scorecard, time_recorded_per_team, yearly_billing

st.set_page_config(page_title="Auto Analytics Dashboard", layout="wide")
st.title("Auto Analytics & Reporting Dashboard")
st.caption("Integrated view from monday.com, Harvest, and Xero. Uses demo data if credentials are missing.")

connector = DataConnector()
data = connector.load_data()
deals = data["deals"]
time_entries = data["time_entries"]
invoices = data["invoices"]

all_teams = sorted(set(deals.get("team", [])) | set(time_entries.get("team", [])))

st.sidebar.header("Team Targets")
default_targets: dict[str, TeamTargets] = {}
for team in all_teams:
    with st.sidebar.expander(team, expanded=False):
        revenue_target = st.number_input(f"{team} revenue target", min_value=0.0, value=250000.0, step=5000.0)
        collection_target = st.number_input(f"{team} collection target", min_value=0.0, value=200000.0, step=5000.0)
        utilization_target_hours = st.number_input(f"{team} utilization target hours", min_value=0.0, value=1800.0, step=50.0)
        profitability_target_pct = st.number_input(f"{team} profitability target %", min_value=0.0, value=35.0, step=1.0)
    default_targets[team] = TeamTargets(
        revenue_target=revenue_target,
        collection_target=collection_target,
        utilization_target_hours=utilization_target_hours,
        profitability_target_pct=profitability_target_pct,
    )

billing_month = monthly_billing(invoices)
billing_year = yearly_billing(invoices)
time_team = time_recorded_per_team(time_entries)
profitability = deal_profitability(deals)
scorecard = team_scorecard(deals, time_entries, invoices, default_targets)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total billed", f"${invoices['total'].sum():,.0f}")
col2.metric("Money collected", f"${invoices['amount_paid'].sum():,.0f}")
col3.metric("Total hours recorded", f"{time_entries['hours'].sum():,.0f}h")
col4.metric("Average deal margin", f"{profitability['profit_margin_pct'].mean():.1f}%")

st.subheader("Billing: Monthly vs Yearly")
a, b = st.columns(2)
a.plotly_chart(px.bar(billing_month, x="month", y=["total_billed", "amount_collected", "outstanding"], barmode="group"), use_container_width=True)
b.plotly_chart(px.bar(billing_year, x="year", y=["total_billed", "amount_collected", "outstanding"], barmode="group"), use_container_width=True)

st.subheader("Time Recorded per Team")
st.plotly_chart(px.pie(time_team, names="team", values="hours", hole=0.4), use_container_width=True)

st.subheader("Deal Profitability")
st.plotly_chart(px.scatter(
    profitability,
    x="deal_value",
    y="profit",
    size="cost_to_deliver",
    color="team",
    hover_name="deal_name",
), use_container_width=True)

st.subheader("Auto-generated Team Scorecard")
st.dataframe(scorecard, use_container_width=True)

if st.checkbox("Show raw data tables"):
    st.write("Deals", deals.head(100))
    st.write("Time Entries", time_entries.head(100))
    st.write("Invoices", invoices.head(100))
