import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Multi-Deal Availability Allocation Tool",
    layout="wide",
)

st.title("Multi-Deal Availability-Based Allocation Tool")

st.caption(
    "Edit deals and vehicle availability in the tables below. "
    "Availability = Cash + Unfunded Commitments + Uncalled Capital. "
    "Only vehicles with positive availability receive allocations. "
    "Revolver and DDTL participation is controlled per vehicle. "
    "Target Hold is defined by fund and used to show % of target used per deal. "
    "Allocations are pro-rata by availability off deal size (Term Loan + Revolver + DDTL)."
)

# =======================================
# DEFAULT DATA
# =======================================

default_deals = pd.DataFrame(
    [
        {
            "Deal": "ABC Deal",
            "Est. Closing Date": "2025-12-05",
            "New Deal or Amendment": "New Deal",
            "Transaction Type": "Div Recap",
            "EBITDA ($mm)": 50.0,
            "Senior Net Leverage (x)": 3.0,
            "Total Leverage (x)": 4.0,
            "Opening Spread (bps)": 400,
            "Covenant Lite": "Yes",
            "Internal Rating": "3 (Mid Risk)",
            "S&P Rating": "B+",
            "IC Approved Hold ($)": 50_000_000,
            "Term Loan ($)": 150_000_000,
            "Revolver ($)": 25_000_000,
            "DDTL ($)": 5_000_000,
        },
        {
            "Deal": "XXZ Deal",
            "Est. Closing Date": "2025-12-10",
            "New Deal or Amendment": "Amendment",
            "Transaction Type": "LBO",
            "EBITDA ($mm)": 70.0,
            "Senior Net Leverage (x)": 3.5,
            "Total Leverage (x)": 5.0,
            "Opening Spread (bps)": 425,
            "Covenant Lite": "No",
            "Internal Rating": "4 (Higher Risk)",
            "S&P Rating": "B",
            "IC Approved Hold ($)": 75_000_000,
            "Term Loan ($)": 250_000_000,
            "Revolver ($)": 50_000_000,
            "DDTL ($)": 15_000_000,
        },
    ]
)

default_vehicles = pd.DataFrame(
    [
        {
            "Vehicle": "Fund 1",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Target Hold ($)": 40_000_000,
            "Revolver On": True,
            "DDTL On": True,
        },
        {
            "Vehicle": "Fund 2",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Target Hold ($)": 30_000_000,
            "Revolver On": True,
            "DDTL On": False,
        },
        {
            "Vehicle": "Fund 3",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Target Hold ($)": 20_000_000,
            "Revolver On": False,
            "DDTL On": True,
        },
    ]
)

# =======================================
# LAYOUT: Deals (left) + Vehicles (right)
# =======================================

left_col, right_col = st.columns([2.5, 1.5])

with left_col:
    st.subheader("Deals")

    deals_df = st.data_editor(
        default_deals,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "EBITDA ($mm)": st.column_config.NumberColumn(
                "EBITDA ($mm)", format="%.2f"
            ),
            "Senior Net Leverage (x)": st.column_config.NumberColumn(
                "Senior Net Leverage (x)", format="%.2f"
            ),
            "Total Leverage (x)": st.column_config.NumberColumn(
                "Total Leverage (x)", format="%.2f"
            ),
            "Opening Spread (bps)": st.column_config.NumberColumn(
                "Opening Spread (bps)", format="%d"
            ),
            "IC Approved Hold ($)": st.column_config.NumberColumn(
                "IC Approved Hold ($)", format="%.0f"
            ),
            "Term Loan ($)": st.column_config.NumberColumn(
                "Term Loan ($)", format="%.0f"
            ),
            "Revolver ($)": st.column_config.NumberColumn(
                "Revolver ($)", format="%.0f"
            ),
            "DDTL ($)": st.column_config.NumberColumn(
                "DDTL ($)", format="%.0f"
            ),
        },
    )

with right_col:
    st.subheader("Vehicles / Funds")

    vehicles_df = st.data_editor(
        default_vehicles,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Cash ($)": st.column_config.NumberColumn(
                "Cash ($)", format="%.0f"
            ),
            "Unfunded Commitments ($)": st.column_config.NumberColumn(
                "Unfunded Commitments ($)", format="%.0f"
            ),
            "Uncalled Capital ($)": st.column_config.NumberColumn(
                "Uncalled Capital ($)", format="%.0f"
            ),
            "Target Hold ($)": st.column_config.NumberColumn(
                "Target Hold ($)", format="%.0f"
            ),
            "Revolver On": st.column_config.CheckboxColumn("Revolver On"),
            "DDTL On": st.column_config.CheckboxColumn("DDTL On"),
        },
    )

st.markdown("---")

# =======================================
# Cleaning / helpers
# =======================================

