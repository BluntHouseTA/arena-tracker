import requests
import csv
import os
import yfinance as yf
from datetime import datetime

# --- CONFIGURATION ---
CSV_FILE = "interest_rate_log.csv"
MUNICIPAL_SPREAD = 0.90    # 0.90% Risk Premium

# --- THE DEBT "SHOPPING LIST" ---
PROJECTS = [
    {"name": "SEC Arena",                    "principal": 140000000, "term": 30},
    {"name": "Police Station Redevelop.",    "principal": 56000000,  "term": 30},
    {"name": "Southwest Community Centre",   "principal": 44000000,  "term": 30},
    {"name": "Oak Park Rd Extension",        "principal": 97000000,  "term": 30} 
]

def get_best_rate():
    # 1. Try Bank of Canada (Primary)
    try:
        url = "https://www.bankofcanada.ca/valet/observations/V122544/json?recent_weeks=2"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "observations" in data and len(data["observations"]) > 0:
            val = float(data["observations"][-1]["V122544"]["v"])
            print(f"✅ Source: Bank of Canada. Rate: {val}%")
            return val
    except Exception as e:
        print(f"⚠️ BoC Failed: {e}")
    
    # 2. Try Yahoo Proxy (Backup)
    try:
        print("   Switching to Yahoo Finance Proxy...")
        data = yf.Ticker("^TYX").history(period="1d")
        if not data.empty:
            val = float(data['Close'].iloc[-1])
            
            # SMART FIX: Check if Yahoo is sending 48.7 or 4.87
            if val > 12: 
                val = val / 10  # Convert 48.7 -> 4.87
            
            print(f"✅ Source: Yahoo Proxy. Rate: {val}%")
            return val
    except Exception as e:
        print(f"⚠️ Yahoo Failed: {e}")

    # 3. Fail Safe (If all else fails, use a safe default)
    print("❌ All feeds failed. Using Default.")
    return 3.86

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
        total_interest = total_cost - p["principal"]
        
        grand_total_debt += p["principal"]
        grand_total_annual += annual_payment
        grand_total_interest += total_interest

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "bond_yield": round(bond_yield, 3),
        "total_rate": round(total_rate, 3),
        "grand_annual": round(grand_total_annual, 2),
        "grand_interest": round(grand_total_interest, 2)
    }

def update_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ["date", "bond_yield", "total_rate", "grand_annual", "grand_interest"]
    
    # Force overwrite mode to clear the bad "0.487%" entry from today
    # Since we run this once a day, overwriting today's file is safer
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
    print(f"✅ Dashboard Updated.")

if __name__ == "__main__":
    print("--- City-Wide Debt Tracker ---")
    rate = get_best_rate()
    data = calculate_project_costs(rate)
    update_csv(data)
