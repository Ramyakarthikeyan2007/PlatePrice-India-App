"""
calculations.py - Core Analytical, Nutritional, and Meal Cost Logic for PlatePrice India
========================================================================================
PlatePrice India — Affordable Food & Nutrition Dashboard
All mathematical calculations, filtering, and completeness checks.
"""

import numpy as np
import pandas as pd


# -------------------------------------------------------------------------
# 1. OVERVIEW & KPI DERIVATION
# -------------------------------------------------------------------------
def get_overview_kpis(df):
    """Computes high-level counts, date ranges, and data-tier breakdowns."""
    if df.empty:
        return {
            "total_records": 0, "total_states": 0, "total_centers": 0,
            "total_commodities": 0, "latest_date": "N/A", "earliest_date": "N/A",
            "states": [], "centers": [], "commodities": [], "dates": [], "tiers": {}
        }

    dates = sorted(df["price_date"].unique().tolist())
    tiers = df["data_tier"].value_counts().to_dict() if "data_tier" in df.columns else {}

    return {
        "total_records": len(df),
        "total_states": df["state"].nunique(),
        "total_centers": df["center"].nunique(),
        "total_commodities": df["commodity"].nunique(),
        "latest_date": dates[-1] if dates else "N/A",
        "earliest_date": dates[0] if dates else "N/A",
        "states": sorted(df["state"].unique().tolist()),
        "centers": sorted(df["center"].unique().tolist()),
        "commodities": sorted(df["commodity"].unique().tolist()),
        "dates": dates,
        "tiers": tiers
    }


# -------------------------------------------------------------------------
# 2. FILTERING & PRICE VARIATION
# -------------------------------------------------------------------------
def filter_price_data(df, state=None, center=None, commodity=None, date=None):
    """
    Filters price data progressively.
    Ensures users only compare locations and commodities actually present.
    """
    sub = df.copy()
    if state and state != "All States":
        sub = sub[sub["state"] == state]
    if center and center != "All Centers":
        sub = sub[sub["center"] == center]
    if commodity and commodity != "All Commodities":
        sub = sub[sub["commodity"] == commodity]
    if date and date != "All Dates":
        sub = sub[sub["price_date"] == date]
    return sub


def calculate_price_changes(df, center=None, commodity=None):
    """
    Computes price changes across available historical dates for a commodity.
    Returns DataFrame with earliest price, latest price, absolute difference, and % change.
    """
    sub = df.copy()
    if center and center != "All Centers":
        sub = sub[sub["center"] == center]
    if commodity and commodity != "All Commodities":
        sub = sub[sub["commodity"] == commodity]

    results = []
    # Group by center, commodity, unit
    for (c_name, comm, unit), grp in sub.groupby(["center", "commodity", "unit"]):
        sorted_grp = grp.sort_values("price_date")
        if len(sorted_grp) < 2:
            continue
        p_early = float(sorted_grp["retail_price"].iloc[0])
        p_late = float(sorted_grp["retail_price"].iloc[-1])
        d_early = sorted_grp["price_date"].iloc[0]
        d_late = sorted_grp["price_date"].iloc[-1]
        abs_diff = p_late - p_early
        pct_change = (abs_diff / p_early) * 100.0 if p_early > 0 else 0.0

        results.append({
            "Center": c_name,
            "Commodity": comm,
            "Unit": unit,
            "Base Date": d_early,
            "Base Price (₹)": round(p_early, 2),
            "Latest Date": d_late,
            "Latest Price (₹)": round(p_late, 2),
            "Absolute Change (₹)": round(abs_diff, 2),
            "Price Change (%)": round(pct_change, 1)
        })

    return pd.DataFrame(results).sort_values("Price Change (%)", ascending=False)


# -------------------------------------------------------------------------
# 3. AFFORDABLE NUTRITION (IFCT 2017)
# -------------------------------------------------------------------------
# Maps Indian retail food commodities to IFCT 2017 food composition rows
COMMODITY_TO_IFCT_MAP = {
    "Rice": "Rice",
    "Wheat (Atta)": "Wheat Flour",
    "Tur / Arhar Dal": "Toor Dal",
    "Moong Dal": "Moong Dal",
    "Gram Dal (Chana)": "Chickpeas",
    "Urad Dal": "Toor Dal",               # Reference pulse equivalent
    "Mustard Oil": "Cooking Oil",
    "Sunflower Oil": "Cooking Oil",
    "Soya Oil": "Cooking Oil",
    "Potato": "Potato",
    "Onion": "Onion",
    "Tomato": "Tomato",
    "Milk (Packaged)": "Curd",            # Dairy nutritional baseline
    "Curd (Plain)": "Curd",
    "Egg": "Egg",
    "Chicken (Broiler)": "Chicken",
    "Spinach (Palak)": "Spinach",
    "Chickpeas (Chole)": "Chickpeas"
}

