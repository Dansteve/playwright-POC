import json
import sys
import os
from datetime import datetime

# Add src to path if running directly
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.client import BlueOptimaClient
from src.auth import BlueOptimaAuth

DATA_DIR = "data"

def save_json(name, data):
    """Saves JSON data to the data/Y-m-d/core folder."""
    folder_date = datetime.now().strftime("%Y-%m-%d")
    target_dir = os.path.join(DATA_DIR, folder_date, "core")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    filename = f"{name}_response.json"
    filepath = os.path.join(target_dir, filename)
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"File Written: {filepath}")

def main():
    try:
        client = BlueOptimaClient()
        
        print("\n--- Fetching User Profile ---")
        profile = client.get_profile()
        save_json("profile", profile)
        
        limit = 200
        print(f"\n--- Fetching Developers (Limit {limit}) ---")
        developers = client.get_developers(limit=limit)
        save_json(f"developers_v2_limit_{limit}", developers)
        print(f"Retrieved {len(developers.get('developers', [])) if isinstance(developers, dict) else len(developers)} developers.")

        print(f"\n--- Fetching TLD Developers (Limit {limit}) ---")
        tld_developers = client.get_tld_developers(limit=limit)
        save_json(f"developers_tld_v2_limit_{limit}", tld_developers)
        print(f"Retrieved {len(tld_developers.get('developers', [])) if isinstance(tld_developers, dict) else len(tld_developers)} TLD developers.")
        
        print(f"\n--- Fetching Compass Developers (Limit {limit}) ---")
        compass_devs = client.get_compass_developers(limit=limit)
        save_json(f"developers_execution_compass_tld_v1_limit_{limit}", compass_devs)
        print(f"Retrieved {len(compass_devs)} compass developers.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
