import sys
from pathlib import Path
base_dir=Path(__file__).resolve().parent
sys.path.append(str(base_dir/"src"))

CSV_PATH=base_dir/"data"/"Updating Pricing.csv"
MODEL_PATH=base_dir/"models"/"Model1.pkl"
from predictor import PetrolCalculator

def main() -> None:
    try:
        calculator=PetrolCalculator(csv_path=CSV_PATH, model_path=MODEL_PATH)
        df = calculator.load_data()
        print(f"Petrol Price Predictor Loaded Successfully ")
        print("Enter the Brent Crude Price")
        brent_input=float(input())
        final_price=calculator.calculate_expected_price(df, brent_input)
        print(f"Predicted Petrol Price: Rs: {final_price:.2f}")
    except Exception as e:
        print(f"Startup Error:{e}")
        sys.exit(1)
if __name__ =="__main__":
    main()