import requests
import os
import json

# --- הגדרות ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_FILE = "prices_db.json"
THRESHOLD = 0.01  # רגישות: 0.01 זה 1%. רוצה יותר רגיש? שנה ל-0.005

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending msg: {e}")

def get_politics_markets():
    # שואב את 10 השווקים המובילים בקטגוריית פוליטיקה (Tag ID 1)
    url = "https://gamma-api.polymarket.com/markets?tag_id=1&limit=10&active=True&order=volume24hr&direction=desc"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return []

# 1. טעינת זיכרון (מה היה המחיר בפעם הקודמת?)
old_prices = {}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            old_prices = json.load(f)
    except: pass

# 2. הבאת נתונים טריים
markets = get_politics_markets()
current_prices = {}
alerts = []

print(f"Checking {len(markets)} markets...")

for m in markets:
    m_id = str(m.get('id'))
    question = m.get('question', 'Unknown')
    
    # חילוץ מחיר ה-YES
    try:
        raw_prices = m.get('outcomePrices')
        # טיפול במקרים שהמחיר מגיע כמחרוזת ג'ייסון
        if isinstance(raw_prices, str):
            prices = json.loads(raw_prices)
        else:
            prices = raw_prices
            
        current_price = float(prices[0]) # המחיר של האופציה הראשונה (לרוב YES)
        current_prices[m_id] = current_price
    except:
        continue # אם לא הצלחנו לקרוא מחיר, מדלגים

    # 3. בדיקת שינויים
    if m_id in old_prices:
        old_p = old_prices[m_id]
        diff = current_price - old_p
        
        # אם השינוי גדול מהרף שהגדרנו
        if abs(diff) >= THRESHOLD:
            direction = "📈 זינוק" if diff > 0 else "📉 צניחה"
            change_pct = diff * 100
            # הוספת התראה לרשימה
            alerts.append(f"*{question}*\n{direction}: מ-{old_p:.2f} ל-{current_price:.2f} ({change_pct:+.1f}%)")

# 4. שמירת המצב העדכני לזיכרון
with open(DB_FILE, "w") as f:
    json.dump(current_prices, f)

# 5. דיווח
if alerts:
    print("Changes detected! Sending Telegram...")
    full_message = "🚨 *עדכון פוליטי חם:*\n\n" + "\n\n".join(alerts)
    send_telegram_msg(full_message)
else:
    print("No significant changes. Staying quiet.")
