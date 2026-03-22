import os
import re
import joblib
import pandas as pd
import yfinance as yf
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Load the model
model = None
MODEL_PATH = "stock_model.pkl"
if os.path.exists(MODEL_PATH):
    print("Loading AI Model Brain...")
    model = joblib.load(MODEL_PATH)
else:
    print(f"⚠️ Model file '{MODEL_PATH}' not found!")

def extract_ticker(input_str):
    input_str = input_str.strip()
    
    # Simple regex for common URLs (ported from telegram_bot.py)
    match = re.search(r'finance\.yahoo\.com/quote/([^/\?]+)', input_str)
    if match: return match.group(1).upper()
    
    # NSE India link
    match = re.search(r'nseindia\.com/(?:get-quote|equity-stockWatch)/equity/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    
    # Screener.in link
    match = re.search(r'screener\.in/company/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    
    # Groww link
    match = re.search(r'groww\.in/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"

    # Mappings for common names
    mappings = {
        "asianpaint": "ASIANPAINT.NS", "reliance": "RELIANCE.NS", "tcs": "TCS.NS",
        "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS", "infosys": "INFY.NS",
        "sbi": "SBIN.NS", "airtel": "BHARTIARTL.NS", "itc": "ITC.NS",
        "zomato": "ZOMATO.NS", "apple": "AAPL", "google": "GOOGL", "tesla": "TSLA"
    }
    
    keyword = input_str.lower().replace(" ", "").replace("-", "")
    for key, mapped_ticker in mappings.items():
        if key in keyword:
            return mapped_ticker
            
    return input_str.upper()

def prepare_features(df):
    df = df.ffill()
    if len(df) < 50: return pd.DataFrame() 
    df.loc[:, 'SMA_10'] = df['Close'].rolling(window=10).mean()
    df.loc[:, 'SMA_50'] = df['Close'].rolling(window=50).mean()
    df.loc[:, 'Return'] = df['Close'].pct_change()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df.loc[:, 'RSI'] = 100 - (100 / (1 + rs))
    
    return df.dropna()

def calculate_investment(df, investment_amount, prediction, confidence):
    closes = df['Close']
    returns = closes.pct_change().dropna()
    current_price = float(closes.iloc[-1])
    
    recent_returns = returns.iloc[-20:]
    recent_avg = float(recent_returns.mean()) * 100
    recent_vol = float(recent_returns.std()) * 100
    
    week_return = ((closes.iloc[-1] / closes.iloc[-min(5, len(closes))]) - 1) * 100
    month_return = ((closes.iloc[-1] / closes.iloc[-min(22, len(closes))]) - 1) * 100
    
    confidence_factor = confidence / 100.0
    expected_move_pct = (abs(recent_avg) if prediction == 1 else -abs(recent_avg)) * confidence_factor
    
    expected_profit = investment_amount * (expected_move_pct / 100)
    risk = "🔴 HIGH" if recent_vol > 3 else "🟡 MEDIUM" if recent_vol > 1.5 else "🟢 LOW"
    
    return {
        "shares": round(float(investment_amount / current_price), 2),
        "expected_profit": round(float(expected_profit), 2),
        "expected_pct": round(float(expected_move_pct), 2),
        "risk": risk,
        "price": round(float(current_price), 2),
        "week": round(float(week_return), 2),
        "month": round(float(month_return), 2)
    }

@app.route("/", methods=['GET'])
def home():
    return "🤖 AI Stock Predictor Bot is running! 📈 Visit /whatsapp for the webhook."

@app.route("/whatsapp", methods=['GET', 'POST'])
def whatsapp_reply():
    if request.method == 'GET':
        return "🤖 AI Stock Predictor Bot is running! 📈"
    
    msg_body = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    reply = resp.message()
    
    if model is None:
        reply.body("⚠️ Model not loaded. Please check server logs.")
        return str(resp)

    # Check for investment amount
    parts = msg_body.split()
    investment_amount = None
    text = msg_body
    if len(parts) >= 2:
        try:
            investment_amount = float(parts[-1].replace(",", ""))
            text = " ".join(parts[:-1])
        except ValueError:
            pass

    ticker = extract_ticker(text)
    
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="2y")
        
        if df.empty:
            reply.body(f"❌ '{ticker}' data not found. Use a valid symbol or name.")
            return str(resp)
            
        prepared_df = prepare_features(df)
        if prepared_df.empty:
            reply.body("❌ Not enough data for technical indicators.")
            return str(resp)
            
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
        latest_data = prepared_df.iloc[-1][features].to_frame().T
        
        prediction = model.predict(latest_data)[0]
        proba = model.predict_proba(latest_data)[0]
        curr_price = float(latest_data['Close'].iloc[0])
        rsi_val = float(latest_data['RSI'].iloc[0])
        
        trend = "🚀 UP" if prediction == 1 else "📉 DOWN"
        conf = (proba[1] if prediction == 1 else proba[0]) * 100
        
        msg = (
            f"🤖 *AI Stock Predictor (WhatsApp)*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📈 *Stock:* {ticker}\n"
            f"💵 *Price:* ₹{curr_price:,.2f}\n"
            f"🎯 *Prediction:* {trend}\n"
            f"🔔 *Confidence:* {conf:.1f}%\n"
            f"📊 *RSI:* {rsi_val:.1f}\n"
        )
        
        if investment_amount:
            inv = calculate_investment(df, investment_amount, prediction, conf)
            expected_profit = float(inv['expected_profit'])
            ps = "+" if expected_profit >= 0 else ""
            msg += (
                f"\n💰 *Investment (₹{investment_amount:,.0f})*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📦 *Shares:* {inv['shares']}\n"
                f"⚡ *Risk:* {inv['risk']}\n"
                f"✅ *Target (1D):* {ps}₹{expected_profit:,.0f} ({ps}{inv['expected_pct']}%)\n"
                f"📅 *W/M:* {inv['week']:+}% / {inv['month']:+}%"
            )
        else:
            msg += "\n💡 Hint: Try `Reliance 50000`"

        msg += "\n\n⚠️ Education only. Trade at your own risk."
        reply.body(msg)
        
    except Exception as e:
        reply.body(f"❌ Error: {str(e)}")
        
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
