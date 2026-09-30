"""
Panchang & Astronomical Timing Engine for Market-Rover.
Calculates high-precision Vedic Panchang attributes:
- 27 Nakshatras (Ashwini to Revati)
- 30 Tithis (Shukla and Krishna Pakshas)
- 27 Nitya Yogas & 11 Karanas
- Auspicious Yogas: Guru Pushya, Ravi Pushya, Sarvartha Siddhi, Amrita Siddhi, Abhijit Muhurat
- Inauspicious Periods: Rahu Kaalam, Yama Gandam, Gulika Kalam
- Market Hours & NSE Trading Holiday Verification (09:15 AM - 03:30 PM IST)

Pure Python implementation with ZERO C-dependencies for 100% Green-on-Arrival (GoA) portability.
"""
import math
import datetime
from typing import Dict, List, Any, Optional, Tuple

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]

NITYA_YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Rahu Kaalam octaves (1-indexed octave of daylight 6 AM - 6 PM, 1.5h per octave)
RAHU_KAALAM_OCTAVES = {
    0: (7.5, 9.0),   # Monday
    1: (15.0, 16.5), # Tuesday
    2: (12.0, 13.5), # Wednesday
    3: (13.5, 15.0), # Thursday
    4: (10.5, 12.0), # Friday
    5: (9.0, 10.5),  # Saturday
    6: (16.5, 18.0)  # Sunday
}

YAMA_GANDAM_OCTAVES = {
    0: (10.5, 12.0), # Monday
    1: (9.0, 10.5),  # Tuesday
    2: (7.5, 9.0),   # Wednesday
    3: (6.0, 7.5),   # Thursday
    4: (15.0, 16.5), # Friday
    5: (13.5, 15.0), # Saturday
    6: (12.0, 13.5)  # Sunday
}

# Official NSE Trading Holidays (YYYY-MM-DD -> Holiday Name)
NSE_TRADING_HOLIDAYS = {
    # 2025 Holidays
    "2025-01-26": "Republic Day",
    "2025-02-26": "Mahashivratri",
    "2025-03-14": "Holi",
    "2025-03-31": "Id-Ul-Fitr (Ramzan Id)",
    "2025-04-10": "Mahavir Jayanti",
    "2025-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-01": "Maharashtra Day",
    "2025-06-07": "Bakri Id",
    "2025-07-06": "Moharram",
    "2025-08-15": "Independence Day",
    "2025-08-27": "Ganesh Chaturthi",
    "2025-10-02": "Mahatma Gandhi Jayanti",
    "2025-10-21": "Dussehra",
    "2025-11-01": "Diwali Laxmi Pujan (Muhurat Trading only)",
    "2025-11-05": "Guru Nanak Jayanti",
    "2025-12-25": "Christmas",

    # 2026 Holidays
    "2026-01-26": "Republic Day",
    "2026-02-15": "Mahashivratri",
    "2026-03-04": "Holi",
    "2026-03-21": "Id-Ul-Fitr",
    "2026-03-27": "Ram Navami",
    "2026-03-31": "Mahavir Jayanti",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id",
    "2026-06-26": "Muharram",
    "2026-08-15": "Independence Day",
    "2026-08-26": "Milad-un-Nabi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan (Muhurat Trading only)",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas",

    # 2027 Holidays
    "2027-01-26": "Republic Day",
    "2027-03-06": "Mahashivratri",
    "2027-03-23": "Holi",
    "2027-03-26": "Good Friday",
    "2027-04-14": "Dr. Ambedkar Jayanti",
    "2027-05-01": "Maharashtra Day",
    "2027-08-15": "Independence Day",
    "2027-10-02": "Mahatma Gandhi Jayanti",
    "2027-10-10": "Dussehra",
    "2027-10-29": "Diwali Laxmi Pujan",
    "2027-11-14": "Guru Nanak Jayanti",
    "2027-12-25": "Christmas"
}


