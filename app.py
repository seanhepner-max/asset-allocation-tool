# ==========================
# DEAL INPUT BLOCK
# ==========================

st.markdown("---")
st.subheader(f"Deal {d+1}")

# ----------------------------------------------------
# HEADER ROW (column titles)
# ----------------------------------------------------
header_cols = st.columns(
    [
        1.5,  # Deal
        1.2,  # Est. Closing
        1.5,  # New/Amendment
        1.3,  # Transaction Type
        1.0,  # EBITDA
        1.3,  # Senior Leverage
        1.3,  # Total Leverage
        1.2,  # Opening Spread
        1.0,  # Covenant Lite
        1.3,  # Internal Rating
        1.0,  # S&P Rating
        1.8,  # IC Approved Hold
    ]
)

headers = [
    "Deals",
    "Est. Closing Date",
    "New Deal or Amendment",
    "Transaction Type",
    "EBITDA ($mm)",
    "Senior Net Leverage (x)",
    "Total Leverage (x)",
    "Opening Spread (bps)",
    "Covenant Lite",
    "Internal Rating",
    "S&P Rating",
    "IC Approved Hold ($)",
]

for col, name in zip(header_cols, headers):
    col.markdown(f"**{name}**")

# ----------------------------------------------------
# INPUT ROW (user entries)
# ----------------------------------------------------
input_cols = st.columns(
    [
        1.5, 1.2, 1.5, 1.3, 1.0, 1.3, 1.3, 1.2, 1.0, 1.3, 1.0, 1.8
    ]
)

with input_cols[0]:
    deal_name = st.text_input(
        "",
        value=f"Deal {d+1}",
        key=f"deal_name_{d}",
    )

with input_cols[1]:
    est_closing = st.date_input(
        "",
        value=date.today(),
        key=f"closing_{d}",
    )

with input_cols[2]:
    new_or_amend = st.selectbox(
        "",
        options=["New Deal", "Amendment"],
        index=0,
        key=f"new_or_amend_{d}",
    )

with input_cols[3]:
    transaction_type = st.text_input(
        "",
        value="LBO",
        key=f"txn_type_{d}",
    )

with input_cols[4]:
    ebitda = st.number_input(
        "",
        min_value=0.0,
        value=50.0,
        step=1.0,
        format="%.2f",
        key=f"ebitda_{d}",
    )

with input_cols[5]:
    senior_lev = st.number_input(
        "",
        min_value=0.0,
        value=3.5,
        step=0.1,
        format="%.1f",
        key=f"senior_lev_{d}",
    )

with input_cols[6]:
    total_lev = st.number_input(
        "",
        min_value=0.0,
        value=4.5,
        step=0.1,
        format="%.1f",
        key=f"total_lev_{d}",
    )

with input_cols[7]:
    opening_spread = st.number_input(
        "",
        min_value=0,
        value=400,
        step=25,
        key=f"spread_{d}",
    )

with input_cols[8]:
    cov_lite = st.selectbox(
        "",
        options=["No", "Yes"],
        key=f"covlite_{d}",
    )

with input_cols[9]:
    internal_rating = st.text_input(
        "",
        value="3 (Mid Risk)",
        key=f"int_rating_{d}",
    )

with input_cols[10]:
    sp_rating = st.text_input(
        "",
        value="B+",
        key=f"sp_rating_{d}",
    )

with input_cols[11]:
    ic_approved_hold = st.number_input(
        "",
        min_value=0.0,
        value=50_000_000.0,
        step=1_000_000.0,
        format="%.0f",
        key=f"ic_hold_{d}",
    )

# Store output
deals.append(
    {
        "Deal": deal_name,
        "Est. Closing Date": est_closing,
        "New/Amendment": new_or_amend,
        "Transaction Type": transaction_type,
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
