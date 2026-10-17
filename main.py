import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pre-fetched data
try:
    with open("orders.json") as f:
        raw_orders = json.load(f)
    with open("rates.json") as f:
        USD_PER_UNIT = json.load(f).get("usd_per_unit", {"USD": 1.0, "INR": 0.011, "EUR": 1.09})
except Exception:
    raw_orders = []
    USD_PER_UNIT = {"USD": 1.0, "INR": 0.011, "EUR": 1.09}

# 1. Deduplicate: Keep row with latest updated_at per order id
current_orders = {}
for o in raw_orders:
    oid = o["id"]
    if oid not in current_orders or o["updated_at"] > current_orders[oid]["updated_at"]:
        current_orders[oid] = o

@app.post("/answer")
async def answer(request: Request):
    body = await request.json()
    question = body.get("question", "")
    
    q = question.lower()
    
    # Helper to parse date
    def parse_date(ts):
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts)

    # --- LOGIC 1: REVENUE ---
    if "revenue" in q:
        region_match = re.search(r'(north|south|east|west|central)', q)
        region = region_match.group(1).capitalize() if region_match else None
        
        month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', q)
        months = {"january":1, "february":2, "march":3, "april":4, "may":5, "june":6, "july":7, "august":8, "september":9, "october":10, "november":11, "december":12}
        month = months.get(month_match.group(1)) if month_match else None
        
        year_match = re.search(r'202\d', q)
        year = int(year_match.group(0)) if year_match else None

        total_usd = 0.0
        for o in current_orders.values():
            # Rule: Only 'paid' counts as revenue
            if o["status"] != "paid":
                continue
            if region and o["region"].lower() != region.lower():
                continue
                
            dt = parse_date(o["created_at"])
            if month and dt.month != month:
                continue
            if year and dt.year != year:
                continue
                
            rate = USD_PER_UNIT.get(o["currency"], 1.0)
            total_usd += (o["amount"] * rate)
            
        return {"answer": round(total_usd, 2)}

    # --- LOGIC 2: REFUNDS ---
    if "refund" in q:
        total_usd = 0.0
        for o in current_orders.values():
            if o["status"] == "refunded":
                rate = USD_PER_UNIT.get(o["currency"], 1.0)
                total_usd += (o["amount"] * rate)
        return {"answer": round(total_usd, 2)}

    # --- LOGIC 3: PRODUCT COUNTS / QUANTITIES ---
    products = ["blender", "toaster", "kettle", "juicer", "grinder", "rice cooker", "air fryer", "mixer"]
    for p in products:
        if p in q:
            total_qty = 0
            for o in current_orders.values():
                if o["product"].lower() == p and o["status"] == "paid":
                    total_qty += o["qty"]
            return {"answer": total_qty}

    # --- LOGIC 4: UNIQUE CUSTOMERS ---
    if "customer" in q:
        unique_customers = set()
        for o in current_orders.values():
            if o["status"] == "paid":
                unique_customers.add(o["customer"])
        return {"answer": len(unique_customers)}

    return {"answer": "Question not understood."}