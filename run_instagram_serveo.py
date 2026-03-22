import subprocess
import threading
import time
import sys
import re

FLASK_PORT = 5001

def start_flask():
    """Run the Instagram Flask bot."""
    print(f"[Web] Starting Flask server on port {FLASK_PORT}...")
    subprocess.run([sys.executable, "instagram_bot.py"], check=True)

def main():
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)  # Give Flask a moment to start

    print("[Tunnel] Starting Serveo tunnel...")
    # Open serveo tunnel
    process = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:localhost:{FLASK_PORT}", "serveo.net"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    public_url = None
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if "Forwarding HTTP traffic from" in line:
            public_url = line.split("from")[-1].strip()
            break
        elif "serveousercontent.com" in line:
            match = re.search(r'(https://[a-zA-Z0-9-]+\.serveousercontent\.com)', line)
            if match:
                public_url = match.group(1)
                break
        elif "http" in line:
            match = re.search(r'(https://[^\s]+)', line)
            if match:
                public_url = match.group(1)
                break
        else:
            print(f"[Serveo Log] {line}")
            
    if public_url:
        print("\n" + "="*60)
        print("DEPLOYMENT SUCCESSFUL (AUTONOMOUS)!")
        print("="*60)
        print(f"Public URL  : {public_url}")
        print(f"Instagram Webhook: {public_url}/instagram")
        print("="*60)
        print("\n[Hint] Set the Instagram webhook in Twilio Console:")
        print(f"   Messaging -> Sandbox -> Webhook URL: {public_url}/instagram")
        print("\nPress Ctrl+C to stop the server.\n")
    else:
        print("\n[Error] Could not find Public URL from Serveo. Exiting.")
        sys.exit(1)

    # Keep alive and print remaining output
    try:
        while True:
            out = process.stdout.readline()
            if out == '' and process.poll() is not None:
                break
            if out:
                print(f"[Serveo] {out.strip()}")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
