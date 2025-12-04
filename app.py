import streamlit as st
import pandas as pd

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(
    page_title="Multi-Deal Availability Allocation Tool (Grid)",
    layout="wide",
)

st.title("Multi-Deal Availability-Based Allocation Tool (Grid Version)")

st.caption(
    "Edit deals and vehicle availability directly in the tables. "
    "Availability = Cash + Unfunded Commitments + Uncalled Capital. "
    "Only vehicles with positive availability receive allocations. "
    "Revolver and DDTL participation is controlled per vehicle."
)

# =======================================
# Helper: build editable AgGrid
# =======================================

def editable_grid(df: pd.DataFrame, key: str, fit_columns: bool = True):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True)

    if fit_columns:
        gb.configure_grid_options(domLayout="normal")

    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode="AS_INPUT",
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        key=key,
    )

    return pd.DataFrame(grid_response["data"])


# =======================================
# DEFAULT DATA (you can tweak these)
# =======================================

# Default deals grid: columns in the order of your template
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

# Default vehicles grid: one row per vehicle/fund
default_vehicles = pd.DataFrame(
    [
        {
            "Vehicle": "Fund 1",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Revolver On": True,
            "DDTL On": True,
        },
        {
            "Vehicle": "Fund 2",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Revolver On": True,
            "DDTL On": False,
        },
        {
            "Vehicle": "Fund 3",
            "Cash ($)": 5_000_000,
            "Unfunded Commitments ($)": 5_000_000,
            "Uncalled Capital ($)": 10_000_000,
            "Revolver On": False,
            "DDTL On": True,
        },
    ]
)

# =======================================
# LAYOUT: Deals grid (left) + Vehicles (right)
# =======================================

left_col, right_col = st.columns([2.5, 1.5])