def clean_deals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    num_cols = [
        "EBITDA ($mm)",
        "Senior Net Leverage (x)",
        "Total Leverage (x)",
        "Opening Spread (bps)",
        "IC Approved Hold ($)",
        "Term Loan ($)",
        "Revolver ($)",
        "DDTL ($)",
    ]
    for col in num_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    text_cols = [
        "Deal",
        "Est. Closing Date",
        "New Deal or Amendment",
        "Transaction Type",
        "Covenant Lite",
        "Internal Rating",
        "S&P Rating",
    ]
    for col in text_cols:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()

    return out


def clean_vehicles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    num_cols = ["Cash ($)", "Unfunded Commitments ($)", "Uncalled Capital ($)", "Target Hold ($)"]
    for col in num_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    for col in ["Revolver On", "DDTL On"]:
        if col in out.columns:
            out[col] = out[col].fillna(False).astype(bool)

    if "Vehicle" in out.columns:
        out["Vehicle"] = out["Vehicle"].astype(str).str.strip()

    return out


def compute_availability(vdf: pd.DataFrame) -> pd.DataFrame:
    df = vdf.copy()
    df["Availability ($)"] = (
        df["Cash ($)"] + df["Unfunded Commitments ($)"] + df["Uncalled Capital ($)"]
    )
    return df


def fmt_dollars(x) -> str:
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            x = 0.0
        return f"${float(x):,.0f}"
    except Exception:
        return "$0"


def fmt_percent(x) -> str:
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            x = 0.0
        return f"{float(x):,.2f}%"
    except Exception:
        return "0.00%"


# =======================================
# Allocation logic
# =======================================

