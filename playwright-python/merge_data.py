import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def merge_developer_data():
    folder_date = datetime.now().strftime("%Y-%m-%d")
    working_dir = os.path.join(DATA_DIR, folder_date, "working")
    
    if not os.path.exists(working_dir):
        print(f"Error: Directory not found: {working_dir}")
        return

    merged_data = []
    total_count = 0
    
    # Files are likely named developers_execution_compass_tld_v1_limit_10_offset_X.json
    files = [f for f in os.listdir(working_dir) if f.startswith("developers_execution_compass_tld_v1") and f.endswith("_response.json")]
    files.sort() 
    
    print(f"Found {len(files)} response files in working directory.")
    
    processed_files = []
    for filename in files:
        filepath = os.path.join(working_dir, filename)
        with open(filepath, "r") as f:
            try:
                data = json.loads(f.read())
                if isinstance(data, list):
                    merged_data.extend(data)
                elif isinstance(data, dict):
                    if "metaData" in data and "totalCount" in data["metaData"] and total_count == 0:
                        total_count = data["metaData"]["totalCount"]
                    
                    for key in ["developers", "items", "data", "metrics"]:
                        if key in data and isinstance(data[key], list):
                            merged_data.extend(data[key])
                            break
                processed_files.append(filepath)
            except Exception as e:
                print(f"Failed to parse {filename}: {e}")

    if merged_data:
        core_dir = os.path.join(DATA_DIR, folder_date, "core")
        if not os.path.exists(core_dir):
            os.makedirs(core_dir)
            
        output_file = os.path.join(core_dir, "developers_execution_compass_tld_v1_merge.json")
        with open(output_file, "w") as f:
            json.dump({"totalCount": total_count, "count": len(merged_data), "developers": merged_data}, f, indent=4)
        print(f"Successfully merged {len(merged_data)} records into {output_file}")
        
        # Cleanup individual files
        print("Cleaning up working directory...")
        for filepath in processed_files:
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Failed to delete {filepath}: {e}")
        
        # Optional: remove working dir if empty
        if not os.listdir(working_dir):
            os.rmdir(working_dir)
            print("Working directory removed.")
    else:
        print("No data found to merge.")

if __name__ == "__main__":
    merge_developer_data()
