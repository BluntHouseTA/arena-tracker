import requests
import csv
import os
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
CSV_FILE = "interest_rate_log.csv"
MUNICIPAL_SPREAD = 0.90    # 0.90% Risk Premium
SAFE_FALLBACK_RATE = 3.86  # Emergency number if all else fails

# --- THE DEBT "SHOPPING LIST" ---
PROJECTS = [
    {"name": "SEC Arena",                    "principal": 140000000, "term": 30},
    {"name": "Police Station Redevelop.",    "principal": 56000000,  "term": 30},
    {"name": "Southwest Community Centre",   "principal": 44000000,  "term": 30},
    {"name": "Oak Park Rd Extension",        "principal": 97000000,  "term": 30} 
]

def get_rate():
    # --- ATTEMPT 1: TRADING ECONOMICS (Real-Time) ---
    try:
        url = "https://tradingeconomics.com/gcan30y:ind"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        print(f"🌍 Attempting Trading Economics...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for the specific rate element
            rate_element = soup.find(id="market_last")
            if rate_element:
                val = float(rate_element.text.strip())
                print(f"✅ Success: TradingEconomics Rate is {val}%")
                return val
            
            # Fallback to table search
            rows = soup.find_all("tr")
            for row in rows:
                if "Canada 30Y" in row.text:
                    cols = row.find_all("td")
                    if len(cols) > 1:
                        val = float(cols[1].text.strip())
                        print(f"✅ Success: TradingEconomics (Table) Rate is {val}%")
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

    # --- ATTEMPT 3: SAFETY NET (Never Empty) ---
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

    # ADDING THE TIMESTAMP HERE
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"), # Capture Time!
        "bond_yield": round(bond_yield, 3),
        "total_rate": round(total_rate, 3),
        "grand_annual": round(grand_total_annual, 2),
        "grand_interest": round(grand_total_interest, 2)
    }

def update_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ["date", "bond_yield", "total_rate", "grand_annual", "grand_interest"]
    
    # We switch to 'w' (Overwrite) briefly to fix the broken file
    # You can change this back to 'a' (Append) later if you want history.
    mode = 'w' 
    
    with open(CSV_FILE, mode=mode, newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
    print(f"✅ Dashboard Updated.")

if __name__ == "__main__":
    rate = get_rate()
    data = calculate_project_costs(rate)
    update_csv(data)
