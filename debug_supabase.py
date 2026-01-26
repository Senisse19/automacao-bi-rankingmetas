import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") + "/rest/v1/nexus_jobs"
headers = {
    "apikey": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "Authorization": "Bearer " + os.getenv("SUPABASE_SERVICE_ROLE_KEY")
}
params = {"select": "id", "limit": 1}

print(f"URL: {url}")
resp = requests.get(url, headers=headers, params=params)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