def check_trading_day_status(target_date: datetime.date) -> Dict[str, Any]:
    """
    Checks if a given date is an active NSE/BSE trading day.

    Returns:
        Dict with is_trading_day (bool), status_label (str), and next_trading_day (str).
    """
    date_str = target_date.strftime("%Y-%m-%d")
    weekday_idx = target_date.weekday()

    if weekday_idx == 5:
        is_open = False
        reason = "Saturday (Weekend - Exchange Closed)"
    elif weekday_idx == 6:
        is_open = False
        reason = "Sunday (Weekend - Exchange Closed)"
    elif date_str in NSE_TRADING_HOLIDAYS:
        is_open = False
        reason = f"NSE Trading Holiday ({NSE_TRADING_HOLIDAYS[date_str]})"
    else:
        is_open = True
        reason = "Active Trading Day (09:15 AM - 03:30 PM IST)"

    # Calculate next active trading day if market is closed
    next_day = target_date + datetime.timedelta(days=1)
    while next_day.weekday() >= 5 or next_day.strftime("%Y-%m-%d") in NSE_TRADING_HOLIDAYS:
        next_day += datetime.timedelta(days=1)

    return {
        "is_trading_day": is_open,
        "market_hours": "09:15 - 15:30 IST",
        "status_label": reason,
        "next_trading_day": next_day.strftime("%Y-%m-%d") if not is_open else date_str
    }


def _calculate_julian_day(dt: datetime.datetime) -> float:
    """Calculates Julian Day Number for a UTC datetime."""
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def _lahiri_ayanamsha(jd: float) -> float:
    """Calculates Lahiri (Chitrapaksha) Ayanamsha in degrees."""
    t = (jd - 2451545.0) / 36525.0
    ayanamsha = 23.856667 + (50.290966 * t * 100.0) / 3600.0
    return ayanamsha


def _sun_ecliptic_longitude(jd: float) -> float:
    """Computes Tropical Sun Ecliptic Longitude in degrees (0 - 360)."""
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * (t ** 2)
    m = 357.52911 + 35999.05029 * t - 0.0001537 * (t ** 2)
    m_rad = math.radians(m % 360.0)

    c = (1.914602 - 0.004817 * t - 0.000014 * (t ** 2)) * math.sin(m_rad) + \
        (0.019993 - 0.000101 * t) * math.sin(2 * m_rad) + \
        0.000289 * math.sin(3 * m_rad)

    true_long = (l0 + c) % 360.0
    return true_long


def _moon_ecliptic_longitude(jd: float) -> float:
    """Computes Tropical Moon Ecliptic Longitude in degrees (0 - 360)."""
    t = (jd - 2451545.0) / 36525.0
    l_prime = 218.3164477 + 481267.88123421 * t
    d = 297.8501921 + 445267.1114034 * t
    m = 357.5291092 + 35999.0502909 * t
    m_prime = 134.9633964 + 477198.8675055 * t
    f = 93.2720950 + 483202.0175233 * t

    d_rad = math.radians(d % 360.0)
    m_rad = math.radians(m % 360.0)
    mp_rad = math.radians(m_prime % 360.0)
    f_rad = math.radians(f % 360.0)

    correction = (
        6.288774 * math.sin(mp_rad) +
        1.274027 * math.sin(2 * d_rad - mp_rad) +
        0.658314 * math.sin(2 * d_rad) +
        0.213618 * math.sin(2 * mp_rad) -
        0.185116 * math.sin(m_rad) -
        0.114332 * math.sin(2 * f_rad) +
        0.058793 * math.sin(2 * d_rad - 2 * mp_rad) +
        0.057066 * math.sin(2 * d_rad - m_rad - mp_rad) +
        0.053322 * math.sin(2 * d_rad + mp_rad) +
        0.046153 * math.sin(2 * d_rad - m_rad)
    )

    moon_long = (l_prime + correction) % 360.0
    return moon_long


