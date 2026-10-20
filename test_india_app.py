"""
test_india_app.py - Automated Test Suite for PlatePrice India Dashboard
========================================================================
Tests:
1. Baseline dataset ingestion and schema verification
2. Filter logic and cascading constraints
3. Historical price changes calculation
4. Affordable nutrition derivations (IFCT 2017)
5. Meal costing with completeness safety checks
6. Wholesale vs retail price spread
7. CSV upload validator and template generation
"""

import sys
import io
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

import data_loader as dl
import calculations as calc
import pandas as pd


def run_all_tests():
    print("=" * 70)
    print("RUNNING PLATEPRICE INDIA AUTOMATED TEST SUITE")
    print("=" * 70)

    # Test 1: Load baseline datasets
    retail_df, nutr_df, meals_df, wholesale_df = dl.load_baseline_data()
    assert len(retail_df) > 0, "Failed: Retail dataset is empty!"
    assert len(nutr_df) > 0, "Failed: Nutrition dataset is empty!"
    assert len(meals_df) > 0, "Failed: Meals dataset is empty!"
    assert len(wholesale_df) > 0, "Failed: Wholesale dataset is empty!"
    print(f"[PASS] Test 1: Baseline datasets loaded successfully.")
    print(f"       Retail Rows: {len(retail_df)}, Nutrition Rows: {len(nutr_df)}, Meals Rows: {len(meals_df)}, Wholesale Rows: {len(wholesale_df)}")

    # Test 2: KPI metrics
    kpis = calc.get_overview_kpis(retail_df)
    assert kpis["total_states"] >= 8, f"Expected at least 8 states, got {kpis['total_states']}"
    assert kpis["total_centers"] >= 10, f"Expected at least 10 centers, got {kpis['total_centers']}"
    assert kpis["total_commodities"] >= 20, f"Expected at least 20 commodities, got {kpis['total_commodities']}"
    assert "2026-10-01" in kpis["dates"]
    print(f"[PASS] Test 2: KPI summary metrics verified ({kpis['total_commodities']} commodities across {kpis['total_centers']} centers).")

    # Test 3: Filter logic
    delhi_rice = calc.filter_price_data(retail_df, state="Delhi", center="Delhi", commodity="Rice", date="2026-10-01")
    assert not delhi_rice.empty, "Failed: Delhi Rice filter returned empty!"
    p_val = float(delhi_rice["retail_price"].iloc[0])
    assert p_val == 42.0, f"Expected Delhi Rice price to be 42.0, got {p_val}"
    print(f"[PASS] Test 3: Filter logic verified (Delhi Rice on 2026-10-01: ₹{p_val}/kg).")

    # Test 4: Historical price change calculation
    changes_df = calc.calculate_price_changes(retail_df, center="Delhi", commodity="Potato")
    assert not changes_df.empty, "Failed: Price change calculation returned empty!"
    chg_row = changes_df.iloc[0]
    # In Delhi Potato: 2025-10-01 (18.0) -> 2026-10-01 (28.0) = +10.0 Rs (+55.6%)
    assert chg_row["Base Price (₹)"] > 0 and chg_row["Latest Price (₹)"] > 0
    print(f"[PASS] Test 4: Price change calculation verified (Delhi Potato: ₹{chg_row['Base Price (₹)']} -> ₹{chg_row['Latest Price (₹)']} [{chg_row['Price Change (%)']}%]).")

    # Test 5: Affordable nutrition derivation
    nutr_res, _ = calc.calculate_affordable_nutrition(retail_df, nutr_df, center="Delhi", observation_date="2026-10-01")
    assert not nutr_res.empty, "Failed: Nutrition calculation returned empty!"
    # Verify Rice cost per 100 kcal in Delhi (Price = ₹42/kg -> Cost/100g = ₹4.20 -> Cost/100 kcal = (4.20 / 356) * 100 = 1.18 Rs)
    rice_nutr = nutr_res[nutr_res["Commodity"] == "Rice"].iloc[0]
    expected_c_100k = round((4.20 / 356.0) * 100.0, 2)
    assert rice_nutr["Cost per 100 kcal (₹)"] == expected_c_100k, f"Expected {expected_c_100k}, got {rice_nutr['Cost per 100 kcal (₹)']}"
    print(f"[PASS] Test 5: Affordable nutrition calculations verified (Delhi Rice: ₹{rice_nutr['Cost per 100 kcal (₹)']} per 100 kcal).")

    # Test 6: Budget meal calculator with completeness safety
    # Test Delhi where all ingredients for Veg Dal Rice Meal (Rice, Tur Dal, Onion, Tomato, Spinach, Mustard Oil, Curd) exist
    meals_delhi, _ = calc.calculate_budget_meal_costs(meals_df, retail_df, center="Delhi", observation_date="2026-10-01")
    assert len(meals_delhi) == 4, f"Expected 4 meals, got {len(meals_delhi)}"
    veg_dal = next(m for m in meals_delhi if m["Meal Name"] == "Veg Dal Rice Meal")
    assert veg_dal["Status"] == "COMPLETE", f"Expected Veg Dal Rice Meal to be COMPLETE in Delhi, got {veg_dal['Status']}"
    assert veg_dal["Calculated Cost (₹)"] > 0, "Cost must be strictly positive"
    print(f"[PASS] Test 6A: Complete meal cost calculated (Delhi Veg Dal Rice Meal: ₹{veg_dal['Calculated Cost (₹)']}).")

    # Test incomplete meal detection: simulate unpriced ingredient
    test_empty_prices = pd.DataFrame(columns=["center", "commodity", "retail_price", "unit", "price_date"])
    meals_incomplete, _ = calc.calculate_budget_meal_costs(meals_df, test_empty_prices, center="SimulatedCenter", observation_date="2026-10-01")
    for m in meals_incomplete:
        assert m["Status"] == "INCOMPLETE", "Meal must be flagged INCOMPLETE when ingredients are unpriced!"
        assert m["Calculated Cost (₹)"] is None, "Cost must be None for incomplete meal!"
        assert "UNREPORTED" in m["Formatted Cost"]
    print(f"[PASS] Test 6B: Incomplete meal safety rule strictly enforced (missing costs are NEVER treated as zero).")

    # Test 7: Wholesale mandi vs retail spread
    spread_df = calc.compare_wholesale_vs_retail(wholesale_df, retail_df, center="Delhi", price_date="2026-10-01")
    assert not spread_df.empty, "Failed: Wholesale comparison returned empty!"
    assert "Retail Spread (₹/kg)" in spread_df.columns
    print(f"[PASS] Test 7: Wholesale vs retail spread verified ({len(spread_df)} mandi comparisons).")

    # Test 8: CSV upload validation
    valid_csv_text = "state,center,commodity,retail_price,unit,price_date\nDelhi,Delhi,Rice,45.0,₹/kg,2026-10-01\n"
    is_valid, parsed_df = dl.validate_uploaded_csv(io.StringIO(valid_csv_text))
    assert is_valid is True, f"Valid CSV rejected: {parsed_df}"
    assert len(parsed_df) == 1
    assert parsed_df["data_tier"].iloc[0] == "User Uploaded Data"

    # Test invalid CSV (negative price)
    bad_csv_text = "state,center,commodity,retail_price,unit,price_date\nDelhi,Delhi,Rice,-10.0,₹/kg,2026-10-01\n"
    is_valid_bad, err_msg = dl.validate_uploaded_csv(io.StringIO(bad_csv_text))
    assert is_valid_bad is False, "Failed: Negative price was not rejected!"
    print(f"[PASS] Test 8: CSV upload validator correctly accepts valid files and rejects invalid/negative prices.")

    # Test 9: Data Transparency and Source Classification Integrity
    # Verify baseline records are explicitly classified as demonstration data
    assert (retail_df["data_tier"] == "Demonstration Data — Not Verified Official Prices").all(), \
        "Failed: Retail baseline rows must be labeled 'Demonstration Data — Not Verified Official Prices'!"
    assert not (retail_df["data_tier"] == "Official Baseline Data").any(), \
        "Failed: Retail baseline rows must NEVER be labeled 'Official Baseline Data' without verification!"
    assert (wholesale_df["data_tier"] == "Demonstration Wholesale Data — Not Verified Official Prices").all(), \
        "Failed: Wholesale rows must be labeled 'Demonstration Wholesale Data — Not Verified Official Prices'!"
    # Verify strict segregation: wholesale records have mandi_name and wholesale_price_kg; retail records do not
    assert "wholesale_price_kg" not in retail_df.columns, "Failed: Retail CSV must not mix wholesale columns!"
    assert "mandi_name" not in retail_df.columns, "Failed: Retail CSV must not mix mandi names!"
    print("[PASS] Test 9: Data transparency, source classification, and wholesale segregation verified.")

    print("\nALL 9 AUTOMATED TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_all_tests()
