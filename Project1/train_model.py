import numpy as np
import pandas as pd
import pickle
from sklearn import linear_model

df = pd.read_csv(r"C:\Users\Home\Desktop\AI\Python-Workspace\Project 1\Final Correlation Prices.csv")
df.dropna(subset=['Platts_Arab_Gulf_Mean'], inplace=True)

lr = linear_model.LinearRegression()
lr.fit(df[['Brent_Crude']], df['Platts_Arab_Gulf_Mean'])

with open('Model1.pkl', 'wb') as f:
    pickle.dump(lr, f)
