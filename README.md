# PlatePrice India — Affordable Food & Nutrition Dashboard

An interactive, India-focused Python data application built with **Streamlit** to analyse domestic retail food prices, track inflation trends across official reporting centers, evaluate nutritional affordability using official ICMR-NIN Indian Food Composition Tables (IFCT 2017), and estimate student budget meal costs with strict data-integrity rules.

---

## 📌 Project Overview

**PlatePrice India** is tailored specifically for the Indian food economy. It bridges consumer price monitoring and public nutrition by answering key questions:
- *How do retail prices of essential food items differ across Indian metropolitan centers and states?*
- *Which foods deliver the highest caloric and protein density per rupee spent (₹/100 kcal, ₹/10g protein)?*
- *What is the actual wholesale-to-retail markup between APMC Mandis (AGMARKNET) and city retail stores?*
- *How much does a nutritious student meal cost, and how can we safeguard meal budgets against incomplete or missing price data?*

---

## 🏗️ Directory Structure

```text
PlatePrice_India_App/
├── .streamlit/
│   └── config.toml               # Saffron/orange & slate white dashboard theme
├── assets/                       # UI assets and logos
├── data/
│   ├── indian_retail_food_prices.csv  # 745 retail price observations (DCA framework)
│   ├── food_nutrition.csv             # 15 staple foods with IFCT 2017 (ICMR-NIN) codes
│   ├── indian_meal_ingredients.csv    # 26 recipe ingredients across 4 student meals
│   ├── wholesale_mandi_prices.csv     # AGMARKNET APMC wholesale benchmark prices
│   └── sample_dca_template.csv        # Downloadable template for custom CSV uploads
├── app.py                        # Streamlit multi-view dashboard application
├── calculations.py               # Pure-Python analytics, filters, and meal costing engine
├── data_loader.py                # Safe relative path loader & upload validator
├── test_india_app.py             # 9-point automated test suite with data transparency checks
├── requirements.txt              # Minimal project dependencies
├── .gitignore                    # Clean Git exclusion rules
└── README.md                     # Complete project documentation
```

---

## 🏛️ Official Data Sources & Technical Status

