import requests
from requests.structures import CaseInsensitiveDict

api_key = "dd2141beb4764309a38b08dd3360b9e6"

url = f"https://api.geoapify.com/v1/postcode/list?&countrycode=de&limit=20&geometry=original&filter=rect:8.303646633584322,49.56318958410171,11.11799160014175,50.83655794972171&apiKey={api_key}"

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"

resp = requests.get(url, headers=headers)

print(resp.status_code)
print(resp.json())
open("debug_geoapify.json", "w", encoding="utf-8").write(resp.text)