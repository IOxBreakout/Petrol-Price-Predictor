import streamlit as st
import pandas as pd
from pathlib import Path
import sys

base_dir=Path(__file__).resolve().parent
sys.path.append(str(base_dir/"src"))
from predictor import PetrolCalculator
CSV_PATH=base_dir / "data" / "Updating Pricing.csv"
MODEL_PATH=base_dir / "models" / "Model1.pkl"

@st.cache_resource
def get_calculator() -> PetrolCalculator:
    return PetrolCalculator(csv_path=CSV_PATH, model_path=MODEL_PATH)

@st.cache_data(ttl=3600)
def get_data(_calculator: PetrolCalculator) -> pd.DataFrame:
    return _calculator.load_data()

calculator=get_calculator()
df=get_data(calculator)

st.title("Petrol Price Predictor")
st.markdown("Automated Forecasting using International Price")
st.divider()
st.subheader("1. Market Inputs")
brent_input=st.number_input("Enter Brent Crude Price ($):", min_value=10.0, max_value=200.0, value=75.0, step=0.5)
if st.button("Predict Expected Retail Price", type="primary"):
    final_price=calculator.calculate_expected_price(df,brent_input)
    st.divider()
    st.metric(label="Predicted Petrol Price",value=f"Rs. {final_price:.2f}")