# 📊 Detailed Project Report: AI Stock Analysis & Predictor Bots

## 1. Introduction
The **AI Stock Analysis** project is an end-to-end machine learning pipeline and multi-channel bot integration system. The goal of the project is to provide retail investors with quick, accessible, and data-driven insights into short-term stock movements. By leveraging historical market data, technical indicators, and a powerful Random Forest classifier, the system democratizes quantitative financial analysis through familiar platforms like Telegram, WhatsApp, and Instagram.

---

## 2. Methodology & Code Architecture

### 2.1 Data Gathering
The foundation of the prediction model is built on historical price data fetched directly from Yahoo Finance via the `yfinance` library.
* **Scope:** The model focuses on the Top 50 Indian Companies (Nifty 50), including giants like Reliance, TCS, HDFC Bank, Infosys, etc.
* **Scale:** To ensure robustness, the training script (`train_massive_model.py`) fetches the **maximum available history** for each of these 50 tickers.
* **Result:** This creates a massive, multi-decade dataset spanning over **200,000+ trading days** combined across all stocks (`massive_training_dataset.csv`).

### 2.2 Feature Engineering
Raw price metrics (Open, High, Low, Close, Volume) alone are noisy. The `prepare_features()` function applies quantitative transformations to extract meaningful trends and momentum:
- **SMA_10 & SMA_50:** 10-day and 50-day Simple Moving Averages to capture short-term and medium-term trends.
- **Return:** The daily percentage change (`df['Close'].pct_change()`).
- **RSI (Relative Strength Index):** A 14-day momentum oscillator that measures the speed and change of price movements to identify overbought (>70) or oversold (<30) conditions.
- **Target Variable:** The model is framed as a binary classification problem. A target of `1` indicates the stock will close higher the *next* day, while `0` indicates it will close lower or flat.

### 2.3 Machine Learning Model
The core intelligence of the bots is powered by `scikit-learn`'s **RandomForestClassifier**.
- **Hyperparameters:** `n_estimators=100`, `max_depth=10`, `random_state=42`.
- **Why Random Forest?** It processes non-linear relationships well, is resistant to overfitting (due to the specified max_depth), and provides feature importance metrics implicitly.
- **Training Process:** The massive dataset is split into an 80/20 train-test ratio. The model is trained and subsequently serialized using `joblib` into `stock_model.pkl` (approx. 5.7 MB) so it can be loaded instantaneously by the user-facing bots.

---

## 3. Bot Integrations & User Experience

The predictive model is wrapped inside highly accessible bot interfaces. All bots share a unified logic pipeline:
1. **Ticker Extraction:** A robust Regex engine (`extract_ticker()`) parses user input (e.g., "Reliance", "AAPL", or full Screener/Groww/AngelOne URLs) and resolves them to their proper Yahoo Finance ticker symbol (e.g., `RELIANCE.NS`).
2. **Live Data Fetch:** The bot dynamically fetches the latest 2-5 years of data for the requested stock.
3. **Live Prediction:** The exact feature engineering logic applied during training is applied to the live data point. The pre-trained model outputs a prediction predicting Tomorrow's trajectory along with a **Confidence Score** derived from `predict_proba`.
4. **Investment Calculator:** If the user provides a monetary amount (e.g., "Reliance 50000"), the bot calculates:
   - Expected Profit (based on localized 20-day volatility and AI confidence weighting).
   - Best & Worst case scenarios.
   - Dynamic Risk Rating (Low/Medium/High) based on recent standard deviation.

### 3.1 Telegram Bot (`telegram_bot.py`)
- Powered by `pyTelegramBotAPI`. Uses long polling (`bot.infinity_polling()`) to actively listen for messages. Formats responses beautifully using Markdown and native Telegram emojis.

### 3.2 WhatsApp & Instagram Bots (`whatsapp_bot.py`, `instagram_bot.py`)
- Powered by `Flask` and `Twilio` Webhooks (`MessagingResponse`).
- These scripts act as active HTTP servers listening on ports 5000/5001. They parse `POST` requests sent by Meta/Twilio whenever a user sends a message on WhatsApp or Instagram, responding with formatted XML.

---

## 4. Autonomous Deployment System
Deploying local webhooks to the public internet securely is handled by custom wrapper scripts:
- **Ngrok Deployer (`run_instagram_ngrok.py`)**: Uses the `pyngrok` library to spawn the Flask app in a background thread while automatically establishing a secure Ngrok tunnel and exposing the public Webhook URL.
- **Serveo SSH Tunnel (`run_instagram_serveo.py`)**: An authentication-free autonomous alternative that utilizes `subprocess` to trigger a reverse SSH tunnel via `serveo.net`, entirely bypassing third-party login requirements or API tokens.

## 5. Conclusion
This project demonstrates a production-grade transition from raw financial data scraping to machine learning, and finally to cross-platform product deployment. It packages complex statistical modeling into an interface as simple as texting a friend.
