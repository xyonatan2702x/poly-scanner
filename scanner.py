import requests
import os
import json
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    print(f"Attempting to send message...") # נראה את זה בלוג
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload)
        print(f"Telegram status: {resp.status_code}")
        print(f"Telegram response: {resp.text}")
    except Exception as e:
        print(f"Telegram Error: {e}")

print("--- STARTING SCANNER ---")

# 1. ננסה למשוך נתונים (בלי פילטרים מסובכים כדי להיות בטוחים שנקבל משהו)
url = "https://gamma-api.polymarket.com/markets?limit=5&active=True&order=volume24hr&direction=desc"
print(f"Fetching from: {url}")

try:
    response = requests.get(url)
    markets = response.json()
    print(f"Markets found: {len(markets)}")
except Exception as e:
    print(f"API Error: {e}")
    markets = []

# 2. נבנה הודעה בכל מקרה - גם אם אין שינוי!
message = "✅ **הסורק רץ תקין!**\n\nהנה המצב בשווקים כרגע:\n"

for m in markets:
    try:
        question = m.get('question', 'Unknown')
        # מנסים לחלץ מחיר, אם נכשל - נשים 0
        prices = json.loads(m.get('outcomePrices', '[0,0]')) if isinstance(m.get('outcomePrices'), str) else m.get('outcomePrices', [0,0])
        current_price = float(prices[0])
        message += f"📍 {question}\n💰 מחיר: {current_price:.2f}\n\n"
    except Exception as e:
        print(f"Error parsing market: {e}")
        continue

# 3. שלח את ההודעה עכשיו!
send_telegram_msg(message)

# 4. יצירת קובץ "סתם" כדי לראות שהשמירה עובדת
with open("prices_db.json", "w") as f:
    f.write(json.dumps({"status": "working", "time": time.time()}))

print("--- FINISHED ---")
