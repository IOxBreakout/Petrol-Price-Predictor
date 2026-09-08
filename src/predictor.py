import pandas as pd
import pickle
from pathlib import Path
from typing import Any

class PetrolCalculator:

    def __init__(self, csv_path: Path, model_path: Path) -> None:
        self.csv_path = csv_path
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self) -> Any:
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError(f"File Not Found at {self.model_path}")

    def load_data(self) -> pd.DataFrame:
        if self.csv_path.exists():
            df = pd.read_csv(self.csv_path)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], format="mixed").dt.strftime("%Y-%m-%d")
            return df
        else:
            raise FileNotFoundError(f"File Not Found at {self.csv_path}")

    def get_exchange_rate(self, df: pd.DataFrame) -> float:
        dollar_series = df["Dollar"].dropna()
        dollar_value = dollar_series.iloc[-1]
        return float(dollar_value)

    def get_platts_average(self, df: pd.DataFrame) -> float:
        platts_input = df["Platts Arab Gulf Mean"]
        platts_clean = platts_input.dropna()
        platts_7day = platts_clean.tail(7)
        platts_average = platts_7day.mean()
        return float(platts_average)

    def get_forecasted_platts_list(self, brent_input: float, df: pd.DataFrame) -> list[float]:
        today = pd.Timestamp.now().strftime("%Y-%m-%d")
        today_row = df[df["Date"] == today]
        is_today_missing = today_row.empty or today_row["Platts Arab Gulf Mean"].isna().all()
        platts_series = df["Platts Arab Gulf Mean"].dropna()
        
        if is_today_missing:
            price_list = platts_series.tail(6).tolist()
            input_df = pd.DataFrame({"Brent_Crude": [brent_input]})
            predicted_val = float(self.model.predict(input_df)[0])
            price_list.append(predicted_val)
            return price_list
        else:
            price_list = platts_series.tail(7).tolist()
            return price_list

    def calculate_expected_price(self, df: pd.DataFrame, brent_input: float) -> float:
        price_list = self.get_forecasted_platts_list(brent_input, df)
        Petrol_Platts_Arab_Gulf_Mean = sum(price_list) / 7
        
        Premium_including_Freight = 15.25
        Cost_and_Freight = Petrol_Platts_Arab_Gulf_Mean + Premium_including_Freight
        
        SBP_Avg_Exchange_Rate = self.get_exchange_rate(df)
        Conversion_Factor = 158.98
        Cost_and_Freight_in_Pak_Rs = Cost_and_Freight * (SBP_Avg_Exchange_Rate / Conversion_Factor)
        
        Incidentals = 0.46
        Ocean_Loss_or_Gain = -0.6
        Petrol_Cost_at_Karachi_Port = Cost_and_Freight_in_Pak_Rs + Incidentals + Ocean_Loss_or_Gain
        
        Exchange_Rate_Adjustment = 2.44
        Customs_Duty = 21.02
        Ex_Refinery_Import_Price = Petrol_Cost_at_Karachi_Port + Exchange_Rate_Adjustment + Customs_Duty
        
        IFEM = 7.6
        OMCs_Margin = 7.87
        Dealers_Margin = 9.98  # Changed from 8.64 on August 21, 2026
        Price_before_Taxes = Ex_Refinery_Import_Price + IFEM + OMCs_Margin + Dealers_Margin
        
        Petroleum_Levy = 80.00
        Climate_Support_Levy = 5.00
        Sales_Tax = 0.00
        
        Total_Petrol_Price = Price_before_Taxes + Petroleum_Levy + Climate_Support_Levy + Sales_Tax
        return float(Total_Petrol_Price)