def calculate_affordable_nutrition(prices_df, nutrition_df, center="Delhi", observation_date="2026-10-01"):
    """
    Connects Indian food prices with official IFCT 2017 nutritional benchmarks.
    Computes:
    - Cost per 100g of edible food portion
    - Cost per 100 kcal of dietary energy
    - Cost per 10g of dietary protein
    """
    sub_prices = prices_df[
        (prices_df["center"].str.contains(center, case=False, na=False)) &
        (prices_df["price_date"] == observation_date)
    ]
    if sub_prices.empty:
        # Fallback to latest date for that center
        center_matches = prices_df[prices_df["center"].str.contains(center, case=False, na=False)]
        if not center_matches.empty:
            observation_date = center_matches["price_date"].max()
            sub_prices = center_matches[center_matches["price_date"] == observation_date]
        else:
            return pd.DataFrame(), observation_date

    results = []
    for _, prow in sub_prices.iterrows():
        comm = prow["commodity"]
        nutr_name = COMMODITY_TO_IFCT_MAP.get(comm)
        if not nutr_name:
            continue

        n_matches = nutrition_df[nutrition_df["food_item"] == nutr_name]
        if n_matches.empty:
            continue
        nrow = n_matches.iloc[0]

        price_val = float(prow["retail_price"])
        unit_str = prow["unit"]

        # Unit scaling: convert to price per 100g edible portion
        # If ₹/kg -> 1000g, price_100g = price / 10
        # If ₹/litre -> ~1000ml (density approx 0.9-1.0), price_100g = price / 10
        # If ₹/dozen -> 12 eggs (~600g, 50g each), price_100g = (price / 12) * 2 = price / 6
        if "dozen" in unit_str.lower():
            cost_100g = price_val / 6.0
        else:
            cost_100g = price_val / 10.0

        kcal = float(nrow["calories_per_100g"])
        prot = float(nrow["protein_g_per_100g"])
        carb = float(nrow.get("carbohydrates_g_per_100g", 0.0))
        fat = float(nrow.get("fat_g_per_100g", 0.0))
        fibre = float(nrow.get("fibre_g_per_100g", 0.0))

        cost_100_kcal = (cost_100g / kcal) * 100.0 if kcal > 0 else np.nan
        cost_10g_prot = (cost_100g / prot) * 10.0 if prot > 0 else np.nan

        results.append({
            "Commodity": comm,
            "Nutritional Reference": nutr_name,
            "Retail Price": price_val,
            "Unit": unit_str,
            "Cost per 100g (₹)": round(cost_100g, 2),
            "Energy (kcal/100g)": kcal,
            "Protein (g/100g)": prot,
            "Carbohydrates (g/100g)": carb,
            "Fat (g/100g)": fat,
            "Dietary Fibre (g/100g)": fibre,
            "Cost per 100 kcal (₹)": round(cost_100_kcal, 2) if pd.notna(cost_100_kcal) else None,
            "Cost per 10g Protein (₹)": round(cost_10g_prot, 2) if pd.notna(cost_10g_prot) else None,
            "Source Code": nrow.get("source_code", "IFCT 2017")
        })

    return pd.DataFrame(results), observation_date


# -------------------------------------------------------------------------
# 4. BUDGET MEAL CALCULATOR (COMPLETENESS-AWARE)
# -------------------------------------------------------------------------
RECIPE_TO_PRICE_COMMODITY_MAP = {
    "Rice": "Rice",
    "Toor Dal": "Tur / Arhar Dal",
    "Moong Dal": "Moong Dal",
    "Chickpeas": "Chickpeas (Chole)",
    "Potato": "Potato",
    "Onion": "Onion",
    "Tomato": "Tomato",
    "Spinach": "Spinach (Palak)",
    "Cooking Oil": "Mustard Oil",
    "Curd": "Curd (Plain)",
    "Egg": "Egg",
    "Chicken": "Chicken (Broiler)"
}

