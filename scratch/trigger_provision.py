import requests
import sys

URL = "https://hil-rover-9514347926.us-central1.run.app/api/provision"

try:
    print(f"Triggering provisioning at {URL}...")
    response = requests.post(URL, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
