import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import joblib
import os

st.set_page_config(page_title="Share Market AI Predictor", page_icon="📈", layout="wide")

# Custom UI Stylesheet - Premium Look
st.markdown("""
<style>
    .pred-up {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 8px solid #28a745;
    }
    .pred-down {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 8px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 AI Share Market Predictor")
st.markdown("Yeh AI Model lagbhag **2 Lakh historical data points** (Nifty 50 companies) par fully trained hai.")
st.markdown("---")

# Sidebar
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.header("Prediction Settings")
ticker_input = st.sidebar.text_input(
    "Stock Symbol / Company Link",
    "RELIANCE.NS",
    help="Koi bhi link ya naam: 'AAPL', 'Reliance', 'screener.in/company/RELIANCE', 'groww.in/stocks/reliance-share-price', 'angelone.in/stocks/reliance-share-price'"
)
investment_amount = st.sidebar.number_input(
    "💰 Investment Amount (₹)",
    min_value=1000, max_value=10000000,
    value=50000, step=1000,
    help="Aap kitna paisa lagana chahte hain? Model profit/loss estimate karega."
)

def extract_ticker(input_str):
    import re
    input_str = input_str.strip().lower()
    
    # 1. Yahoo Finance Link Checking
    if "finance.yahoo.com/quote/" in input_str:
        match = re.search(r'finance\.yahoo\.com/quote/([^/\?]+)', input_str)
        if match:
            return match.group(1).upper()
    
    # NSE India link (e.g. nseindia.com/get-quote/equity/JINDALSTEL/...)
    match = re.search(r'nseindia\.com/(?:get-quote|equity-stockWatch)/equity/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    match = re.search(r'nseindia\.com/[^/]+/([A-Z]{2,20})(?:/|\?|$)', input_str.upper())
    if match: return match.group(1) + ".NS"
            
    # 2. Google Finance
    match = re.search(r'google\.com/finance/quote/([^:]+):([^/\?]+)', input_str)
    if match:
        ticker_part = match.group(1).upper()
        exchange = match.group(2).upper()
        if exchange == "NSE": return ticker_part + ".NS"
        if exchange == "BOM": return ticker_part + ".BO"
        return ticker_part

    # 3. Screener.in
    match = re.search(r'screener\.in/company/([^/\?]+)', input_str)
    if match: return match.group(1).upper() + ".NS"
    
    # 4. Groww link (e.g. groww.in/stocks/reliance-share-price)
    match = re.search(r'groww\.in/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    
    # 5. Angel One / Angel Broking link
    match = re.search(r'angelone\.in/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    match = re.search(r'angelbroking\.com/stocks/([^/\?]+)', input_str)
    if match:
        slug = match.group(1).replace("-share-price", "").replace("-", "")
        return slug.upper() + ".NS"
    
    # 6. TradingView
    match = re.search(r'tradingview\.com/symbols/([A-Z]+)-([^/\?]+)', input_str.upper())
    if match:
        exchange_tv, ticker_tv = match.group(1), match.group(2)
        if exchange_tv == "NSE": return ticker_tv + ".NS"
        if exchange_tv == "BSE": return ticker_tv + ".BO"
        return ticker_tv

    # 7. Extract company name if user pastes a URL (e.g. www.asianpaints.com)
    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+?)\.(?:com|in|co\.in|net|org)', input_str)
    if domain_match:
        keyword = domain_match.group(1).lower()
    else:
        keyword = input_str.lower()
        
    keyword = keyword.replace(" ", "").replace("-", "")

    # 3. Smart Dictionary Mappings for Indian Nifty 50 & US Tech Giants
    mappings = {
        "asianpaint": "ASIANPAINT.NS", "reliance": "RELIANCE.NS", "tcs": "TCS.NS",
        "hdfc": "HDFCBANK.NS", "hdfcbank": "HDFCBANK.NS", "icici": "ICICIBANK.NS",
        "icicibank": "ICICIBANK.NS", "infosys": "INFY.NS", "infy": "INFY.NS",
        "sbi": "SBIN.NS", "statebank": "SBIN.NS", "bhartiartl": "BHARTIARTL.NS",
        "airtel": "BHARTIARTL.NS", "itc": "ITC.NS", "hindunilvr": "HINDUNILVR.NS",
        "hul": "HINDUNILVR.NS", "lt": "LT.NS", "larsen": "LT.NS",
        "bajfinance": "BAJFINANCE.NS", "bajajfinance": "BAJFINANCE.NS",
        "hcltech": "HCLTECH.NS", "hcl": "HCLTECH.NS", "maruti": "MARUTI.NS",
        "sunpharma": "SUNPHARMA.NS", "tatamotors": "TATAMOTORS.NS",
        "kotak": "KOTAKBANK.NS", "ntpc": "NTPC.NS", "mahindra": "M&M.NS",
        "axisbank": "AXISBANK.NS", "axis": "AXISBANK.NS", "titan": "TITAN.NS",
        "ongc": "ONGC.NS", "tatasteel": "TATASTEEL.NS", "coalindia": "COALINDIA.NS",
        "bajajfinsv": "BAJAJFINSV.NS", "powergrid": "POWERGRID.NS",
        "ltim": "LTIM.NS", "bajajauto": "BAJAJ-AUTO.NS", "adaniports": "ADANIPORTS.NS",
        "adanient": "ADANIENT.NS", "adani": "ADANIENT.NS", "techm": "TECHM.NS",
        "grasim": "GRASIM.NS", "ultracemco": "ULTRACEMCO.NS", "ultratech": "ULTRACEMCO.NS",
        "nestle": "NESTLEIND.NS", "wipro": "WIPRO.NS", "jswsteel": "JSWSTEEL.NS",
        "indusind": "INDUSINDBK.NS", "hindalco": "HINDALCO.NS", "divislab": "DIVISLAB.NS",
        "drreddy": "DRREDDY.NS", "tataconsum": "TATACONSUM.NS", "cipla": "CIPLA.NS",
        "britannia": "BRITANNIA.NS", "apollo": "APOLLOHOSP.NS", "eicher": "EICHERMOT.NS",
        "bpcl": "BPCL.NS", "hero": "HEROMOTOCO.NS", "shreecem": "SHREECEM.NS",
        
        "apple": "AAPL", "google": "GOOGL", "alphabet": "GOOGL",
        "microsoft": "MSFT", "amazon": "AMZN", "tesla": "TSLA"
    }
    
    for key, mapped_ticker in mappings.items():
        if key in keyword:
            return mapped_ticker

    return input_str.upper()

ticker = extract_ticker(ticker_input)
period = st.sidebar.selectbox("Past Data Reference", ["1y", "2y", "5y", "10y", "max"], index=2)
st.sidebar.markdown("---")
st.sidebar.info("Model kal ke (Next Trading Session) market close ko predict karta hai.")

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
    return df.dropna()

@st.cache_resource
def load_model():
    if os.path.exists("stock_model.pkl"):
        return joblib.load("stock_model.pkl")
    return None

def calculate_investment(df, investment_amount, prediction, confidence=100.0):
    """Stock-specific P&L estimate using RECENT momentum"""
    closes = df['Close']
    returns = closes.pct_change().dropna()
    current_price = float(closes.iloc[-1])
    
    # === RECENT 20-day metrics ===
    recent_returns = returns.iloc[-20:]
    recent_avg = float(recent_returns.mean()) * 100
    recent_vol = float(recent_returns.std()) * 100
    
    shares = investment_amount / current_price
    
    confidence_factor = confidence / 100.0
    if prediction == 1:
        expected_move_pct = abs(recent_avg) * confidence_factor
    else:
        expected_move_pct = -abs(recent_avg) * confidence_factor
    
    if abs(expected_move_pct) < 0.01:
        expected_move_pct = recent_vol * 0.5 * (1 if prediction == 1 else -1)

    expected_profit = investment_amount * (expected_move_pct / 100)
    best_case = investment_amount * ((expected_move_pct + recent_vol) / 100)
    worst_case = investment_amount * ((expected_move_pct - recent_vol) / 100)
    
    return {
        "shares": round(float(shares), 2),
        "expected_pct": round(float(expected_move_pct), 2),
        "expected_profit": round(float(expected_profit), 2),
        "best_case": round(float(best_case), 2),
        "worst_case": round(float(worst_case), 2),
        "volatility": round(float(recent_vol), 2)
    }

model = load_model()

if model is None:
    st.error("⚠️ Model file 'stock_model.pkl' nahi milli. Kripya pehle model train karein.")
else:
    if st.sidebar.button("🔮 Pata lagao kal kya hoga?", use_container_width=True):
        with st.spinner(f"{ticker} ka live data Yahoo Finance se download ho raha hai..."):
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                st.error("Is stock ka data nahi mila. Sahi symbol check karein.")
            else:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"📊 Live Data Chart: {ticker}")
                    # Candlestick ya line chart, hum normal st.line_chart use kar sakte hain
                    st.line_chart(df[['Close', 'Open']])
                
                prepared_df = prepare_features(df)
                
                with col2:
                    if prepared_df.empty:
                        st.error("Technical analysis (Features) calculate karne ke liye data bohot kam hai.")
                    else:
                        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
                        latest_data = prepared_df.iloc[-1][features].to_frame().T
                        
                        # AI Magic here
                        prediction = model.predict(latest_data)[0]
                        proba = model.predict_proba(latest_data)[0]
                        
                        st.subheader("💡 Kal Ki Prediction (Next Day)")
                        
                        confidence = proba[1] * 100 if prediction == 1 else proba[0] * 100
                        
                        if prediction == 1:
                            st.markdown(f'<div class="pred-up">⬆️ Share Uthega (UP)<br><span style="font-size:20px; font-weight:normal;">Machine Confidence: {confidence:.1f}%</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="pred-down">⬇️ Share Girega (DOWN)<br><span style="font-size:20px; font-weight:normal;">Machine Confidence: {confidence:.1f}%</span></div>', unsafe_allow_html=True)
                        
                        current_price = float(latest_data['Close'].iloc[0])
                        rsi_val = float(latest_data['RSI'].iloc[0])
                        
                        # RSI Commentary
                        if rsi_val > 70:
                            rsi_note = "🔴 Overbought — Bahut upar hai, girne ka risk"
                        elif rsi_val < 30:
                            rsi_note = "🟢 Oversold — Bahut neeche, rebound ho sakta hai"
                        else:
                            rsi_note = "🟡 Normal Zone"
                        
                        st.caption(f"Last Price: ₹{current_price:.2f} | RSI: {rsi_val:.1f} — {rsi_note}")
                
                # Investment Calculator Section
                st.markdown("---")
                st.subheader("💰 Investment Profit/Loss Calculator")
                
                inv = calculate_investment(df, investment_amount, prediction)
                
                ci1, ci2, ci3, ci4 = st.columns(4)
                ci1.metric("💸 Investment", f"₹{investment_amount:,.0f}")
                ci2.metric("📦 Shares (approx)", f"{inv['shares']:.2f}")
                ci3.metric("📈 Daily Volatility", f"±{inv['volatility']:.2f}%")
                ci4.metric("📊 Avg Expected Move", f"{inv['expected_pct']:+.2f}%")
                
                cr1, cr2, cr3 = st.columns(3)
                cr1.metric(
                    "✅ Expected Profit/Loss",
                    f"₹{inv['expected_profit']:+,.0f}",
                    delta=f"{inv['expected_pct']:+.2f}%"
                )
                cr2.metric(
                    "🟢 Best Case (Optimistic)",
                    f"₹{inv['best_case']:+,.0f}",
                    delta="1-sigma up"
                )
                cr3.metric(
                    "🔴 Worst Case (Risk)",
                    f"₹{inv['worst_case']:+,.0f}",
                    delta="1-sigma down",
                    delta_color="inverse"
                )
                
                st.info("⚠️ **Disclaimer:** Yeh predictions pichle 2 Lakh+ data points ke technical analysis par based ek AI algorithm ka anuman hai. Real time news/events isko galat bhi sabit kar sakte hain, isliye financial risks apne zimmewari par lein.")
                
                with st.expander("🔍 View Technical Indicators (Latest Row & Raw Data)"):
                    st.write("Current Features sent to the Model:")
                    st.dataframe(latest_data)
                    st.write("Recent Historical Data:")
                    st.dataframe(df.tail(10))

