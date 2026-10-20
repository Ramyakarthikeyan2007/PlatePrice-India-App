"""
app.py - PlatePrice India: Affordable Food & Nutrition Dashboard
=================================================================
An interactive, India-focused Streamlit web application.
Data Sources:
- Department of Consumer Affairs (DCA) Price Monitoring Division (fcainfoweb.nic.in)
- Indian Food Composition Tables (IFCT 2017, ICMR-NIN)
- AGMARKNET Wholesale Mandi Benchmarks (agmarknet.gov.in)
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Graceful Streamlit import check
try:
    import streamlit as st
except ImportError:
    print("\n[ERROR] Streamlit is not installed in the current environment.")
    print("Please install requirements using: pip install -r requirements.txt")
    print("Then launch the app with: streamlit run app.py\n")
    sys.exit(1)

# Import local data loader and calculation modules
import data_loader as dl
import calculations as calc


# -------------------------------------------------------------------------
# 1. STREAMLIT CONFIGURATION & INDIAN THEME CSS
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="PlatePrice India — Food Price & Nutrition Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for India-Focused Dashboard
st.markdown("""
<style>
    /* Main body background */
    .main {
        background-color: #f8fafc;
    }
    
    /* Indian Flag Saffron Gradient Header */
    .hero-india {
        background: linear-gradient(135deg, #c2410c 0%, #ea580c 45%, #f97316 100%);
        color: white;
        padding: 1.8rem 2.2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-india h1 {
        color: #ffffff !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .hero-india p {
        color: #ffedd5 !important;
        font-size: 1.05rem;
        margin-bottom: 0;
    }

    /* Metric Cards */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .kpi-card h3 {
        color: #64748b;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }
    .kpi-card .kpi-value {
        color: #ea580c;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .kpi-card .kpi-sub {
        color: #94a3b8;
        font-size: 0.8rem;
    }

    /* Data Tier Badges */
    .badge-demo {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-uploaded {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fcd34d;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-wholesale {
        background-color: #f3e8ff;
        color: #6b21a8;
        border: 1px solid #d8b4fe;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-official {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #7dd3fc;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
    }

    /* Completeness Badges */
    .badge-complete {
        background-color: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-incomplete {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }

    /* Notice Box */
    .callout-box {
        background-color: #fff7ed;
        border-left: 4px solid #ea580c;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# 2. DATA INITIALIZATION & SESSION STATE
# -------------------------------------------------------------------------
@st.cache_data
def load_all_initial_data():
    return dl.load_baseline_data()

baseline_retail_df, nutrition_df, meals_df, wholesale_df = load_all_initial_data()

# Session State for User Uploaded Data
if "user_uploaded_df" not in st.session_state:
    st.session_state.user_uploaded_df = None
if "active_data_source" not in st.session_state:
    st.session_state.active_data_source = "Demonstration Data — Not Verified Official Prices"

# Determine active working retail dataset
if st.session_state.user_uploaded_df is not None:
    if st.session_state.active_data_source == "User Uploaded Only":
        active_retail_df = st.session_state.user_uploaded_df.copy()
    else:  # Merged
        active_retail_df = pd.concat([baseline_retail_df, st.session_state.user_uploaded_df], ignore_index=True)
else:
    active_retail_df = baseline_retail_df.copy()

kpis = calc.get_overview_kpis(active_retail_df)


# -------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & DATA SOURCE SELECTOR
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🇮🇳 PlatePrice India")
    st.markdown("Affordable Food & Nutrition Dashboard")
    st.markdown("---")

    nav_section = st.radio(
        "Navigation",
        [
            "🏠 1. India Overview",
            "🛒 2. Food Price Explorer",
            "🥗 3. Affordable Nutrition",
            "🍱 4. Budget Meal Calculator",
            "🌾 5. Wholesale Mandi Prices (AGMARKNET)",
            "📁 6. CSV Upload & Template",
            "📖 7. Data Quality & Sources"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📊 Active Dataset Tier")
    if st.session_state.user_uploaded_df is not None:
        st.markdown(f"<span class='badge-uploaded'>{st.session_state.active_data_source}</span>", unsafe_allow_html=True)
        st.caption(f"Includes {len(st.session_state.user_uploaded_df)} custom uploaded rows.")
    else:
        st.markdown("<span class='badge-demo'>Demonstration Data — Not Verified Official Prices</span>", unsafe_allow_html=True)
        st.caption("Illustrative demonstration benchmark data. Not verified official government observations.")

    st.markdown("---")
    st.markdown(f"**Centers Monitored:** {kpis['total_centers']}")
    st.markdown(f"**Commodities:** {kpis['total_commodities']}")
    st.markdown(f"**Latest Observation:** {kpis['latest_date']}")


# -------------------------------------------------------------------------
# SECTION A: INDIA OVERVIEW
# -------------------------------------------------------------------------
if nav_section.startswith("🏠"):
    st.markdown("""
    <div class="hero-india">
        <h1>🇮🇳 PlatePrice India: Food Prices & Nutrition</h1>
        <p>Tracking retail food price movements across Indian states, evaluating nutritious bargains, and calculating plate costs.</p>
    </div>
    """, unsafe_allow_html=True)

    # Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Reporting Centers</h3>
            <div class="kpi-value">{kpis['total_centers']}</div>
            <div class="kpi-sub">Across {kpis['total_states']} States & UTs</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Commodities</h3>
            <div class="kpi-value">{kpis['total_commodities']}</div>
            <div class="kpi-sub">Grains, Pulses, Oils, Veggies</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Observation Dates</h3>
            <div class="kpi-value">{len(kpis['dates'])} Dates</div>
            <div class="kpi-sub">{kpis['earliest_date']} to {kpis['latest_date']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Price Records</h3>
            <div class="kpi-value">{kpis['total_records']:,}</div>
            <div class="kpi-sub">Demonstration Records (₹ INR)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Latest Available Benchmark Prices Table
    st.subheader(f"📌 Latest Available Retail Prices ({kpis['latest_date']})")
    st.markdown("Sample demonstration retail prices from monitored centers (prices in ₹/kg or ₹/litre):")

    latest_sub = active_retail_df[active_retail_df["price_date"] == kpis["latest_date"]]
    pivot_latest = latest_sub.pivot_table(
        index="commodity",
        columns="center",
        values="retail_price",
        aggfunc="mean"
    )

    # Show first 5 major metro centers for clean display
    display_centers = [c for c in ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai", "Lucknow"] if c in pivot_latest.columns]
    if display_centers:
        st.dataframe(pivot_latest[display_centers].round(2).fillna("—"), use_container_width=True)
    else:
        st.dataframe(pivot_latest.round(2), use_container_width=True)

    # Recent Price Changes Section
    st.markdown("---")
    st.subheader("📈 Annual Price Changes (October 2025 vs. October 2026)")
    st.markdown("Recalculated price movement across Indian centers where historical observations exist:")

    changes_df = calc.calculate_price_changes(active_retail_df)
    if not changes_df.empty:
        chg_col1, chg_col2 = st.columns([1.3, 1.0])
        with chg_col1:
            st.dataframe(
                changes_df[["Center", "Commodity", "Unit", "Base Price (₹)", "Latest Price (₹)", "Absolute Change (₹)", "Price Change (%)"]].head(10),
                use_container_width=True,
                hide_index=True
            )
        with chg_col2:
            st.markdown("""
            **Key Inflation Insights:**
            - **Perishables Volatility:** Vegetables (**Onion** and **Potato**) show the highest price volatility (+35% to +60%) between post-monsoon cycles.
            - **Pulses (Dal):** Tur/Arhar dal experienced steady escalation (+12% to +16%), reflecting supply-demand shifts.
            - **Edible Oils:** Mustard oil and sunflower oil increased moderately (+8% to +10%).
            - **Staple Cereals:** Rice and wheat atta remained the most stable (+5% to +10%).
            """)

    st.markdown("""
    <div class="callout-box">
        <strong>Data Transparency & Verification Notice:</strong> The active baseline dataset consists of 
        <strong>Demonstration Data — Not Verified Official Prices</strong>. While modeled after the 
        Department of Consumer Affairs 22-commodity monitoring framework, these figures have not been traced 
        to verified government survey returns. Upload your own validated CSV in the <strong>CSV Upload</strong> 
        section to analyze real or official data.
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------------------------------
# SECTION B: FOOD PRICE EXPLORER
# -------------------------------------------------------------------------
elif nav_section.startswith("🛒"):
    st.subheader("🛒 Food Price Explorer")
    st.markdown("Filter, search, and compare retail prices across available Indian locations and commodities.")

    # Cascading Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        state_list = ["All States"] + kpis["states"]
        sel_state = st.selectbox("Select State / UT:", state_list, index=0)

    with f2:
        if sel_state != "All States":
            avail_centers = sorted(active_retail_df[active_retail_df["state"] == sel_state]["center"].unique().tolist())
        else:
            avail_centers = kpis["centers"]
        center_list = ["All Centers"] + avail_centers
        sel_center = st.selectbox("Select Reporting Center / Market:", center_list, index=0)

    with f3:
        if sel_center != "All Centers":
            avail_comms = sorted(active_retail_df[active_retail_df["center"] == sel_center]["commodity"].unique().tolist())
        elif sel_state != "All States":
            avail_comms = sorted(active_retail_df[active_retail_df["state"] == sel_state]["commodity"].unique().tolist())
        else:
            avail_comms = kpis["commodities"]
        comm_list = ["All Commodities"] + avail_comms
        sel_comm = st.selectbox("Select Commodity:", comm_list, index=0)

    with f4:
        date_list = ["All Dates"] + sorted(kpis["dates"], reverse=True)
        sel_date = st.selectbox("Select Observation Date:", date_list, index=1 if len(date_list) > 1 else 0)

    # Filtered Results
    filtered_df = calc.filter_price_data(active_retail_df, sel_state, sel_center, sel_comm, sel_date)

    st.markdown(f"**Found {len(filtered_df)} Matching Observation Records**")

    if filtered_df.empty:
        st.warning("No price records match the selected combination. Please adjust your filters.")
    else:
        st.dataframe(
            filtered_df[["state", "center", "commodity", "retail_price", "unit", "price_date", "market_type", "data_tier"]].rename(
                columns={
                    "state": "State", "center": "Center", "commodity": "Commodity",
                    "retail_price": "Retail Price (₹)", "unit": "Unit",
                    "price_date": "Date", "market_type": "Market Type", "data_tier": "Source Tier"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        # Cross-Center Bar Chart Comparison
        if sel_comm != "All Commodities" and sel_date != "All Dates":
            comm_sub = active_retail_df[(active_retail_df["commodity"] == sel_comm) & (active_retail_df["price_date"] == sel_date)]
            if not comm_sub.empty and len(comm_sub) > 1:
                st.markdown(f"#### Cross-Center Price Comparison for **{sel_comm}** ({sel_date})")
                fig, ax = plt.subplots(figsize=(10, 3.8))
                centers_plot = comm_sub["center"].str.replace(r"\(.*\)", "", regex=True).str.strip().tolist()
                prices_plot = comm_sub["retail_price"].tolist()
                unit_label = comm_sub["unit"].iloc[0]

                bars = ax.bar(centers_plot, prices_plot, color="#ea580c", edgecolor="#333333", width=0.55)
                ax.set_ylabel(f"Price ({unit_label})", fontsize=9)
                ax.set_title(f"{sel_comm} Retail Prices Across Monitored Centers", fontsize=10, fontweight="bold")
                ax.grid(axis="y", linestyle="--", alpha=0.5)
                plt.xticks(rotation=25, ha="right", fontsize=9)

                for bar in bars:
                    h = bar.get_height()
                    ax.annotate(f"₹{h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 3),
                                textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

                plt.tight_layout()
                st.pyplot(fig)


# -------------------------------------------------------------------------
# SECTION C: AFFORDABLE NUTRITION (IFCT 2017)
# -------------------------------------------------------------------------
elif nav_section.startswith("🥗"):
    st.subheader("🥗 Affordable Nutrition in India")
    st.markdown(
        "Evaluate which foods provide the most cost-effective **calories** and **dietary protein** "
        "by combining retail prices with the **Indian Food Composition Tables (IFCT 2017)** from ICMR-NIN."
    )

    n_c1, n_c2 = st.columns([1, 1])
    with n_c1:
        nutr_center = st.selectbox("Select Center / City:", ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai", "Lucknow", "Jaipur"], index=0)
    with n_c2:
        nutr_date = st.selectbox("Select Observation Date:", sorted(kpis["dates"], reverse=True), index=0)

    nutr_df, actual_nutr_date = calc.calculate_affordable_nutrition(active_retail_df, nutrition_df, center=nutr_center, observation_date=nutr_date)

    if nutr_df.empty:
        st.warning(f"No nutritional match available for **{nutr_center}** on **{nutr_date}**.")
    else:
        st.markdown(f"#### Nutritional Affordability Metrics: **{nutr_center}** ({actual_nutr_date})")

        st.dataframe(
            nutr_df[[
                "Commodity", "Retail Price", "Unit", "Cost per 100g (₹)", "Energy (kcal/100g)",
                "Protein (g/100g)", "Cost per 100 kcal (₹)", "Cost per 10g Protein (₹)", "Source Code"
            ]],
            use_container_width=True,
            hide_index=True
        )

        n_plot1, n_plot2 = st.columns(2)
        with n_plot1:
            st.markdown("##### ⚡ Cost per 100 kcal of Energy (Lower is cheaper)")
            fig_kcal, ax_kcal = plt.subplots(figsize=(6, 3.8))
            items_kcal = nutr_df["Commodity"].tolist()
            vals_kcal = [float(x) if x is not None else 0.0 for x in nutr_df["Cost per 100 kcal (₹)"]]

            bars_k = ax_kcal.bar(items_kcal, vals_kcal, color="#0284c7", edgecolor="#333333")
            ax_kcal.set_ylabel("₹ per 100 kcal", fontsize=9)
            ax_kcal.set_title(f"Energy Efficiency in {nutr_center}", fontsize=10, fontweight="bold")
            ax_kcal.grid(axis="y", linestyle="--", alpha=0.5)
            plt.xticks(rotation=35, ha="right", fontsize=8)
            for bar in bars_k:
                h = bar.get_height()
                ax_kcal.annotate(f"₹{h:.2f}", xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 2),
                                 textcoords="offset points", ha="center", va="bottom", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig_kcal)

        with n_plot2:
            st.markdown("##### 💪 Cost per 10g Dietary Protein (Lower is cheaper)")
            prot_sub = nutr_df.dropna(subset=["Cost per 10g Protein (₹)"]).copy()
            if not prot_sub.empty:
                fig_p, ax_p = plt.subplots(figsize=(6, 3.8))
                items_p = prot_sub["Commodity"].tolist()
                vals_p = [float(x) for x in prot_sub["Cost per 10g Protein (₹)"]]

                bars_p = ax_p.bar(items_p, vals_p, color="#ea580c", edgecolor="#333333")
                ax_p.set_ylabel("₹ per 10g Protein", fontsize=9)
                ax_p.set_title(f"Protein Efficiency in {nutr_center}", fontsize=10, fontweight="bold")
                ax_p.grid(axis="y", linestyle="--", alpha=0.5)
                plt.xticks(rotation=35, ha="right", fontsize=8)
                for bar in bars_p:
                    h = bar.get_height()
                    ax_p.annotate(f"₹{h:.2f}", xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 2),
                                  textcoords="offset points", ha="center", va="bottom", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig_p)

        st.info(
            "📌 **Dietary Education Notice:** Nutritional values are standardized laboratory reference estimates from the "
            "**Indian Food Composition Tables (IFCT 2017)** published by ICMR-NIN. Actual nutrient density in home cooking "
            "may vary depending on crop cultivars, soil conditions, polishes, and culinary preparation methods."
        )


# -------------------------------------------------------------------------
# SECTION D: BUDGET MEAL CALCULATOR (COMPLETENESS-AWARE)
# -------------------------------------------------------------------------
elif nav_section.startswith("🍱"):
    st.subheader("🍱 Budget Meal Calculator")
    st.markdown(
        "Estimate realistic ingredient and meal costs for common Indian student plates. "
        "**Strict Integrity Rule:** If any recipe ingredient is unpriced in the selected center, the meal is marked "
        "**`INCOMPLETE`** and its cost is marked **`UNREPORTED`** rather than treated as zero."
    )

    mc1, mc2, mc3 = st.columns([1, 1, 1])
    with mc1:
        sel_meal = st.selectbox(
            "Select Meal Recipe:",
            ["All Meals", "Veg Dal Rice Meal", "Veg Chole Rice Meal", "Egg Curry Rice Meal", "Chicken Rice Meal"]
        )
    with mc2:
        m_center = st.selectbox("Select Target Center / City:", ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai", "Lucknow"], index=0)
    with mc3:
        p_scale = st.slider("Plate Serving Size Multiplier:", min_value=0.5, max_value=2.5, value=1.0, step=0.25)

    meals_calc, obs_meal_date = calc.calculate_budget_meal_costs(
        meals_df, active_retail_df, center=m_center, meal_name=sel_meal, portion_multiplier=p_scale
    )

    st.markdown(f"#### Meal Plate Costs for **{m_center}** ({obs_meal_date}) — Serving Size: **{p_scale:.1f}x**")

    for m in meals_calc:
        with st.expander(f"🍽️ {m['Meal Name']} — {m['Formatted Cost']}", expanded=True):
            status_cls = "badge-complete" if m["Status"] == "COMPLETE" else "badge-incomplete"
            st.markdown(f"**Recipe Completeness:** <span class='{status_cls}'>{m['Status']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Priced Ingredients:** {m['Priced Ingredients Count']} of {m['Total Ingredients Count']}")
            st.markdown(f"*{m['Integrity Note']}*")

            # Ingredients Breakdown Table
            breakdown_df = pd.DataFrame(m["Breakdown"])
            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# SECTION E: WHOLESALE MANDI VS RETAIL (AGMARKNET)
# -------------------------------------------------------------------------
elif nav_section.startswith("🌾"):
    st.subheader("🌾 Wholesale Mandi Prices vs. Consumer Retail (AGMARKNET)")
    st.markdown(
        "Compare wholesale farmgate/mandi prices from agricultural APMCs with urban consumer retail prices. "
        "**Methodological Rule:** Wholesale mandi data is kept strictly distinct from retail price series."
    )
    st.caption("ℹ️ Wholesale figures shown are Demonstration Wholesale Data — Not Verified Official Prices, based on AGMARKNET reporting formats.")

    if wholesale_df.empty:
        st.info("No wholesale mandi data available.")
    else:
        w_center = st.selectbox("Select Mandi Center:", ["Delhi", "Mumbai", "Bengaluru"], index=0)
        spread_res = calc.compare_wholesale_vs_retail(wholesale_df, active_retail_df, center=w_center)

        if spread_res.empty:
            st.warning(f"No wholesale records available for {w_center}.")
        else:
            st.dataframe(spread_res, use_container_width=True, hide_index=True)

            st.markdown("""
            **Understanding the Wholesale-Retail Spread:**
            - **Wholesale Price:** The modal price at which agricultural produce changes hands in APMC mandis (e.g., Azadpur Mandi, Delhi).
            - **Retail Price:** The price paid by urban consumers at local retail stores or street vendors.
            - **Price Spread / Markup:** Accounts for transportation costs, packing, grading, transit wastage (10–20% in perishables like tomatoes), and retail distributor margins.
            """)


# -------------------------------------------------------------------------
# SECTION F: CSV UPLOAD & TEMPLATE DOWNLOAD
# -------------------------------------------------------------------------
elif nav_section.startswith("📁"):
    st.subheader("📁 CSV Data Upload & Template Generator")
    st.markdown(
        "Upload your own Indian retail food price CSV (such as daily DCA reports or local survey data) "
        "to update the dashboard instantly."
    )

    u_col1, u_col2 = st.columns([1.2, 1.0])

    with u_col1:
        st.markdown("#### Upload Custom Indian Food Price CSV")
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

        if uploaded_file is not None:
            is_valid, result = dl.validate_uploaded_csv(uploaded_file)
            if is_valid:
                st.session_state.user_uploaded_df = result
                st.success(f"Successfully loaded and validated {len(result)} records from '{uploaded_file.name}'!")

                mode_option = st.radio(
                    "Select Integration Mode:",
                    ["Merge with Baseline Demonstration Data", "View Uploaded Data Only"],
                    index=0
                )
                if mode_option == "Merge with Baseline Demonstration Data":
                    st.session_state.active_data_source = "Merged Demonstration + Uploaded"
                else:
                    st.session_state.active_data_source = "User Uploaded Data"
                st.rerun()
            else:
                st.error(f"Validation Error: {result}")

        if st.session_state.user_uploaded_df is not None:
            if st.button("🗑️ Reset to Baseline Demonstration Data"):
                st.session_state.user_uploaded_df = None
                st.session_state.active_data_source = "Demonstration Data — Not Verified Official Prices"
                st.rerun()

    with u_col2:
        st.markdown("#### Download Standard CSV Template")
        st.markdown(
            "Use this standardized template to format your data correctly. "
            "Required headers: `state`, `center`, `commodity`, `retail_price`, `unit`, `price_date`."
        )

        template_df = dl.get_sample_template()
        csv_bytes = template_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download Sample DCA CSV Template",
            data=csv_bytes,
            file_name="plateprice_india_sample_template.csv",
            mime="text/csv"
        )

        st.markdown("##### Template Preview:")
        st.dataframe(template_df.head(4), use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# SECTION G: DATA QUALITY & OFFICIAL SOURCES
# -------------------------------------------------------------------------
elif nav_section.startswith("📖"):
    st.subheader("📖 Data Quality, Verification Status & Official Sources")

    st.markdown("""
    ### Data Tiers & Verification Status
    - **Demonstration Data — Not Verified Official Prices:** The built-in baseline dataset is structured following the Department of Consumer Affairs (DCA) 22-commodity monitoring framework for educational demonstration. These records have **not** been individually verified against official government daily price returns and must not be cited as official figures.
    - **User Uploaded Data:** Any dataset uploaded by the user via the CSV Upload tool is tracked and tagged as "User Uploaded Data" and validated against strict schema and non-negative price rules.
    - **Wholesale Mandi Data:** Modeled from AGMARKNET APMC reporting formats and tagged as "Demonstration Wholesale Data — Not Verified Official Prices". Wholesale and retail price series are kept strictly segregated.

    ---

    ### Official Government of India Portals & Reference Standards
    1. **Department of Consumer Affairs (DCA) Price Monitoring Division:**
       - **Portal:** [https://fcainfoweb.nic.in/](https://fcainfoweb.nic.in/)
       - **Description:** Monitors daily retail and wholesale prices of 22 essential commodities across designated reporting centers throughout India.
       - **Access Mode:** Interactive ASP.NET WebForms portal with daily report generation. Because no unauthenticated REST API exists, live automated scraping is not implemented to prevent breakage; data is loaded via demonstration baseline records and user CSV uploads.
    2. **Open Government Data (OGD) Portal India:**
       - **Portal:** [https://data.gov.in/](https://data.gov.in/)
       - **Description:** Central repository for published government datasets.
    3. **AGMARKNET Portal (Directorate of Marketing & Inspection):**
       - **Portal:** [https://agmarknet.gov.in/](https://agmarknet.gov.in/)
       - **Description:** Daily wholesale prices and arrivals from registered APMC mandis across India.
    4. **Indian Food Composition Tables (IFCT 2017):**
       - **Institution:** National Institute of Nutrition (NIN) / Indian Council of Medical Research (ICMR).
       - **Citation:** Longvah, T., Ananthan, R., Bhaskarachary, K., & Venkaiah, K. (2017). *Indian Food Composition Tables*. Hyderabad: ICMR-NIN.

    ---

    ### Methodological Hygiene & Integrity Rules
    - **No Fabricated Verification:** Unverified demonstration records are explicitly labeled and never claimed to be verified official surveys.
    - **Wholesale vs. Retail Separation:** Mandi prices from AGMARKNET formats are kept strictly separate from retail consumer prices.
    - **Missing Price Handling:** If a recipe ingredient is missing from the active dataset, the meal cost is flagged as `UNREPORTED`. It is **never** treated as zero.
    """)

    st.caption("PlatePrice India — Developed for educational Python for Data Science demonstration.")
