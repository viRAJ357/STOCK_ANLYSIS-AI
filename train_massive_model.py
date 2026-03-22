# train_massive_model.py
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import io
import sys

# Windows terminal me unicode errors avoid karne ke liye
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

nifty50_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", 
    "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATAMOTORS.NS",
    "KOTAKBANK.NS", "NTPC.NS", "M&M.NS", "AXISBANK.NS", "TITAN.NS", 
    "ONGC.NS", "TATASTEEL.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "ASIANPAINT.NS",
    "ADANIENT.NS", "POWERGRID.NS", "LTIM.NS", "BAJAJ-AUTO.NS", "ADANIPORTS.NS",
    "HDFCLIFE.NS", "SBIKARD.NS", "TECHM.NS", "GRASIM.NS", "ULTRACEMCO.NS",
    "NESTLEIND.NS", "WIPRO.NS", "JSWSTEEL.NS", "INDUSINDBK.NS", "HINDALCO.NS",
    "DIVISLAB.NS", "DRREDDY.NS", "TATACONSUM.NS", "CIPLA.NS", "BRITANNIA.NS",
    "APOLLOHOSP.NS", "EICHERMOT.NS", "BPCL.NS", "HEROMOTOCO.NS", "SHREECEM.NS"
]

def prepare_features(df):
    df = df.ffill()
    if len(df) < 50:
        return pd.DataFrame() 
        
    df.loc[:, 'SMA_10'] = df['Close'].rolling(window=10).mean()
    df.loc[:, 'SMA_50'] = df['Close'].rolling(window=50).mean()
    df.loc[:, 'Return'] = df['Close'].pct_change()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df.loc[:, 'RSI'] = 100 - (100 / (1 + rs))
    
    df.loc[:, 'Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df = df.dropna()
    return df

def build_massive_dataset():
    print(f"Data download shuru kar rahe hain {len(nifty50_tickers)} TOP Indian companies ka...")
    
    all_dataframes = []
    total_rows = 0
    
    for i, ticker in enumerate(nifty50_tickers):
        print(f"[{i+1}/{len(nifty50_tickers)}] Fetching {ticker} (max available history)...")
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="max")
            if not df.empty:
                df = prepare_features(df)
                if not df.empty:
                    df['Ticker'] = ticker 
                    all_dataframes.append(df)
                    total_rows += len(df)
                    print(f"  -> {len(df)} price rows mili. Total ab tak: {total_rows} rows")
        except Exception as e:
            print(f"  -> Error fetching {ticker}: {e}")
        
    print(f"\nSari downloading khatam! Total rows mili hain: {total_rows}")
    
    if len(all_dataframes) > 0:
        massive_df = pd.concat(all_dataframes)
        csv_filename = "massive_training_dataset.csv"
        print(f"Dataset ko '{csv_filename}' mein save kar rahe hain...")
        massive_df.to_csv(csv_filename)
        return massive_df
    else:
        print("Data nahi mila!")
        return None

def train_and_save_model(df):
    print("\nMassive Model Training Start Ho Rahi Hai!!! (Lakhon data points parameter par)")
    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
    
    X = df[features]
    y = df['Target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    
    print(f"Training on {len(X_train)} dataset points... please wait!")
    model.fit(X_train, y_train)
    print("Training complete!")
    
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"\nModel Accuracy Testing Data Par: {acc*100:.2f}%")
    
    joblib.dump(model, 'stock_model.pkl')
    print("Model saved successfully in 'stock_model.pkl' (Pre-Trained Brain)!")

if __name__ == "__main__":
    df = build_massive_dataset()
    if df is not None:
        train_and_save_model(df)
