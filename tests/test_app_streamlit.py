import sys
import importlib
import types
import pytest
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _import_app_with_stub():
    """Import the app module while stubbing Streamlit to avoid UI side-effects."""
    # Create a minimal streamlit stub
    stub = types.ModuleType("streamlit")
    stub.set_page_config = lambda **kwargs: None

    # Lightweight session_state emulation that supports both item and attribute access
    class _SessionState:
        def __init__(self):
            self._store = {}

        def __contains__(self, key):
            return key in self._store

        def __getattr__(self, key):
            try:
                return self._store[key]
            except KeyError:
                raise AttributeError(key)

        def __setattr__(self, key, value):
            if key == '_store':
                super().__setattr__(key, value)
            else:
                self._store[key] = value

        def __getitem__(self, key):
            return self._store[key]

        def __setitem__(self, key, value):
            self._store[key] = value

    stub.session_state = _SessionState()

    def cache_data_decorator(ttl=None):
        def decorator(f):
            return f
        return decorator

    stub.cache_data = cache_data_decorator

    # Insert stub into sys.modules before importing app
    sys.modules['streamlit'] = stub

    # Ensure a fresh import
    if 'app' in sys.modules:
        del sys.modules['app']

    app = importlib.import_module('app')

    return app


def test_load_portfolio_file_valid_and_drops_invalid():
    app = _import_app_with_stub()

    csv = (
        "Symbol,Company Name\n"
        "RELIANCE,Reliance Industries Ltd\n"
        "'; DROP TABLE--,Malicious Corp\n"
        ",NoSymbol Corp\n"
    )

    df = app.load_portfolio_file(csv.encode('utf-8'), 'test.csv')

    # Valid symbol should remain and malicious row should be dropped
    symbols = df['Symbol'].astype(str).tolist()
    assert 'RELIANCE' in symbols
    # Ensure malicious pattern was removed
    assert not any(s.strip().startswith("'") for s in symbols)


def test_load_portfolio_file_missing_columns_raises():
    app = _import_app_with_stub()

    bad_csv = "Ticker,Name\nAAPL,Apple Inc\n"

    with pytest.raises(ValueError):
        app.load_portfolio_file(bad_csv.encode('utf-8'), 'bad.csv')


def test_load_report_content_reads_file(tmp_path):
    app = _import_app_with_stub()

    # Use configured REPORT_DIR to place a temporary file so app.load_report_content can read it
    from config import REPORT_DIR

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    test_path = REPORT_DIR / 'market_rover_report_test.txt'
    content = 'SAMPLE REPORT CONTENT'
    test_path.write_text(content, encoding='utf-8')

    try:
        loaded = app.load_report_content(str(test_path))
        assert loaded == content
    finally:
        # Cleanup
        if test_path.exists():
            test_path.unlink()
