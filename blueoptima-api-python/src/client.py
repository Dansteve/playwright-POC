import requests
from .auth import BlueOptimaAuth

class BlueOptimaClient:
    BASE_URL = "https://uix.blueoptima.com/api"

    def __init__(self, auth=None):
        self.auth = auth or BlueOptimaAuth()

    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}{endpoint}"
        headers = self.auth.get_headers()
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint, json_data=None):
        url = f"{self.BASE_URL}{endpoint}"
        headers = self.auth.get_headers()
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def get_profile(self):
        """Retrieves the user profile."""
        return self._get("/v4/profile")

    def get_developers(self, limit=200, offset=0):
        """Retrieves developers list (v2)."""
        return self._post("/v2/developers", json_data={"limit": limit, "offset": offset})

    def get_tld_developers(self, limit=200, offset=0):
        """Retrieves TLD developers list (v2)."""
        return self._post("/v2/tld/developers", json_data={"limit": limit, "offset": offset})

    def get_compass_developers(self, team_id=10642, limit=200, offset=0, start_date=None, end_date=None):
        """Retrieves compass developers using the complex multi-segment API."""
        import datetime
        now = datetime.datetime.now()
        first_of_month = now.replace(day=1).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")

        payload = {
            "teamId": team_id,
            "startDate": start_date or first_of_month,
            "endDate": end_date or today,
            "offset": offset,
            "limit": limit
        }
        return self._post("/v1/tld/compass/execution/developers", json_data=payload)
