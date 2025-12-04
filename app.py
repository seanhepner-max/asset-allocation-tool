import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


# =========================
#   DATA MODELS & ENGINE
# =========================

@dataclass
class AssetClass:
    """Represents an asset class."""
    name: str
    enabled: bool = True   # global on/off toggle


@dataclass
class Vehicle:
    """Represents an investment vehicle (account, fund, etc.)."""
    name: str
    capacity: float              # total dollars allocated to this vehicle
    enabled: bool = True         # vehicle-level on/off
    allowed_assets: Dict[str, bool] = field(default_factory=dict)

    def is_asset_allowed(self, asset_name: str) -> bool:
        # If not specified, assume allowed.
        return self.allowed_assets.get(asset_name, True)


@dataclass
class AllocationResult:
    """Final allocation result."""
    # nested dict: vehicle -> asset -> amount
    amounts: Dict[str, Dict[str, float]]


# ---------- Rule System ----------

class RuleContext:
    """
    Context passed to rules, containing all the inputs.
    You can add more attributes as you need.
    """
    def __init__(
        self,
        total_portfolio_value: float,
        asset_classes: Dict[str, AssetClass],
        vehicles: Dict[str, Vehicle],
        initial_targets: Dict[str, float],
    ):
        self.total_portfolio_value = total_portfolio_value
        self.asset_classes = asset_classes
        self.vehicles = vehicles
        self.initial_targets = initial_targets


