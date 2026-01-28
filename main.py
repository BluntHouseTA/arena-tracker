import requests
import csv
import os
from datetime import datetime

# --- CONFIGURATION ---
PROJECT_NAME = "Brantford SEC Arena"
PRINCIPAL = 140000000      # $140 Million
AMORTIZATION = 30          # 30 Years
MUNICIPAL_SPREAD = 1.10    # 1.10% Risk Premium
HOUSEHOLDS = 45000         # Est. Taxable Households
CSV_FILE = "interest_rate_log.csv"

# --- MANUAL OVERRIDE (REAL TIME QUOTES) ---
# If you have a live rate (like 3.861), type it here.
# Set to 0 if you want to try the automatic Bank of Canada API.
MANUAL_OVERRIDE = 3.861 

def get_bond_yield():
    """
    Decides whether to use the Manual Override or fetch from API.
    """
    if MANUAL_OVERRIDE > 0:
        print(f"⚠️ Using Manual Override Rate: {MANUAL_OVERRIDE}%")
        return MANUAL_OVERRIDE

    # If Override is 0, try the Bank of Canada API (Series V122544)
    series_id = "V122544"
    url = f"https://www.bankofcanada.ca/valet/observations/{series_id}/json?recent=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if "observations" in data and len(data["observations"]) > 0:
            return float(data["observations"][-1][series_id]["v"])
    except Exception as e:
        print(f"API Error: {e}")
    
    return None

def calculate_impact(bond_yield):
    total_rate = bond_yield + MUNICIPAL_SPREAD
    r = (total_rate / 100)
    numerator = PRINCIPAL * (r * (1 + r)**AMORTIZATION)
    denominator = ((1 + r)**AMORTIZATION) - 1
    annual_payment = numerator / denominator
    total_cost = annual_payment * AMORTIZATION
    total_interest = total_cost - PRINCIPAL
    household_impact = annual_payment / HOUSEHOLDS
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "bond_yield": bond_yield,
        "total_rate": round(total_rate, 3),
        "annual_payment": round(annual_payment, 2),
        "total_interest": round(total_interest, 2),
        "household_impact": round(household_impact, 2)
    }

def update_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    
    # Check if we already have data for today to avoid duplicates
    if file_exists:
        with open(CSV_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1 and data["date"] in lines[-1]:
                # If today exists, OVERWRITE the last line with the new manual rate
                print("♻️ Updating today's existing entry...")
                lines[-1] = f"{data['date']},{data['bond_yield']},{data['total_rate']},{data['annual_payment']},{data['total_interest']},{data['household_impact']}\n"
                with open(CSV_FILE, 'w') as f_write:
                    f_write.writelines(lines)
                print(f"✅ Updated {CSV_FILE} with Manual Rate.")
                return

    # If new day, append as normal
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    print(f"✅ Data saved to {CSV_FILE}")

if __name__ == "__main__":
    print("--- Starting Rate Check ---")
    bond_yield = get_bond_yield()
    
    if bond_yield:
        print(f"Using Yield: {bond_yield}%")
        data = calculate_impact(bond_yield)
        update_csv(data)
    else:
        print("❌ Failed to get a rate.")
        exit(1)
