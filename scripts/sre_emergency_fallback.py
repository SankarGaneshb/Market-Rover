import os
import json
import urllib.request
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
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = {
        "title": f"🚨 SRE EMERGENCY: {title}",
        "body": body,
        "labels": ["sre-alert", "bug", "p0"]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            issue_data = json.loads(res_body)
            print(f"SRE_FALLBACK_SUCCESS: Created emergency issue: {issue_data.get('html_url')}")
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