class AllocationRule:
    """
    Base class for all rules.
    Each rule takes a proposed allocation (vehicle -> asset -> amount)
    and returns a possibly modified allocation.
    """
    def apply(
        self,
        ctx: RuleContext,
        proposed: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        raise NotImplementedError


class MaxAssetInVehicleRule(AllocationRule):
    """
    Enforce a maximum % of a vehicle's capacity that can go into a given asset.
    Example: High Yield <= 20% of IRA.
    """
    def __init__(self, vehicle_name: str, asset_name: str, max_pct_of_vehicle: float):
        self.vehicle_name = vehicle_name
        self.asset_name = asset_name
        self.max_pct_of_vehicle = max_pct_of_vehicle

    def apply(
        self,
        ctx: RuleContext,
        proposed: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        vname = self.vehicle_name
        aname = self.asset_name

        if vname not in proposed or aname not in proposed[vname]:
            return proposed

        max_amount = ctx.vehicles[vname].capacity * self.max_pct_of_vehicle
        current = proposed[vname][aname]

        if current > max_amount:
            # Reduce to max and spread excess across other assets
            excess = current - max_amount
            proposed[vname][aname] = max_amount

            other_assets = {
                k: v for k, v in proposed[vname].items()
                if k != aname and v > 0
            }
            total_other = sum(other_assets.values())

            if total_other > 0:
                for asset, amt in other_assets.items():
                    share = amt / total_other
                    proposed[vname][asset] += excess * share

        return proposed


class MinAssetInPortfolioRule(AllocationRule):
    """
    Enforce a minimum % of the *total portfolio* in a given asset.
    """
    def __init__(self, asset_name: str, min_pct_of_portfolio: float):
        self.asset_name = asset_name
        self.min_pct_of_portfolio = min_pct_of_portfolio

    def apply(
        self,
        ctx: RuleContext,
        proposed: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        aname = self.asset_name

        current_total = sum(
            proposed[v].get(aname, 0.0) for v in proposed
        )
        min_required = ctx.total_portfolio_value * self.min_pct_of_portfolio

        if current_total >= min_required or current_total == 0:
            return proposed

        shortfall = min_required - current_total

        # Increase proportionally across vehicles holding the asset
        contributing = {
            v: proposed[v].get(aname, 0.0)
            for v in proposed if proposed[v].get(aname, 0.0) > 0
        }
        total_contrib = sum(contributing.values())

        if total_contrib == 0:
            return proposed  # Cannot apply rule; asset not allocated anywhere

        for vname, amt in contributing.items():
            share = amt / total_contrib
            proposed[vname][aname] += shortfall * share

        return proposed


# ---------- Allocator Core ----------

class Allocator:
    def __init__(
        self,
        asset_classes: List[AssetClass],
        vehicles: List[Vehicle],
        rules: Optional[List[AllocationRule]] = None,
    ):
        self.asset_classes = {a.name: a for a in asset_classes}
        self.vehicles = {v.name: v for v in vehicles}
        self.rules = rules or []

    def allocate(
        self,
        total_portfolio_value: float,
        target_allocation: Dict[str, float],
    ) -> AllocationResult:

        # 1. Normalize target weights after removing disabled assets
        filtered_targets = {
            a: w for a, w in target_allocation.items()
            if self.asset_classes[a].enabled and w > 0
        }
        total_weight = sum(filtered_targets.values())
        normalized_targets = {a: w / total_weight for a, w in filtered_targets.items()}

        # 2. Enabled vehicles only
        enabled_vehicles = {n: v for n, v in self.vehicles.items() if v.enabled}

        # Rescale vehicles to match total portfolio value
        total_capacity = sum(v.capacity for v in enabled_vehicles.values())
        scaling = total_portfolio_value / total_capacity
        for v in enabled_vehicles.values():
            v.capacity *= scaling

        # 3. Initial allocation
        proposed = {}
        for vname, vehicle in enabled_vehicles.items():
            proposed[vname] = {}

            allowed_weight_sum = sum(
                w for a, w in normalized_targets.items()
                if vehicle.is_asset_allowed(a)
            )

            for asset, w in normalized_targets.items():
                if not vehicle.is_asset_allowed(asset):
                    continue

                adj_w = w / allowed_weight_sum
                proposed[vname][asset] = adj_w * vehicle.capacity

        # 4. Apply rules
        ctx = RuleContext(
            total_portfolio_value,
            self.asset_classes,
            enabled_vehicles,
            normalized_targets,
        )

        for rule in self.rules:
            proposed = rule.apply(ctx, proposed)

        # 5. Normalize again per vehicle
        for vname, vehicle in enabled_vehicles.items():
            total_alloc = sum(proposed[vname].values())
            factor = vehicle.capacity / total_alloc
            for asset in proposed[vname]:
                proposed[vname][asset] *= factor

        return AllocationResult(proposed)


# =========================
#       STREAMLIT UI
# =========================

st.set_page_config(page_title="Asset Allocation Tool", layout="wide")

st.title("Asset Allocation Tool")
st.caption("Toggle assets, set targets, apply rules, and generate a visual allocation.")



# ---------- SIDEBAR INPUTS ----------

st.sidebar.header("Portfolio Settings")
total_value = st.sidebar.number_input(
    "Total Portfolio Value",
    min_value=0.0,
    value=1_000_000.0,
    step=50_000.0
)

st.sidebar.header("Vehicle Capacities")
taxable_cap = st.sidebar.number_input(
    "Taxable Capacity", value=600_000.0, step=50_000.0
)
ira_cap = st.sidebar.number_input(
    "IRA Capacity", value=400_000.0, step=50_000.0
)

st.sidebar.header("Rules")
max_hy_ira = st.sidebar.slider(
    "Max High Yield in IRA (%)", 0, 100, 20
)
min_cash_pct = st.sidebar.slider(
    "Min Cash in Portfolio (%)", 0, 20, 5
)



# ---------- MAIN TARGET WEIGHTS + TOGGLES ----------

st.subheader("Target Asset Allocation")

cols = st.columns(5)

with cols[0]:
    us_enabled = st.checkbox("US Equity Enabled", True)
    us_w = st.slider("US Equity %", 0.0, 1.0, 0.40)

with cols[1]:
    intl_enabled = st.checkbox("Intl Equity Enabled", True)
    intl_w = st.slider("Intl Equity %", 0.0, 1.0, 0.20)

with cols[2]:
    pc_enabled = st.checkbox("Private Credit Enabled", True)
    pc_w = st.slider("Private Credit %", 0.0, 1.0, 0.25)

with cols[3]:
    hy_enabled = st.checkbox("High Yield Enabled", True)
    hy_w = st.slider("High Yield %", 0.0, 1.0, 0.10)

with cols[4]:
    cash_enabled = st.checkbox("Cash Enabled", True)
    cash_w = st.slider("Cash %", 0.0, 1.0, 0.05)


raw_targets = {
    "US Equity": us_w,
    "Intl Equity": intl_w,
    "Private Credit": pc_w,
    "High Yield": hy_w,
    "Cash": cash_w,
}

assets = [
    AssetClass("US Equity", us_enabled),
    AssetClass("Intl Equity", intl_enabled),
    AssetClass("Private Credit", pc_enabled),
    AssetClass("High Yield", hy_enabled),
    AssetClass("Cash", cash_enabled),
]

vehicles = [
    Vehicle(
        "Taxable",
        taxable_cap,
        allowed_assets={
            "US Equity": True,
            "Intl Equity": True,
            "Private Credit": False,
            "High Yield": True,
            "Cash": True,
        },
    ),
    Vehicle(
        "IRA",
        ira_cap,
        allowed_assets={
            "US Equity": True,
            "Intl Equity": True,
            "Private Credit": True,
            "High Yield": True,
            "Cash": True,
        },
    ),
]

rules = [
    MaxAssetInVehicleRule("IRA", "High Yield", max_hy_ira / 100),
    MinAssetInPortfolioRule("Cash", min_cash_pct / 100),
]

allocator = Allocator(assets, vehicles, rules)



# ---------- RUN ALLOCATION ----------

if st.button("Run Allocation"):
    try:
        result = allocator.allocate(total_value, raw_targets)

        # Convert nested dict to DataFrame
        rows = []
        for vehicle, asset_dict in result.amounts.items():
            for asset, amt in asset_dict.items():
                rows.append({"Vehicle": vehicle, "Asset Class": asset, "Amount": amt})

        df = pd.DataFrame(rows)

        st.subheader("Allocation by Vehicle and Asset")
        table = df.pivot_table(index="Vehicle", columns="Asset Class", values="Amount")
        st.dataframe(table.fillna(0.0))

        st.subheader("Portfolio Totals by Asset Class")
        totals = df.groupby("Asset Class")["Amount"].sum().reset_index()
        totals["Weight %"] = totals["Amount"] / total_value * 100
        st.dataframe(totals)

        st.bar_chart(totals.set_index("Asset Class")["Amount"])

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Adjust settings, then click **Run Allocation**.")
