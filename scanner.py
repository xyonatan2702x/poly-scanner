import requests
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        # זה ידפיס לנו בגיטהב בדיוק מה הבעיה
        print(f"--- Telegram Diagnostic ---")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        print(f"---------------------------")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

# משיכת נתונים פשוטה לבדיקה
try:
    url = "https://gamma-api.polymarket.com/markets?tag_id=1&limit=3&active=True"
    markets = requests.get(url).json()
    msg = "🚀 בדיקת חיבור לסורק פולימרקט!"
    send_telegram_msg(msg)
except Exception as e:
    print(f"General error: {e}")

print("Finish")