def calculate_panchang(dt: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Computes complete Vedic Panchang and Market Hours alignment.
    """
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
        dt = dt.replace(tzinfo=None)

    dt_utc = dt - datetime.timedelta(hours=5, minutes=30)
    jd = _calculate_julian_day(dt_utc)
    ayanamsha = _lahiri_ayanamsha(jd)

    sun_tropical = _sun_ecliptic_longitude(jd)
    moon_tropical = _moon_ecliptic_longitude(jd)

    sun_sidereal = (sun_tropical - ayanamsha) % 360.0
    moon_sidereal = (moon_tropical - ayanamsha) % 360.0

    # 1. Nakshatra
    nakshatra_idx = int(moon_sidereal / (360.0 / 27.0)) % 27
    nakshatra_name = NAKSHATRAS[nakshatra_idx]
    nakshatra_progress = (moon_sidereal % (360.0 / 27.0)) / (360.0 / 27.0)

    # 2. Tithi
    diff = (moon_sidereal - sun_sidereal) % 360.0
    tithi_idx = int(diff / 12.0) % 30
    tithi_name = TITHIS[tithi_idx]
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"

    # 3. Nitya Yoga
    yoga_deg = (moon_sidereal + sun_sidereal) % 360.0
    yoga_idx = int(yoga_deg / (360.0 / 27.0)) % 27
    yoga_name = NITYA_YOGAS[yoga_idx]

    # 4. Weekday & Rahu Kaalam
    weekday_idx = dt.weekday()
    weekday_name = WEEKDAYS[weekday_idx]

    rahu_start, rahu_end = RAHU_KAALAM_OCTAVES[weekday_idx]
    yama_start, yama_end = YAMA_GANDAM_OCTAVES[weekday_idx]

    def _format_time(hours_float: float) -> str:
        h = int(hours_float)
        m = int((hours_float - h) * 60)
        return f"{h:02d}:{m:02d}"

    rahu_str = f"{_format_time(rahu_start)} - {_format_time(rahu_end)} IST"
    yama_str = f"{_format_time(yama_start)} - {_format_time(yama_end)} IST"

    # 5. Market-Hours Muhurat Determination (09:15 - 15:30 IST)
    # Abhijit Muhurat: ~11:45 AM - 12:35 PM IST (falls perfectly within trading hours, except Wed)
    if weekday_name == "Wednesday":
        market_muhurat_str = "10:15 - 11:45 IST (Shubh Choghadiya - Market Hours)"
        is_in_market_hours = True
    else:
        market_muhurat_str = "11:45 - 12:35 IST (Abhijit Muhurat - Market Hours)"
        is_in_market_hours = True

    # 6. Auspicious Yogas Detection
    special_yogas = []

    if nakshatra_name == "Pushya" and weekday_name == "Thursday":
        special_yogas.append("Guru Pushya Yoga (Supreme Wealth Window)")

    if nakshatra_name == "Pushya" and weekday_name == "Sunday":
        special_yogas.append("Ravi Pushya Yoga (Auspicious Wealth Window - Weekend)")

    ss_combinations = [
        ("Sunday", "Hasta"), ("Sunday", "Pushya"), ("Sunday", "Uttara Phalguni"),
        ("Monday", "Rohini"), ("Monday", "Mrigashira"), ("Monday", "Pushya"), ("Monday", "Anuradha"),
        ("Tuesday", "Ashwini"), ("Tuesday", "Krittika"),
        ("Wednesday", "Rohini"), ("Wednesday", "Mrigashira"), ("Wednesday", "Hasta"),
        ("Thursday", "Pushya"), ("Thursday", "Punarvasu"), ("Thursday", "Anuradha"),
        ("Friday", "Revati"), ("Friday", "Ashwini"), ("Friday", "Anuradha"),
        ("Saturday", "Rohini"), ("Saturday", "Swati")
    ]
    if (weekday_name, nakshatra_name) in ss_combinations:
        special_yogas.append("Sarvartha Siddhi Yoga (All-Accomplishing Alignment)")

    as_combinations = [
        ("Sunday", "Hasta"), ("Monday", "Mrigashira"), ("Tuesday", "Ashwini"),
        ("Wednesday", "Anuradha"), ("Thursday", "Pushya"), ("Friday", "Revati"), ("Saturday", "Rohini")
    ]
    if (weekday_name, nakshatra_name) in as_combinations:
        special_yogas.append("Amrita Siddhi Yoga (Long-Term Compounding Alignment)")

    if tithi_name == "Shukla Tritiya" and dt.month in [4, 5]:
        special_yogas.append("Akshaya Tritiya (Eternal Prosperity Day)")
    if (tithi_name == "Krishna Trayodashi" or tithi_name == "Amavasya") and dt.month in [10, 11]:
        special_yogas.append("Dhanteras / Diwali Muhurat Trading Window")

    is_auspicious = len(special_yogas) > 0 or (nakshatra_name in ["Rohini", "Pushya", "Uttara Phalguni", "Hasta", "Anuradha", "Revati", "Shravana"] and paksha == "Shukla")

    # 7. Trading Day Status Check
    trading_status = check_trading_day_status(dt.date())

    return {
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M:%S"),
        "weekday": weekday_name,
        "nakshatra": {
            "name": nakshatra_name,
            "number": nakshatra_idx + 1,
            "progress_pct": round(nakshatra_progress * 100, 1)
        },
        "tithi": {
            "name": tithi_name,
            "number": tithi_idx + 1,
            "paksha": paksha
        },
        "yoga": {
            "name": yoga_name,
            "number": yoga_idx + 1
        },
        "timings": {
            "market_hours_muhurat": market_muhurat_str,
            "is_market_hours": is_in_market_hours,
            "rahu_kaalam": rahu_str,
            "yama_gandam": yama_str
        },
        "market_status": trading_status,
        "special_yogas": special_yogas,
        "is_auspicious": is_auspicious,
        "sun_longitude_deg": round(sun_sidereal, 2),
        "moon_longitude_deg": round(moon_sidereal, 2)
    }


def scan_auspicious_month_windows(
    year: int,
    month: int,
    market_days_only: bool = True,
    from_date: Optional[datetime.date] = None
) -> List[Dict[str, Any]]:
    """
    Scans a calendar month for auspicious investment windows with market hours & holiday checks.

    Args:
        year: Year (e.g. 2026)
        month: Month (1-12)
        market_days_only: If True, prioritizes active trading days (Mon-Fri, non-holidays) for instant live execution.
        from_date: Optional date threshold; ignores dates strictly before this date (e.g. to filter out past dates).
    """
    results = []
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days

    for day in range(1, num_days + 1):
        target_day_date = datetime.date(year, month, day)
        if from_date and target_day_date < from_date:
            continue

        dt = datetime.datetime(year, month, day, 12, 0, 0)
        panchang = calculate_panchang(dt)
        trading_status = panchang["market_status"]

        score = 0
        reasons = []
        score_breakdown = {}

        # Yogas scoring
        if any("Guru Pushya" in y for y in panchang["special_yogas"]):
            score += 100
            reasons.append("Guru Pushya Yoga (Supreme Wealth Window)")
            score_breakdown["Guru Pushya Yoga"] = 100
        elif any("Ravi Pushya" in y for y in panchang["special_yogas"]):
            score += 85
            reasons.append("Ravi Pushya Yoga (Wealth Window)")
            score_breakdown["Ravi Pushya Yoga"] = 85
        elif any("Amrita Siddhi" in y for y in panchang["special_yogas"]):
            score += 70
            reasons.append("Amrita Siddhi Yoga (Compounding Alignment)")
            score_breakdown["Amrita Siddhi Yoga"] = 70
        elif any("Sarvartha Siddhi" in y for y in panchang["special_yogas"]):
            score += 60
            reasons.append("Sarvartha Siddhi Yoga (Success Alignment)")
            score_breakdown["Sarvartha Siddhi Yoga"] = 60

        if panchang["nakshatra"]["name"] in ["Pushya", "Rohini", "Uttara Phalguni", "Hasta", "Anuradha", "Revati", "Shravana"]:
            score += 30
            reasons.append(f"Auspicious Nakshatra ({panchang['nakshatra']['name']})")
            score_breakdown[f"Nakshatra ({panchang['nakshatra']['name']})"] = 30

        if panchang["tithi"]["paksha"] == "Shukla":
            score += 15
            reasons.append("Shukla Paksha (Growth Phase)")
            score_breakdown["Shukla Paksha (Growth)"] = 15

        if panchang["tithi"]["name"] == "Amavasya" and month not in [10, 11]:
            score -= 40
            reasons.append("Amavasya (Avoided)")
            score_breakdown["Amavasya Penalty"] = -40

        # Market Hours & Trading Day Modifiers
        if trading_status["is_trading_day"]:
            score += 25 # Boost active trading days
            market_note = "🟢 Active Trading Day (09:15 - 15:30 IST)"
            score_breakdown["Active Market Hours (NSE/BSE)"] = 25
        else:
            score -= 30 # Penalize weekends/holidays for live SIP execution
            market_note = f"⚠️ {trading_status['status_label']} -> Shift execution to {trading_status['next_trading_day']} Market Open"
            reasons.append(market_note)
            score_breakdown["Non-Trading Day Penalty"] = -30

        # Filter if market_days_only is requested and score is good
        if score >= 35:
            if not market_days_only or trading_status["is_trading_day"]:
                results.append({
                    "date": panchang["date"],
                    "weekday": panchang["weekday"],
                    "score": score,
                    "score_breakdown": score_breakdown,
                    "is_trading_day": trading_status["is_trading_day"],
                    "market_note": market_note,
                    "next_trading_day": trading_status["next_trading_day"],
                    "nakshatra": panchang["nakshatra"]["name"],
                    "tithi": panchang["tithi"]["name"],
                    "special_yogas": panchang["special_yogas"],
                    "auspicious_window": panchang["timings"]["market_hours_muhurat"],
                    "rahu_kaalam": panchang["timings"]["rahu_kaalam"],
                    "reasons": reasons
                })

    # Sort descending by score, and secondarily by date
    results.sort(key=lambda x: (x["score"], -int(x["date"].replace("-", ""))), reverse=True)
    return results
