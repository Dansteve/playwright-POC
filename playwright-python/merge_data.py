import os
import json
from datetime import datetime

DATA_DIR = "data"

def merge_developer_data():
    folder_date = datetime.now().strftime("%Y-%m-%d")
    core_dir = os.path.join(DATA_DIR, folder_date, "core")
    
    if not os.path.exists(core_dir):
        print(f"Error: Directory not found: {core_dir}")
        return

    merged_data = []
    total_count = 0
    
    # Files are likely named developers_execution_compass_tld_v1_limit_10_offset_X.json
    files = [f for f in os.listdir(core_dir) if f.startswith("developers_execution_compass_tld_v1") and f.endswith("_response.json")]
    files.sort() # Sort to keep some order, though offset is better
    
    print(f"Found {len(files)} response files.")
    
    for filename in files:
        filepath = os.path.join(core_dir, filename)
        with open(filepath, "r") as f:
            try:
                data = json.loads(f.read())
                # Adjust based on actual structure. Assuming a list or a dict with a 'developers' key
                if isinstance(data, list):
                    merged_data.extend(data)
                elif isinstance(data, dict):
                    # Check if it has totalCount
                    if "totalCount" in data and total_count == 0:
                        total_count = data["totalCount"]
                    
                    # Extract developers list - adjust key as needed (e.g., 'developers', 'items', or just the data itself)
                    for key in ["developers", "items", "data"]:
                        if key in data and isinstance(data[key], list):
                            merged_data.extend(data[key])
                            break
                    else:
                        # If no key found, maybe the dict itself is the object and we need to check fields
                        # If the whole response is one dev record (unlikely for paginated)
                        pass
            except Exception as e:
                print(f"Failed to parse {filename}: {e}")

    if merged_data:
        output_file = os.path.join(DATA_DIR, folder_date, f"merged_developers_{folder_date}.json")
        with open(output_file, "w") as f:
            json.dump({"totalCount": total_count, "count": len(merged_data), "developers": merged_data}, f, indent=4)
        print(f"Successfully merged {len(merged_data)} records into {output_file}")
    else:
        print("No data found to merge.")

if __name__ == "__main__":
    merge_developer_data()
