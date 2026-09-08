import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

# --- 1. PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "agbro_multan_prices_2015_2026_hijri.csv"
)
MODEL_3D_PATH = os.path.join(BASE_DIR, "Model_3D.pkl")
MODEL_7D_PATH = os.path.join(BASE_DIR, "Model_7D.pkl")
META_PATH = os.path.join(BASE_DIR, "model_meta_direct.pkl")


# --- 2. DATA PREPARATION & FEATURE ENGINEERING ---
def load_and_prepare_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required CSV not found at: {file_path}")

    df = pd.read_csv(file_path)

    # Clean whitespace from column headers
    df.columns = df.columns.str.strip()

    # Broad column mapping dictionary
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
    df = df.rename(columns=col_map)

    # Dynamic fallback for Farm_Rate if standard rename missed it
    if "Farm_Rate" not in df.columns:
        for col in df.columns:
            if any(
                k in col.lower() for k in ["rate", "price", "farm", "broiler"]
            ) and ("doc" not in col.lower()):
                df = df.rename(columns={col: "Farm_Rate"})
                break

    if "Farm_Rate" not in df.columns:
        raise KeyError(
            f"Could not locate price column! Available columns in CSV: {list(df.columns)}"
        )

    # Parse dates explicitly to suppress parsing warnings
    date_col = next(
        (col for col in df.columns if "date" in col.lower()), df.columns[0]
    )
    df["Date"] = pd.to_datetime(
        df[date_col], format="mixed", dayfirst=True, errors="coerce"
    )
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # Fallbacks for optional columns
    if "Multan_DOC_Rate" not in df.columns:
        df["Multan_DOC_Rate"] = 75.0
    if "Hijri_Day" not in df.columns:
        df["Hijri_Day"] = 15
    if "Hijri_Month" not in df.columns:
        df["Hijri_Month"] = 1

    # Core Lags
    df["Farm_Rate_Lag1"] = df["Farm_Rate"].shift(1)
    df["Farm_Rate_Lag7"] = df["Farm_Rate"].shift(7)
    df["DOC_Lag42"] = df["Multan_DOC_Rate"].shift(42)

    # Momentum & Moving Averages
    df["Farm_Rate_3D_MA"] = df["Farm_Rate_Lag1"].rolling(3).mean()
    df["Farm_Rate_7D_MA"] = df["Farm_Rate_Lag1"].rolling(7).mean()
    df["Farm_Rate_30D_MA"] = df["Farm_Rate_Lag1"].rolling(30).mean()
    df["Price_Momentum"] = df["Farm_Rate_Lag1"] - df["Farm_Rate_Lag7"]

    # Mean-Reversion Metric (30-Day Z-Score)
    std_30d = df["Farm_Rate_Lag1"].rolling(30).std().replace(0, 1.0)
    df["Price_ZScore_30D"] = (
        df["Farm_Rate_Lag1"] - df["Farm_Rate_30D_MA"]
    ) / std_30d

    # Calendar Features
    df["Day_Of_Week"] = df["Date"].dt.weekday
    df["Month"] = df["Date"].dt.month
    df["Day_Of_Year"] = df["Date"].dt.dayofyear
    df["Is_Wedding_Season"] = df["Hijri_Month"].apply(
        lambda x: 1 if x in [2, 3, 4, 5, 6, 10] else 0
    )

    # DIRECT MULTI-HORIZON TARGETS
    df["Target_Delta_3D"] = df["Farm_Rate"].shift(-3) - df["Farm_Rate_Lag1"]
    df["Target_Delta_7D"] = df["Farm_Rate"].shift(-7) - df["Farm_Rate_Lag1"]

    df = df.dropna().reset_index(drop=True)
    return df


print(f"📊 Loading Agbro Multan dataset from: {DATA_PATH}...")
df = load_and_prepare_data(DATA_PATH)
print(f"✅ Preprocessed {len(df)} daily price records successfully.")

feature_cols = [
    "Multan_DOC_Rate",
    "DOC_Lag42",
    "Farm_Rate_Lag1",
    "Farm_Rate_Lag7",
    "Farm_Rate_3D_MA",
    "Farm_Rate_7D_MA",
    "Farm_Rate_30D_MA",
    "Price_Momentum",
    "Price_ZScore_30D",
    "Day_Of_Week",
    "Month",
    "Day_Of_Year",
    "Hijri_Day",
    "Hijri_Month",
    "Is_Wedding_Season",
]

baselines = {}
for m in range(1, 13):
    baselines[m] = {
        "start_day": 28 if m in [1, 3, 5, 7, 8, 10, 12] else 27,
        "end_day": 30 if m in [1, 3, 5, 7, 8, 10, 12] else 29,
        "min_3d_ratio": 0.96,
    }

X = df[feature_cols]
y_3d = df["Target_Delta_3D"]
y_7d = df["Target_Delta_7D"]

split_idx = int(len(df) * 0.85)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y3_train, y3_test = y_3d.iloc[:split_idx], y_3d.iloc[split_idx:]
y7_train, y7_test = y_7d.iloc[:split_idx], y_7d.iloc[split_idx:]

# --- 3. TRAIN 3-DAY DIRECT MODEL ---
print("🚀 Training 3-Day Direct Model...")
model_3d = XGBRegressor(
    n_estimators=300, learning_rate=0.03, max_depth=4, random_state=42
)
model_3d.fit(X_train, y3_train)

# --- 4. TRAIN 7-DAY DIRECT MODEL ---
print("🚀 Training 7-Day Direct Model...")
model_7d = XGBRegressor(
    n_estimators=300, learning_rate=0.03, max_depth=4, random_state=42
)
model_7d.fit(X_train, y7_train)

# --- 5. EVALUATION ---
p3 = model_3d.predict(X_test)
p7 = model_7d.predict(X_test)

# Apply realistic market delta caps (matching app display logic)
p3_capped = np.clip(p3, -15.0, 15.0)
p7_capped = np.clip(p7, -20.0, 20.0)

y3_actual_price = X_test["Farm_Rate_Lag1"] + y3_test
y7_actual_price = X_test["Farm_Rate_Lag1"] + y7_test

y3_pred_price = X_test["Farm_Rate_Lag1"] + p3_capped
y7_pred_price = X_test["Farm_Rate_Lag1"] + p7_capped

mae_3d = mean_absolute_error(y3_actual_price, y3_pred_price)
mae_7d = mean_absolute_error(y7_actual_price, y7_pred_price)

rmse_3d = np.sqrt(mean_squared_error(y3_actual_price, y3_pred_price))
rmse_7d = np.sqrt(mean_squared_error(y7_actual_price, y7_pred_price))

print("\n" + "=" * 55)
print(f"✅ 3-Day Direct Model MAE: {mae_3d:.2f} PKR | RMSE: {rmse_3d:.2f} PKR")
print(f"✅ 7-Day Direct Model MAE: {mae_7d:.2f} PKR | RMSE: {rmse_7d:.2f} PKR")
print("=" * 55 + "\n")

# --- 6. SAVE ARTIFACTS ---
os.makedirs(BASE_DIR, exist_ok=True)
joblib.dump(model_3d, MODEL_3D_PATH)
joblib.dump(model_7d, MODEL_7D_PATH)

meta = {"feature_cols": feature_cols, "baselines": baselines}
joblib.dump(meta, META_PATH)

print("💾 All models and metadata saved successfully.")