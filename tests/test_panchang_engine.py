"""
Unit tests for Panchang & Muhurtha-SIP Calculation Engine with Market Hours & Holiday Filters.
"""
import pytest
import datetime
from rover_tools.panchang_engine import (
    calculate_panchang,
    scan_auspicious_month_windows,
    check_trading_day_status,
    NAKSHATRAS,
    TITHIS,
    _calculate_julian_day,
    _lahiri_ayanamsha
)
from rover_tools.sip_planner import MuhurthaSIPPlanner


def test_julian_day_calculation():
    """Verify Julian Day formula against known astronomical date."""
    dt_j2000 = datetime.datetime(2000, 1, 1, 12, 0, 0)
    jd = _calculate_julian_day(dt_j2000)
    assert abs(jd - 2451545.0) < 0.01


def test_panchang_attributes():
    """Verify Panchang calculation returns valid Vedic attributes & market hours."""
    dt = datetime.datetime(2026, 10, 15, 12, 0, 0)
    res = calculate_panchang(dt)

    assert "nakshatra" in res
    assert res["nakshatra"]["name"] in NAKSHATRAS
    assert 1 <= res["nakshatra"]["number"] <= 27

    assert "tithi" in res
    assert res["tithi"]["name"] in TITHIS
    assert 1 <= res["tithi"]["number"] <= 30
    assert res["tithi"]["paksha"] in ["Shukla", "Krishna"]

    assert "timings" in res
    assert "rahu_kaalam" in res["timings"]
    assert "market_hours_muhurat" in res["timings"]
    assert "market_status" in res


def test_trading_day_status():
    """Verify weekend and NSE holiday detection."""
    # 1. Republic Day (Holiday)
    holiday = check_trading_day_status(datetime.date(2026, 1, 26))
    assert holiday["is_trading_day"] is False
    assert "Republic Day" in holiday["status_label"]

    # 2. Weekend (Sunday)
    sunday = check_trading_day_status(datetime.date(2026, 10, 18))
    assert sunday["is_trading_day"] is False
    assert "Weekend" in sunday["status_label"]

    # 3. Active Trading Day (Thursday)
    thursday = check_trading_day_status(datetime.date(2026, 10, 15))
    assert thursday["is_trading_day"] is True
    assert "Active Trading Day" in thursday["status_label"]


def test_scan_auspicious_month_windows_market_days():
    """Verify month scan returns only active market trading days when requested."""
    windows = scan_auspicious_month_windows(2026, 10, market_days_only=True)
    assert isinstance(windows, list)
    assert len(windows) > 0

    for w in windows:
        assert w["is_trading_day"] is True


def test_from_date_filter_and_rollover():
    """Verify that from_date filters out past dates and planner rolls over when past."""
    # 1. from_date filter in scan
    windows_oct_late = scan_auspicious_month_windows(2026, 10, market_days_only=True, from_date=datetime.date(2026, 10, 10))
    for w in windows_oct_late:
        assert datetime.datetime.strptime(w["date"], "%Y-%m-%d").date() >= datetime.date(2026, 10, 10)

    # 2. Planner auto-rollover for past dates
    planner = MuhurthaSIPPlanner()
    plan = planner.calculate_plan(budget=25000.0, market_days_only=True)
    today = datetime.date.today()
    primary_date = datetime.datetime.strptime(plan["primary_window"]["date"], "%Y-%m-%d").date()
    assert primary_date >= today


def test_sip_planner_allocation():
    """Verify dynamic lot-sizing and budget calculation with active market hours."""
    planner = MuhurthaSIPPlanner()
    plan = planner.calculate_plan(budget=25000.0, year=2026, month=10, market_days_only=True)

    assert plan["budget"] == 25000.0
    assert "primary_window" in plan
    assert plan["primary_window"]["is_trading_day"] is True
    assert "order_basket" in plan
    assert len(plan["order_basket"]) > 0

    assert plan["total_estimated_spend"] <= 25000.0
    assert plan["remaining_cash"] >= 0.0

    for item in plan["order_basket"]:
        assert item["quantity"] >= 1
        assert item["ltp"] > 0
        assert item["estimated_cost"] > 0