with left_col:
    st.subheader("Deals (edit directly in grid)")
    st.markdown(
        "First column is **Deals**, followed by all metrics and facility sizes "
        "(Term Loan / Revolver / DDTL)."
    )

    num_rows = st.number_input(
        "Number of deal rows",
        min_value=1,
        max_value=50,
        value=default_deals.shape[0],
        step=1,
    )

    # Adjust default_deals rows if the user changes num_rows
    if num_rows > default_deals.shape[0]:
        # add blank rows
        for _ in range(num_rows - default_deals.shape[0]):
            default_deals = pd.concat(
                [
                    default_deals,
                    pd.DataFrame(
                        [
                            {
                                col: ""
                                if default_deals[col].dtype == "O"
                                else 0
                                for col in default_deals.columns
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
    elif num_rows < default_deals.shape[0]:
        default_deals = default_deals.head(num_rows).copy()

    deals_df = editable_grid(default_deals, key="deals_grid")

with right_col:
    st.subheader("Vehicles / Funds (Availability & Toggles)")
    st.markdown(
        "Enter **Cash, Unfunded Commitments, Uncalled Capital** and whether "
        "each vehicle participates in **Revolver** and **DDTL**. "
        "Availability is computed automatically in the allocation step."
    )

    vehicles_df = editable_grid(default_vehicles, key="vehicles_grid")

st.markdown("---")

# =======================================
# Allocation logic
# =======================================

def compute_availability(vdf: pd.DataFrame) -> pd.DataFrame:
    df = vdf.copy()
    # Coerce numeric columns
    for col in ["Cash ($)", "Unfunded Commitments ($)", "Uncalled Capital ($)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["Availability ($)"] = (
        df["Cash ($)"] + df["Unfunded Commitments ($)"] + df["Uncalled Capital ($)"]
    )
    return df


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


if st.button("Calculate Allocations"):
    # --- Clean vehicles & availability ---
    vdf = compute_availability(vehicles_df)
    positive_mask = vdf["Availability ($)"] > 0
    vdf_pos = vdf[positive_mask].copy()
    total_avail = vdf_pos["Availability ($)"].sum()

    if total_avail <= 0:
        st.error(
            "Total availability across all vehicles is zero or invalid. "
            "Please enter positive values for Cash, Unfunded, or Uncalled Capital."
        )
    else:
        # Show availability summary
        st.subheader("Vehicle Availability Summary")
        st.dataframe(
            vdf[
                [
                    "Vehicle",
                    "Cash ($)",
                    "Unfunded Commitments ($)",
                    "Uncalled Capital ($)",
                    "Availability ($)",
                    "Revolver On",
                    "DDTL On",
                ]
            ],
            use_container_width=True,
        )

        # --- Loop through deals and allocate per deal ---
        for idx, row in deals_df.iterrows():
            deal_name = str(row.get("Deal", f"Deal {idx+1}")).strip()
            if not deal_name:
                deal_name = f"Deal {idx+1}"

            st.markdown("---")
            st.subheader(f"Deal {idx+1}: {deal_name}")

            # Build a one-row summary like your template (Deals first column)
            summary = pd.DataFrame(
                [
                    {
                        "Deals": deal_name,
                        "Est. Closing Date": row.get("Est. Closing Date", ""),
                        "New Deal or Amendment": row.get("New Deal or Amendment", ""),
                        "Transaction Type": row.get("Transaction Type", ""),
                        "EBITDA ($mm)": safe_float(row.get("EBITDA ($mm)", 0)),
                        "Senior Net Leverage (x)": safe_float(
                            row.get("Senior Net Leverage (x)", 0)
                        ),
                        "Total Leverage (x)": safe_float(
                            row.get("Total Leverage (x)", 0)
                        ),
                        "Opening Spread (bps)": safe_float(
                            row.get("Opening Spread (bps)", 0)
                        ),
                        "Covenant Lite": row.get("Covenant Lite", ""),
                        "Internal Rating": row.get("Internal Rating", ""),
                        "S&P Rating": row.get("S&P Rating", ""),
                        "IC Approved Hold ($)": safe_float(
                            row.get("IC Approved Hold ($)", 0)
                        ),
                    }
                ]
            )

            st.markdown("**Deal Summary (row-style, matching template order)**")
            st.dataframe(summary, use_container_width=True)

            # --- Get facility sizes for this deal ---
            tl_total = safe_float(row.get("Term Loan ($)", 0))
            rev_total = safe_float(row.get("Revolver ($)", 0))
            ddtl_total = safe_float(row.get("DDTL ($)", 0))

            # Initialize allocation vectors
            alloc_term = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_rev = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_ddtl = pd.Series(0.0, index=vdf["Vehicle"])

            # ---- Term Loan: all vehicles with Availability > 0 (no toggles) ----
            if tl_total > 0 and total_avail > 0:
                base_shares = vdf_pos["Availability ($)"] / total_avail
                alloc_term.loc[vdf_pos["Vehicle"]] = base_shares * tl_total

            # ---- Revolver: Availability > 0 and Revolver On == True ----
            if rev_total > 0:
                rev_mask = (vdf["Availability ($)"] > 0) & (vdf["Revolver On"] == True)
                rev_den = vdf.loc[rev_mask, "Availability ($)"].sum()
                if rev_den > 0:
                    rev_shares = vdf.loc[rev_mask, "Availability ($)"] / rev_den
                    alloc_rev.loc[vdf.loc[rev_mask, "Vehicle"]] = (
                        rev_shares * rev_total
                    )

            # ---- DDTL: Availability > 0 and DDTL On == True ----
            if ddtl_total > 0:
                ddtl_mask = (vdf["Availability ($)"] > 0) & (vdf["DDTL On"] == True)
                ddtl_den = vdf.loc[ddtl_mask, "Availability ($)"].sum()
                if ddtl_den > 0:
                    ddtl_shares = vdf.loc[ddtl_mask, "Availability ($)"] / ddtl_den
                    alloc_ddtl.loc[vdf.loc[ddtl_mask, "Vehicle"]] = (
                        ddtl_shares * ddtl_total
                    )

            # ---- Build allocation table: facilities as rows, vehicles as columns ----
            alloc_df = pd.DataFrame({"Facility": ["Term Loan", "Revolver", "DDTL"]})

            for v in vdf["Vehicle"]:
                alloc_df[v] = [
                    alloc_term.loc[v],
                    alloc_rev.loc[v],
                    alloc_ddtl.loc[v],
                ]

            alloc_df = alloc_df.set_index("Facility")

            st.markdown("**Facility Allocations (Vehicles Across Columns)**")
            st.dataframe(
                alloc_df.style.format("{:,.0f}"),
                use_container_width=True,
            )

else:
    st.info(
        "Edit the Deals and Vehicles grids above, then click **Calculate Allocations** "
        "to compute pro-rata allocations by facility and vehicle."
    )
