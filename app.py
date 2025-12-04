import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Multi-Deal Availability Allocation Tool",
    layout="wide"
)

st.title("Multi-Deal Availability-Based Allocation Tool")

st.caption(
    "Define vehicles and their availability, then size multiple deals. "
    "Availability = Cash + Un-called Capital + Unfunded Commitments. "
    "Only vehicles with positive availability receive allocations. "
    "Revolver and DDTL participation is toggled per vehicle."
)

# ==========================
# VEHICLE SETUP (SIDEBAR)
# ==========================

st.sidebar.header("Vehicle Setup")

default_vehicle_names = ["Vehicle 1", "Vehicle 2", "Vehicle 3"]

num_vehicles = st.sidebar.number_input(
    "Number of Vehicles",
    min_value=1,
    max_value=10,
    value=3,
    step=1,
)

vehicles_data = []

for i in range(int(num_vehicles)):
    st.sidebar.markdown(f"**Vehicle {i+1}**")
    name = st.sidebar.text_input(
        f"Name {i+1}",
        value=default_vehicle_names[i] if i < len(default_vehicle_names) else f"Vehicle {i+1}",
        key=f"name_{i}",
    )
    cash = st.sidebar.number_input(
        f"Cash ($) – {name}",
        min_value=0.0,
        value=5_000_000.0,
        step=500_000.0,
        format="%.0f",
        key=f"cash_{i}",
    )
    uncalled = st.sidebar.number_input(
        f"Un-called Capital ($) – {name}",
        min_value=0.0,
        value=20_000_000.0,
        step=1_000_000.0,
        format="%.0f",
        key=f"uncalled_{i}",
    )
    unfunded = st.sidebar.number_input(
        f"Unfunded Commitments ($) – {name}",
        min_value=0.0,
        value=10_000_000.0,
        step=1_000_000.0,
        format="%.0f",
        key=f"unfunded_{i}",
    )
    rev_on = st.sidebar.checkbox(
        f"Participate in Revolver – {name}",
        value=True,
        key=f"rev_on_{i}",
    )
    ddtl_on = st.sidebar.checkbox(
        f"Participate in DDTL – {name}",
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

# Build vehicle DataFrame and availability once
vehicles_df = pd.DataFrame(vehicles_data)
vehicles_df["Availability"] = (
    vehicles_df["Cash"]
    + vehicles_df["Un-called Capital"]
    + vehicles_df["Unfunded Commitments"]
)

# Only vehicles with positive availability are eligible for Term Loan
positive_mask = vehicles_df["Availability"] > 0
vehicles_pos = vehicles_df[positive_mask].copy()
total_availability = vehicles_pos["Availability"].sum()

# ==========================
# MULTI-DEAL SETUP (MAIN)
# ==========================

st.markdown("---")
st.header("Deals")

num_deals = st.number_input(
    "Number of Deals",
    min_value=1,
    max_value=20,
    value=3,
    step=1,
)

# Collect all deal inputs first
deals = []

for d in range(int(num_deals)):
    st.markdown("---")
    st.subheader(f"Deal {d+1}")

    # Top-level: deal name
    deal_name = st.text_input(
        "Deal Name",
        value=f"Deal {d+1}",
        key=f"deal_name_{d}",
    )

    # Metrics row: left-to-right
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        ebitda = st.number_input(
            "EBITDA ($mm)",
            min_value=0.0,
            value=50.0,
            step=1.0,
            format="%.2f",
            key=f"ebitda_{d}",
        )
        senior_lev = st.number_input(
            "Senior Net Leverage (x)",
            min_value=0.0,
            value=3.5,
            step=0.1,
            format="%.1f",
            key=f"senior_lev_{d}",
        )
    with mcol2:
        total_lev = st.number_input(
            "Total Leverage (x)",
            min_value=0.0,
            value=4.5,
            step=0.1,
            format="%.1f",
            key=f"total_lev_{d}",
        )
        opening_spread = st.number_input(
            "Opening Spread (bps)",
            min_value=0,
            value=400,
            step=25,
            key=f"spread_{d}",
        )
    with mcol3:
        cov_lite = st.selectbox(
            "Covenant Lite?",
            options=["No", "Yes"],
            index=0,
            key=f"covlite_{d}",
        )
        ic_approved_hold = st.number_input(
            "IC Approved Hold ($)",
            min_value=0.0,
            value=50_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"ic_hold_{d}",
        )
    with mcol4:
        internal_rating = st.text_input(
            "Internal Rating",
            value="3 (Mid Risk)",
            key=f"int_rating_{d}",
        )
        sp_rating = st.text_input(
            "S&P Rating",
            value="B+",
            key=f"sp_rating_{d}",
        )

    # Facility sizes for this deal
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        term_loan_total = st.number_input(
            "Total Term Loan ($)",
            min_value=0.0,
            value=100_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"tl_{d}",
        )
    with fcol2:
        revolver_total = st.number_input(
            "Total Revolver ($)",
            min_value=0.0,
            value=25_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"rev_{d}",
        )
    with fcol3:
        ddtl_total = st.number_input(
            "Total DDTL ($)",
            min_value=0.0,
            value=15_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"ddtl_{d}",
        )

    deals.append(
        {
            "name": deal_name,
            "EBITDA": ebitda,
            "Senior Leverage": senior_lev,
            "Total Leverage": total_lev,
            "Spread": opening_spread,
            "Covenant Lite": cov_lite,
            "Internal Rating": internal_rating,
            "S&P Rating": sp_rating,
            "IC Approved Hold": ic_approved_hold,
            "TL": term_loan_total,
            "REV": revolver_total,
            "DDTL": ddtl_total,
        }
    )

st.markdown("---")

# ==========================
# CALCULATE ALLOCATIONS
# ==========================

if st.button("Calculate Allocations for All Deals"):
    if total_availability <= 0:
        st.error(
            "Total availability across all vehicles is zero. "
            "Please enter positive availability (Cash + Un-called + Unfunded)."
        )
    else:
        # Show a summary of vehicles and availability once (top)
        st.subheader("Vehicle Availability Summary")

        avail_display_cols = [
            "Vehicle",
            "Cash",
            "Un-called Capital",
            "Unfunded Commitments",
            "Availability",
            "Revolver On",
            "DDTL On",
        ]

        st.dataframe(
            vehicles_df[avail_display_cols].style.format(
                {
                    "Cash": "{:,.0f}",
                    "Un-called Capital": "{:,.0f}",
                    "Unfunded Commitments": "{:,.0f}",
                    "Availability": "{:,.0f}",
                }
            ),
            use_container_width=True,
        )

        # Loop through each deal top-to-bottom
        for idx, deal in enumerate(deals):
            st.markdown("---")
            st.subheader(f"Deal {idx+1}: {deal['name']}")

            # -------- Deal metrics box (horizontal) --------
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
                        f"{deal['EBITDA']:,.2f}",
                        f"{deal['Senior Leverage']:.1f}",
                        f"{deal['Total Leverage']:.1f}",
                        f"{deal['Spread']}",
                        deal["Covenant Lite"],
                        deal["Internal Rating"],
                        deal["S&P Rating"],
                        f"{deal['IC Approved Hold']:,.0f}",
                    ],
                }
            )

            # Show metrics row-like
            mcol_a, mcol_b = st.columns(2)
            with mcol_a:
                st.markdown("**Deal Metrics**")
                st.table(metrics_df.iloc[:4])
            with mcol_b:
                st.markdown("**Ratings / Hold**")
                st.table(metrics_df.iloc[4:])

            # -------- Allocation calculations --------

            # Term Loan: all vehicles with Availability > 0
            tl_total = deal["TL"]
            rev_total = deal["REV"]
            ddtl_total = deal["DDTL"]

            alloc_term = pd.Series(0.0, index=vehicles_df["Vehicle"])
            alloc_rev = pd.Series(0.0, index=vehicles_df["Vehicle"])
            alloc_ddtl = pd.Series(0.0, index=vehicles_df["Vehicle"])

            # Term Loan
            if tl_total > 0 and total_availability > 0:
                base_shares = vehicles_pos["Availability"] / total_availability
                alloc_term.loc[vehicles_pos["Vehicle"]] = base_shares * tl_total

            # Revolver: only Availability > 0 AND Revolver On
            if rev_total > 0:
                rev_mask = (vehicles_df["Availability"] > 0) & (vehicles_df["Revolver On"])
                rev_denominator = vehicles_df.loc[rev_mask, "Availability"].sum()
                if rev_denominator > 0:
                    rev_shares = (
                        vehicles_df.loc[rev_mask, "Availability"] / rev_denominator
                    )
                    alloc_rev.loc[vehicles_df.loc[rev_mask, "Vehicle"]] = (
                        rev_shares * rev_total
                    )

            # DDTL: only Availability > 0 AND DDTL On
            if ddtl_total > 0:
                ddtl_mask = (vehicles_df["Availability"] > 0) & (vehicles_df["DDTL On"])
                ddtl_denominator = vehicles_df.loc[ddtl_mask, "Availability"].sum()
                if ddtl_denominator > 0:
                    ddtl_shares = (
                        vehicles_df.loc[ddtl_mask, "Availability"] / ddtl_denominator
                    )
                    alloc_ddtl.loc[vehicles_df.loc[ddtl_mask, "Vehicle"]] = (
                        ddtl_shares * ddtl_total
                    )

            # Build an allocation table with vehicles across the top
            alloc_df = pd.DataFrame(
                {
                    "Facility": ["Term Loan", "Revolver", "DDTL"],
                }
            )

            for v in vehicles_df["Vehicle"]:
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
    st.info("Define vehicles and deals, then click **Calculate Allocations for All Deals**.")
