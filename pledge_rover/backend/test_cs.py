import cloudscraper
import json

def test_nse_cloudscraper():
    scraper = cloudscraper.create_scraper()
    print("Testing NSE with Cloudscraper...")
    try:
        url = "https://www.nseindia.com/api/corporates-sast-reg31?index=equities"
        r = scraper.get(url, timeout=15)
        print("Status Code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Records:", len(data.get('data', [])))
        else:
            print(r.text[:200])
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test_nse_cloudscraper()
