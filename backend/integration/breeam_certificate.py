import base64
from typing import Optional

import requests

from utils.config import settings


class BreeamClient:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or settings.BREEAM_USERNAME
        self.password = password or settings.BREEAM_PASSWORD
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Accept": "application/json",
        }
        self.base_url = "https://api.breeam.com/datav1"

    def get_country(self):
        url = f"{self.base_url}/countries"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = BreeamClient()
    countries = client.get_country()
    print(countries)
