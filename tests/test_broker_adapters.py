"""
Unit tests for Zero-OAuth Broker & Calendar Adapters.
"""
import pytest
import json
import urllib.parse
from rover_tools.broker_adapters import ZerodhaKiteAdapter, GrowwAdapter, ICICIDirectAdapter
from rover_tools.calendar_adapter import CalendarSyncAdapter
from rover_tools.sip_planner import MuhurthaSIPPlanner


@pytest.fixture
def sample_plan():
    planner = MuhurthaSIPPlanner()
    return planner.calculate_plan(budget=25000.0, year=2026, month=10)


def test_zerodha_kite_adapter(sample_plan):
    """Verify Zerodha Kite basket schema and deep link generation."""
    basket = sample_plan["order_basket"]
    kite_payload = ZerodhaKiteAdapter.generate_basket_payload(basket)

    assert isinstance(kite_payload, list)
    assert len(kite_payload) == len(basket)

    for item in kite_payload:
        assert item["variety"] == "regular"
        assert item["exchange"] == "NSE"
        assert item["transaction_type"] == "BUY"
        assert item["order_type"] == "MARKET"
        assert item["quantity"] >= 1
        assert "tradingsymbol" in item
        assert not item["tradingsymbol"].endswith(".NS")

    deep_link = ZerodhaKiteAdapter.generate_deep_link(basket)
    assert deep_link.startswith("https://kite.zerodha.com/connect/basket?data=")

    # Verify decoded payload from URL
    encoded_part = deep_link.split("data=")[1]
    decoded_json = urllib.parse.unquote(encoded_part)
    parsed = json.loads(decoded_json)
    assert len(parsed) == len(basket)


def test_groww_adapter(sample_plan):
    """Verify Groww asset links and summary generator."""
    basket = sample_plan["order_basket"]
    links = GrowwAdapter.generate_asset_links(basket)

    assert len(links) == len(basket)
    for l in links:
        assert "groww_url" in l
        assert l["groww_url"].startswith("https://groww.in/stocks/")
        assert l["quantity"] >= 1

    summary = GrowwAdapter.generate_copyable_summary(basket)
    assert "GROWW 1-CLICK ORDER LIST" in summary


def test_icici_direct_adapter(sample_plan):
    """Verify ICICI Direct Breeze payload."""
    basket = sample_plan["order_basket"]
    breeze_items = ICICIDirectAdapter.generate_breeze_payload(basket)

    assert len(breeze_items) == len(basket)
    for b in breeze_items:
        assert b["exchange_code"] == "NSE"
        assert b["action"] == "buy"
        assert b["order_type"] == "market"


def test_calendar_sync_adapter(sample_plan):
    """Verify Google Calendar URL and .ics file format."""
    broker_link = "https://kite.zerodha.com/connect/basket?data=test"

    # 1. Google Calendar URL
    gcal_url = CalendarSyncAdapter.generate_google_calendar_url(sample_plan, "Zerodha", broker_link)
    assert gcal_url.startswith("https://calendar.google.com/calendar/render?")
    assert "action=TEMPLATE" in gcal_url
    assert "Muhurtha+SIP" in gcal_url or "Muhurtha%20SIP" in gcal_url

    # 2. .ics content
    ics_text = CalendarSyncAdapter.generate_ics_content(sample_plan, "Zerodha", broker_link)
    assert "BEGIN:VCALENDAR" in ics_text
    assert "BEGIN:VEVENT" in ics_text
    assert "BEGIN:VALARM" in ics_text
    assert "TRIGGER:-PT15M" in ics_text
    assert "END:VALARM" in ics_text
    assert "END:VEVENT" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "kite.zerodha.com" in ics_text


def test_amo_execution_mode(sample_plan):
    """Verify AMO payload generation across Zerodha, Groww, ICICI Direct, and Calendar."""
    basket = sample_plan["order_basket"]

    # 1. Zerodha AMO variety
    zk_amo = ZerodhaKiteAdapter.generate_basket_payload(basket, variety="amo")
    for item in zk_amo:
        assert item["variety"] == "amo"

    # 2. Groww AMO summary
    groww_amo = GrowwAdapter.generate_copyable_summary(basket, execution_mode="AMO")
    assert "AMO / OFF-MARKET" in groww_amo

    # 3. ICICI Direct AMO validity
    icici_amo = ICICIDirectAdapter.generate_breeze_payload(basket, execution_mode="AMO")
    for item in icici_amo:
        assert item["validity"] == "amo"

    # 4. Calendar Sync in AMO mode
    gcal_amo = CalendarSyncAdapter.generate_google_calendar_url(sample_plan, "Zerodha", execution_mode="AMO")
    assert "AMO" in gcal_amo

    ics_amo = CalendarSyncAdapter.generate_ics_content(sample_plan, "Zerodha", execution_mode="AMO")
    assert "AMO" in ics_amo
    assert "09:15 AM" in ics_amo
