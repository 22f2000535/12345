import urllib.request
import json
import time

# The full URL for page 1 that you provided
BASE_URL = "https://exam.sanand.workers.dev/questionData?email=22f2000535%40ds.study.iitm.ac.in&quizSign=XBhp45CZ%2B04TzrLSvK3Zk1GbVeO7FW2cB5jJtp6aZpJDsZTxK0LZc1sBEqsXih5LI9NUPd2wK%2BG0xaqP4F5oBxxyDiM4qA2fDI7l2NpyXngUNdwmQTqJgBIRN5PjKaQIWh9bV5vraMpuuGJ%2FqP3ZizFt77KTld0CjLXG6kwN%2BWDKJpeT8SwQcBJCLvBYzAMm6ylhAd8Vlvgc8isSMRcm%2B2ETHLe2eGMK1CSBK1OelkHL2ptk4PKdvgeCF59U02migU%2B16jJ0iAA8NEnFQG0qBUjqBzw1TqNrQWtTZK1tg2%2F0WGMfNtyuPd9zriHz9e%2FPeyH6scCYr9%2Bo4fhHryM0AQ%3D%3D&questionId=q-ledger-agent-server&path=%2Forders"

def get_request(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return req

all_orders = []
page = 1
pages = 85 # We know there are 85 pages

print("Fetching orders...")
while page <= pages:
    # Replace the page number in the URL
    if "&page=" in BASE_URL:
        url = BASE_URL.split("&page=")[0] + f"&page={page}"
    else:
        url = BASE_URL + f"&page={page}"
        
    try:
        req = get_request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            all_orders.extend(data.get("orders", []))
            print(f"Fetched page {page}/85")
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        break
        
    page += 1
    time.sleep(0.1)

with open("orders.json", "w") as f:
    json.dump(all_orders, f)
print(f"Saved {len(all_orders)} orders to orders.json!")

print("Fetching rates...")
RATES_URL = BASE_URL.replace("path=%2Forders", "path=%2Frates").split("&page=")[0]
try:
    req = get_request(RATES_URL)
    with urllib.request.urlopen(req) as response:
        rates_data = json.loads(response.read().decode())
        with open("rates.json", "w") as f:
            json.dump(rates_data, f)
    print("Saved rates.json!")
except Exception as e:
    print(f"Error fetching rates: {e}")