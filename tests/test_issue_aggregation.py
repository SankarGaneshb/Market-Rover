import json
from pathlib import Path
from datetime import datetime
import os

from scripts import generate_daily_issue_report as gen

METRICS_DIR = Path('metrics')
METRICS_DIR.mkdir(exist_ok=True)


def test_aggregate_groups(tmp_path, monkeypatch):
    date_str = datetime.utcnow().date().isoformat()
    errors_file = METRICS_DIR / f"errors_{date_str}.jsonl"

    # Create synthetic error records
    recs = [
        {"ts": "2025-12-26T00:00:00Z", "type": "ValueError", "message": "bad value", "user_id": "user1", "trace": "ValueError: bad value\n  File \"a.py\", line 10"},
        {"ts": "2025-12-26T00:01:00Z", "type": "ValueError", "message": "bad value", "user_id": "user2", "trace": "ValueError: bad value\n  File \"a.py\", line 10"},
        {"ts": "2025-12-26T00:02:00Z", "type": "KeyError", "message": "missing", "user_id": "user1", "trace": "KeyError: 'x'\n  File \"b.py\", line 20"},
    ]

    with errors_file.open('w', encoding='utf-8') as f:
        for r in recs:
            f.write(json.dumps(r) + '\n')

    errors = gen.load_errors(date_str)
    assert len(errors) == 3

    summary = gen.aggregate(errors)
    # We expect 2 groups (ValueError and KeyError)
    assert any('ValueError' in s['signature'] for s in summary)
    assert any('KeyError' in s['signature'] for s in summary)

    # Clean up
    errors_file.unlink()
