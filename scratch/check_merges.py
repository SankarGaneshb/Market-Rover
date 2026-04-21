import requests

repo = "SankarGaneshb/Market-Rover"
url = f"https://api.github.com/repos/{repo}/pulls?state=closed"

try:
    r = requests.get(url)
    r.raise_for_status()
    pulls = r.json()
    print("Recent Merged PRs:")
    for p in pulls[:15]:
        merged = p.get('merged_at') is not None
        print(f"PR #{p['number']}: {p['title']} (Merged: {merged})")
except Exception as e:
    print(f"Error: {e}")
