import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Availability-Based Pro-Rata Allocation",
    layout="wide"
)

st.title("Availability-Based Pro-Rata Allocation Tool")

st.caption(
    "Availability = Cash + Un-called Capital + Unfunded Commitments. "
    "Only vehicles with positive Availability receive allocations. "
    "Revolver and DDTL can be toggled on/off by vehicle."
)

# ---------------------------
# Deal-level metrics
# ---------------------------
st.header("Deal Metrics")

mcol1, mcol2, mcol3 = st.columns(3)
with mcol1:
    ebitda = st.number_input(
        "EBITDA ($mm)",
        min_value=0.0,
        value=50.0,
        step=1.0,
        format="%.2f",
    )
    senior_lev = st.number_input(
        "Senior Net Leverage (x)",
        min_value=0.0,
        value=3.5,
        step=0.1,
        format="%.1f",
    )
with mcol2:
    total_lev = st.number_input(
        "Total Leverage (x)",
        min_value=0.0,
        value=4.5,
        step=0.1,
        format="%.1f",
    )
    opening_spread = st.number_input(
        "Opening Spread (bps)",
        min_value=0,
        value=400,
        step=25,
    )
with mcol3:
    cov_lite = st.selectbox(
        "Covenant Lite?",
        options=["No", "Yes"],
        index=0,
    )
    ic_approved_hold = st.number_input(
        "IC Approved Hold ($)",
        min_value=0.0,
        value=50_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )

rcol1, rcol2 = st.columns(2)
with rcol1:
    internal_rating = st.text_input("Internal Rating", value="3 (Mid Risk)")
with rcol2:
    sp_rating = st.text_input("S&P Rating", value="B+")

st.markdown("---")

# ---------------------------
# Deal facility sizes
# ---------------------------
st.header("Deal Facility Sizes")

col_tl, col_rev, col_ddtl = st.columns(3)
with col_tl:
    term_loan_total = st.number_input(
        "Total Term Loan ($)",
        min_value=0.0,
        value=100_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )
with col_rev:
    revolver_total = st.number_input(
        "Total Revolver ($)",
        min_value=0.0,
        value=25_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )
with col_ddtl:
    ddtl_total = st.number_input(
        "Total Delayed Draw Term Loan (DDTL) ($)",
        min_value=0.0,
        value=15_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )

st.markdown("---")

# ---------------------------
# Vehicle inputs
# ---------------------------

st.header("Vehicle Inputs (Availability & Facility Toggles)")

st.caption(
    "Per vehicle: enter Cash, Un-called Capital, Unfunded Commitments. "
    "Availability = sum of those three. Only vehicles with Availability > 0 receive allocations. "
    "Revolver / DDTL toggles control whether that vehicle participates in those facilities."
)

default_vehicle_names = ["Vehicle 1", "Vehicle 2"]

num_vehicles = st.number_input(
    "Number of Vehicles",
    min_value=1,
    max_value=10,
    value=len(default_vehicle_names),
    step=1,
)

vehicles_data = []

for i in range(int(num_vehicles)):
    st.subheader(f"Vehicle {i+1}")

    row1 = st.columns(4)
    with row1[0]:
        name = st.text_input(
            "Name",
            value=default_vehicle_names[i] if i < len(default_vehicle_names) else f"Vehicle {i+1}",
            key=f"name_{i}",
        )
    with row1[1]:
        cash = st.number_input(
            "Cash ($)",
            min_value=0.0,
            value=5_000_000.0,
            step=500_000.0,
            format="%.0f",
            key=f"cash_{i}",
        )
    with row1[2]:
        uncalled = st.number_input(
            "Un-called Capital ($)",
            min_value=0.0,
            value=20_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"uncalled_{i}",
        )
    with row1[3]:
        unfunded = st.number_input(
            "Unfunded Commitments ($)",
            min_value=0.0,
            value=10_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"unfunded_{i}",
        )

    row2 = st.columns(2)
    with row2[0]:
        rev_on = st.checkbox(
            "Participate in Revolver?",
            value=True,
            key=f"rev_on_{i}",
        )
    with row2[1]:
        ddtl_on = st.checkbox(
            "Participate in DDTL?",
            value=True,
            key=f"ddtl_on_{i}",
        )

    vehicles_data.append(
        {
            "Vehicle": name,
            "Cash": cash,
            "Un-called Capital": uncalled,
            "Unfunded Commitments": unfunded,
            "Revolver On": rev_on,
            "DDTL On": ddtl_on,
        }
    )

st.markdown("---")

# ---------------------------
# Computation
# ---------------------------

