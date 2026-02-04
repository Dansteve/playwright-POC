import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage

DATA_DIR = "data"
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
COMPASS_FETCH_LIMIT = 7000

def extract_params_from_payload(payload_str):
    if not payload_str:
        return ""
    try:
        data = json.loads(payload_str)
        params = []
        for key in ["limit", "startDate", "endDate", "teamId"]:
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
    if is_core:
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

    # Capture headers for manual fetch (X-Auth-Token, etc.)
    req_headers = response.request.headers
    if any(k.lower() in ["x-auth-token", "authorization"] for k in req_headers) or "api/v2/tld/developers" in url:
        global CAPTURED_HEADERS
        CAPTURED_HEADERS.update(req_headers)
        print(f"!!! Updated captured headers from: {url}")

    if "api/" in url:
        is_targeted = "target" if name else "extra"
        print(f"Network Intercepted ({is_targeted}): {url} (Status: {response.status})")

    if name:
        url_path_only = url.split("?")[0]
        is_core = any(url_path_only.endswith(target) for target in TARGET_ENDPOINTS)
        
        if response.status == 200:
            try:
                data = response.json()
                save_json_data(name, data, folder_date, "responses", is_core=is_core)
                SAVED_ENDPOINTS.add(name)
            except Exception as e:
                print(f"Failed to process response for {name}: {e}")
        else:
            print(f"SKIPPED: {url} (Status: {response.status})")

def run_manual_fetch(page):
    if not CAPTURED_HEADERS:
        print("CRITICAL: No headers captured. Manual fetch blocked.")
        return

    print("\n--- Triggering Browser-Native Fetch for Compass (Limit 7000) ---")
    
    folder_date = datetime.now().strftime("%Y-%m-%d")
    payload = {
        "limit": COMPASS_FETCH_LIMIT,
        "startDate": folder_date,
        "endDate": folder_date,
        "teamId": None
    }
    
    filtered_headers = {k: v for k, v in CAPTURED_HEADERS.items() 
                       if k.lower() not in ['content-length', 'host', 'connection']}
    
    js_fetch = """
    async (headers, payload) => {
        try {
            const url = "https://uix.blueoptima.com/api/v1/tld/compass/execution/developers";
            console.log(`Native fetch to: ${url}`);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    ...headers,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload),
                credentials: 'include'
            });
            return { ok: response.ok, status: response.status, url: url };
        } catch (e) {
            return { ok: false, error: e.message };
        }
    }
    """
    
    try:
        print(f"Triggering native fetch from browser context with limit {COMPASS_FETCH_LIMIT}...")
        result = page.evaluate(js_fetch, [filtered_headers, payload])
        print(f"Native fetch trigger result: {result}")
    except Exception as e:
        print(f"Failed to trigger native fetch: {e}")

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

    print(f"--- Starting Python Data Extraction (Interception + Manual Fallback) ---")
    print(f"User: {username}")
    print(f"Demo Mode: {demo_mode}")

    with sync_playwright() as p:
        # Note: Using the provided executable path for Chrome
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
                
                print("Waiting 15 seconds for initial loader on Compass page...")
                time.sleep(15)
                
                print("Searching for 'Developer view' trigger...")
                team_trigger = page.get_by_text("Team view", exact=False)
                developer_trigger = page.get_by_text("Developer view", exact=False)
                
                try:
                    developer_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Developer view' button...")
                    developer_trigger.first.click()
                    print("Wait 5s for sequence...")
                    time.sleep(5)
                    
                    team_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Team view' button...")
                    team_trigger.first.click()
                    print("Wait 5s for sequence...")
                    time.sleep(5)
                    
                    developer_trigger.first.wait_for(state="visible", timeout=30000)
                    print("Clicking 'Developer view' button...")
                    developer_trigger.first.click()
                    
                    print("Trigger sequence complete!")
                except Exception as click_err:
                    print(f"WARNING: Trigger sequence failed: {click_err}")
                
                print("Waiting 15 seconds for network capture...")
                time.sleep(15)

                # Trigger the browser-native high-limit fetch
                run_manual_fetch(page)
                
                print("Waiting 10 seconds for native fetch interception...")
                time.sleep(10)
                
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
