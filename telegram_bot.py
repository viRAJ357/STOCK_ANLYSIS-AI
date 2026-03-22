import telebot
import yfinance as yf
import pandas as pd
import joblib
import os
import re
import numpy as np

TOKEN = "8552070438:AAFAAQGut_XhPX9edgkHn1xS1SupiVdO4Ak"
bot = telebot.TeleBot(TOKEN)

def extract_ticker(input_str):
    import re
    input_str = input_str.strip()
    
    match = re.search(r'finance\.yahoo\.com/quote/([^/\?]+)', input_str)
    if match: return match.group(1).upper()
    
    # NSE India link (e.g. nseindia.com/get-quote/equity/JINDALSTEL/...)
    match = re.search(r'nseindia\.com/(?:get-quote|equity-stockWatch)/equity/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    match = re.search(r'nseindia\.com/[^/]+/([A-Z]{2,20})(?:/|\?|$)', input_str.upper())
    if match: return match.group(1) + ".NS"
    
    match = re.search(r'google\.com/finance/quote/([^:]+):([^/\?]+)', input_str)
    if match: 
        ticker = match.group(1).upper()
        exchange = match.group(2).upper()
        if exchange == "NSE": return ticker + ".NS"
        if exchange == "BOM": return ticker + ".BO"
        return ticker
        
    match = re.search(r'screener\.in/company/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    
    # ✅ Groww link support
    match = re.search(r'groww\.in/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    
    # ✅ Angel One / Angel Broking link support
    match = re.search(r'angelone\.in/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    match = re.search(r'angelbroking\.com/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    
    match = re.search(r'tradingview\.com/symbols/([A-Z]+)-([^/\?]+)', input_str.upper())
    if match:
        exchange, ticker = match.group(1), match.group(2)
        if exchange == "NSE": return ticker + ".NS"
        if exchange == "BSE": return ticker + ".BO"
        return ticker

    input_str_lower = input_str.lower()
    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+?)\.(?:com|in|co\.in|net|org)', input_str_lower)
    if domain_match:
        keyword = domain_match.group(1).lower()
    else:
        keyword = input_str_lower
        
    keyword = keyword.replace(" ", "").replace("-", "")

    mappings = {
        "asianpaint": "ASIANPAINT.NS", "reliance": "RELIANCE.NS", "tcs": "TCS.NS",
        "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS", "infosys": "INFY.NS", "infy": "INFY.NS",
        "sbi": "SBIN.NS", "statebank": "SBIN.NS", "bharti": "BHARTIARTL.NS", "airtel": "BHARTIARTL.NS",
        "itc": "ITC.NS", "hindunilvr": "HINDUNILVR.NS", "hul": "HINDUNILVR.NS", 
        "larsen": "LT.NS", "lt": "LT.NS", "bajfinance": "BAJFINANCE.NS", "bajajfinance": "BAJFINANCE.NS",
        "hcltech": "HCLTECH.NS", "hcl": "HCLTECH.NS", "maruti": "MARUTI.NS",
        "sunpharma": "SUNPHARMA.NS", "tatamotors": "TATAMOTORS.NS",
        "kotak": "KOTAKBANK.NS", "ntpc": "NTPC.NS", "mahindra": "M&M.NS",
        "axis": "AXISBANK.NS", "titan": "TITAN.NS", "ongc": "ONGC.NS",
        "tatasteel": "TATASTEEL.NS", "coalindia": "COALINDIA.NS",
        "wipro": "WIPRO.NS", "jswsteel": "JSWSTEEL.NS", "zomato": "ZOMATO.NS",
        "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT", "amazon": "AMZN", "tesla": "TSLA"
    }
    
    for key, mapped_ticker in mappings.items():
        if key in keyword:
            return mapped_ticker
            
    if domain_match and len(keyword) < 15:
        return keyword.upper() + ".NS"

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
    rs = gain / loss
    df.loc[:, 'RSI'] = 100 - (100 / (1 + rs))
    
    df.loc[:, 'Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df.dropna()

def calculate_investment(df, investment_amount, prediction, confidence):
    """Stock-specific P&L estimate using RECENT momentum (not all-time averages)"""
    closes = df['Close']
    returns = closes.pct_change().dropna()
    current_price = float(closes.iloc[-1])
    
    # === RECENT 20-day metrics (STOCK-SPECIFIC — will differ per stock!) ===
    recent_returns = returns.iloc[-20:]   # last 20 trading days
    recent_avg = float(recent_returns.mean()) * 100      # recent avg daily return %
    recent_vol = float(recent_returns.std()) * 100        # recent daily volatility %
    
    # Overall volatility for risk rating
    overall_vol = float(returns.std()) * 100
    
    # Period-wise actual returns
    week_return = ((closes.iloc[-1] / closes.iloc[-min(5, len(closes))]) - 1) * 100
    month_return = ((closes.iloc[-1] / closes.iloc[-min(22, len(closes))]) - 1) * 100
    three_month_return = ((closes.iloc[-1] / closes.iloc[-min(66, len(closes))]) - 1) * 100
    
    # 52-week high/low
    year_data = closes.iloc[-min(252, len(closes)):]
    high_52w = float(year_data.max())
    low_52w = float(year_data.min())
    from_52w_high = ((current_price - high_52w) / high_52w) * 100
    
    shares = investment_amount / current_price
    
    # Expected move = recent avg daily return, weighted by AI confidence
    confidence_factor = confidence / 100.0
    if prediction == 1:
        expected_move_pct = abs(recent_avg) * confidence_factor
    else:
        expected_move_pct = -abs(recent_avg) * confidence_factor
    
    # If recent_avg is near zero, fallback to recent volatility-based estimate
    if abs(expected_move_pct) < 0.01:
        expected_move_pct = recent_vol * 0.5 * (1 if prediction == 1 else -1)

    expected_profit = investment_amount * (expected_move_pct / 100)
    best_case = investment_amount * ((expected_move_pct + recent_vol) / 100)
    worst_case = investment_amount * ((expected_move_pct - recent_vol) / 100)
    
    # Weekly/Monthly projected
    week_projected = investment_amount * (week_return / 100) if abs(week_return) < 50 else 0
    month_projected = investment_amount * (month_return / 100) if abs(month_return) < 100 else 0
    
    # Risk Rating (based on recent vol, not all-time)
    if recent_vol > 3:
        risk = "🔴 HIGH RISK"
    elif recent_vol > 1.5:
        risk = "🟡 MEDIUM RISK"
    else:
        risk = "🟢 LOW RISK"
    
    return {
        "shares": round(float(shares), 2),
        "expected_pct": round(float(expected_move_pct), 2),
        "expected_profit": round(float(expected_profit), 2),
        "best_case": round(float(best_case), 2),
        "worst_case": round(float(worst_case), 2),
        "volatility": round(float(recent_vol), 2),
        "week_return": round(float(week_return), 2),
        "month_return": round(float(month_return), 2),
        "three_month_return": round(float(three_month_return), 2),
        "high_52w": round(float(high_52w), 2),
        "low_52w": round(float(low_52w), 2),
        "from_52w_high": round(float(from_52w_high), 2),
        "week_projected": round(float(week_projected), 2),
        "month_projected": round(float(month_projected), 2),
        "risk": risk,
        "current_price": round(float(current_price), 2)
    }

model = None
if os.path.exists("stock_model.pkl"):
    print("Loading 2 Lakh+ Data Model Brain...")
    model = joblib.load("stock_model.pkl")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "🤖 *AI Stock Predictor Bot* mein swagat hai! 📈\n\n"
        "Main 2 Lakh+ historical data par trained hoon.\n\n"
        "*Kya bhej sakte hain:*\n"
        "• Naam: `Reliance`, `TCS`, `Mahindra`\n"
        "• Symbol: `AAPL`, `RELIANCE.NS`\n"
        "• Link: Screener, Groww, Angel One, NSE India\n\n"
        "*Investment Calculator:*\n"
        "Naam ke saath amount likhein:\n"
        "`Mahindra 2000`\n"
        "`Tata 5000`\n"
        "`Reliance 50000`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def predict_stock(message):
    if model is None:
        bot.reply_to(message, "⚠️ Model load nahi hua hai. Server par error hai.")
        return
    
    text = message.text.strip()
    
    # Check investment amount (last word)
    investment_amount = None
    parts = text.split()
    if len(parts) >= 2:
        try:
            investment_amount = float(parts[-1].replace(",", ""))
            text = " ".join(parts[:-1])
        except ValueError:
            pass
        
    bot.reply_to(message, "📡 Live Market Data fetch kar raha hoon... thoda rukiye ⏳")
    ticker = extract_ticker(text)
    
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5y")
        
        if df.empty:
            bot.reply_to(message, f"❌ '{ticker}' ka data nahi mila. Sahi symbol bhejein.")
            return
            
        prepared_df = prepare_features(df)
        if prepared_df.empty:
            bot.reply_to(message, "❌ Technical indicators ke liye data kam hai.")
            return
            
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
        latest_data = prepared_df.iloc[-1][features].to_frame().T
        
        prediction = model.predict(latest_data)[0]
        proba = model.predict_proba(latest_data)[0]
        current_price = float(latest_data['Close'].iloc[0])
        rsi_val = float(latest_data['RSI'].iloc[0])
        sma10 = float(latest_data['SMA_10'].iloc[0])
        sma50 = float(latest_data['SMA_50'].iloc[0])
        
        if prediction == 1:
            confidence = proba[1] * 100
            trend_line = "🚀 *Kal Upar Jayega (UP)* ⬆️"
            trend_emoji = "📈"
        else:
            confidence = proba[0] * 100
            trend_line = "🔥 *Kal Niche Girega (DOWN)* ⬇️"
            trend_emoji = "📉"
        
        # RSI condition
        if rsi_val > 70:
            rsi_comment = "🔴 Overbought (careful!)"
        elif rsi_val < 30:
            rsi_comment = "🟢 Oversold (rebound?)"
        else:
            rsi_comment = "🟡 Normal"
        
        # SMA Trend
        if current_price > sma10 > sma50:
            sma_trend = "🟢 Strong Uptrend"
        elif current_price > sma50:
            sma_trend = "🟡 Mild Uptrend"
        elif current_price < sma10 < sma50:
            sma_trend = "🔴 Strong Downtrend"
        else:
            sma_trend = "🟡 Sideways"
        
        msg = (
            f"{trend_emoji} *{ticker} — PREDICTION* {trend_emoji}\n"
            f"{'─'*30}\n"
            f"💵 *Price:* `₹{current_price:.2f}`\n"
            f"{trend_line}\n"
            f"🤖 *Confidence:* `{confidence:.1f}%`\n"
            f"📊 *RSI ({rsi_val:.0f}):* {rsi_comment}\n"
            f"📉 *Trend:* {sma_trend}\n"
        )
        
        # Investment Calculator
        if investment_amount:
            inv = calculate_investment(df, investment_amount, prediction, confidence)
            ps = "+" if inv['expected_profit'] >= 0 else ""
            ws = "+" if inv['worst_case'] >= 0 else ""
            bs = "+" if inv['best_case'] >= 0 else ""
            
            msg += (
                f"\n💰 *INVESTMENT — ₹{investment_amount:,.0f}*\n"
                f"{'─'*30}\n"
                f"📦 *Shares:* `{inv['shares']:.2f}` @ ₹{inv['current_price']:.2f}\n"
                f"⚡ *Risk Level:* {inv['risk']}\n\n"
                f"*Kal Ka Estimate (1 Day):*\n"
                f"✅ Expected: `{ps}₹{inv['expected_profit']:,.0f}` ({ps}{inv['expected_pct']:.2f}%)\n"
                f"🟢 Best: `{bs}₹{inv['best_case']:,.0f}`\n"
                f"🔴 Worst: `{ws}₹{inv['worst_case']:,.0f}`\n\n"
                f"*Stock Performance:*\n"
                f"📅 1 Week: `{inv['week_return']:+.2f}%` (₹{inv['week_projected']:+,.0f})\n"
                f"📅 1 Month: `{inv['month_return']:+.2f}%` (₹{inv['month_projected']:+,.0f})\n"
                f"📅 3 Month: `{inv['three_month_return']:+.2f}%`\n\n"
                f"*52-Week Range:*\n"
                f"⬇️ Low: `₹{inv['low_52w']:,.2f}`\n"
                f"⬆️ High: `₹{inv['high_52w']:,.2f}`\n"
                f"📍 From High: `{inv['from_52w_high']:+.1f}%`\n"
            )
        else:
            msg += "\n💡 Amount bhi likhein: `Reliance 50000`\n"
        
        msg += "\n⚠️ _Disclaimer: Educational only. Trade at your own risk._"
            
        bot.reply_to(message, msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Telegram Bot Server Running!")
bot.infinity_polling()
