import requests
import os
import sys
import socket
import urllib.request

def debug_connection():
    target_url = "https://uix.blueoptima.com/api/v1/authenticate"
    
    print("--- Network Debugging ---")
    print(f"Python Version: {sys.version}")
    
    # 1. Check DNS resolution
    print("\n1. Testing DNS Resolution...")
    try:
        host = target_url.split("//")[1].split("/")[0]
        ip = socket.gethostbyname(host)
        print(f"SUCCESS: {host} resolved to {ip}")
    except Exception as e:
        print(f"FAILURE: Could not resolve {host}. Error: {e}")

    # 2. Check System Proxies
    print("\n2. Checking System Proxies...")
    proxies = urllib.request.getproxies()
    if proxies:
        print(f"Detected Proxies: {proxies}")
    else:
        print("No system proxies detected.")

    # 3. Test HTTP Get (No Auth)
    print("\n3. Testing Connection (verify=True)...")
    try:
        response = requests.get(target_url, timeout=10)
        print(f"SUCCESS: Status Code {response.status_code}")
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}: {e}")

    # 4. Test HTTP Get (verify=False)
    print("\n4. Testing Connection (verify=False)...")
    try:
        response = requests.get(target_url, timeout=10, verify=False)
        print(f"SUCCESS (Insecure): Status Code {response.status_code}")
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_connection()