if st.button("Calculate Allocations"):
    deals = clean_deals(deals_df)
    vdf = clean_vehicles(vehicles_df)
    vdf = compute_availability(vdf)

    positive_mask = vdf["Availability ($)"] > 0
    vdf_pos = vdf[positive_mask].copy()
    total_avail = vdf_pos["Availability ($)"].sum()

    if total_avail <= 0:
        st.error(
            "Total availability across all vehicles is zero or invalid. "
            "Please enter positive values for Cash, Unfunded, or Uncalled Capital."
        )
    else:
        # -------- Vehicle availability summary --------
        st.subheader("Vehicle Availability Summary")

        avail_display = vdf[
            [
                "Vehicle",
                "Cash ($)",
                "Unfunded Commitments ($)",
                "Uncalled Capital ($)",
                "Availability ($)",
                "Target Hold ($)",
                "Revolver On",
                "DDTL On",
            ]
        ].copy()

        for col in ["Cash ($)", "Unfunded Commitments ($)", "Uncalled Capital ($)", "Availability ($)", "Target Hold ($)"]:
            avail_display[col] = avail_display[col].apply(fmt_dollars)

        st.dataframe(avail_display, use_container_width=True)

        # -------- Loop through deals --------
        for idx, row in deals.iterrows():
            deal_name = row.get("Deal", f"Deal {idx+1}") or f"Deal {idx+1}"

            # Skip completely empty rows
            if (
                (str(deal_name).strip() == "")
                and row.get("Term Loan ($)", 0) == 0
                and row.get("Revolver ($)", 0) == 0
                and row.get("DDTL ($)", 0) == 0
            ):
                continue

            st.markdown("---")
            st.subheader(f"Deal {idx+1}: {deal_name}")

            # -------- Deal summary --------
            summary = pd.DataFrame(
                [
                    {
                        "Deal": deal_name,
                        "Est. Closing Date": row.get("Est. Closing Date", ""),
                        "New Deal or Amendment": row.get("New Deal or Amendment", ""),
                        "Transaction Type": row.get("Transaction Type", ""),
                        "EBITDA ($mm)": f"{row.get('EBITDA ($mm)', 0.0):,.2f}",
                        "Senior Net Leverage (x)": f"{row.get('Senior Net Leverage (x)', 0.0):,.2f}",
                        "Total Leverage (x)": f"{row.get('Total Leverage (x)', 0.0):,.2f}",
                        "Opening Spread (bps)": f"{row.get('Opening Spread (bps)', 0.0):,.0f}",
                        "Covenant Lite": row.get("Covenant Lite", ""),
                        "Internal Rating": row.get("Internal Rating", ""),
                        "S&P Rating": row.get("S&P Rating", ""),
                        "IC Approved Hold ($)": fmt_dollars(row.get("IC Approved Hold ($)", 0.0)),
                    }
                ]
            )

            st.markdown("**Deal Summary**")
            st.dataframe(summary, use_container_width=True)

            # -------- Facility sizes (DEAL SIZE) --------
            tl_total = row.get("Term Loan ($)", 0.0)
            rev_total = row.get("Revolver ($)", 0.0)
            ddtl_total = row.get("DDTL ($)", 0.0)
            deal_total = float(tl_total + rev_total + ddtl_total)

            # Init allocation vectors (numeric)
            alloc_term = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_rev = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_ddtl = pd.Series(0.0, index=vdf["Vehicle"])

            # Term Loan: all positive-availability vehicles
            if tl_total > 0 and total_avail > 0:
                base_shares = vdf_pos["Availability ($)"] / total_avail
                for veh, share in base_shares.items():
                    alloc_term.loc[veh] = share * tl_total

            # Revolver: positive availability + Revolver On
            if rev_total > 0:
                rev_mask = (vdf["Availability ($)"] > 0) & (vdf["Revolver On"])
                rev_den = vdf.loc[rev_mask, "Availability ($)"].sum()
                if rev_den > 0:
                    rev_shares = vdf.loc[rev_mask, "Availability ($)"] / rev_den
                    for veh, share in rev_shares.items():
                        alloc_rev.loc[veh] = share * rev_total

            # DDTL: positive availability + DDTL On
            if ddtl_total > 0:
                ddtl_mask = (vdf["Availability ($)"] > 0) & (vdf["DDTL On"])
                ddtl_den = vdf.loc[ddtl_mask, "Availability ($)"].sum()
                if ddtl_den > 0:
                    ddtl_shares = vdf.loc[ddtl_mask, "Availability ($)"] / ddtl_den
                    for veh, share in ddtl_shares.items():
                        alloc_ddtl.loc[veh] = share * ddtl_total

            # -------- Allocation table: facilities x vehicles --------
            alloc_numeric = pd.DataFrame({"Facility": ["Term Loan", "Revolver", "DDTL"]})
            for veh in vdf["Vehicle"]:
                tl_val = alloc_term.get(veh, 0.0)
                rev_val = alloc_rev.get(veh, 0.0)
                ddtl_val = alloc_ddtl.get(veh, 0.0)
                alloc_numeric[veh] = [tl_val, rev_val, ddtl_val]

            # Format to $ strings for display
            alloc_fmt = alloc_numeric.copy()
            for veh in vdf["Vehicle"]:
                alloc_fmt[veh] = alloc_fmt[veh].apply(fmt_dollars)

            st.markdown("**Facility Allocations (Vehicles Across Columns)**")
            st.dataframe(alloc_fmt.set_index("Facility"), use_container_width=True)

            # -------- Pro-rata share by vehicle (based on DEAL SIZE & Target Hold) --------
            st.markdown("**Pro-Rata Share of Deal by Vehicle (with Target Hold)**")

            vehicle_total_alloc = alloc_term + alloc_rev + alloc_ddtl
            pro_rata_numeric = pd.DataFrame(
                {
                    "Vehicle": vdf["Vehicle"],
                    "Allocated_numeric": [
                        vehicle_total_alloc.get(veh, 0.0) for veh in vdf["Vehicle"]
                    ],
                    "Target_numeric": [
                        vdf.set_index("Vehicle").loc[veh, "Target Hold ($)"]
                        if veh in vdf["Vehicle"].values
                        else 0.0
                        for veh in vdf["Vehicle"]
                    ],
                }
            )

            # Build display table
            pro_rata_df = pd.DataFrame()
            pro_rata_df["Vehicle"] = pro_rata_numeric["Vehicle"]
            pro_rata_df["Allocated ($)"] = pro_rata_numeric["Allocated_numeric"].apply(
                fmt_dollars
            )
            pro_rata_df["Target Hold ($)"] = pro_rata_numeric["Target_numeric"].apply(
                fmt_dollars
            )

            # % of Deal
            if deal_total > 0:
                pro_rata_df["Pro-Rata Share of Deal (%)"] = [
                    fmt_percent(a / deal_total * 100.0)
                    for a in pro_rata_numeric["Allocated_numeric"]
                ]
            else:
                pro_rata_df["Pro-Rata Share of Deal (%)"] = ""

            # % of Target Hold used (for this deal only)
            pct_of_target = []
            for a, t in zip(
                pro_rata_numeric["Allocated_numeric"],
                pro_rata_numeric["Target_numeric"],
            ):
                if t > 0:
                    pct_of_target.append(fmt_percent(a / t * 100.0))
                else:
                    pct_of_target.append("")
            pro_rata_df["% of Target Hold (This Deal)"] = pct_of_target

            st.dataframe(pro_rata_df, use_container_width=True)

else:
    st.info(
        "Edit the Deals and Vehicles tables above, then click **Calculate Allocations** "
        "to compute pro-rata allocations by facility and vehicle, plus each vehicle's "
        "pro-rata and % of its Target Hold used for each deal."
    )
