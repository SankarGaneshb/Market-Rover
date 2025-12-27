"""
Daily issue aggregation script for Market-Rover.
Reads `metrics/errors_YYYY-MM-DD.jsonl`, groups by signature (type + top stack line),
computes counts and unique users, and writes a summary JSON to `reports/daily_issues_YYYYMMDD.json`.

Run manually or schedule with cron/GitHub Actions.
"""
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import argparse
import os
import sys
import requests

# Add project root to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import ISSUE_OWNERS, LABEL_RULES

METRICS_DIR = Path(__file__).parent.parent / "metrics"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_errors_for_month(year: int, month: int):
    """Load and aggregate errors for all days in the given month."""
    out = []
    
    # Calculate start and end range for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    current = start_date
    while current < end_date:
        date_str = current.strftime("%Y-%m-%d")
        p = METRICS_DIR / f"errors_{date_str}.jsonl"
        if p.exists():
            with p.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        current += timedelta(days=1)
        
    return out


def signature_for(rec: dict) -> str:
    # Use error type + first non-empty line from trace as signature
    etype = rec.get('type', 'Unknown')
    trace = rec.get('trace', '') or ''
    first_line = ''
    for ln in trace.splitlines():
        ln = ln.strip()
        if ln:
            first_line = ln
            break
    sig = f"{etype} | {first_line[:200]}"
    return sig


def aggregate(errors: list):
    groups = defaultdict(list)
    for rec in errors:
        sig = signature_for(rec)
        groups[sig].append(rec)

    summary = []
    for sig, items in groups.items():
        users = set()
        for it in items:
            if it.get('user_id'):
                users.add(it.get('user_id'))
        summary.append({
            'signature': sig,
            'occurrences': len(items),
            'unique_users': len(users),
            'sample': items[0],
            'last_seen': max(it.get('ts') for it in items)
        })

    # sort by occurrences*unique_users (simple impact score)
    # compute impact score and sort
    for item in summary:
        item['impact_score'] = item['occurrences'] * max(1, item['unique_users'])

    summary.sort(key=lambda x: x['impact_score'], reverse=True)
    return summary


def write_report(date_str: str, summary: list):
    out = REPORTS_DIR / f"daily_issues_{date_str}.json"
    with out.open('w', encoding='utf-8') as f:
        json.dump({'date': date_str, 'summary': summary}, f, indent=2)
    return out


def post_to_slack(summary: list, webhook: str, max_items: int = 3):
    if not webhook:
        return False
    if not summary:
        return False

    top = summary[:max_items]
    text = f"Daily Issue Report ({datetime.utcnow().date().isoformat()})\nTop {len(top)} issues:\n"
    for i, item in enumerate(top, 1):
        text += f"{i}. {item['signature'][:200]} — occurrences: {item['occurrences']}, users: {item['unique_users']}\n"

    payload = {"text": text}
    try:
        r = requests.post(webhook, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def create_github_issue(item: dict, repo: str = None, token: str = None):
    """Create a GitHub issue for the given aggregated item.

    Expects `repo` in the form 'owner/repo'. Uses `token` for Authorization.
    """
    if not repo or not token:
        return False

    owner_repo = repo
    url = f"https://api.github.com/repos/{owner_repo}/issues"
    title = f"Automated Alert: {item['signature'][:80]}"
    body = (
        f"Automated daily issue detected.\n\nSignature: {item['signature']}\n"
        f"Occurrences: {item['occurrences']}\nUnique users: {item['unique_users']}\nLast seen: {item.get('last_seen')}\n\n"
        f"Sample record:\n```\n{json.dumps(item.get('sample', {}), indent=2)}\n```")

    # Allow labels and assignees via environment for auto-assignment
    labels_env = os.getenv('GITHUB_ISSUE_LABELS', '')
    assignees_env = os.getenv('GITHUB_ISSUE_ASSIGNEES', '')
    labels = [l.strip() for l in labels_env.split(',') if l.strip()] if labels_env else ["automated-alert"]
    assignees = [a.strip() for a in assignees_env.split(',') if a.strip()] if assignees_env else []

    # Pattern-based enhancements from config mappings
    sig = item.get('signature', '')
    # Add labels from LABEL_RULES when patterns match
    for pat, lab in LABEL_RULES:
        if pat.lower() in sig.lower() and lab not in labels:
            labels.append(lab)

    # Add assignees based on ISSUE_OWNERS mapping
    for key, owners in ISSUE_OWNERS.items():
        if key.lower() in sig.lower():
            for o in owners:
                if o not in assignees:
                    assignees.append(o)

    payload = {"title": title, "body": body, "labels": labels}
    if assignees:
        payload["assignees"] = assignees

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Default to previous month
    today = datetime.utcnow().date()
    first = today.replace(day=1)
    last_month = first - timedelta(days=1)
    
    parser.add_argument('--year', type=int, help='Year to aggregate (YYYY)', default=last_month.year)
    parser.add_argument('--month', type=int, help='Month to aggregate (1-12)', default=last_month.month)
    
    args = parser.parse_args()
    
    print(f"Aggregating errors for {args.year}-{args.month:02d}...")
    errors = load_errors_for_month(args.year, args.month)
    summary = aggregate(errors)
    
    date_str = f"{args.year}-{args.month:02d}"
    
    # Write report
    out = REPORTS_DIR / f"monthly_issues_{date_str}.json"
    with out.open('w', encoding='utf-8') as f:
        json.dump({'month': date_str, 'summary': summary}, f, indent=2)
    
    print(f"Wrote report: {out}")
    # Optionally post to Slack if webhook provided via env
    webhook = os.getenv('SLACK_WEBHOOK', '')
    if webhook:
        posted = post_to_slack(summary, webhook)
        if posted:
            print("Posted summary to Slack")
    # Optionally create GitHub issue for top item if impact exceeds threshold
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    GITHUB_REPO = os.getenv('GITHUB_REPO', 'SankarGaneshb/Market-Rover')
    ISSUE_IMPACT_THRESHOLD = int(os.getenv('ISSUE_IMPACT_THRESHOLD', '10'))
    if summary and GITHUB_TOKEN:
        top = summary[0]
        if top.get('impact_score', 0) >= ISSUE_IMPACT_THRESHOLD:
            created = create_github_issue(top, repo=GITHUB_REPO, token=GITHUB_TOKEN)
            if created:
                print("Created GitHub issue for top item")
