
import requests
from PIL import Image
from io import BytesIO

url = "https://logo.clearbit.com/tcs.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Testing download from {url}")
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        print(f"Image Size: {img.size}")
        img.save("test_logo.png")
        print("Saved test_logo.png")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
