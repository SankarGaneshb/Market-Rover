import os
import requests
import json
import sys

def create_emergency_issue(title, body):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    if not token or not repo:
        print("SRE_FALLBACK_ERROR: GITHUB_TOKEN or GITHUB_REPOSITORY not set.")
        return False

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": f"🚨 SRE EMERGENCY: {title}",
        "body": body,
        "labels": ["sre-alert", "bug", "p0"]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"SRE_FALLBACK_SUCCESS: Created emergency issue: {response.json().get('html_url')}")
        return True
    except Exception as e:
        print(f"SRE_FALLBACK_CRITICAL_FAILURE: Could not create GitHub issue: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sre_emergency_fallback.py <title> <body>")
        sys.exit(1)

    title = sys.argv[1]
    body = sys.argv[2]
    create_emergency_issue(title, body)
