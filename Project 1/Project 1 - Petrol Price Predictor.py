import numpy as np
import pandas as pd
import yfinance as yf
import pickle
from sklearn import linear_model

with open('Model1.pkl','rb') as f:
          lr = pickle.load(f)

df=pd.read_csv(r"C:\Users\Home\Desktop\AI\Python-Workspace\Project 1\Updating Pricing.csv")

df["Date"] = pd.to_datetime(df["Date"], format="mixed").dt.date
today = pd.Timestamp.now().date()

platts_series = df["Platts Arab Gulf Mean"].dropna()

today_row = df[df["Date"] == today]
is_today_missing = (
    today_row.empty or pd.isna(today_row["Platts Arab Gulf Mean"].values[0])
)

if is_today_missing:
    Price_7day_List = platts_series.tail(6).tolist()

    try:
        brent = yf.Ticker("BZ=F")
        df1 = brent.history(period="1d", interval="1m")

        if not df1.empty:
            live_price = round(df1["Close"].iloc[-1], 2)
        else:
            raise ValueError("Empty ticker history returned.")
    except Exception as e:
        live_price = float(input("Enter live Brent Crude (Oil) Price manually [Check investing.com or oilprice.com]: "))

    latest_val = float(lr.predict([[live_price]])[0])
    Price_7day_List.append(latest_val)
else:
    Price_7day_List = platts_series.tail(7).tolist()

Price_7day_Sum = sum(Price_7day_List)

Petrol_Platts_Arab_Gulf_Mean = Price_7day_Sum/7
Premium_including_Freight = 10.98000
Cost_and_Freight = Petrol_Platts_Arab_Gulf_Mean + Premium_including_Freight
#sbp_exchange_rate_list = [278.15,278.11,278.10,278.10,278.06,278.05,278.05]
#SBP_Avg_Exchange_Rate = 278.10317
"""Live_Rate = yf.Ticker("USDPKR=X")
df1 = Live_Rate.history(period="1d", prepost=False)

if df1.empty:
    print("Enter Dollar to Pkr Rate:")
    Live_Rate1 = float(input())
else:
    Live_Rate1 = round(df['Close'].iloc[-1], 2)

SBP_Exchange_Rate_List.append(Live_Rate1)
SBP_Exchange_Rate_List.pop(0)"""
SBP_Series = df["Dollar"].dropna()
SBP_Exchange_Rate_List = SBP_Series.tail(7).tolist()
SBP_Exchange_Rate_Sum = sum(SBP_Exchange_Rate_List)
SBP_Avg_Exchange_Rate = SBP_Exchange_Rate_Sum/7
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
print(f"Expexted Petrol Price is: {Total_Petrol_Price:.2f}")