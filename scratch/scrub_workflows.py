import os
from pathlib import Path

def scrub_file(file_path):
    print(f"Scrubbing {file_path}...")
    try:
        # Read the file with 'utf-8-sig' to handle BOM automatically
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        # Keep only ASCII characters (0-127)
        original_len = len(content)
        scrubbed_content = "".join([c for c in content if ord(c) < 128])

        if len(scrubbed_content) != original_len:
            print(f"  Removed {original_len - len(scrubbed_content)} non-ASCII characters.")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(scrubbed_content)
        else:
            print("  No non-ASCII characters found.")
    except Exception as e:
        print(f"  Error: {e}")

files_to_scrub = [
    ".github/workflows/greetings.yml",
    ".github/workflows/validate_issue_assignees.yml",
    ".github/workflows/schedule_system_health.yml",
    ".github/workflows/daily_issue_report.yml",
    ".github/workflows/weekly_backtest.yml"
]

for f in files_to_scrub:
    scrub_file(f)
