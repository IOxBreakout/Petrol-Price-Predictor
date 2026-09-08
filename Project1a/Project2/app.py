import calendar
from datetime import datetime
import os
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Chicken Buying Assistant",
    page_icon="🐔",
    layout="wide",
)

# --- 2. PATHS & ASSET LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "agbro_multan_prices_2015_2026_hijri.csv"
)
MODEL_3D_PATH = os.path.join(BASE_DIR, "Model_3D.pkl")
MODEL_7D_PATH = os.path.join(BASE_DIR, "Model_7D.pkl")
META_PATH = os.path.join(BASE_DIR, "model_meta_direct.pkl")


@st.cache_resource
def load_assets():
    """Loads models, metadata, and reads actual Agbro price dataset."""
    if (
        not os.path.exists(MODEL_3D_PATH)
        or not os.path.exists(MODEL_7D_PATH)
        or not os.path.exists(META_PATH)
    ):
        st.error(
            "Model files missing! Please run train_model.py first to generate direct models."
        )
        st.stop()

    m3d = joblib.load(MODEL_3D_PATH)
    m7d = joblib.load(MODEL_7D_PATH)
    meta = joblib.load(META_PATH)

    if not os.path.exists(DATA_PATH):
        st.error(f"Dataset missing at {DATA_PATH}. Please check file path.")
        st.stop()

    df_hist = pd.read_csv(DATA_PATH)
    df_hist.columns = df_hist.columns.str.strip()

    col_map = {
        "Farm Rate": "Farm_Rate",
        "Farm_Price": "Farm_Rate",
        "Rate": "Farm_Rate",
        "Rates": "Farm_Rate",
        "Price": "Farm_Rate",
        "Broiler_Rate": "Farm_Rate",
        "Broiler Rate": "Farm_Rate",
        "DOC Rate": "Multan_DOC_Rate",
        "DOC_Rate": "Multan_DOC_Rate",
        "DOC": "Multan_DOC_Rate",
        "Hijri Day": "Hijri_Day",
        "Hijri Month": "Hijri_Month",
    }
    df_hist = df_hist.rename(columns=col_map)

    if "Farm_Rate" not in df_hist.columns:
        for col in df_hist.columns:
            if any(
                k in col.lower() for k in ["rate", "price", "farm", "broiler"]
            ) and ("doc" not in col.lower()):
                df_hist = df_hist.rename(columns={col: "Farm_Rate"})
                break

    date_col = next(
        (col for col in df_hist.columns if "date" in col.lower()),
        df_hist.columns[0],
    )
    df_hist["Date"] = pd.to_datetime(
        df_hist[date_col], format="mixed", dayfirst=True, errors="coerce"
    )
    df_hist = (
        df_hist.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    )

    return m3d, m7d, meta["feature_cols"], meta["baselines"], df_hist


model_3d, model_7d, feature_cols, baselines, df_hist = load_assets()

HIJRI_MAP = {
    1: "Muharram",
    2: "Safar",
    3: "Rabi Al-Awwal",
    4: "Rabi Al-Thani",
    5: "Jumada Al-Awwal",
    6: "Jumada Al-Thani",
    7: "Rajab",
    8: "Shaban",
    9: "Ramadan",
    10: "Shawwal",
    11: "Dhul Qadah",
    12: "Dhul Hijjah",
}

# --- 3. SIDEBAR CONTROLS ---
st.title("🐔 Smart Chicken Purchasing Assistant")
st.caption(
    "Direct Multi-Horizon AI Forecasting for Multan Poultry Gate Rates."
)

st.sidebar.header("⚙️ Market Inputs")
use_live_date = st.sidebar.checkbox("Use Today's System Date", value=True)
selected_date = (
    datetime.now()
    if use_live_date
    else st.sidebar.date_input("Select Base Date", datetime.now())
)

if not isinstance(selected_date, datetime):
    selected_date = datetime.combine(selected_date, datetime.min.time())

st.sidebar.subheader("Price Metrics (PKR)")

# Extract actual latest historical statistics directly from Agbro CSV
latest_farm_rate = float(df_hist["Farm_Rate"].dropna().iloc[-1])
recent_30d_mean = float(df_hist["Farm_Rate"].dropna().tail(30).mean())
recent_30d_std = float(df_hist["Farm_Rate"].dropna().tail(30).std())
recent_3d_mean = float(df_hist["Farm_Rate"].dropna().tail(3).mean())
lag7_rate = (
    float(df_hist["Farm_Rate"].dropna().iloc[-7])
    if len(df_hist) >= 7
    else latest_farm_rate
)

latest_doc = (
    float(df_hist["Multan_DOC_Rate"].dropna().iloc[-1])
    if "Multan_DOC_Rate" in df_hist.columns
    else 75.0
)
lag42_doc = (
    float(df_hist["Multan_DOC_Rate"].dropna().iloc[-42])
    if "Multan_DOC_Rate" in df_hist.columns and len(df_hist) >= 42
    else 68.0
)

farm_rate_lag1 = st.sidebar.number_input(
    "Today's Farm Rate", value=latest_farm_rate, step=1.0
)
farm_rate_lag7 = st.sidebar.number_input(
    "Farm Rate (7 Days Ago)", value=lag7_rate, step=1.0
)
doc_rate = st.sidebar.number_input("Current DOC Rate", value=latest_doc, step=1.0)
doc_lag42 = st.sidebar.number_input(
    "DOC Rate 42 Days Ago", value=lag42_doc, step=1.0
)

