from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class TeamTargets:
    revenue_target: float
    collection_target: float
    utilization_target_hours: float
    profitability_target_pct: float


def monthly_billing(invoices: pd.DataFrame) -> pd.DataFrame:
    df = invoices.copy()
    df["month"] = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").astype(str)
    return (
        df.groupby("month", as_index=False)
        .agg(total_billed=("total", "sum"), amount_collected=("amount_paid", "sum"), outstanding=("amount_due", "sum"))
        .sort_values("month")
    )


def yearly_billing(invoices: pd.DataFrame) -> pd.DataFrame:
    df = invoices.copy()
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    return (
        df.groupby("year", as_index=False)
        .agg(total_billed=("total", "sum"), amount_collected=("amount_paid", "sum"), outstanding=("amount_due", "sum"))
        .sort_values("year")
    )


def time_recorded_per_team(time_entries: pd.DataFrame) -> pd.DataFrame:
    return (
        time_entries.groupby("team", as_index=False)
        .agg(hours=("hours", "sum"), billable_amount=("billable_amount", "sum"))
        .sort_values("hours", ascending=False)
    )


def deal_profitability(deals: pd.DataFrame) -> pd.DataFrame:
    df = deals.copy()
    df["profit"] = df["deal_value"] - df["cost_to_deliver"]
    df["profit_margin_pct"] = (df["profit"] / df["deal_value"]).replace([pd.NA, pd.NaT], 0).fillna(0) * 100
    return df.sort_values("profit", ascending=False)


def team_scorecard(
    deals: pd.DataFrame,
    time_entries: pd.DataFrame,
    invoices: pd.DataFrame,
    targets: dict[str, TeamTargets],
) -> pd.DataFrame:
    profitability = deal_profitability(deals)
    by_team_profit = profitability.groupby("team", as_index=False).agg(
        revenue=("deal_value", "sum"),
        profit=("profit", "sum"),
    )
    by_team_profit["profitability_pct"] = (by_team_profit["profit"] / by_team_profit["revenue"]).fillna(0) * 100

    time_team = time_recorded_per_team(time_entries)

    merged = by_team_profit.merge(time_team, on="team", how="outer").fillna(0)
    total_collected = float(invoices["amount_paid"].sum())

    rows = []
    for _, row in merged.iterrows():
        team = row["team"]
        t = targets.get(
            team,
            TeamTargets(revenue_target=0, collection_target=0, utilization_target_hours=0, profitability_target_pct=0),
        )
        revenue = float(row["revenue"])
        profit = float(row["profit"])
        hours = float(row["hours"])
        profitability_pct = float(row["profitability_pct"])
        collection_share = 0 if merged["revenue"].sum() == 0 else revenue / merged["revenue"].sum()
        collected_team = total_collected * collection_share

        rows.append(
            {
                "team": team,
                "revenue": revenue,
                "profit": profit,
                "profitability_pct": profitability_pct,
                "hours": hours,
                "collected_estimate": collected_team,
                "revenue_vs_target_pct": 0 if t.revenue_target == 0 else revenue / t.revenue_target * 100,
                "collection_vs_target_pct": 0 if t.collection_target == 0 else collected_team / t.collection_target * 100,
                "utilization_vs_target_pct": 0 if t.utilization_target_hours == 0 else hours / t.utilization_target_hours * 100,
                "profitability_vs_target_pct": 0
                if t.profitability_target_pct == 0
                else profitability_pct / t.profitability_target_pct * 100,
            }
        )
    return pd.DataFrame(rows).sort_values("revenue", ascending=False)
