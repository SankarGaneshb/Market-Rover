#!/usr/bin/env python3
"""Run the daily aggregator with secrets provided interactively.

Prompts for a GitHub Personal Access Token (hidden) and accepts optional
values for repository, assignees, labels, Slack webhook and threshold.

This wrapper does not print the token or store it on disk.
"""
import os
import argparse
import getpass
import subprocess
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Run daily aggregator with interactive token input')
    parser.add_argument('--date', help='Date to aggregate (YYYY-MM-DD). Defaults to today', default=datetime.utcnow().date().isoformat())
    parser.add_argument('--repo', help='GitHub repo (owner/repo). Defaults to repo configured in workflow', default=None)
    parser.add_argument('--assignees', help='Comma-separated assignees', default=None)
    parser.add_argument('--labels', help='Comma-separated labels', default=None)
    parser.add_argument('--slack', help='Slack webhook URL (optional)', default=None)
    parser.add_argument('--threshold', help='ISSUE_IMPACT_THRESHOLD (optional)', default=None)
    parser.add_argument('--token', help='GitHub PAT (unsafe on CLI). If not provided, will prompt securely.', default=None)
    args = parser.parse_args()

    token = args.token
    if not token:
        try:
            token = getpass.getpass('Enter GitHub Personal Access Token (input hidden): ')
        except Exception:
            print('Could not read token securely. You may provide --token, but avoid pasting secrets in logs.')
            return 1

    if not token:
        print('No token provided; aborting.')
        return 2

    # Prepare environment for subprocess without modifying caller env
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = token
    if args.repo:
        env['GITHUB_REPO'] = args.repo
    if args.assignees:
        env['GITHUB_ISSUE_ASSIGNEES'] = args.assignees
    if args.labels:
        env['GITHUB_ISSUE_LABELS'] = args.labels
    if args.slack:
        env['SLACK_WEBHOOK'] = args.slack
    if args.threshold:
        env['ISSUE_IMPACT_THRESHOLD'] = args.threshold

    # Run the aggregator script using project PYTHONPATH so local imports resolve
    cmd = ['python3', 'scripts/generate_daily_issue_report.py', '--date', args.date]

    print(f'Running aggregator for date {args.date}...')
    print('Note: token was read securely and will not be shown.')

    # Use PYTHONPATH=. to make sure imports like `config` resolve
    run_env = env.copy()
    run_env['PYTHONPATH'] = run_env.get('PYTHONPATH', '')
    if run_env['PYTHONPATH']:
        run_env['PYTHONPATH'] = '.:' + run_env['PYTHONPATH']
    else:
        run_env['PYTHONPATH'] = '.'

    result = subprocess.run(cmd, env=run_env)

    if result.returncode == 0:
        print('Aggregator finished successfully.')
    else:
        print(f'Aggregator exited with code {result.returncode}.')

    # Avoid printing secrets; just return same exit code
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
