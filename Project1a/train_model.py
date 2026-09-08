import pandas as pd
import pickle
from pathlib import Path
from sklearn import linear_model

# Get directory where train_model.py lives
base_dir = Path(__file__).resolve().parent

CSV_PATH = base_dir / "Final Correlation Prices.csv"
MODEL_PATH = base_dir / "models" / "Model1.pkl"

def train_and_serialize_model() -> None:
    try:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not CSV_PATH.exists():
            raise FileNotFoundError(
                f"Missing training dataset! 'Final Correlation Prices.csv' expected at: {CSV_PATH}"
            )

        print("Loading training data...")
        df = pd.read_csv(CSV_PATH)

        df.dropna(subset=["Platts_Arab_Gulf_Mean"], inplace=True)

        print("Training Linear Regression model...")
        lr = linear_model.LinearRegression()
        lr.fit(df[["Brent_Crude"]], df["Platts_Arab_Gulf_Mean"])

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(lr, f)

        print(f"Model trained successfully! Saved to: {MODEL_PATH}")

    except Exception as e:
        print(f"Training Error: {e}")

if __name__ == "__main__":
    train_and_serialize_model()