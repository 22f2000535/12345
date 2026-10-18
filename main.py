import json
import re
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import traceback

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

# Deduplicate: Keep row with latest updated_at per order id
current_orders = {}
for o in raw_orders:
    oid = o["id"]
    if oid not in current_orders or o["updated_at"] > current_orders[oid]["updated_at"]:
        current_orders[oid] = o

def parse_date(ts):
    if ts.endswith("Z"):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return datetime.fromisoformat(ts)

@app.post("/answer")
async def answer(request: Request):
    try:
        body = await request.json()
        question = body.get("question", "")
        q = question.lower()

        # --- 1. Extract Filters ---
        
        # Region
        region_match = re.search(r'(north|south|east|west|central)', q)
        region = region_match.group(1).capitalize() if region_match else None

        # Month
        month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', q)
        months = {"january":1, "february":2, "march":3, "april":4, "may":5, "june":6, "july":7, "august":8, "september":9, "october":10, "november":11, "december":12}
        month = months.get(month_match.group(1)) if month_match else None

        # Year
        year_match = re.search(r'202\d', q)
        year = int(year_match.group(0)) if year_match else None

        # Status (Only apply if explicitly mentioned)
        status = None
        if "refund" in q:
            status = "refunded"
        elif "void" in q:
            status = "void"
        elif "paid" in q:
            status = "paid"

        # Product
        product_match = re.search(r'(blender|toaster|kettle|juicer|grinder|rice cooker|air fryer|mixer)', q)
        product = product_match.group(1).lower() if product_match else None

        # --- 2. Filter the Data ---
        filtered_orders = []
        for o in current_orders.values():
            # If status is specified in the question, filter by it. Otherwise, default to 'paid' for revenue, or include all for counts.
            if status:
                if o["status"] != status:
                    continue
            elif "revenue" in q or "total" in q:
                if o["status"] != "paid":
                    continue

            if region and o["region"].lower() != region.lower():
                continue
            
            if product and o["product"].lower() != product:
                continue

            dt = parse_date(o["created_at"])
            if month and dt.month != month:
                continue
            if year and dt.year != year:
                continue
            
            filtered_orders.append(o)

        # --- 3. Determine Operation ---
        
        # Count vs Sum
        is_count = any(w in q for w in ["count", "how many", "number of"])
        
        if is_count:
            return {"answer": len(filtered_orders)}
            
        else:
            # Sum (Revenue / Amount)
            total_usd = 0.0
            for o in filtered_orders:
                rate = USD_PER_UNIT.get(o["currency"], 1.0)
                total_usd += (o["amount"] * rate)
            return {"answer": round(total_usd, 2)}

    except Exception as e:
        error_msg = traceback.format_exc()
        print(error_msg)
        return {"error": str(e), "details": error_msg}
