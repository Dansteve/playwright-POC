import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

class BlueOptimaAuth:
    AUTH_URL = "https://iam.blueoptima.com/api/v1/authenticate/pat"
    REFRESH_URL = "https://uix.blueoptima.com/api/v1/refreshToken"

    def __init__(self, pat=None):
        self.pat = pat or os.getenv("BLUEOPTIMA_PAT", "")
        self.token = None
        self.expiry_time = 0

        if not self.pat:
            raise ValueError("BlueOptima PAT not found. Please set BLUEOPTIMA_PAT environment variable.")

    def authenticate(self):
        """Authenticates with the PAT and retrieves a JWT token."""
        print("Authenticating with BlueOptima PAT...")
        payload = {"personalAccessToken": self.pat}
        response = requests.post(self.AUTH_URL, json=payload)
        
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
