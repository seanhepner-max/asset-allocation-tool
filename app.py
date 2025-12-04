import streamlit as st
import pandas as pd

st.set_page_config(page_title="Availability-Based Pro-Rata Allocation", layout="wide")

st.title("Availability-Based Pro-Rata Allocation Tool")
st.caption(
    "Enter Cash, Un-called Capital, and Unfunded Commitments for each vehicle. "
    "Availability determines pro-rata share of Term Loan, Revolver, and DDTL allocations."
)

# ---------------------------
# Deal size inputs (top)
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
# Vehicle / investor inputs
# ---------------------------

st.header("Vehicle Inputs (for Availability)")

st.caption(
    "Availability = Cash + Un-called Capital + Unfunded Commitments. "
    "Pro-rata share = Availability / Total Availability."
)

# You can change these names to whatever you use internally
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

    cols = st.columns(4)
    with cols[0]:
        name = st.text_input(
            "Name",
            value=default_vehicle_names[i] if i < len(default_vehicle_names) else f"Vehicle {i+1}",
            key=f"name_{i}",
        )
    with cols[1]:
        cash = st.number_input(
            "Cash ($)",
            min_value=0.0,
            value=5_000_000.0,
            step=500_000.0,
            format="%.0f",
            key=f"cash_{i}",
        )
    with cols[2]:
        uncalled = st.number_input(
            "Un-called Capital ($)",
            min_value=0.0,
            value=20_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"uncalled_{i}",
        )
    with cols[3]:
        unfunded = st.number_input(
            "Unfunded Commitments ($)",
            min_value=0.0,
            value=10_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"unfunded_{i}",
        )

    vehicles_data.append(
        {
            "Vehicle": name,
            "Cash": cash,
            "Un-called Capital": uncalled,
            "Unfunded Commitments": unfunded,
        }
    )

st.markdown("---")

# ---------------------------
# Computation
# ---------------------------

if st.button("Calculate Pro-Rata Allocations"):
    df = pd.DataFrame(vehicles_data)

    # Availability definition: sum of the three fields
    df["Availability"] = (
        df["Cash"] + df["Un-called Capital"] + df["Unfunded Commitments"]
    )

    total_availability = df["Availability"].sum()

    if total_availability <= 0:
        st.error("Total Availability is zero. Please enter positive values.")
    else:
        # Pro-rata share based on Availability
        df["Availability Share %"] = df["Availability"] / total_availability * 100.0

        # Allocate each facility by Availability share
        df["Term Loan Allocation ($)"] = df["Availability"] / total_availability * term_loan_total
        df["Revolver Allocation ($)"] = df["Availability"] / total_availability * revolver_total
        df["DDTL Allocation ($)"] = df["Availability"] / total_availability * ddtl_total

        # Display summary
        st.subheader("Availability and Pro-Rata Shares")
        st.dataframe(
            df[
                [
                    "Vehicle",
                    "Cash",
                    "Un-called Capital",
                    "Unfunded Commitments",
                    "Availability",
                    "Availability Share %",
                ]
            ].style.format(
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

        # Optional visualization: stacked bar of allocations
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

