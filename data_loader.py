"""
data_loader.py - Data Ingestion, CSV Upload Validation, and Template Exporter
=============================================================================
PlatePrice India: Affordable Food & Nutrition Dashboard
Handles relative paths on Windows/Linux and enforces strict schema validation.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np


def resolve_file(filename, search_dirs=None):
    """Locates dataset files dynamically across various launch directories."""
    base_dir = Path(__file__).resolve().parent
    if search_dirs is None:
        search_dirs = [
            base_dir / "data",
            base_dir,
            Path("data"),
            Path("PlatePrice/PlatePrice_India_App/data"),
            Path("PlatePrice_India_App/data")
        ]
    for d in search_dirs:
        candidate = Path(d) / filename
        if candidate.exists():
            return candidate.resolve()
    cur = Path(filename)
    if cur.exists():
        return cur.resolve()
    raise FileNotFoundError(f"Could not locate '{filename}' in candidate paths: {search_dirs}")


def load_baseline_data():
    """
    Loads official baseline Indian retail food prices, nutrition benchmarks,
    student meal ingredients, and wholesale mandi benchmarks.
    """
    retail_path = resolve_file("indian_retail_food_prices.csv")
    nutr_path = resolve_file("food_nutrition.csv")
    meals_path = resolve_file("indian_meal_ingredients.csv")
    wholesale_path = resolve_file("wholesale_mandi_prices.csv")

    retail_df = pd.read_csv(retail_path)
    nutr_df = pd.read_csv(nutr_path)
    meals_df = pd.read_csv(meals_path)
    wholesale_df = pd.read_csv(wholesale_path) if Path(wholesale_path).exists() else pd.DataFrame()

    # Enforce date string formatting
    retail_df["price_date"] = pd.to_datetime(retail_df["price_date"]).dt.strftime("%Y-%m-%d")

    return retail_df, nutr_df, meals_df, wholesale_df


REQUIRED_COLUMNS = ["state", "center", "commodity", "retail_price", "unit", "price_date"]

def validate_uploaded_csv(uploaded_file):
    """
    Validates an uploaded user CSV file.
    Returns: (is_valid, dataframe_or_error_message)
    """
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        return False, f"Failed to parse CSV file: {e}"

    # Check required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, f"Missing required columns in CSV: {', '.join(missing_cols)}. Please match the template structure."

    # Validate price values
    try:
        df["retail_price"] = pd.to_numeric(df["retail_price"], errors="coerce")
    except Exception as e:
        return False, f"Error converting retail_price to numeric: {e}"

    if df["retail_price"].isnull().any():
        return False, "CSV contains invalid or non-numeric values in 'retail_price'."

    if (df["retail_price"] <= 0).any():
        return False, "CSV contains negative or zero prices. All prices must be strictly positive (> 0)."

    # Validate dates
    try:
        df["price_date"] = pd.to_datetime(df["price_date"]).dt.strftime("%Y-%m-%d")
    except Exception as e:
        return False, f"Invalid date format in 'price_date': {e}. Use YYYY-MM-DD format."

    # Standardize metadata columns if missing
    if "source" not in df.columns:
        df["source"] = "User Uploaded CSV"
    if "data_tier" not in df.columns:
        df["data_tier"] = "User Uploaded Data"
    if "zone" not in df.columns:
        df["zone"] = "User Specified"
    if "market_type" not in df.columns:
        df["market_type"] = "Uploaded Market"

    return True, df


def get_sample_template():
    """Returns the sample CSV template as a DataFrame."""
    try:
        t_path = resolve_file("sample_dca_template.csv")
        return pd.read_csv(t_path)
    except Exception:
        # Fallback dictionary
        return pd.DataFrame([
            {"state": "Delhi", "center": "Delhi", "commodity": "Rice", "retail_price": 42.0, "unit": "₹/kg", "price_date": "2026-10-01", "zone": "North", "market_type": "DCA Reporting Center", "source": "User Uploaded DCA Report", "data_tier": "User Uploaded Data"},
            {"state": "Maharashtra", "center": "Mumbai", "commodity": "Tur / Arhar Dal", "retail_price": 159.0, "unit": "₹/kg", "price_date": "2026-10-01", "zone": "West", "market_type": "DCA Reporting Center", "source": "User Uploaded DCA Report", "data_tier": "User Uploaded Data"}
        ])
