import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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


def render_razorpay_buttons(compact=False):
    if compact:
        components.html(
            """
            <div style="font-family: sans-serif; text-align: center;">
                <p style="font-size: 13px; font-weight: 600; margin: 4px 0;">Monthly Plan — ₹99/mo</p>
                <form>
                    <script src="https://checkout.razorpay.com/v1/payment-button.js"
                            data-payment_button_id="pl_U380DaigJ2TGTN"
                            async>
                    </script>
                </form>
                <p style="font-size: 13px; font-weight: 600; margin: 10px 0 4px 0;">Yearly Plan — ₹699/yr (Save 41%)</p>
                <form>
                    <script src="https://checkout.razorpay.com/v1/payment-button.js"
                            data-payment_button_id="pl_U382n3tm4IReDi"
                            async>
                    </script>
                </form>
            </div>
            """,
            height=175,
        )
    else:
        components.html(
            """
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; font-family: sans-serif; padding: 6px 0;">
                <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 14px 18px; background: #fafafa;">
                    <div style="font-weight: 700; font-size: 15px; margin-bottom: 4px;">📅 Monthly Pass — ₹99/mo</div>
                    <div style="font-size: 12px; color: #555; margin-bottom: 10px;">Unlimited files & Excel export for 30 days</div>
                    <form>
                        <script src="https://checkout.razorpay.com/v1/payment-button.js"
                                data-payment_button_id="pl_U380DaigJ2TGTN"
                                async>
                        </script>
                    </form>
                </div>
                <div style="border: 2px solid #2b6cb0; border-radius: 10px; padding: 14px 18px; background: #ebf8ff;">
                    <div style="font-weight: 700; font-size: 15px; color: #1a365d; margin-bottom: 4px;">⭐ Annual Pass — ₹699/yr (Best Value)</div>
                    <div style="font-size: 12px; color: #2c5282; margin-bottom: 10px;">Full year access — save ₹489 vs monthly</div>
                    <form>
                        <script src="https://checkout.razorpay.com/v1/payment-button.js"
                                data-payment_button_id="pl_U382n3tm4IReDi"
                                async>
                        </script>
                    </form>
                </div>
            </div>
            """,
            height=155,
        )


st.title("Workshop Service Category & Profit Dashboard")

# --- ACCESS & TRIAL CONTROL ---
valid_pro_keys = st.secrets.get("VALID_KEYS", ["PRO-2026", "CLIENT-101"])
trial_key = "TRIAL-2026"

if "access_mode" not in st.session_state:
    st.session_state["access_mode"] = None

with st.sidebar:
    st.header("🔑 Access & License")
    user_key = st.text_input("Enter License Key:", type="password").strip()

    if user_key in valid_pro_keys:
        st.session_state["access_mode"] = "PRO"
    elif user_key == trial_key:
        st.session_state["access_mode"] = "TRIAL"

    if st.session_state["access_mode"] != "PRO":
        if st.button("🎁 Start Free Trial (25 Rows)", use_container_width=True):
            st.session_state["access_mode"] = "TRIAL"

    st.markdown("---")
    st.markdown("**Buy Pro License Key:**")
    render_razorpay_buttons(compact=True)
    st.caption("Instant checkout via UPI, Card, or NetBanking.")

mode = st.session_state["access_mode"]

# --- LANDING PAYWALL ---
if mode is None:
    st.info("👋 Welcome! Test the dashboard with a **Free Trial** (first 25 rows) or unlock **Full Pro Access** below.")
    col_trial, col_pro = st.columns([1, 1.4])
    with col_trial:
        st.markdown(
            """
            ### 🎁 Free Trial Mode
            * Upload **1 JC Invoice Statement**
            * Preview first **25 rows** on screen
            * Check **Free, Paid, RE Maestros & Accidental** split
            """
        )
        if st.button("🚀 Launch Free Trial Now", key="main_trial_btn"):
            st.session_state["access_mode"] = "TRIAL"
            st.rerun()

    with col_pro:
        st.markdown(
            """
            ### ⭐ Full Pro Access
            * **100% of Rows & Unlimited Multi-File Merging**
            * **1-Click Clean Excel Report Download**
            * **Service Consultant KPI Breakdown**
            """
        )
        render_razorpay_buttons(compact=False)
    st.stop()

# --- STATUS BANNER ---
if mode == "TRIAL":
    st.warning(
        "🎁 **FREE TRIAL MODE ACTIVE:** Previewing up to **25 rows** from **1 file**. "
        "Full monthly files, multi-file merging, and Excel downloads require a Pro License Key."
    )
    render_razorpay_buttons(compact=False)
else:
    st.success("✅ **PRO ACCESS ACTIVE:** Unlimited rows, multi-file uploads, and Excel exports unlocked.")

# --- FILE UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload JC Invoice Statement (.xlsx / .xls)",
    type=["xlsx", "xls"],
    accept_multiple_files=(mode == "PRO"),
    key="jc_statement_uploader",
)

if uploaded_files and not isinstance(uploaded_files, list):
    uploaded_files = [uploaded_files]


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

    total_raw_rows = len(df)

    # --- CAP FREE TRIAL TO FIRST 25 ROWS ---
    if mode == "TRIAL" and total_raw_rows > 25:
        df = df.head(25).copy()
        st.warning(
            f"🔒 **Trial Limit Reached:** Showing preview for **25 of {total_raw_rows:,} rows** "
            f"({total_raw_rows - 25:,} rows hidden). Unlock Pro below to process the full file and download Excel."
        )

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

    st.subheader("Overall Business Summary" + (" (25-Row Trial Preview)" if mode == "TRIAL" else ""))
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

    # --- EXCEL EXPORT (PRO ONLY) ---
    if mode == "PRO":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="Category_Profit_Summary", index=False)
            if "Service Consultant" in df.columns:
                adv.to_excel(writer, sheet_name="Advisor_Performance", index=False)
            df.to_excel(writer, sheet_name="Detailed_Line_Items", index=False)

        st.download_button(
            label="📥 Download Profit & Category Excel Report",
            data=output.getvalue(),
            file_name="Service_Category_Profit_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(f"🔒 **{max(0, total_raw_rows - 25):,} remaining rows & Excel Export** require a Pro License Key.")
        render_razorpay_buttons(compact=False)
