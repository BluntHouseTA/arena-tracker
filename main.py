import requests
import csv
import os
from datetime import datetime
from bs4 import BeautifulSoup

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

def get_trading_economics_rate():
    """
    Scrapes https://tradingeconomics.com/gcan30y:ind
    Exclusively uses this source.
    """
    url = "https://tradingeconomics.com/gcan30y:ind"
    
    # We pretend to be a real Chrome browser to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"🌍 Connecting to {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"Website blocked us (Status Code: {response.status_code})")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for the specific ID "market_last" (Best Match)
        rate_element = soup.find(id="market_last")
        if rate_element:
            val = float(rate_element.text.strip())
            print(f"✅ Success: TradingEconomics Rate is {val}%")
            return val
        
        # Method 2: Look for the table cell if Method 1 fails
        rows = soup.find_all("tr")
        for row in rows:
            if "Canada 30Y" in row.text:
                cols = row.find_all("td")
                if len(cols) > 1:
                    val = float(cols[1].text.strip())
                    print(f"✅ Success: TradingEconomics (Table) Rate is {val}%")
                    return val
                    
        raise Exception("Could not find the rate on the page layout.")

    except Exception as e:
        print(f"❌ Error scraping Trading Economics: {e}")
        raise e  # Crash the script so we get a notification email

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
    mode = 'a' if file_exists else 'w'
    
    with open(CSV_FILE, mode=mode, newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    print(f"✅ Dashboard CSV Updated.")

if __name__ == "__main__":
    print("--- Trading Economics Scraper ---")
    rate = get_trading_economics_rate()
    if rate:
        data = calculate_project_costs(rate)
        update_csv(data)
