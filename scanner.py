import requests
import os
import json
import csv
import io

# --- הגדרות ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SHEET_URL = os.getenv('SHEET_URL')
DB_FILE = "prices_db.json"
THRESHOLD = 0.01  # רגישות (0.01 זה 1%)

# 👇 הכותרת החדשה שביקשת 👇
HEADER_TEXT = "📊 שווקי חיזוי פולמרקט"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending msg: {e}")

def get_slug_from_url(url):
    try:
        if "event/" in url:
            return url.split("event/")[1].split("/")[0].split("?")[0]
        return None
    except:
        return None

def get_sheet_markets():
    print("Reading Google Sheet...")
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
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
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    try:
        resp = requests.get(url).json()
        if resp and isinstance(resp, list) and len(resp) > 0:
            market = resp[0]['markets'][0]
            try:
                outcome_prices = json.loads(market.get('outcomePrices', '[0]'))
                current_price = float(outcome_prices[0])
            except:
                current_price = 0
            
            # נתונים ל-24 שעות
            change_24h = float(market.get('oneDayPriceChange', 0) or 0) * 100
            volume_24h = float(market.get('volume24hr', 0) or 0)

            return {
                'id': str(market['id']),
                'question': market['question'],
                'price': current_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h
            }
    except Exception as e:
        print(f"Error fetching data for {slug}: {e}")
    return None

# --- לוגיקה ---

old_prices = {}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            old_prices = json.load(f)
    except: pass

slugs_to_scan = get_sheet_markets()
current_prices = {}
alerts = []

for slug in slugs_to_scan:
    data = fetch_market_data(slug)
    if not data:
        continue
        
    m_id = data['id']
    price = data['price']
    current_prices[m_id] = price
    
    if m_id in old_prices:
        old_p = old_prices[m_id]
        diff = price - old_p
        
        if abs(diff) >= THRESHOLD:
            direction = "📈" if diff > 0 else "📉"
            last_run_pct = diff * 100
            
            msg = f"*{data['question']}*\n"
            msg += f"{direction} כעת: {price:.2f} ({last_run_pct:+.1f}%)\n"
            msg += f"📅 ב-24 שעות: {data['change_24h']:+.1f}%\n"
            msg += f"💰 נפח יומי: ${data['volume_24h']:,.0f}"
            alerts.append(msg)

with open(DB_FILE, "w") as f:
    json.dump(current_prices, f)

if alerts:
    full_msg = f"*{HEADER_TEXT}*\n\n" + "\n\n".join(alerts)
    send_telegram_msg(full_msg)
else:
    print("No changes.")
