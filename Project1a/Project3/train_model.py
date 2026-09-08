import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

BASE_DIR = r"C:\Users\Home\Desktop\AI\Python-Workspace\Project3"
DATA_FOLDER = os.path.join(BASE_DIR, "multan_crop_data")
MODEL_FILE = os.path.join(BASE_DIR, "commodity_valuation_model.pkl")

CPI_INDEX = {
    2016: 0.38,
    2017: 0.40,
    2018: 0.42,
    2019: 0.46,
    2020: 0.51,
    2021: 0.56,
    2022: 0.68,
    2023: 0.88,
    2024: 0.95,
    2025: 0.98,
    2026: 1.00,
}


def standardize_unit_price(df: pd.DataFrame) -> pd.Series:
    """Standardizes price across weight-based and count-based schemas."""
    cols = [c.strip() for c in df.columns]
    df.columns = cols

    if "Price per kg" in df.columns:
        return df["Price per kg"]
    elif "Price per 100 kg" in df.columns:
        return df["Price per 100 kg"] / 100.0

    for col in df.columns:
        if "100" in col:
            return df[col] / 100.0
        elif "Dozen" in col or "12" in col:
            return df[col] / 12.0

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        return df[numeric_cols[-1]]

    return pd.Series(dtype=float)


def load_and_preprocess_data(folder_path: str):
    all_records = []
    commodity_metadata = {}

    for file in os.listdir(folder_path):
        if not file.endswith(".csv"):
            continue

        commodity_name = os.path.splitext(file)[0].strip()
        file_path = os.path.join(folder_path, file)

        try:
            df = pd.read_csv(file_path)

            df["Unit_Price"] = standardize_unit_price(df)

            # Silently coerce non-date header metadata rows into NaT
            df["Date"] = pd.to_datetime(
                df["Date"], format="%d %b %y", errors="coerce"
            )
            df = (
                df.dropna(subset=["Date", "Unit_Price"])
                .sort_values("Date")
                .reset_index(drop=True)
            )

            if df.empty:
                print(f"Skipping empty or unparseable file: {file}")
                continue

            df["Year"] = df["Date"].dt.year
            df["Month_Name"] = df["Date"].dt.strftime("%b")
            df["CPI_Factor"] = df["Year"].map(CPI_INDEX).fillna(1.0)
            df["Real_Unit_Price"] = df["Unit_Price"] / df["CPI_Factor"]

            p33 = df["Real_Unit_Price"].quantile(0.33)
            p66 = df["Real_Unit_Price"].quantile(0.66)

            def label_price(val):
                if val <= p33:
                    return 0
                elif val <= p66:
                    return 1
                else:
                    return 2

            df["Price_Class"] = df["Real_Unit_Price"].apply(label_price)

            category_breakdown = {}
            cat_names = {0: "Cheap", 1: "Normal", 2: "Expensive"}

            for code, name in cat_names.items():
                cat_df = df[df["Price_Class"] == code]
                if not cat_df.empty:
                    min_r = cat_df["Real_Unit_Price"].min()
                    max_r = cat_df["Real_Unit_Price"].max()
                    month_dist = (
                        cat_df["Month_Name"].value_counts(normalize=True) * 100
                    )
                    top_months = month_dist[
                        month_dist >= 8.0
                    ].index.tolist()

                    category_breakdown[name] = {
                        "min_real": round(min_r, 2),
                        "max_real": round(max_r, 2),
                        "dominant_months": top_months,
                    }

            commodity_metadata[commodity_name.lower()] = {
                "display_name": commodity_name,
                "p33_real": p33,
                "p66_real": p66,
                "latest_nominal_avg": df["Unit_Price"].iloc[-30:].mean(),
                "categories": category_breakdown,
            }

            df["DayOfYear"] = df["Date"].dt.dayofyear
            df["Sin_Day"] = np.sin(2 * np.pi * df["DayOfYear"] / 365.25)
            df["Cos_Day"] = np.cos(2 * np.pi * df["DayOfYear"] / 365.25)
            df["Commodity_Name"] = commodity_name.lower()

            all_records.append(df)
            print(f"Successfully processed: {file}")

        except Exception as e:
            print(f"Error processing {file}: {e}")

    if not all_records:
        raise ValueError("No valid CSV files were processed.")

    combined_df = pd.concat(all_records, ignore_index=True)
    return combined_df, commodity_metadata


def train():
    df, commodity_metadata = load_and_preprocess_data(DATA_FOLDER)

    df = pd.get_dummies(df, columns=["Commodity_Name"], prefix="cmd")

    feature_cols = [
        col
        for col in df.columns
        if col.startswith("cmd_")
        or col in ["Sin_Day", "Cos_Day", "Real_Unit_Price"]
    ]

    X = df[feature_cols]
    y = df["Price_Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=150, max_depth=12, random_state=42
    )
    clf.fit(X_train, y_train)

    artifacts = {
        "model": clf,
        "feature_cols": feature_cols,
        "commodity_metadata": commodity_metadata,
        "cpi_index": CPI_INDEX,
    }

    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(artifacts, f)

    print(
        f"\nModel saved successfully to '{MODEL_FILE}'. Metadata updated."
    )


if __name__ == "__main__":
    train()