def calculate_budget_meal_costs(meals_df, prices_df, center="Delhi", observation_date="2026-10-01", meal_name=None, portion_multiplier=1.0):
    """
    Computes exact ingredient and meal cost for standard Indian student plates.
    
    INTEGRITY RULE:
    If any recipe ingredient lacks an authentic retail price, the meal is marked
    as 'INCOMPLETE'. Missing costs are NEVER treated as zero.
    """
    sub_prices = prices_df[
        (prices_df["center"].str.contains(center, case=False, na=False)) &
        (prices_df["price_date"] == observation_date)
    ]
    if sub_prices.empty:
        center_matches = prices_df[prices_df["center"].str.contains(center, case=False, na=False)]
        if not center_matches.empty:
            observation_date = center_matches["price_date"].max()
            sub_prices = center_matches[center_matches["price_date"] == observation_date]

    # Create price lookup dictionary
    price_dict = {}
    unit_dict = {}
    for _, r in sub_prices.iterrows():
        price_dict[r["commodity"]] = float(r["retail_price"])
        unit_dict[r["commodity"]] = r["unit"]

    filtered_meals = meals_df.copy()
    if meal_name and meal_name != "All Meals":
        filtered_meals = filtered_meals[filtered_meals["meal_name"] == meal_name]

    meal_summaries = []
    for m_name, group in filtered_meals.groupby("meal_name"):
        total_meal_cost = 0.0
        missing_items = []
        priced_items = []
        ingredient_breakdown = []

        for _, ing_row in group.iterrows():
            item = ing_row["food_item"]
            raw_qty_g = float(ing_row["quantity_g"]) * portion_multiplier
            matched_comm = RECIPE_TO_PRICE_COMMODITY_MAP.get(item)

            if matched_comm and matched_comm in price_dict:
                price_unit = price_dict[matched_comm]
                u_str = unit_dict.get(matched_comm, "₹/kg")

                # Unit conversion for costing
                # If ₹/dozen -> 1 egg is ~50g; 12 eggs = 600g. Cost per gram = price / 600.
                if "dozen" in u_str.lower():
                    cost = raw_qty_g * (price_unit / 600.0)
                else:
                    # ₹/kg or ₹/litre -> cost per gram = price / 1000
                    cost = (raw_qty_g / 1000.0) * price_unit

                total_meal_cost += cost
                priced_items.append(item)
                ingredient_breakdown.append({
                    "Ingredient": item,
                    "Matched Commodity": matched_comm,
                    "Portion Quantity": f"{raw_qty_g:.1f} g",
                    "Retail Price": f"₹{price_unit:.2f} ({u_str})",
                    "Ingredient Cost": round(cost, 2),
                    "Status": "Priced"
                })
            else:
                missing_items.append(item)
                ingredient_breakdown.append({
                    "Ingredient": item,
                    "Matched Commodity": matched_comm or "Untracked",
                    "Portion Quantity": f"{raw_qty_g:.1f} g",
                    "Retail Price": "Unpriced in center",
                    "Ingredient Cost": None,
                    "Status": "MISSING"
                })

        is_complete = (len(missing_items) == 0)

        meal_summaries.append({
            "Meal Name": m_name,
            "Center": center,
            "Observation Date": observation_date,
            "Portion Multiplier": f"{portion_multiplier:.1f}x",
            "Status": "COMPLETE" if is_complete else "INCOMPLETE",
            "Calculated Cost (₹)": round(total_meal_cost, 2) if is_complete else None,
            "Formatted Cost": f"₹{total_meal_cost:.2f}" if is_complete else "UNREPORTED (Incomplete Recipe)",
            "Priced Ingredients Count": len(priced_items),
            "Total Ingredients Count": len(group),
            "Missing Ingredients": ", ".join(missing_items) if missing_items else "None",
            "Breakdown": ingredient_breakdown,
            "Integrity Note": "All ingredients fully priced." if is_complete else f"Missing prices for {len(missing_items)} ingredients ({', '.join(missing_items)}). Missing costs are NOT estimated as zero."
        })

    return meal_summaries, observation_date


# -------------------------------------------------------------------------
# 5. WHOLESALE MANDI VS RETAIL SPREAD (AGMARKNET)
# -------------------------------------------------------------------------
def compare_wholesale_vs_retail(wholesale_df, retail_df, center="Delhi", price_date="2026-10-01"):
    """
    Compares wholesale mandi modal price with consumer retail price.
    Calculates the wholesale-to-retail price spread and percentage markup.
    """
    if wholesale_df.empty or retail_df.empty:
        return pd.DataFrame()

    sub_w = wholesale_df[
        (wholesale_df["center"].str.contains(center, case=False, na=False)) &
        (wholesale_df["price_date"] == price_date)
    ]
    sub_r = retail_df[
        (retail_df["center"].str.contains(center, case=False, na=False)) &
        (retail_df["price_date"] == price_date)
    ]

    spread_rows = []
    for _, w_row in sub_w.iterrows():
        comm = w_row["commodity"]
        r_matches = sub_r[sub_r["commodity"] == comm]
        if r_matches.empty:
            continue

        r_price = float(r_matches["retail_price"].iloc[0])
        w_price_kg = float(w_row["wholesale_price_kg"])
        w_price_quintal = float(w_row["wholesale_price_quintal"])
        spread_rs = r_price - w_price_kg
        markup_pct = (spread_rs / w_price_kg) * 100.0 if w_price_kg > 0 else 0.0

        spread_rows.append({
            "Center": center,
            "Mandi Name": w_row["mandi_name"],
            "Commodity": comm,
            "Wholesale (₹/quintal)": f"₹{w_price_quintal:,.0f}",
            "Wholesale (₹/kg)": round(w_price_kg, 2),
            "Retail Price (₹/kg)": round(r_price, 2),
            "Retail Spread (₹/kg)": round(spread_rs, 2),
            "Retail Markup (%)": round(markup_pct, 1),
            "Observation Date": price_date
        })

    return pd.DataFrame(spread_rows)
