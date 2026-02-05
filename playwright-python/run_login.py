import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TARGET_ENDPOINTS = [
    "api/v2/developers",
    "api/v2/tld/developers",
    "api/v1/tld/compass/execution/developers"
]

NAME_MAPPING = {
    "api/v2/developers": "developers",
    "api/v2/tld/developers": "developers_tld",
    "api/v1/tld/compass/execution/developers": "developers_execution_compass_tld_v1"
}

SAVED_ENDPOINTS = set()
CAPTURED_HEADERS = {}
CAPTURED_METADATA = {}
SAVE_REQUESTS = os.getenv('SAVE_REQUESTS', 'false').lower() == 'true'
COMPASS_FETCH_LIMIT = 7000

def extract_params_from_payload(payload_str):
    if not payload_str:
        return ""
    try:
        data = json.loads(payload_str)
        params = []
        for key in ["limit", "startDate", "endDate", "teamId", "offset"]:
            if key in data:
                params.append(f"{key}_{data[key]}")
        return "_" + "_".join(params) if params else ""
    except:
        return ""

def get_base_name(url, post_data=None):
    url_parts = url.split("?")
    url_path = url_parts[0]
    query_string = url_parts[1] if len(url_parts) > 1 else ""
    
    path = url_path.split("://")[-1].split("/", 1)[-1]
    if not path.startswith("api/"):
        return None
        
    parts = path.split("/")
    if parts[0] == "api":
        parts = parts[1:]
        
    version = parts[0] if parts[0].startswith("v") else None
    rest = parts[1:] if version else parts
    
    rest = list(rest)
    rest.reverse()
    
    if version:
        rest.append(version)
        
    base_name = "_".join(rest)
    
    if "limit=" in query_string:
        for param in query_string.split("&"):
            if param.startswith("limit="):
                limit_val = param.split("=")[1]
                base_name += f"_limit_{limit_val}"
                break
    
    if post_data:
        base_name += extract_params_from_payload(post_data)
                
    return base_name

def save_json_data(name, data, folder_date, type_suffix="responses", is_core=False):
    # Specialized routing for paginated developer data to keep core clean
    if name.startswith("developers_execution_compass_tld_v1"):
        subfolder = "working"
        filename = f"{name}_{type_suffix[:-1] if type_suffix.endswith('s') else type_suffix}.json"
    elif is_core:
        subfolder = "core"
        filename = f"{name}_{type_suffix[:-1] if type_suffix.endswith('s') else type_suffix}.json"
    else:
        subfolder = f"{type_suffix}"
        filename = f"{name}_{type_suffix[:-1] if type_suffix.endswith('s') else type_suffix}.json"

    target_dir = os.path.join(DATA_DIR, folder_date, subfolder)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    filepath = os.path.join(target_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"File Written: {filepath}")

def handle_request(request):
    url = request.url
    if "api/" in url:
        name = get_base_name(url, request.post_data)
        if name:
            folder_date = datetime.now().strftime("%Y-%m-%d")
            url_path_only = url.split("?")[0]
            is_core = any(url_path_only.endswith(target) for target in TARGET_ENDPOINTS)
            
            if SAVE_REQUESTS:
                req_data = {
                    "method": request.method,
                    "url": url,
                    "headers": request.headers,
                    "postData": request.post_data
                }
                save_json_data(name, req_data, folder_date, "requests", is_core=is_core)

def handle_response(response):
    url = response.url
    name = get_base_name(url, response.request.post_data)
    folder_date = datetime.now().strftime("%Y-%m-%d")

    if "api/" in url:
        is_targeted = "target" if name else "extra"
        print(f"Network Intercepted ({is_targeted}): {url} (Status: {response.status})")

    if name:
        url_path_only = url.split("?")[0]
        is_core = any(url_path_only.endswith(target) for target in TARGET_ENDPOINTS)
        
        if response.status == 200:
            try:
                data = response.json()
                if "metaData" in data:
                    global CAPTURED_METADATA
                    CAPTURED_METADATA = data["metaData"]
                    print(f"Captured Metadata: {CAPTURED_METADATA}")
                
                save_json_data(name, data, folder_date, "responses", is_core=is_core)
                SAVED_ENDPOINTS.add(name)
            except Exception as e:
                print(f"Failed to process response for {name}: {e}")
        else:
            print(f"SKIPPED: {url} (Status: {response.status})")

