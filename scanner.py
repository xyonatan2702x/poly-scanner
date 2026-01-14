import requests
import os
import json
import csv
import io

# --- הגדרות ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SHEET_URL = os.getenv('SHEET_URL')  # הקישור לשיטס
DB_FILE = "prices_db.json"
THRESHOLD = 0  # התראה בשינוי של 1%. לבדיקה עכשיו שים 0

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending msg: {e}")

def get_slug_from_url(url):
    # מחלץ את השם המזהה של האירוע מתוך הקישור
    # דוגמה: polymarket.com/event/trump-win -> trump-win
    try:
        if "event/" in url:
            return url.split("event/")[1].split("/")[0].split("?")[0]
        return None
    except:
        return None

def get_sheet_markets():
    # מושך את רשימת הלינקים מהגוגל שיטס
    print("Reading Google Sheet...")
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        
        # קריאת ה-CSV
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        slugs = []
        for row in reader:
            if row and "polymarket.com" in row[0]:
                slug = get_slug_from_url(row[0])
                if slug:
                    slugs.append(slug)
        return slugs
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []

def fetch_market_data(slug):
    # פונה ל-API כדי לקבל פרטים על האירוע לפי ה-Slug
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    try:
        resp = requests.get(url).json()
        # אירוע יכול להכיל כמה שווקים, אנחנו ניקח את הראשון/הראשי
        if resp and isinstance(resp, list) and len(resp) > 0:
            market = resp[0]['markets'][0]
            return {
                'id': str(market['id']),
                'question': market['question'],
                'price': float(json.loads(market['outcomePrices'])[0])
            }
    except Exception as e:
        print(f"Error fetching data for {slug}: {e}")
    return None

# --- התחלת ריצה ---

# 1. טעינת היסטוריה
old_prices = {}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            old_prices = json.load(f)
    except: pass

# 2. קבלת רשימת שווקים מהשיטס
slugs_to_scan = get_sheet_markets()
print(f"Found {len(slugs_to_scan)} markets in Sheet.")

current_prices = {}
alerts = []

# 3. סריקת כל שוק
for slug in slugs_to_scan:
    data = fetch_market_data(slug)
    if not data:
        continue
        
    m_id = data['id']
    price = data['price']
    current_prices[m_id] = price
    
    # בדיקת שינוי
    if m_id in old_prices:
        old_p = old_prices[m_id]
        diff = price - old_p
        
        if abs(diff) >= THRESHOLD:
            direction = "📈" if diff > 0 else "📉"
            pct = diff * 100
            alerts.append(f"*{data['question']}*\n{direction} {old_p:.2f} -> {price:.2f} ({pct:+.1f}%)")

# 4. שמירה
with open(DB_FILE, "w") as f:
    json.dump(current_prices, f)

# 5. שליחת התראה
if alerts:
    msg = "📊 *עדכון מהרשימה האישית שלך:*\n\n" + "\n\n".join(alerts)
    send_telegram_msg(msg)
    print("Sent alerts.")
else:
    print("No changes in tracked markets.")
