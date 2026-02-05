import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

class BlueOptimaAuth:
    AUTH_URL_PAT = "https://iam.blueoptima.com/api/v1/authenticate/pat"
    AUTH_URL_USER = "https://uix.blueoptima.com/api/v1/authenticate"
    REFRESH_URL = "https://uix.blueoptima.com/api/v1/refreshToken"

    def __init__(self, pat=None, username=None, password=None, verify=True, proxies=None):
        self.pat = pat or os.getenv("BLUEOPTIMA_PAT")
        self.username = username or os.getenv("BLUEOPTIMA_USERNAME")
        self.password = password or os.getenv("BLUEOPTIMA_PASSWORD")
        self.verify = verify
        
        # Load proxies from env if not explicitly passed
        if proxies:
            self.proxies = proxies
        else:
            http_proxy = os.getenv("BLUEOPTIMA_HTTP_PROXY")
            https_proxy = os.getenv("BLUEOPTIMA_HTTPS_PROXY")
            self.proxies = {}
            if http_proxy: self.proxies["http"] = http_proxy
            if https_proxy: self.proxies["https"] = https_proxy

        self.token = None
        self.expiry_time = 0

        # Set a default user agent that looks like a browser
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.session.verify = self.verify
        if self.proxies:
            print(f"Using Proxies: {self.proxies}")
            self.session.proxies.update(self.proxies)

        if not self.pat and not (self.username and self.password):
            raise ValueError("BlueOptima credentials not found. Please set BLUEOPTIMA_PAT or both BLUEOPTIMA_USERNAME and BLUEOPTIMA_PASSWORD.")

    def authenticate(self):
        """Authenticates using PAT or Username/Password fallback."""
        if self.pat:
            return self.authenticate_with_pat()
        else:
            return self.authenticate_with_password()

    def authenticate_with_pat(self):
        """Authenticates with the PAT."""
        print("Authenticating with BlueOptima PAT...")
        payload = {"personalAccessToken": self.pat}
        try:
            response = self.session.post(self.AUTH_URL_PAT, json=payload)
            return self._handle_auth_response(response)
        except requests.exceptions.SSLError as e:
            print(f"\nCRITICAL SSL ERROR: {e}")
            print("Tip: If you are on a VPN, you might need to set verify=False or install corporate root certs.")
            raise
        except Exception as e:
            print(f"Connection Error: {e}")
            raise

    def authenticate_with_password(self):
        """Authenticates with Username and Password."""
        print(f"Authenticating with BlueOptima Username: {self.username}...")
        payload = {
            "userName": self.username,
            "password": self.password,
            "terminate": True
        }
        response = self.session.post(self.AUTH_URL_USER, json=payload)
        return self._handle_auth_response(response)

    def _handle_auth_response(self, response):
        """Shared logic for processing auth responses."""
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            # Set expiry to 10 minutes (600 seconds), minus 30s buffer
            self.expiry_time = time.time() + 570
            print("Authentication successful.")
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    def get_token(self):
        """Returns a valid token, refreshing if necessary."""
        if not self.token or time.time() > self.expiry_time:
            return self.authenticate()
        return self.token

    def get_headers(self):
        """Returns the headers required for API calls."""
        return {
            "X-Auth-Token": self.get_token(),
            "Content-Type": "application/json"
        }
