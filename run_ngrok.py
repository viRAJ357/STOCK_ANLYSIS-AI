"""
WhatsApp Bot + Ngrok Launcher
Run this script to start the bot and expose it publicly via ngrok.
"""
import threading
import time
import os
import sys

from pyngrok import ngrok, conf

# ── Ngrok Auth Token ────────────────────────────────────────────────────────
NGROK_AUTH_TOKEN = "3BHkrH6bJIW94romykEoGAYFYII_2Gjx7zf4MaJhYd2mZpg4Q"
FLASK_PORT = 5000

def start_flask():
    """Run the WhatsApp Flask bot."""
    # Import app from whatsapp_bot.py
    from whatsapp_bot import app
    print(f"🚀 Starting Flask server on port {FLASK_PORT}...")
    app.run(port=FLASK_PORT, use_reloader=False)

def main():
    # Configure ngrok authtoken
    print("🔑 Configuring ngrok authtoken...")
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)  # Give Flask a moment to start

    # Open ngrok tunnel
    print(f"🌐 Opening ngrok tunnel on port {FLASK_PORT}...")
    tunnel = ngrok.connect(FLASK_PORT)
    public_url = tunnel.public_url

    print("\n" + "="*60)
    print("✅ DEPLOYMENT SUCCESSFUL!")
    print("="*60)
    print(f"🌍 Public URL  : {public_url}")
    print(f"📱 WhatsApp Webhook: {public_url}/whatsapp")
    print("="*60)
    print("\n💡 Set the WhatsApp webhook in Twilio Console:")
    print(f"   Messaging → Sandbox → Webhook URL: {public_url}/whatsapp")
    print("\nPress Ctrl+C to stop the server.\n")

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        ngrok.kill()
        sys.exit(0)

if __name__ == "__main__":
    main()
