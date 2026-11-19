import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Service Profit Dashboard", layout="wide")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,)
st.title("Workshop Service Category & Profit Dashboard")
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Service Profit Dashboard", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Workshop Service Category & Profit Dashboard")

# --- PAID ACCESS GATE ---
valid_keys = st.secrets.get("VALID_KEYS", ["TRIAL-2026"])

with st.sidebar:
    st.header("🔑 Pro Access")
    user_key = st.text_input("Enter your License Key:", type="password")
    st.markdown("---")
    st.markdown("**Don't have a key?**")
    # Replace the URL below with your Razorpay / Cosmofeed / UPI payment link
    st.link_button(
        "💳 Unlock Full Access — ₹499/mo",
        "https://rzp.io/l/your-payment-link",
        use_container_width=True,
    )
    st.caption("Instant activation via UPI, Card, or NetBanking.")

if user_key.strip() not in valid_keys:
    st.info("🔒 Enter your **License Key** in the left sidebar to unlock multi-file uploads and profit reports.")
    st.markdown(
        """
        ### What You Get With Pro Access:
        * **Instant Category Sorting:** Automatically separates **Free Service, Paid Service, RE Maestros, and Accidental** job cards.
        * **Exact Pre-Tax Business & Gross Profit:** Calculates `Basic Amount` and net dealer margin (`Basic Amount − NDP`) in 2 seconds.
        * **Multi-File Merging:** Combine an entire month's daily JC Invoice Statements in one drag-and-drop.
        * **1-Click Clean Excel Export:** Ready-to-share management summary sheets.
        """
    )
    st.stop()  # Stops the rest of the app from running until a valid key is entered

# --- EVERYTHING BELOW THIS LINE ONLY RUNS FOR PAID USERS ---
uploaded_files = st.file_uploader(
    "Upload JC Invoice Statement (.xlsx / .xls)",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
)
# ... (keep all your existing dashboard code below unchanged) ...

uploaded_files = st.file_uploader(
    "Upload JC Invoice Statement (.xlsx / .xls)",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
)

def load_jc_statement(file):
    raw = pd.read_excel(file, header=None)
    header_idx = 0
    for idx, row in raw.iterrows():
        if "Invoice number" in row.astype(str).values:
            header_idx = idx
            break
    df = pd.read_excel(file, header=header_idx)
    df = df.dropna(subset=["Job ID"]).copy()
    df["Source_File"] = file.name
    return df

def classify_job(group):
    j_types = set(group["Job Type"].dropna().astype(str).str.strip())
    b_types = set(group["Bill Type"].dropna().astype(str).str.strip())
    descs = " ".join(
        group["Part Description/Labour Description"].dropna().astype(str)
    ).lower()

    if "Accidental" in j_types:
        return "Accidental"
    if "FreeService" in b_types:
        return "Free Service"
    if "LabourAMC" in b_types or "maestros" in descs:
        return "RE Maestros"
    if "PaidService" in b_types:
        return "Paid Service"
    return "Warranty / Campaign / Other"

def calculate_line_cost(row):
    item_group = str(row.get("Item Group", "")).strip()
    uom = str(row.get("UOM", "")).strip().upper()
    qty = float(row.get("Issues Qty/Labour Man Hour", 0) or 0)
    ndp = float(row.get("NDP", 0) or 0)
    basic = float(row.get("Basic Amount", 0) or 0)
    desc = str(row.get("Part Description/Labour Description", "")).upper()

    if item_group == "Labour":
        return 0.0

    if uom in ["ML", "GMS"]:
        pack_size = 1000.0
        if "500" in desc:
            pack_size = 500.0
        elif "150" in desc:
            pack_size = 150.0
        elif "10 GMS" in desc or "10GMS" in desc:
            pack_size = 10.0
        cost = (ndp / pack_size) * qty
        return min(cost, basic)

    return ndp * qty

if uploaded_files:
    dfs = [load_jc_statement(f) for f in uploaded_files]
    df = pd.concat(dfs, ignore_index=True)

    num_cols = [
        "Issues Qty/Labour Man Hour",
        "NDP",
        "Basic Amount",
        "Total Tax Amount",
        "Total Amount",
        "Discount(Dealer Value)",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    job_map = df.groupby("Job ID").apply(classify_job).to_dict()
    df["Service_Category"] = df["Job ID"].map(job_map)

    df["Estimated_Cost"] = df.apply(calculate_line_cost, axis=1)
    df["Gross_Profit"] = df["Basic Amount"] - df["Estimated_Cost"]

    biz_pre_tax = df["Basic Amount"].sum()
    tot_profit = df["Gross_Profit"].sum()
    tot_tax = df["Total Tax Amount"].sum()
    tot_jobs = df["Job ID"].nunique()

    st.subheader("Overall Business Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Job Cards", f"{tot_jobs:,}")
    k2.metric("Business (Before Tax)", f"Rs. {biz_pre_tax:,.2f}")
    k3.metric("Total Gross Profit", f"Rs. {tot_profit:,.2f}")
    k4.metric("Total GST Collected", f"Rs. {tot_tax:,.2f}")

    cat_order = [
        "Free Service",
        "Paid Service",
        "RE Maestros",
        "Accidental",
        "Warranty / Campaign / Other",
    ]
    summary = (
        df.groupby("Service_Category")
        .agg(
            Job_Cards=("Job ID", "nunique"),
            Line_Items=("Invoice number", "count"),
            Business_Before_Tax=("Basic Amount", "sum"),
            Estimated_Cost=("Estimated_Cost", "sum"),
            Gross_Profit=("Gross_Profit", "sum"),
            Tax_Amount=("Total Tax Amount", "sum"),
            Total_With_Tax=("Total Amount", "sum"),
        )
        .reindex(cat_order)
        .dropna(how="all")
        .reset_index()
    )
    margin = (summary["Gross_Profit"] / summary["Business_Before_Tax"].replace(0, pd.NA)) * 100
    summary["Profit_Margin_%"] = margin.fillna(0).round(1)

    st.subheader("Category Breakdown")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Business Before Tax by Category**")
        st.bar_chart(summary.set_index("Service_Category")["Business_Before_Tax"])
    with c2:
        st.markdown("**Gross Profit by Category**")
        st.bar_chart(summary.set_index("Service_Category")["Gross_Profit"])

    if "Service Consultant" in df.columns:
        st.subheader("Service Consultant Performance")
        adv = (
            df.groupby(["Service Consultant", "Service_Category"])
            .agg(
                Job_Cards=("Job ID", "nunique"),
                Business_Before_Tax=("Basic Amount", "sum"),
                Gross_Profit=("Gross_Profit", "sum"),
            )
            .reset_index()
        )
        st.dataframe(adv, use_container_width=True, hide_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Category_Profit_Summary", index=False)
        if "Service Consultant" in df.columns:
            adv.to_excel(writer, sheet_name="Advisor_Performance", index=False)
        df.to_excel(writer, sheet_name="Detailed_Line_Items", index=False)

    st.download_button(
        label="Download Profit & Category Excel Report",
        data=output.getvalue(),
        file_name="Service_Category_Profit_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
