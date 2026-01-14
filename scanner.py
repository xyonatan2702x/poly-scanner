import requests
import os

# הגדרות
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_top_politics_markets():
    # פנייה ל-API של פולימרקט לקבלת שווקים פוליטיים מובילים
    url = "https://gamma-api.polymarket.com/markets?tag_id=1&limit=10&active=True&order=volume24hr&direction=desc"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# ריצה ראשונית לבדיקה
markets = get_top_politics_markets()
message = "🤖 *סורק פולימרקט התחיל לעבוד!*\n\n"
for m in markets:
    title = m.get('question', 'Unknown')
    outcome = m.get('outcomePrices', ['N/A', 'N/A'])
    message += f"📍 {title}\n💰 מחיר YES: {outcome[0]}\n\n"

send_telegram_msg(message)
print("Done!")
