# 📈 AI Stock Analysis & Predictor Bots TELEGRAM BOT DEPLOYMENT http://t.me/nikhil_stock_bot

> [!NOTE] 
> 📄 **[Click here to read the Detailed Project Report & Methodology](PROJECT_REPORT.md)**

This repository implements a powerful AI-based Stock Market Analysis project. It features a trained machine learning model capable of analyzing historical stock data and technical indicators to predict short-term stock movements.

The project also includes fully functional conversational bots for **Telegram**, **WhatsApp**, and **Instagram**! These bots serve as dedicated financial assistants, allowing users to check stock prices, get AI predictions, and receive detailed investment risk/reward calculations by simply sending a message.

## 🚀 Project Features
- **Machine Learning Model**: Trained on over 200,000+ data points for accurate pattern recognition.
- **Technical Indicators**: Calculates SMA_10, SMA_50, and RSI for comprehensive trend analysis.
- **Investment Calculator**: Estimates projected profits, best/worst-case scenarios, and risk levels based on recent stock volatility.
- **Multi-Platform Bots**: Interfaces for Telegram, WhatsApp, and Instagram using Twilio/Meta webhooks.
- **Autonomous Deployment**: Includes Ngrok and Serveo scripts for seamless, autonomous local deployment and webhook tunneling.

---

## 📂 Project Structure

```text
📦 STOCK_ANLYSIS-AI
 ┣ 📜 README.md                 # Project Overview & Structure
 ┣ 📜 app.py                    # Main web app or API interface
 ┣ 📜 stock_model.pkl           # Pre-trained Machine Learning Model
 ┣ 📜 stock_predictor.py        # Core prediction and ML logic script
 ┣ 📜 requirements.txt          # Python dependencies
 ┃
 ┣ 🤖 BOT INTERFACES
 ┃ ┣ 📜 telegram_bot.py         # Telegram Bot implementation (using pyTelegramBotAPI)
 ┃ ┣ 📜 whatsapp_bot.py         # WhatsApp Bot implementation (via Twilio webhook & Flask)
 ┃ ┗ 📜 instagram_bot.py        # Instagram Bot implementation (via Twilio webhook & Flask)
 ┃
 ┣ 🌐 DEPLOYMENT & TUNNELS
 ┃ ┣ 📜 run_ngrok.py            # Script to run Flask + Ngrok tunnel automatically
 ┃ ┣ 📜 run_instagram_ngrok.py  # Instagram-specific Ngrok launcher
 ┃ ┗ 📜 run_instagram_serveo.py # Autonomous Serveo SSH tunnel launcher (No auth required)
 ┃
 ┗ 📊 DATA & TRAINING
   ┣ 📜 train_from_csv.py       # Script to train models from local CSV datasets
   ┣ 📜 train_massive_model.py  # Script for training the large-scale 2-Lakh+ data model
   ┣ 📜 AAPL_dataset.csv        # Apple stock historical dataset
   ┣ 📜 RELIANCE_dataset.csv    # Reliance stock historical dataset
   ┗ 📜 massive_training_dataset.csv # The primary large-scale training dataset
```

## 🛠️ Setup & Installation
1. Clone the repository: `git clone https://github.com/viRAJ357/STOCK_ANLYSIS-AI.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run any bot: `python telegram_bot.py` or use the autonomous deployment scripts like `python run_instagram_serveo.py` to get a public URL for Webhooks.
