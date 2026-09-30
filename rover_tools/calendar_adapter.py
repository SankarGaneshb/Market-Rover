"""
Calendar Sync Adapter for Market-Rover.
Generates RFC 5545 .ics files and instant Google Calendar links with:
- 15-minute advance reminder alarm
- Embedded 1-click broker execution links
- Auspicious Muhurat and Nakshatra summary
"""
import datetime
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple


class CalendarSyncAdapter:
    """Generates standard .ics payloads and Google Calendar instant-add URLs."""

    @staticmethod
    def _parse_event_datetimes(date_str: str, time_str: str) -> Tuple[datetime.datetime, datetime.datetime]:
        """Parses the date and time window string into start and end datetimes."""
        # Date format: YYYY-MM-DD
        year, month, day = map(int, date_str.split("-"))

        # Default start: 11:45 AM, end: 12:45 PM IST if parsing complex string
        start_hour, start_min = 11, 45
        end_hour, end_min = 12, 45

        try:
            if " - " in time_str:
                parts = time_str.split(" - ")
                s_part = parts[0].replace("IST", "").strip()
                e_part = parts[1].split()[0].strip()

                if ":" in s_part:
                    s_h, s_m = map(int, s_part.split(":"))
                    start_hour, start_min = s_h, s_m
                if ":" in e_part:
                    e_h, e_m = map(int, e_part.split(":"))
                    end_hour, end_min = e_h, e_m
        except Exception:
            pass

        start_dt = datetime.datetime(year, month, day, start_hour, start_min)
        end_dt = datetime.datetime(year, month, day, end_hour, end_min)
        return start_dt, end_dt

    @classmethod
    def generate_google_calendar_url(
        cls,
        plan: Dict[str, Any],
        broker_name: str = "Zerodha",
        broker_link: Optional[str] = None,
        execution_mode: str = "LIVE"
    ) -> str:
        """
        Generates an instant 1-click Google Calendar Event URL.
        """
        primary = plan["primary_window"]
        date_str = primary["date"]
        time_str = primary["auspicious_time"]
        is_amo = execution_mode.upper() == "AMO"

        if is_amo:
            # AMO event is scheduled for next trading day morning 09:00 AM - 09:30 AM IST
            target_date = primary.get("next_trading_day", date_str)
            y, m, d = map(int, target_date.split("-"))
            start_dt = datetime.datetime(y, m, d, 9, 0)
            end_dt = datetime.datetime(y, m, d, 9, 30)
            title = f"🌙 Muhurtha SIP (AMO Auto-Executes @ 09:15 AM Open - {broker_name})"
            mode_desc = "Execution Mode: 🌙 AMO (After Market Order) - Auto-executes at 09:15 AM Market Open"
        else:
            start_dt, end_dt = cls._parse_event_datetimes(date_str, time_str)
            title = f"🪔 Muhurtha SIP Execution ({primary.get('nakshatra', 'Auspicious')} - {broker_name})"
            mode_desc = f"Execution Mode: ⚡ Next Session Live ({time_str})"

        # Format for Google Calendar URL (YYYYMMDDTHHMMSS)
        fmt = "%Y%m%dT%H%M%S"
        dates_param = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"

        # Build description
        desc_lines = [
            mode_desc,
            f"Planetary Yoga: {', '.join(primary.get('special_yogas', ['Subha Muhurtham']))}",
            f"Market Safety: {plan.get('safety_status', {}).get('rating', 'STRONG')}",
            "",
            "📦 Allocated Order Basket:"
        ]
        for item in plan.get("order_basket", []):
            desc_lines.append(f"• {item['quantity']} qty {item['clean_symbol']} (LTP ~Rs. {item['ltp']})")

        desc_lines.append(f"\nTotal Budget: Rs. {plan.get('total_estimated_spend', 0):,.2f}")

        if broker_link:
            desc_lines.append(f"\n🚀 1-CLICK BROKER EXECUTION LINK:\n{broker_link}")

        desc_text = "\n".join(desc_lines)

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates_param,
            "details": desc_text,
            "location": "NSE / BSE India"
        }

        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    @classmethod
    def generate_ics_content(
        cls,
        plan: Dict[str, Any],
        broker_name: str = "Zerodha",
        broker_link: Optional[str] = None,
        execution_mode: str = "LIVE"
    ) -> str:
        """
        Generates RFC 5545 standard .ics file content with 15-min advance alarm.
        """
        primary = plan["primary_window"]
        date_str = primary["date"]
        time_str = primary["auspicious_time"]
        is_amo = execution_mode.upper() == "AMO"

        if is_amo:
            target_date = primary.get("next_trading_day", date_str)
            y, m, d = map(int, target_date.split("-"))
            start_dt = datetime.datetime(y, m, d, 9, 0)
            end_dt = datetime.datetime(y, m, d, 9, 30)
            summary = f"🌙 Muhurtha SIP AMO (Auto-Executes @ 09:15 AM Open - {broker_name})"
            mode_desc = "Mode: 🌙 AMO (After Market Order) - Auto-executes at 09:15 AM Market Open"
            alarm_desc = "Reminder: AMO Orders will execute in 15 minutes when NSE opens at 09:15 AM!"
        else:
            start_dt, end_dt = cls._parse_event_datetimes(date_str, time_str)
            summary = f"🪔 Muhurtha SIP ({primary.get('nakshatra', 'Auspicious')} Window - {broker_name})"
            mode_desc = f"Auspicious SIP Window: {time_str}"
            alarm_desc = "Reminder: Muhurtha SIP Auspicious Window opens in 15 minutes!"

        dt_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dt_start = start_dt.strftime("%Y%m%dT%H%M%S")
        dt_end = end_dt.strftime("%Y%m%dT%H%M%S")

        desc = f"{mode_desc}\\n"
        desc += f"Yoga: {', '.join(primary.get('special_yogas', ['Subha Muhurtham']))}\\n"
        desc += f"Safety: {plan.get('safety_status', {}).get('rating', 'STRONG')}\\n\\n"
        desc += "Basket:\\n"
        for item in plan.get("order_basket", []):
            desc += f"- {item['quantity']}x {item['clean_symbol']}\\n"
        if broker_link:
            desc += f"\\n1-Click Trade Link: {broker_link}"

        uid = f"muhurtha-sip-{date_str}-{execution_mode.lower()}-{int(datetime.datetime.now().timestamp())}@marketrover.ai"

        ics_text = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Market-Rover//Muhurtha SIP Engine//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dt_stamp}
DTSTART:{dt_start}
DTEND:{dt_end}
SUMMARY:{summary}
DESCRIPTION:{desc}
LOCATION:NSE / BSE India
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:{alarm_desc}
END:VALARM
END:VEVENT
END:VCALENDAR"""
        return ics_text.strip()
