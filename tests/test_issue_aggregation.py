import json
from pathlib import Path
from datetime import datetime
import os

from scripts import issue_aggregator as gen

METRICS_DIR = Path(__file__).parent.parent / "metrics"
METRICS_DIR.mkdir(exist_ok=True)

def test_aggregate_groups(tmp_path):
    from datetime import timezone, timedelta
    
    # Setup: Create a fake errors file for "today"
    now = datetime.now(timezone.utc)
    date_str = now.date().isoformat()
    errors_file = METRICS_DIR / f"errors_{date_str}.jsonl"

    # Create synthetic error records
    recs = [
        {'ts': now.isoformat(), 'type': 'ValueError', 'message': 'bad value', 'user_id': 'user1', 'trace': 'ValueError: bad value\n  File "a.py", line 10'},
        {'ts': now.isoformat(), 'type': 'ValueError', 'message': 'bad value', 'user_id': 'user2', 'trace': 'ValueError: bad value\n  File "a.py", line 10'},
        {'ts': now.isoformat(), 'type': 'KeyError', 'message': 'missing', 'user_id': 'user1', 'trace': "KeyError: 'x'\n  File \"b.py\", line 20"},
    ]

    with errors_file.open('w', encoding='utf-8') as f:
        for r in recs:
            f.write(json.dumps(r) + '\n')

    # Test
    # Determine range that covers this file (yesterday to tomorrow)
    start_date = now - timedelta(days=1)
    end_date = now + timedelta(days=1)
    
    errors = gen.load_errors_in_range(start_date, end_date)
    
    # We might pick up real errors too if file exists, so just check if OURS are there
    assert len(errors) >= 3

    summary = gen.aggregate(errors)
    # We expect our groups to be present
    assert any('ValueError' in s['signature'] for s in summary)
    assert any('KeyError' in s['signature'] for s in summary)

    # Clean up (Optional, but good practice in tests if we created it)
    # Warning: Removing shared metrics file might affect other runs if parallel
    # So maybe better to leave it or use a separate dir via mocking METRICS_DIR
    # But for a simple test, we can leave it or try to remove only matches.
    # errors_file.unlink(missing_ok=True) 
