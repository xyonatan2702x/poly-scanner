import requests
import os
import json

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_FILE = "prices_db.json"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_markets():
    url = "https://gamma-api.polymarket.com/markets?tag_id=1&limit=10&active=True&order=volume24hr&direction=desc"
    return requests.get(url).json()

# טעינת מחירים קודמים
old_prices = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        old_prices = json.load(f)

new_markets = get_markets()
current_prices = {}
alerts = []

for m in new_markets:
    m_id = m.get('id')
    question = m.get('question')
    # מחיר YES הוא בד"כ האינדקס הראשון
    try:
        current_price = float(m.get('outcomePrices', [0, 0])[0])
    except: continue
    
    current_prices[m_id] = current_price
    
    # בדיקה אם יש שינוי
    if m_id in old_prices:
        old_p = old_prices[m_id]
        diff = current_price - old_p
        # אם השינוי גדול מ-1% (0.01)
        if abs(diff) >= 0.00001:
            direction = "📈 עלה" if diff > 0 else "📉 ירד"
            alerts.append(f"*{question}*\n{direction} ל-{current_price:.2f} (היה {old_p:.2f})")

# שמירת המחירים החדשים לפעם הבאה
with open(DB_FILE, "w") as f:
    json.dump(current_prices, f)

# שליחת התראות אם נמצאו שינויים
if alerts:
    full_message = "🔔 *זיהיתי שינויים בפולימרקט:*\n\n" + "\n\n".join(alerts)
    send_telegram_msg(full_message)
else:
    print("No significant changes detected.")