latest_hijri_month = (
    int(df_hist["Hijri_Month"].dropna().iloc[-1])
    if "Hijri_Month" in df_hist.columns
    else 2
)
latest_hijri_day = (
    int(df_hist["Hijri_Day"].dropna().iloc[-1])
    if "Hijri_Day" in df_hist.columns
    else 11
)

st.sidebar.subheader("Hijri Calendar")
hijri_month_idx = st.sidebar.selectbox(
    "Hijri Month",
    options=list(HIJRI_MAP.keys()),
    format_func=lambda x: f"{x} - {HIJRI_MAP[x]}",
    index=latest_hijri_month - 1 if 1 <= latest_hijri_month <= 12 else 1,
)
hijri_day = st.sidebar.number_input(
    "Hijri Day", min_value=1, max_value=30, value=latest_hijri_day
)

# --- 4. FEATURE CONSTRUCTION & INFERENCE ---
ma_30d = recent_30d_mean if recent_30d_mean > 0 else farm_rate_lag1
std_30d = (
    recent_30d_std if (not np.isnan(recent_30d_std) and recent_30d_std > 0) else 5.0
)
z_score_30d = (farm_rate_lag1 - ma_30d) / std_30d

ma_3d = (farm_rate_lag1 + recent_3d_mean) / 2.0
ma_7d = (farm_rate_lag1 + farm_rate_lag7) / 2.0

feature_dict = {
    "Multan_DOC_Rate": doc_rate,
    "DOC_Lag42": doc_lag42,
    "Farm_Rate_Lag1": farm_rate_lag1,
    "Farm_Rate_Lag7": farm_rate_lag7,
    "Farm_Rate_3D_MA": ma_3d,
    "Farm_Rate_7D_MA": ma_7d,
    "Farm_Rate_30D_MA": ma_30d,
    "Price_Momentum": farm_rate_lag1 - farm_rate_lag7,
    "Price_ZScore_30D": z_score_30d,
    "Day_Of_Week": selected_date.weekday(),
    "Month": selected_date.month,
    "Day_Of_Year": selected_date.timetuple().tm_yday,
    "Hijri_Day": hijri_day,
    "Hijri_Month": hijri_month_idx,
    "Is_Wedding_Season": 1 if hijri_month_idx in [2, 3, 4, 5, 6, 10] else 0,
}

df_input = pd.DataFrame([feature_dict])[feature_cols]

raw_delta_3d = float(model_3d.predict(df_input)[0])
raw_delta_7d = float(model_7d.predict(df_input)[0])

# Realistic market delta caps (max +/- 15 to 20 PKR movement)
delta_3d = np.clip(raw_delta_3d, -15.0, 15.0)
delta_7d = np.clip(raw_delta_7d, -20.0, 20.0)

pred_3d_price = round(farm_rate_lag1 + delta_3d, 2)
pred_7d_price = round(farm_rate_lag1 + delta_7d, 2)

# --- 5. BUYING WINDOW EVALUATION ---
current_day = selected_date.day
current_month = selected_date.month

m_info = baselines.get(current_month, {})
start_day = m_info.get("start_day", 1)
end_day = m_info.get("end_day", 3)

if current_day >= end_day:
    target_month_num = current_month + 1 if current_month < 12 else 1
    m_info = baselines.get(target_month_num, {})
    start_day = m_info.get("start_day", 1)
    end_day = m_info.get("end_day", 3)
else:
    target_month_num = current_month

month_name = calendar.month_name[target_month_num]
window_date_range = f"{start_day} {month_name} – {end_day} {month_name}"

savings_3d = round(farm_rate_lag1 - pred_3d_price, 2)
diff_7d = round(pred_7d_price - farm_rate_lag1, 2)

# --- 6. USER INTERFACE DISPLAY ---
st.markdown("### 📅 Optimal Procurement Target")

if start_day <= current_day <= end_day:
    st.success(
        f"🔥 **BUY NOW:** Currently in optimal window! Projected 3-day target rate: **{pred_3d_price} PKR/kg**."
    )
else:
    st.info(
        f"🎯 Next optimal window: **{window_date_range}**\n\n"
        f"Direct 3-Day Forecast: **{pred_3d_price} PKR/kg** | Direct 7-Day Forecast: **{pred_7d_price} PKR/kg**"
    )

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Today's Farm Rate",
        value=f"Rs. {farm_rate_lag1}",
        help="Latest farm rate loaded from Agbro Multan CSV",
    )

with col2:
    delta_3d_val = round(pred_3d_price - farm_rate_lag1, 2)
    st.metric(
        label="3-Day Target Rate",
        value=f"Rs. {pred_3d_price}",
        delta=f"{delta_3d_val:+.2f} PKR",
        delta_color="inverse",
    )

with col3:
    delta_7d_val = round(pred_7d_price - farm_rate_lag1, 2)
    st.metric(
        label="7-Day Target Rate",
        value=f"Rs. {pred_7d_price}",
        delta=f"{delta_7d_val:+.2f} PKR",
        delta_color="inverse",
    )

st.divider()

st.subheader("💡 Strategic Guidance")

if savings_3d > 2.0:
    st.write(
        f"✅ **Wait for dip:** Market is currently elevated. Holding procurement is projected to save **Rs. {savings_3d} per kg** over the next 3 days."
    )
elif savings_3d < -2.0:
    st.write(
        f"⚠️ **Buy early:** Upward movement expected. Purchasing today saves an estimated **Rs. {abs(savings_3d)} per kg** compared to waiting 3 days."
    )
else:
    st.write(
        f"⚖️ **Steady Market:** Prices are trading near equilibrium. Expected 3-day target: **Rs. {pred_3d_price}**."
    )