| Domain | Official Authority | Portal / Reference | Integration Status |
| :--- | :--- | :--- | :--- |
| **Retail Food Prices** | Department of Consumer Affairs (DCA), Ministry of Consumer Affairs, Food & Public Distribution | [Price Monitoring Division (PMD)](https://fcainfoweb.nic.in/) | **Demonstration Baseline + CSV Upload**: The DCA web portal uses stateful ASP.NET WebForms (`__VIEWSTATE`, session postbacks) without an open REST API. To prevent fragile scraping, the app includes a demonstration baseline dataset modeled on the DCA 22-commodity framework, explicitly labeled as **Demonstration Data — Not Verified Official Prices**, along with a strict CSV upload validator for actual user data. |
| **Wholesale Mandi Prices** | Directorate of Marketing & Inspection (DMI), Ministry of Agriculture & Farmers Welfare | [AGMARKNET](https://agmarknet.gov.in/) | **APMC Benchmark Spread**: Wholesale prices from Azadpur (Delhi), Vashi (Mumbai), and Yeshwanthpur (Bengaluru) are labeled as demonstration wholesale benchmarks and are strictly segregated from retail figures. |
| **Food Composition & Nutrition** | ICMR - National Institute of Nutrition (NIN), Hyderabad | *Indian Food Composition Tables (IFCT 2017)* | **Direct IFCT Codes**: Standardized laboratory reference estimates for energy (kcal), protein (g), carbohydrates, fats, and dietary fiber per 100g edible portion. |

---

## 🚀 Key Dashboard Features

### 1. 🇮🇳 India Overview
- Live headline metric cards displaying total centers monitored, commodities tracked, latest observation date, and average staple price.
- Top commodity price changes over time with directional indicators.

### 2. 🔍 Food Price Explorer
- Cascading filters by **State**, **Center / District**, **Market Type** (DCA Official Center vs. Retail Store), and **Commodity**.
- Side-by-side center comparison bar charts and historical price trend lines.
- Complete prices displayed in official Indian units (**₹/kg**, **₹/litre**, **₹/dozen**).

### 3. 🥗 Affordable Nutrition
- Calculates cost efficiency metrics:
  - **Cost per 100 kcal (₹)**: Measures economic energy density.
  - **Cost per 10g Protein (₹)**: Identifies the most cost-effective protein sources (e.g., Gram Dal, Soya Chunks, Eggs).
- Nutrition-to-Price bubble and scatter charts.
- Disclaimers explaining reference estimates from IFCT 2017 and preparation variations.

### 4. 🍲 Budget Meal Calculator
- Cost estimator for common student meals (*Dal Tadka & Rice*, *Aloo Gobi & Roti*, *Egg Curry & Rice*, *Palak Paneer & Roti*).
- Interactive portion and serving size scalers.
- **Strict Data-Integrity Rule**: If any ingredient price is unavailable in a chosen center, the meal is marked **`⚠️ INCOMPLETE`** and the missing cost is never assumed to be zero.

### 5. ⚖️ Wholesale vs. Retail Spread
- Compares farmgate/mandi prices from AGMARKNET with consumer retail shelf prices.
- Computes wholesale-to-retail margin percentages to reveal urban distribution markups.

### 6. 📋 Data Quality & Custom CSV Upload
- Displays null-value counts, date coverage, and reporting center health metrics.
- Built-in **CSV Upload Engine**: Users can upload fresh DCA price files. Uploaded files are strictly validated against required column schemas and valid numeric price bounds before being rendered.
- **One-click Download Template**: Download `sample_dca_template.csv` to format new daily DCA reports easily.

---

## 💻 Setup & Installation on Windows

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- PowerShell or Windows Command Prompt

### Step 1: Navigate to the Application Directory
```powershell
cd C:\Users\ramya\OneDrive\Documents\plateprice\PlatePrice\PlatePrice_India_App
```

### Step 2: Install Required Packages
```powershell
pip install -r requirements.txt
```
*(Dependencies: `streamlit`, `pandas`, `numpy`, `matplotlib`)*

### Step 3: Run the Automated Verification Tests
```powershell
python test_india_app.py
```
*Confirms that all 9 core data loading, calculation, safety validation, and data transparency tests pass.*

### Step 4: Launch the Streamlit Dashboard
```powershell
streamlit run app.py
```
The application will automatically open in your default browser at `http://localhost:8501`.

---

## 🛡️ Data Transparency & Academic Integrity

- **Explicit Demonstration Labeling**: Baseline prices are explicitly labeled **Demonstration Data — Not Verified Official Prices** because individual records cannot be traced to verified government field returns.
- **Separation of Wholesale and Retail**: Wholesale APMC mandi quotes (in quintals/kg) are strictly segregated from retail consumer prices.
- **Nutritional Reference Estimates**: Nutrient values are labeled as laboratory reference estimates from ICMR-NIN IFCT 2017.
- **Safe Missing Price Handling**: Incomplete recipes are flagged and never assigned a zero price.
- **Preservation of Existing Work**: All files from the original international `PlatePrice` project remain completely intact in their original directories.

---

## 📜 References
1. **Department of Consumer Affairs (DCA)**, *Daily Retail Prices of Essential Commodities*, Government of India. [https://fcainfoweb.nic.in/](https://fcainfoweb.nic.in/)
2. **National Institute of Nutrition (ICMR-NIN)**, *Indian Food Composition Tables (IFCT 2017)*, Hyderabad, India.
3. **Directorate of Marketing & Inspection (DMI)**, *AGMARKNET Mandi Price Bulletin*, Ministry of Agriculture & Farmers Welfare. [https://agmarknet.gov.in/](https://agmarknet.gov.in/)
