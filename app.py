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
    "Allocations are pro-rata by availability off each tranche size "
    "(Term Loan, Revolver, DDTL)."
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
        key="deals_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Deal": st.column_config.TextColumn("Deal"),
            "Est. Closing Date": st.column_config.TextColumn("Est. Closing Date"),
            "New Deal or Amendment": st.column_config.TextColumn("New Deal or Amendment"),
            "Transaction Type": st.column_config.TextColumn("Transaction Type"),
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
            "Covenant Lite": st.column_config.TextColumn("Covenant Lite"),
            "Internal Rating": st.column_config.TextColumn("Internal Rating"),
            "S&P Rating": st.column_config.TextColumn("S&P Rating"),
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
        key="vehicles_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        disabled=False,
        column_config={
            "Vehicle": st.column_config.TextColumn("Vehicle"),
            "Cash ($)": st.column_config.NumberColumn("Cash ($)", format="%.0f"),
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

    num_cols = [
        "Cash ($)",
        "Unfunded Commitments ($)",
        "Uncalled Capital ($)",
        "Target Hold ($)",
    ]
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

    vehicles = vdf["Vehicle"].tolist()

    # Vehicles with positive availability (for baseline checks)
    vdf_pos = vdf[vdf["Availability ($)"] > 0].copy()

    if vdf_pos.empty:
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

        for col in [
            "Cash ($)",
            "Unfunded Commitments ($)",
            "Uncalled Capital ($)",
            "Availability ($)",
            "Target Hold ($)",
        ]:
            avail_display[col] = avail_display[col].apply(fmt_dollars)

        st.dataframe(avail_display, use_container_width=True)

        vdf_idx = vdf.set_index("Vehicle")

        # -------- Loop through deals --------
        for idx, row in deals.iterrows():
            deal_name = row.get("Deal", f"Deal {idx+1}") or f"Deal {idx+1}"

            # Skip empty rows (no tranche sizes)
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
                        "IC Approved Hold ($)": fmt_dollars(
                            row.get("IC Approved Hold ($)", 0.0)
                        ),
                    }
                ]
            )

            st.markdown("**Deal Summary**")
            st.dataframe(summary, use_container_width=True)

            # -------- Tranche sizes (DEAL SIZE) --------
            tl_total = float(row.get("Term Loan ($)", 0.0))
            rev_total = float(row.get("Revolver ($)", 0.0))
            ddtl_total = float(row.get("DDTL ($)", 0.0))
            deal_total = tl_total + rev_total + ddtl_total

            # ===== Allocation vectors, indexed by vehicle name =====
            alloc_term = pd.Series(0.0, index=vehicles)
            alloc_rev = pd.Series(0.0, index=vehicles)
            alloc_ddtl = pd.Series(0.0, index=vehicles)

            # ---- Term Loan: all vehicles with Availability > 0 ----
            if tl_total > 0:
                tl_elig = vdf[vdf["Availability ($)"] > 0].copy()
                weights = tl_elig.set_index("Vehicle")["Availability ($)"]
                den = float(weights.sum())
                if den > 0:
                    shares = weights / den  # sum(shares) = 1
                    alloc_term = shares.reindex(vehicles).fillna(0.0) * tl_total

            # ---- Revolver: Availability > 0 AND Revolver On ----
            if rev_total > 0:
                rev_elig = vdf[
                    (vdf["Availability ($)"] > 0) & (vdf["Revolver On"])
                ].copy()
                weights = rev_elig.set_index("Vehicle")["Availability ($)"]
                den = float(weights.sum())
                if den > 0:
                    shares = weights / den
                    alloc_rev = shares.reindex(vehicles).fillna(0.0) * rev_total

            # ---- DDTL: Availability > 0 AND DDTL On ----
            if ddtl_total > 0:
                ddtl_elig = vdf[
                    (vdf["Availability ($)"] > 0) & (vdf["DDTL On"])
                ].copy()
                weights = ddtl_elig.set_index("Vehicle")["Availability ($)"]
                den = float(weights.sum())
                if den > 0:
                    shares = weights / den
                    alloc_ddtl = shares.reindex(vehicles).fillna(0.0) * ddtl_total

            # -------- Allocation table: facilities x vehicles + totals row --------
            alloc_numeric = pd.DataFrame(
                {"Facility": ["Term Loan", "Revolver", "DDTL"]}
            )
            for veh in vehicles:
                alloc_numeric[veh] = [
                    float(alloc_term.get(veh, 0.0) or 0.0),
                    float(alloc_rev.get(veh, 0.0) or 0.0),
                    float(alloc_ddtl.get(veh, 0.0) or 0.0),
                ]

            # Add totals row per vehicle (TL + REV + DDTL for this deal)
            totals_row = {"Facility": "Total"}
            for veh in vehicles:
                totals_row[veh] = (
                    float(alloc_term.get(veh, 0.0) or 0.0)
                    + float(alloc_rev.get(veh, 0.0) or 0.0)
                    + float(alloc_ddtl.get(veh, 0.0) or 0.0)
                )
            alloc_numeric = pd.concat(
                [alloc_numeric, pd.DataFrame([totals_row])],
                ignore_index=True,
            )

            alloc_fmt = alloc_numeric.copy()
            for veh in vehicles:
                alloc_fmt[veh] = alloc_fmt[veh].apply(fmt_dollars)

            st.markdown("**Facility Allocations (Vehicles Across Columns)**")
            st.dataframe(alloc_fmt.set_index("Facility"), use_container_width=True)

            # -------- Tranche consistency check --------
            tl_sum = float(alloc_term.sum())
            rev_sum = float(alloc_rev.sum())
            ddtl_sum = float(alloc_ddtl.sum())

            check_df = pd.DataFrame(
                [
                    {
                        "Tranche": "Term Loan",
                        "Tranche Size ($)": fmt_dollars(tl_total),
                        "Sum of Allocations ($)": fmt_dollars(tl_sum),
                        "Difference ($)": fmt_dollars(tl_sum - tl_total),
                    },
                    {
                        "Tranche": "Revolver",
                        "Tranche Size ($)": fmt_dollars(rev_total),
                        "Sum of Allocations ($)": fmt_dollars(rev_sum),
                        "Difference ($)": fmt_dollars(rev_sum - rev_total),
                    },
                    {
                        "Tranche": "DDTL",
                        "Tranche Size ($)": fmt_dollars(ddtl_total),
                        "Sum of Allocations ($)": fmt_dollars(ddtl_sum),
                        "Difference ($)": fmt_dollars(ddtl_sum - ddtl_total),
                    },
                    {
                        "Tranche": "TOTAL DEAL",
                        "Tranche Size ($)": fmt_dollars(deal_total),
                        "Sum of Allocations ($)": fmt_dollars(tl_sum + rev_sum + ddtl_sum),
                        "Difference ($)": fmt_dollars(
                            (tl_sum + rev_sum + ddtl_sum) - deal_total
                        ),
                    },
                ]
            )
            st.markdown("**Tranche Consistency Check (Should All Be $0 Difference)**")
            st.dataframe(check_df, use_container_width=True)

            # -------- Pro-rata share by vehicle (DEAL SIZE & Target Hold) --------
            st.markdown("**Pro-Rata Share of Deal by Vehicle (with Target Hold)**")

            vehicle_total_alloc = alloc_term + alloc_rev + alloc_ddtl

            pro_rata_numeric = pd.DataFrame(
                {
                    "Vehicle": vehicles,
                    "Allocated_numeric": [
                        float(vehicle_total_alloc.get(veh, 0.0) or 0.0)
                        for veh in vehicles
                    ],
                    "Target_numeric": [
                        float(vdf_idx.loc[veh, "Target Hold ($)"])
                        if veh in vdf_idx.index
                        else 0.0
                        for veh in vehicles
                    ],
                }
            )

            pro_rata_df = pd.DataFrame()
            pro_rata_df["Vehicle"] = pro_rata_numeric["Vehicle"]
            pro_rata_df["Allocated ($)"] = pro_rata_numeric["Allocated_numeric"].apply(
                fmt_dollars
            )
            pro_rata_df["Target Hold ($)"] = pro_rata_numeric["Target_numeric"].apply(
                fmt_dollars
            )

            if deal_total > 0:
                pro_rata_df["Pro-Rata Share of Deal (%)"] = [
                    fmt_percent(a / deal_total * 100.0)
                    for a in pro_rata_numeric["Allocated_numeric"]
                ]
            else:
                pro_rata_df["Pro-Rata Share of Deal (%)"] = ""

            pct_of_target = []
            for a, t in zip(
                pro_rata_numeric["Allocated_numeric"],
                pro_rata_numeric["Target_numeric"],
            ):
                t_val = float(t) if t is not None else 0.0
                if t_val > 0:
                    pct_of_target.append(fmt_percent(a / t_val * 100.0))
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