def run_pagination(page):
    print("\n--- Starting Pagination Capture ---")
    
    # Wait for the table/pagination to be visible
    next_button_selector = '[data-qa="uix-tld-compass-execution-developer-table-next"]'
    try:
        page.wait_for_selector(next_button_selector, timeout=30000)
    except Exception as e:
        print(f"Pagination button not found: {e}")
        return

    page_num = 1
    max_pages = 999 # Fallback
    
    # Give a moment for the first page response to be processed by handle_response
    time.sleep(2)
    
    if CAPTURED_METADATA and "totalCount" in CAPTURED_METADATA:
        total = CAPTURED_METADATA["totalCount"]
        per_page = CAPTURED_METADATA.get("perPage", 10)
        max_pages = (total + per_page - 1) // per_page
        print(f"Pagination Plan: {total} items, {per_page}/page -> {max_pages} pages.")

    while page_num < max_pages:
        print(f"Captured Page {page_num}/{max_pages}. Looking for Next button...")
        
        next_button = page.locator(next_button_selector)
        
        # Check if button is disabled or hidden
        is_visible = next_button.is_visible()
        # Some UIs mark it disabled via class or attribute
        is_disabled = "pagination-item--disabled" in (next_button.get_attribute("class") or "") or not next_button.is_enabled()
        
        if not is_visible or is_disabled:
            print("Next button not available or disabled. Pagination complete.")
            break
            
        print(f"Clicking Next for Page {page_num + 1}...")
        
        # Reset SAVED_ENDPOINTS for the specific target so we can wait for its refresh
        target_name_to_wait = "developers_execution_compass_tld_v1"
        if target_name_to_wait in SAVED_ENDPOINTS:
            SAVED_ENDPOINTS.remove(target_name_to_wait)
            
        next_button.click()
        
        # Wait for the specific response OR a reasonable timeout
        start_wait = time.time()
        max_wait = 30 
        loaded = False
        
        while time.time() - start_wait < max_wait:
            if target_name_to_wait in SAVED_ENDPOINTS:
                print(f"Page {page_num + 1} data received.")
                loaded = True
                break
            time.sleep(1)
            
        if not loaded:
            print(f"Warning: Page {page_num + 1} data load timed out. Continuing anyway...")
        
        page_num += 1
        time.sleep(2) 
        
        if page_num > 200: 
            print("Safety break: capped at 200 pages.")
            break
    
    if page_num >= max_pages:
        print(f"Pagination reached calculated limit ({max_pages}).")

def save_cookies(context, folder_date):
    print(f"Saving browser cookies for {folder_date}...")
    try:
        cookies = context.cookies()
        target_dir = os.path.join(DATA_DIR, folder_date)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        filepath = os.path.join(target_dir, "cookies.json")
        with open(filepath, "w") as f:
            json.dump(cookies, f, indent=4)
        print(f"Cookies saved to: {filepath}")
    except Exception as e:
        print(f"Failed to save cookies: {e}")
    print("--- Check Complete ---\n")

def run():
    username = os.getenv('LOGIN_USERNAME', 'dansteve.adekanbi@coutts.com')
    demo_mode = os.getenv('DEMO', 'true').lower() == 'true'
    folder_date = datetime.now().strftime("%Y-%m-%d")

    print(f"--- Starting Python Data Extraction (Playwright Pagination) ---")
    print(f"User: {username}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:\\Users\\AdekaD\\Downloads\\chrome-win64\\chrome.exe', headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.on("request", handle_request)
        page.on("response", handle_response)

        login_page = LoginPage(page)

        try:
            print("Navigating to login page...")
            login_page.navigate()

            print(f"Entering username: {username}")
            login_page.enter_username(username)
            login_page.wait_for_sso_redirection()

            print("Submitting login...")
            login_page.click_next()

            print("Waiting for login completion...")
            try:
                login_page.wait_for_login_completion()
                print(f"Login successful. Current URL: {page.url}")
                time.sleep(15)
                
                # Force navigation to Compass if not there
                if "/uix/compass" not in page.url:
                    print("Ensuring navigation to Compass page...")
                    page.goto("https://uix.blueoptima.com/uix/compass")
                
                print("Waiting 15 seconds for initial loader on Compass page...")
                time.sleep(15)
                
                print("Searching for 'Developer view' trigger...")
                team_trigger = page.get_by_text("Team view", exact=False)
                developer_trigger = page.get_by_text("Developer view", exact=False)
                
                try:
                    developer_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Developer view' button...")
                    developer_trigger.first.click()
                    time.sleep(5)
                    
                    team_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Team view' button...")
                    team_trigger.first.click()
                    time.sleep(5)
                    
                    developer_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Developer view' button...")
                    developer_trigger.first.click()
                    
                    print("Wait 10s for initial data load...")
                    time.sleep(10)
                except Exception as click_err:
                    print(f"WARNING: Trigger sequence failed: {click_err}")
                
                # Start the pagination loop
                run_pagination(page)
                
                save_cookies(context, folder_date)
                
            except Exception as e:
                print(f"Functional block error: {e}")

        except Exception as e:
            print(f"Entry/Login error: {e}")
            page.screenshot(path="error_screenshot_interception.png")

        if demo_mode:
            print("Demo mode active. Keeping browser open for observation. Press Ctrl+C to exit.")
            while True:
                if not browser.is_connected():
                    break
                time.sleep(1)
        
        browser.close()

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        run()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Closing...")
        sys.exit(0)
