import os
import pickle
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

st.set_page_config(page_title="Petrol Price Predictor", page_icon="⛽", layout="centered")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_resource
def load_model():
    model_path = os.path.join(BASE_DIR, "Model1.pkl")
    with open(model_path, "rb") as f:
        return pickle.load(f)

@st.cache_data(ttl=3600)
def load_historical_data():
    csv_path = os.path.join(BASE_DIR, "Updating Pricing.csv")
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="mixed").dt.date
    return df

def fetch_live_brent():
    try:
        brent = yf.Ticker("BZ=F")
        df1 = brent.history(period="1d", interval="1m")
        if not df1.empty:
            return round(df1["Close"].iloc[-1], 2)
    except Exception:
        pass
    return None

st.title("⛽ Petrol Price Predictor")
st.markdown("Automated forecasting tool using International **Brent Crude** Price")

try:
    lr = load_model()
    df = load_historical_data()
    model_loaded = True
except Exception as e:
    st.error(f"Error loading system files: {e}")
    model_loaded = False

if model_loaded:
    st.divider()
    
    # 1. Fetch / Input Brent Price
    st.subheader("1. Market Inputs")
    live_brent = fetch_live_brent()
    
    if live_brent:
        st.success(f"Fetched Live Brent Crude Price: **${live_brent:.2f}/barrel**")
        brent_input = st.number_input("Brent Crude Price ($)", value=float(live_brent), step=0.5)
    else:
        st.warning("Could not fetch live Brent price automatically.")
        brent_input = st.number_input("Enter Brent Crude Price ($) Manually:", value=75.00, step=0.5)

    # 2. Calculation Logic
    if st.button("Predict Expected Retail Price", type="primary"):
        platts_series = df["Platts Arab Gulf Mean"].dropna()
        today = pd.Timestamp.now().date()
        today_row = df[df["Date"] == today]
        
        is_today_missing = (
            today_row.empty or pd.isna(today_row["Platts Arab Gulf Mean"].values[0])
        )

        if is_today_missing:
            Price_7day_List = platts_series.tail(6).tolist()
            input_df = pd.DataFrame({"Brent_Crude": [brent_input]})
            latest_val = float(lr.predict(input_df)[0])
            Price_7day_List.append(latest_val)
        else:
            Price_7day_List = platts_series.tail(7).tolist()

        Price_7day_Sum = sum(Price_7day_List)
        Petrol_Platts_Arab_Gulf_Mean = Price_7day_Sum / 7
        Premium_including_Freight = 10.98000
        Cost_and_Freight = Petrol_Platts_Arab_Gulf_Mean + Premium_including_Freight

        SBP_Series = df["Dollar"].dropna()
        SBP_Exchange_Rate_List = SBP_Series.tail(7).tolist()
        SBP_Avg_Exchange_Rate = sum(SBP_Exchange_Rate_List) / 7

        Conversion_Factor = 158.98
        Cost_and_Freight_in_Pak_Rs = Cost_and_Freight * (SBP_Avg_Exchange_Rate / Conversion_Factor)
        
        Incidentals = 0.42805
        Ocean_Loss_or_Gain = -0.48388
        Petrol_Cost_at_Karachi_Port = Cost_and_Freight_in_Pak_Rs + Incidentals + Ocean_Loss_or_Gain
        Exchange_Rate_Adjustment = -0.53329
        Customs_Duty = 17.28217
        Ex_Refinery_Import_Price = Petrol_Cost_at_Karachi_Port + Exchange_Rate_Adjustment + Customs_Duty
        
        IFEM = 6.95
        OMCs_Margin = 7.87
        Dealers_Margin = 8.64
        Price_before_Taxes = Ex_Refinery_Import_Price + IFEM + OMCs_Margin + Dealers_Margin
        
        Petroleum_Levy = 80.00
        Climate_Support_Levy = 5.00
        Sales_Tax = 0.00
        Total_Petrol_Price = Price_before_Taxes + Petroleum_Levy + Climate_Support_Levy + Sales_Tax

        st.divider()
        st.metric(label="Predicted Retail Price (PKR/Liter)", value=f"Rs. {Total_Petrol_Price:.2f}")

        #with st.expander("📊 View Cost Breakdown & Tax Structure"):
          #  st.write(f"**Average USD/PKR Exchange Rate:** {SBP_Avg_Exchange_Rate:.2f}")
          #  st.write(f"**Platts Arab Gulf 7-Day Average:** ${Petrol_Platts_Arab_Gulf_Mean:.2f}/barrel")
          #  st.write(f"**Ex-Refinery Import Price:** Rs. {Ex_Refinery_Import_Price:.2f}")
          #  st.write(f"**Total Margins (IFEM + OMC + Dealer):** Rs. {IFEM + OMCs_Margin + Dealers_Margin:.2f}")
          #  st.write(f"**Government Duties (Levy + CSL):** Rs. {Petroleum_Levy + Climate_Support_Levy:.2f}")"""