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
    "Revolver and DDTL participation is controlled per vehicle. "
    "Pro-rata share of each deal by fund is computed from these allocations."
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


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def safe_bool(x):
    # AgGrid may return True/False, 'true'/'false', 'True'/'False', or blanks
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        x_clean = x.strip().lower()
        if x_clean in ["true", "yes", "y", "1"]:
            return True
        if x_clean in ["false", "no", "n", "0", ""]:
            return False
    return False


# =======================================
# DEFAULT DATA (you can tweak these)
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
        "First column is **Deal**, followed by all metrics and facility sizes "
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

    deals_df_raw = editable_grid(default_deals, key="deals_grid")

with right_col:
    st.subheader("Vehicles / Funds (Availability & Toggles)")
    st.markdown(
        "Enter **Cash, Unfunded Commitments, Uncalled Capital** and whether "
        "each vehicle participates in **Revolver** and **DDTL**. "
        "Availability is computed automatically in the allocation step."
    )

    vehicles_df_raw = editable_grid(default_vehicles, key="vehicles_grid")

st.markdown("---")

# =======================================
# Cleaning / typing helpers
# =======================================

def clean_deals(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure numeric columns are numeric, others left as-is."""
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

    # Strip strings in text columns
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

    num_cols = ["Cash ($)", "Unfunded Commitments ($)", "Uncalled Capital ($)"]
    for col in num_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    # Booleans
    for col in ["Revolver On", "DDTL On"]:
        if col in out.columns:
            out[col] = out[col].apply(safe_bool)

    # Vehicle names as strings
    if "Vehicle" in out.columns:
        out["Vehicle"] = out["Vehicle"].astype(str).str.strip()
    return out


def compute_availability(vdf: pd.DataFrame) -> pd.DataFrame:
    df = vdf.copy()
    df["Availability ($)"] = (
        df["Cash ($)"] + df["Unfunded Commitments ($)"] + df["Uncalled Capital ($)"]
    )
    return df


# =======================================
# Allocation logic
# =======================================

if st.button("Calculate Allocations"):
    deals_df = clean_deals(deals_df_raw)
    vdf = clean_vehicles(vehicles_df_raw)
    vdf = compute_availability(vdf)

    # Availability > 0
    positive_mask = vdf["Availability ($)"] > 0
    vdf_pos = vdf[positive_mask].copy()
    total_avail = vdf_pos["Availability ($)"].sum()

    if total_avail <= 0:
        st.error(
            "Total availability across all vehicles is zero or invalid. "
            "Please enter positive values for Cash, Unfunded, or Uncalled Capital."
        )
    else:
        # Show availability summary (formatted with $ and commas)
        st.subheader("Vehicle Availability Summary")
        avail_display = vdf[
            [
                "Vehicle",
                "Cash ($)",
                "Unfunded Commitments ($)",
                "Uncalled Capital ($)",
                "Availability ($)",
                "Revolver On",
                "DDTL On",
            ]
        ]
        st.dataframe(
            avail_display.style.format(
                {
                    "Cash ($)": "${:,.0f}".format,
                    "Unfunded Commitments ($)": "${:,.0f}".format,
                    "Uncalled Capital ($)": "${:,.0f}".format,
                    "Availability ($)": "${:,.0f}".format,
                }
            ),
            use_container_width=True,
        )

        # --- Loop through deals and allocate per deal ---
        for idx, row in deals_df.iterrows():
            deal_name = row.get("Deal", f"Deal {idx+1}") or f"Deal {idx+1}"

            st.markdown("---")
            st.subheader(f"Deal {idx+1}: {deal_name}")

            # Build a one-row summary like your template
            summary = pd.DataFrame(
                [
                    {
                        "Deal": deal_name,
                        "Est. Closing Date": row.get("Est. Closing Date", ""),
                        "New Deal or Amendment": row.get("New Deal or Amendment", ""),
                        "Transaction Type": row.get("Transaction Type", ""),
                        "EBITDA ($mm)": row.get("EBITDA ($mm)", 0.0),
                        "Senior Net Leverage (x)": row.get(
                            "Senior Net Leverage (x)", 0.0
                        ),
                        "Total Leverage (x)": row.get("Total Leverage (x)", 0.0),
                        "Opening Spread (bps)": row.get("Opening Spread (bps)", 0.0),
                        "Covenant Lite": row.get("Covenant Lite", ""),
                        "Internal Rating": row.get("Internal Rating", ""),
                        "S&P Rating": row.get("S&P Rating", ""),
                        "IC Approved Hold ($)": row.get("IC Approved Hold ($)", 0.0),
                    }
                ]
            )

            st.markdown("**Deal Summary (row-style, matching template order)**")
            st.dataframe(
                summary.style.format(
                    {
                        "EBITDA ($mm)": "{:,.2f}".format,
                        "Senior Net Leverage (x)": "{:,.1f}".format,
                        "Total Leverage (x)": "{:,.1f}".format,
                        "Opening Spread (bps)": "{:,.0f}".format,
                        "IC Approved Hold ($)": "${:,.0f}".format,
                    }
                ),
                use_container_width=True,
            )

            # --- Get facility sizes for this deal ---
            tl_total = row.get("Term Loan ($)", 0.0)
            rev_total = row.get("Revolver ($)", 0.0)
            ddtl_total = row.get("DDTL ($)", 0.0)
            deal_total = tl_total + rev_total + ddtl_total

            # Initialize allocation vectors
            alloc_term = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_rev = pd.Series(0.0, index=vdf["Vehicle"])
            alloc_ddtl = pd.Series(0.0, index=vdf["Vehicle"])

            # ---- Term Loan: all vehicles with Availability > 0 ----
            if tl_total > 0 and total_avail > 0:
                base_shares = vdf_pos["Availability ($)"] / total_avail
                alloc_term.loc[vdf_pos["Vehicle"]] = base_shares * tl_total

            # ---- Revolver: Availability > 0 and Revolver On == True ----
            if rev_total > 0:
                rev_mask = (vdf["Availability ($)"] > 0) & (vdf["Revolver On"])
                rev_den = vdf.loc[rev_mask, "Availability ($)"].sum()
                if rev_den > 0:
                    rev_shares = vdf.loc[rev_mask, "Availability ($)"] / rev_den
                    alloc_rev.loc[vdf.loc[rev_mask, "Vehicle"]] = (
                        rev_shares * rev_total
                    )

            # ---- DDTL: Availability > 0 and DDTL On == True ----
            if ddtl_total > 0:
                ddtl_mask = (vdf["Availability ($)"] > 0) & (vdf["DDTL On"])
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
                alloc_df.style.format("${:,.0f}".format),
                use_container_width=True,
            )

            # ---- Pro-rata share of deal by vehicle ----
            st.markdown("**Pro-Rata Share of Deal by Vehicle**")

            vehicle_total_alloc = alloc_term + alloc_rev + alloc_ddtl
            pro_rata_df = pd.DataFrame(
                {
                    "Vehicle": vdf["Vehicle"],
                    "Allocated ($)": vehicle_total_alloc.values,
                }
            )

            if deal_total > 0:
                pro_rata_df["Pro-Rata Share (%)"] = (
                    pro_rata_df["Allocated ($)"] / deal_total * 100.0
                )
            else:
                pro_rata_df["Pro-Rata Share (%)"] = 0.0

            st.dataframe(
                pro_rata_df.style.format(
                    {
                        "Allocated ($)": "${:,.0f}".format,
                        "Pro-Rata Share (%)": "{:,.2f}%".format,
                    }
                ),
                use_container_width=True,
            )

else:
    st.info(
        "Edit the Deals and Vehicles grids above, then click **Calculate Allocations** "
        "to compute pro-rata allocations by facility and vehicle, plus each vehicle's "
        "pro-rata share of the total deal."
    )
