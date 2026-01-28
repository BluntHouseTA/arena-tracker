import requests
import csv
import os
from datetime import datetime

# --- CONFIGURATION ---
CSV_FILE = "interest_rate_log.csv"
MUNICIPAL_SPREAD = 0.90    # 0.90% Risk Premium
SAFE_FALLBACK_RATE = 3.86  # Safety Net if Bank of Canada is down

# --- THE DEBT "SHOPPING LIST" ---
PROJECTS = [
    {"name": "SEC Arena",                    "principal": 140000000, "term": 30},
    {"name": "Police Station Redevelop.",    "principal": 56000000,  "term": 30},
    {"name": "Southwest Community Centre",   "principal": 44000000,  "term": 30},
    {"name": "Oak Park Rd Extension",        "principal": 97000000,  "term": 30} 
]

def get_canadian_rate():
    """
    STRICTLY Bank of Canada. No US proxies allowed.
    """
    try:
        # Get last 10 observations to ensure we find a valid entry
        url = "https://www.bankofcanada.ca/valet/observations/V122544/json?recent=10"
        response = requests.get(url, timeout=20)
        data = response.json()
        
        if "observations" in data and len(data["observations"]) > 0:
            last_entry = data["observations"][-1]
            val = float(last_entry["V122544"]["v"])
            print(f"✅ Source: Bank of Canada. Rate: {val}%")
            return val
            
    except Exception as e:
        print(f"⚠️ Bank of Canada Error: {e}")
    
    # If BoC fails, we use the manual safety rate.
    print(f"❌ API Failed. Using Fallback: {SAFE_FALLBACK_RATE}%")
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
        "date": datetime.now().strftime("%Y-%m-%d"),
        "bond_yield": round(bond_yield, 3),
        "total_rate": round(total_rate, 3),
        "grand_annual": round(grand_total_annual, 2),
        "grand_interest": round(grand_total_interest, 2)
    }

def update_csv(data):
    # 'w' mode overwrites the file to clear any bad data from history
    fieldnames = ["date", "bond_yield", "total_rate", "grand_annual", "grand_interest"]
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
    print(f"✅ Database repaired.")

if __name__ == "__main__":
    rate = get_canadian_rate()
    data = calculate_project_costs(rate)
    update_csv(data)
