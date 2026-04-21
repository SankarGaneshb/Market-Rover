import requests

repo = "SankarGaneshb/Market-Rover"
url = f"https://api.github.com/repos/{repo}/pulls?state=open"

try:
    r = requests.get(url)
    r.raise_for_status()
    pulls = r.json()
    print("Open PRs:")
    for p in pulls:
        print(f"PR #{p['number']}: {p['title']}")
except Exception as e:
    print(f"Error: {e}")