if st.button("Calculate Pro-Rata Allocations"):
    df = pd.DataFrame(vehicles_data)

    # Compute Availability
    df["Availability"] = (
        df["Cash"] + df["Un-called Capital"] + df["Unfunded Commitments"]
    )

    # Vehicles with positive availability
    df_pos = df[df["Availability"] > 0].copy()

    if df_pos.empty:
        st.error("Total Availability is zero. Please enter positive values for at least one vehicle.")
    else:
        # Base availability share (for info only) among positive-availability vehicles
        total_avail_base = df_pos["Availability"].sum()
        df["Availability Share %"] = 0.0
        df.loc[df["Availability"] > 0, "Availability Share %"] = (
            df_pos["Availability"] / total_avail_base * 100.0
        )

        # --- Term Loan allocation (all positive-availability vehicles) ---
        if term_loan_total > 0:
            tl_denominator = total_avail_base  # all with Availability > 0
            df["Term Loan Allocation ($)"] = 0.0
            df.loc[df["Availability"] > 0, "Term Loan Allocation ($)"] = (
                df_pos["Availability"] / tl_denominator * term_loan_total
            )
        else:
            df["Term Loan Allocation ($)"] = 0.0

        # --- Revolver allocation (only vehicles with Availability > 0 AND Revolver On) ---
        if revolver_total > 0:
            rev_mask = (df["Availability"] > 0) & (df["Revolver On"])
            rev_denominator = df.loc[rev_mask, "Availability"].sum()
            df["Revolver Allocation ($)"] = 0.0
            if rev_denominator > 0:
                df.loc[rev_mask, "Revolver Allocation ($)"] = (
                    df.loc[rev_mask, "Availability"] / rev_denominator * revolver_total
                )
        else:
            df["Revolver Allocation ($)"] = 0.0

        # --- DDTL allocation (only vehicles with Availability > 0 AND DDTL On) ---
        if ddtl_total > 0:
            ddtl_mask = (df["Availability"] > 0) & (df["DDTL On"])
            ddtl_denominator = df.loc[ddtl_mask, "Availability"].sum()
            df["DDTL Allocation ($)"] = 0.0
            if ddtl_denominator > 0:
                df.loc[ddtl_mask, "DDTL Allocation ($)"] = (
                    df.loc[ddtl_mask, "Availability"] / ddtl_denominator * ddtl_total
                )
        else:
            df["DDTL Allocation ($)"] = 0.0

        # ---------------------------
        # Output: Deal metrics summary
        # ---------------------------
        st.subheader("Deal Metrics Summary")
        metrics_df = pd.DataFrame(
            {
                "Metric": [
                    "EBITDA ($mm)",
                    "Senior Net Leverage (x)",
                    "Total Leverage (x)",
                    "Opening Spread (bps)",
                    "Covenant Lite",
                    "Internal Rating",
                    "S&P Rating",
                    "IC Approved Hold ($)",
                ],
                "Value": [
                    f"{ebitda:,.2f}",
                    f"{senior_lev:.1f}",
                    f"{total_lev:.1f}",
                    f"{opening_spread}",
                    cov_lite,
                    internal_rating,
                    sp_rating,
                    f"{ic_approved_hold:,.0f}",
                ],
            }
        )
        st.table(metrics_df)

        # ---------------------------
        # Output: Availability summary
        # ---------------------------
        st.subheader("Availability and Pro-Rata Shares")
        display_cols = [
            "Vehicle",
            "Cash",
            "Un-called Capital",
            "Unfunded Commitments",
            "Availability",
            "Availability Share %",
            "Revolver On",
            "DDTL On",
        ]

        st.dataframe(
            df[display_cols].style.format(
                {
                    "Cash": "{:,.0f}",
                    "Un-called Capital": "{:,.0f}",
                    "Unfunded Commitments": "{:,.0f}",
                    "Availability": "{:,.0f}",
                    "Availability Share %": "{:,.2f}",
                }
            ),
            use_container_width=True,
        )

        # ---------------------------
        # Output: Facility allocations
        # ---------------------------
        st.subheader("Facility Allocations by Vehicle")
        alloc_cols = [
            "Vehicle",
            "Term Loan Allocation ($)",
            "Revolver Allocation ($)",
            "DDTL Allocation ($)",
        ]

        st.dataframe(
            df[alloc_cols].style.format(
                {
                    "Term Loan Allocation ($)": "{:,.0f}",
                    "Revolver Allocation ($)": "{:,.0f}",
                    "DDTL Allocation ($)": "{:,.0f}",
                }
            ),
            use_container_width=True,
        )

        # ---------------------------
        # Visuals
        # ---------------------------
        st.subheader("Visual: Allocation by Facility Type")
        chart_df = df.set_index("Vehicle")[
            [
                "Term Loan Allocation ($)",
                "Revolver Allocation ($)",
                "DDTL Allocation ($)",
            ]
        ]
        st.bar_chart(chart_df)

else:
    st.info("Enter values above and click **Calculate Pro-Rata Allocations**.")
