from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import requests


@dataclass
class ConnectorConfig:
    monday_token: str | None = os.getenv("MONDAY_API_TOKEN")
    harvest_token: str | None = os.getenv("HARVEST_API_TOKEN")
    harvest_account_id: str | None = os.getenv("HARVEST_ACCOUNT_ID")
    xero_token: str | None = os.getenv("XERO_ACCESS_TOKEN")
    xero_tenant_id: str | None = os.getenv("XERO_TENANT_ID")


class DataConnector:
    def __init__(self, config: ConnectorConfig | None = None) -> None:
        self.config = config or ConnectorConfig()

    def load_data(self) -> dict[str, pd.DataFrame]:
        """Load data from configured sources. Falls back to generated demo data."""
        if not all([self.config.monday_token, self.config.harvest_token, self.config.xero_token]):
            return self._demo_data()

        try:
            return {
                "deals": self._load_monday_deals(),
                "time_entries": self._load_harvest_time(),
                "invoices": self._load_xero_invoices(),
            }
        except Exception:
            return self._demo_data()

    def _load_monday_deals(self) -> pd.DataFrame:
        query = """
        {
          boards (ids: 1234567890) {
            items_page(limit: 100) {
              items {
                name
                column_values {
                  id
                  text
                }
              }
            }
          }
        }
        """
        resp = requests.post(
            "https://api.monday.com/v2",
            json={"query": query},
            headers={"Authorization": self.config.monday_token or ""},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data["data"]["boards"][0]["items_page"]["items"]
        rows: list[dict[str, Any]] = []
        for it in items:
            mapped = {"deal_name": it["name"]}
            for col in it["column_values"]:
                mapped[col["id"]] = col.get("text")
            rows.append(mapped)
        df = pd.DataFrame(rows)
        if "deal_value" in df.columns:
            df["deal_value"] = pd.to_numeric(df["deal_value"], errors="coerce").fillna(0)
        if "cost_to_deliver" in df.columns:
            df["cost_to_deliver"] = pd.to_numeric(df["cost_to_deliver"], errors="coerce").fillna(0)
        if "close_date" in df.columns:
            df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
        if "team" not in df.columns:
            df["team"] = "Unknown"
        return df

    def _load_harvest_time(self) -> pd.DataFrame:
        headers = {
            "Authorization": f"Bearer {self.config.harvest_token}",
            "Harvest-Account-ID": self.config.harvest_account_id or "",
            "User-Agent": "analytics-dashboard-tool",
        }
        start = (datetime.utcnow() - timedelta(days=365)).date().isoformat()
        end = datetime.utcnow().date().isoformat()
        resp = requests.get(
            "https://api.harvestapp.com/v2/time_entries",
            params={"from": start, "to": end, "per_page": 200},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        entries = resp.json().get("time_entries", [])
        rows = []
        for e in entries:
            rows.append(
                {
                    "date": e.get("spent_date"),
                    "team": (e.get("user") or {}).get("name", "Unknown"),
                    "project": (e.get("project") or {}).get("name", "Unknown"),
                    "client": (e.get("client") or {}).get("name", "Unknown"),
                    "hours": e.get("hours", 0),
                    "billable": e.get("billable", False),
                    "billable_amount": e.get("billable_rate", 0) * e.get("hours", 0),
                }
            )
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df

    def _load_xero_invoices(self) -> pd.DataFrame:
        headers = {
            "Authorization": f"Bearer {self.config.xero_token}",
            "Xero-tenant-id": self.config.xero_tenant_id or "",
            "Accept": "application/json",
        }
        resp = requests.get(
            "https://api.xero.com/api.xro/2.0/Invoices",
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        invoices = resp.json().get("Invoices", [])
        rows = []
        for inv in invoices:
            rows.append(
                {
                    "invoice_number": inv.get("InvoiceNumber"),
                    "contact": (inv.get("Contact") or {}).get("Name", "Unknown"),
                    "status": inv.get("Status", "Unknown"),
                    "date": inv.get("DateString"),
                    "due_date": inv.get("DueDateString"),
                    "amount_due": inv.get("AmountDue", 0),
                    "amount_paid": inv.get("AmountPaid", 0),
                    "total": inv.get("Total", 0),
                }
            )
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df

    def _demo_data(self) -> dict[str, pd.DataFrame]:
        rng = np.random.default_rng(7)
        dates = pd.date_range(end=datetime.utcnow().date(), periods=365, freq="D")
        teams = ["Growth", "Delivery", "Operations", "Customer Success"]
        clients = ["Acme", "Globex", "Initech", "Umbrella", "Stark"]

        deals = pd.DataFrame(
            {
                "deal_name": [f"Deal-{i}" for i in range(1, 101)],
                "team": rng.choice(teams, 100),
                "close_date": rng.choice(dates, 100),
                "deal_value": rng.integers(8000, 120000, 100),
                "cost_to_deliver": rng.integers(3000, 70000, 100),
            }
        )

        time_entries = pd.DataFrame(
            {
                "date": rng.choice(dates, 2000),
                "team": rng.choice(teams, 2000),
                "project": [f"Project-{i%40}" for i in range(2000)],
                "client": rng.choice(clients, 2000),
                "hours": rng.uniform(0.5, 8.0, 2000).round(2),
                "billable": rng.choice([True, False], 2000, p=[0.8, 0.2]),
            }
        )
        time_entries["billable_amount"] = (time_entries["hours"] * rng.uniform(80, 220, 2000)).round(2)

        invoice_dates = pd.DataFrame({"date": rng.choice(dates, 300)})
        invoices = pd.DataFrame(
            {
                "invoice_number": [f"INV-{1000+i}" for i in range(300)],
                "contact": rng.choice(clients, 300),
                "status": rng.choice(["PAID", "AUTHORISED", "SUBMITTED"], 300, p=[0.7, 0.2, 0.1]),
                "date": invoice_dates["date"],
                "due_date": invoice_dates["date"] + pd.to_timedelta(30, unit="D"),
                "total": rng.integers(2000, 65000, 300),
            }
        )
        paid_ratio = rng.uniform(0.65, 1.0, 300)
        invoices["amount_paid"] = (invoices["total"] * paid_ratio).round(2)
        invoices["amount_due"] = (invoices["total"] - invoices["amount_paid"]).round(2)
        return {"deals": deals, "time_entries": time_entries, "invoices": invoices}
