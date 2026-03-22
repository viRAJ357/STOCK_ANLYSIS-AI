# stock_predictor.py
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import sys
import os
import joblib

def fetch_data(ticker, period="5y"):
    print(f"[{ticker}] Ka data Yahoo Finance se download ho raha hai...")
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            print(f"Error: {ticker} ka data nahi mila. Symbol check karein.")
            return None
            
        # Dataset ko CSV file mein save karne ke liye
        csv_filename = f"{ticker}_dataset.csv".replace("^", "") 
        df.to_csv(csv_filename)
        print(f"Dataset mil gaya! '{csv_filename}' file mein save ho gaya hai aapke dekhne ke liye.")
        
        return df
    except Exception as e:
        print(f"Data fetch karne mein error: {e}")
        return None

def prepare_features(df):
    print("Market indicators (Features) banaye ja rahe hain...")
    
    # Replace NaNs that might exist initially
    df = df.ffill()
    
    # Simple Moving Averages
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Daily Return
    df['Return'] = df['Close'].pct_change()
    
    # RSI (Relative Strength Index) calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Target value (1 agar kal price aaj se upar jayega, 0 agar neeche jayega)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    # Drop rows with NaN values (jo moving averages aur rsi ki wajah se aaye hain)
    df = df.dropna()
    return df

def train_model(df):
    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
    
    if os.path.exists('stock_model.pkl'):
        print("\n✅ Pre-Trained Massive Model (2 Lakh+ data points) load kiya ja raha hai...")
        try:
            model = joblib.load('stock_model.pkl')
            return model, features
        except Exception as e:
            print(f"Model load karne mein error: {e}")
            print("Fallback: Sirf current stock data par train kar rahe hain...")
            
    print("\n⚠️ Massive pre-trained model nahi mila. Sirf isi stock ke limited data par model train ho raha hai (Random Forest Classifier)...")
    
    X = df[features]
    y = df['Target']
    
    # Time Series data mein pichla data train(80%), aage ka test(20%) hota hai
    split_index = int(0.8 * len(df))
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]
    
    # Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    
    # Accuracy check
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"\nModel Accuracy (Testing Data Par): {accuracy * 100:.2f}%\n")
    
    return model, features

def predict_tomorrow(model, df, features, ticker):
    print("--------------------------------------------------")
    print(f"   {ticker} ke liye KAL (Next Trading Day) ki Prediction")
    print("--------------------------------------------------")
    
    # Aaj ka (latest) data lo
    latest_data = df.iloc[-1][features].to_frame().T
    
    # Predict karo
    prediction = model.predict(latest_data)
    probabilities = model.predict_proba(latest_data)[0]
    
    if prediction[0] == 1:
        print(f"Prediction: Share UTEGA (Price UP jayega) ⬆️")
        print(f"Confidence (Jeetne ka chance): {probabilities[1]*100:.2f}%")
    else:
        print(f"Prediction: Share GIREGA (Price DOWN jayega) ⬇️")
        print(f"Confidence (Girne ka chance): {probabilities[0]*100:.2f}%")
    
    print("\n⚠️ Disclaimer: Share market prediction kabhi 100% accurate nahi hoti. Yeh model sirf historical patterns aur technical indicators par aadharit hai. Iske base par real paise invest karne se pehle khud research zaroor karein.")

def main():
    # By default Reliance Industries (NSE) ka data lenge.
    # Aap koi bhi ticker daal sakte hain jaise "AAPL" (Apple) ya "^NSEI" (Nifty 50)
    ticker = "RELIANCE.NS" 
    
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        
    df = fetch_data(ticker, period="5y")
    
    if df is not None:
        df = prepare_features(df)
        model, features = train_model(df)
        predict_tomorrow(model, df, features, ticker)

if __name__ == "__main__":
    main()
