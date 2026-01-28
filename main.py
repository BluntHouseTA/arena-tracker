import requests
import csv
import os
from datetime import datetime

# --- CONFIGURATION ---
CSV_FILE = "interest_rate_log.csv"
MUNICIPAL_SPREAD = 0.90    # 0.90% Risk Premium
SAFE_FALLBACK_RATE = 3.86  # Emergency number

# --- THE DEBT "SHOPPING LIST" ---
PROJECTS = [
    {"name": "SEC Arena",                    "principal": 140000000, "term": 30},
    {"name": "Police Station Redevelop.",    "principal": 56000000,  "term": 30},
    {"name": "Southwest Community Centre",   "principal": 44000000,  "term": 30},
    {"name": "Oak Park Rd Extension",        "principal": 97000000,  "term": 30} 
]

def get_rate():
    # --- ATTEMPT 1: TRADING ECONOMICS (Manual Text Search) ---
    try:
        url = "https://tradingeconomics.com/gcan30y:ind"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        print(f"🌍 Attempting Trading Economics (Direct)...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            text = response.text
            # We look for the data-value in the HTML text manually without BS4
            # Pattern: <div id="market_last" ... >3.86</div>
            if 'id="market_last"' in text:
                # Find the start of the number
                start = text.find('id="market_last"')
                # Find the first closing bracket > after that id
                start_val = text.find('>', start) + 1
                # Find the next opening bracket <
                end_val = text.find('<', start_val)
                
                # Extract the number
                val_str = text[start_val:end_val].strip()
                val = float(val_str)
                print(f"✅ Success: TradingEconomics Rate is {val}%")
                return val
            
    except Exception as e:
        print(f"⚠️ TradingEconomics Failed: {e}")

    # --- ATTEMPT 2: BANK OF CANADA (Official Backup) ---
    try:
        print(f"🌍 Attempting Bank of Canada...")
        url = "https://www.bankofcanada.ca/valet/observations/V122544/json?recent=10"
        response = requests.get(url, timeout=15)
        data = response.json()
        if "observations" in data and len(data["observations"]) > 0:
            last_entry = data["observations"][-1]
            val = float(last_entry["V122544"]["v"])
            print(f"✅ Success: Bank of Canada Rate is {val}%")
            return val
    except Exception as e:
        print(f"⚠️ Bank of Canada Failed: {e}")

    # --- ATTEMPT 3: SAFETY NET ---
    print(f"❌ All APIs Failed. Using Fallback: {SAFE_FALLBACK_RATE}%")
    return SAFE_FALLBACK_RATE

def calculate_project_costs(bond_yield):
    total_rate = bond_yield + MUNICIPAL_SPREAD
    r = (total_rate / 100)
    grand_total_debt = 0
    grand_total_annual = 0
    grand_total_interest = 0
    
    for p in PROJECTS:
        numerator = p["principal"] * (r * (1 + r)**p["term"])
        denominator = ((1 + r)**p["term"]) - 1
        annual_payment = numerator / denominator
        total_cost = annual_payment * p["term"]
        grand_total_debt += p["principal"]
        grand_total_annual += annual_payment
        grand_total_interest += (total_cost - p["principal"])

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bond_yield": round(bond_yield, 3),
        "total_rate": round(total_rate, 3),
        "grand_annual": round(grand_total_annual, 2),
        "grand_interest": round(grand_total_interest, 2)
    }

def update_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ["date", "bond_yield", "total_rate", "grand_annual", "grand_interest"]
    
    # Force 'w' (Overwrite) to ensure we fix the missing file issue
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
    print(f"✅ Dashboard Updated.")

if __name__ == "__main__":
    rate = get_rate()
    data = calculate_project_costs(rate)
    update_csv(data)
