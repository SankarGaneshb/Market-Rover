"""
Issue Aggregator & Reporter for Market-Rover.
Aggregates error logs from `metrics/`, generates summary reports, and dispatches notifcations via Slack/Email.

Usage:
    python scripts/issue_aggregator.py --frequency daily
    python scripts/issue_aggregator.py --frequency weekly --email user@example.com
"""
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict
import argparse
import os
import sys
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from config import ISSUE_OWNERS, LABEL_RULES
except ImportError:
    ISSUE_OWNERS = {}
    LABEL_RULES = []

METRICS_DIR = Path(__file__).parent.parent / "metrics"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_errors_in_range(start_date: datetime, end_date: datetime):
    """Load and aggregate errors for the given date range (inclusive start, exclusive end)."""
    out = []
    
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
    # Truncate to avoid huge keys
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
        
        # Find latest timestamp
        timestamps = [it.get('ts') for it in items if it.get('ts')]
        last_seen = max(timestamps) if timestamps else datetime.now(timezone.utc).isoformat()

        summary.append({
            'signature': sig,
            'occurrences': len(items),
            'unique_users': len(users),
            'sample': items[0],
            'last_seen': last_seen
        })

    # Impact Score: occurrences * unique_users
    for item in summary:
        item['impact_score'] = item['occurrences'] * max(1, item['unique_users'])

    summary.sort(key=lambda x: x['impact_score'], reverse=True)
    return summary


def post_to_slack(summary: list, webhook: str, frequency: str):
    """Post rich Block Kit message to Slack."""
    if not webhook or not summary:
        return False

    top_items = summary[:5]
    total_occ = sum(x['occurrences'] for x in summary)
    unique_sigs = len(summary)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {frequency.title()} Issue Report",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Total Errors:*\n{total_occ}"},
                {"type": "mrkdwn", "text": f"*Unique Issues:*\n{unique_sigs}"}
            ]
        },
        {"type": "divider"}
    ]

    for i, item in enumerate(top_items, 1):
        sig = item['signature']
        users = item['unique_users']
        occ = item['occurrences']
        
        # Extract location if possible
        sample = item.get('sample', {})
        context = sample.get('context', {})
        loc = context.get('location', 'Unknown')

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{i}. {sig}*\nLocation: `{loc}` | Users impacted: `{users}` | Count: `{occ}`"
            }
        })

    if len(summary) > 5:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"...and {len(summary) - 5} more issues."}]
        })

    payload = {"blocks": blocks}
    
    try:
        r = requests.post(webhook, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Failed to post to Slack: {e}")
        return False


def send_email_report(summary: list, frequency: str, recipients: list):
    """Send summary via SMTP."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password or not recipients:
        print("Skipping email: Missing credentials or recipients")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = f"Market-Rover {frequency.title()} Issue Report - {datetime.utcnow().date()}"

    # Build HTML body
    html = f"""
    <h2>{frequency.title()} Issue Summary</h2>
    <p>Total Unique Issues: {len(summary)}</p>
    <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr>
            <th>Issue Signature</th>
            <th>Occurrences</th>
            <th>Users Affected</th>
        </tr>
    """
    
    for item in summary[:10]:
        html += f"""
        <tr>
            <td>{item['signature'][:100]}...</td>
            <td>{item['occurrences']}</td>
            <td>{item['unique_users']}</td>
        </tr>
        """
    html += "</table>"
    
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frequency', choices=['daily', 'weekly', 'monthly'], default='daily')
    parser.add_argument('--email', help='Comma-separated email recipients', default='')
    
    args = parser.parse_args()
    
    # Calculate date range
    from datetime import timezone
    today = datetime.now(timezone.utc).date()
    # End date is usually "tomorrow" midnght to capture full "today", 
    # but metrics files are by date.
    # Logic: "Daily" = Yesterday's full logs (completed day) or Last 24h?
    # Safer: "Daily" = Today logs so far + Yesterday
    
    # Simplified Logic:
    # Daily = Look at (Now - 1 day) to Now
    # Weekly = Look at (Now - 7 days) to Now
    # Monthly = Look at (Now - 30 days) to Now
    
    end_date = datetime(today.year, today.month, today.day) + timedelta(days=1) # Midnight tomorrow
    
    if args.frequency == 'daily':
        start_date = end_date - timedelta(days=1)
    elif args.frequency == 'weekly':
        start_date = end_date - timedelta(days=7)
    else:
        start_date = end_date - timedelta(days=30)
        
    print(f"Aggregating errors from {start_date.date()} to {end_date.date()} ({args.frequency})...")
    
    errors = load_errors_in_range(start_date, end_date)
    summary = aggregate(errors)
    
    print(f"Found {len(summary)} unique issues.")
    
    # Save Report
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = REPORTS_DIR / f"report_{args.frequency}_{ts}.json"
    with out_file.open('w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {out_file}")
    
    # Slack
    webhook = os.getenv('SLACK_WEBHOOK')
    if webhook:
        if post_to_slack(summary, webhook, args.frequency):
            print("✅ Slack notification sent.")
            
    # Email
    if args.email:
        recipients = [e.strip() for e in args.email.split(',')]
        if send_email_report(summary, args.frequency, recipients):
             print("✅ Email report sent.")
