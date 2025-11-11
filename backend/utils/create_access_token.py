import requests
import base64
from config import settings

client_id = settings.SUSTAINABILITY_DATA_API_CLIENT_ID
client_secret = settings.SUSTAINABILITY_DATA_API_CLIENT_SECRET
auth_str = f"{client_id}:{client_secret}"
b64_auth = base64.b64encode(auth_str.encode("ascii")).decode("ascii")

url = "https://developer.api.autodesk.com/authentication/v2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
    "Authorization": f"Basic {b64_auth}"
}
data = {
    "grant_type": "client_credentials",
    "scope": "data:read"
}

response = requests.post(url, headers=headers, data=data)
access_token = response.json().get("access_token")