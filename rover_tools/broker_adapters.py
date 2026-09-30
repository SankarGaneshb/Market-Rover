"""
Zero-OAuth Broker Adapters for Market-Rover.
Generates 1-click execution URLs, deep links, and copyable payloads for:
- Zerodha Kite (Kite Publisher Basket Deep Links)
- Groww (Asset Deep Links & Quick Copy Cart)
- ICICI Direct (Breeze Order Parameters & Web Trade Tickets)

100% Zero-OAuth, stateless, and privacy-first (no credentials or tokens stored).
"""
import json
import urllib.parse
from typing import Dict, List, Any


class ZerodhaKiteAdapter:
    """Generates Zerodha Kite Publisher Basket deep links and JSON payloads with Regular or AMO variety."""

    @staticmethod
    def generate_basket_payload(order_basket: List[Dict[str, Any]], variety: str = "regular") -> List[Dict[str, Any]]:
        """
        Formats the internal order basket into the official Zerodha Kite basket schema.
        variety can be 'regular' (for live market hours) or 'amo' (for after-market / weekend orders).
        """
        kite_items = []
        for item in order_basket:
            kite_items.append({
                "variety": variety.lower(),
                "tradingsymbol": item.get("clean_symbol", item["ticker"].replace(".NS", "")),
                "exchange": "NSE",
                "transaction_type": "BUY",
                "order_type": "MARKET",
                "quantity": int(item["quantity"]),
                "readonly": False
            })
        return kite_items

    @classmethod
    def generate_deep_link(cls, order_basket: List[Dict[str, Any]], variety: str = "regular") -> str:
        """
        Generates the 1-click Zerodha Kite Publisher Basket URL.
        Clicking this opens Zerodha Kite directly with the basket pre-populated.
        """
        payload = cls.generate_basket_payload(order_basket, variety=variety)
        payload_json = json.dumps(payload)
        encoded_data = urllib.parse.quote(payload_json)
        return f"https://kite.zerodha.com/connect/basket?data={encoded_data}"


class GrowwAdapter:
    """Generates Groww asset deep links and quick-order payload structures."""

    GROWW_SLUG_MAP = {
        "NIFTYBEES": "nippon-india-nifty-50-bees-etf",
        "GOLDBEES": "nippon-india-etf-gold-bees",
        "SILVERBEES": "nippon-india-silver-bees-etf",
        "JUNIORBEES": "nippon-india-nifty-next-50-junior-bees-etf",
        "RELIANCE": "reliance-industries-ltd",
        "TCS": "tata-consultancy-services-ltd",
        "INFY": "infosys-ltd",
        "HDFCBANK": "hdfc-bank-ltd",
        "ICICIBANK": "icici-bank-ltd"
    }

    @classmethod
    def generate_asset_links(cls, order_basket: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generates direct Groww web/app links for each asset in the basket."""
        links = []
        for item in order_basket:
            symbol = item.get("clean_symbol", item["ticker"].replace(".NS", ""))
            slug = cls.GROWW_SLUG_MAP.get(symbol, symbol.lower())
            links.append({
                "symbol": symbol,
                "name": item.get("name", symbol),
                "quantity": item["quantity"],
                "groww_url": f"https://groww.in/stocks/{slug}"
            })
        return links

    @staticmethod
    def generate_copyable_summary(order_basket: List[Dict[str, Any]], execution_mode: str = "LIVE") -> str:
        """Generates a clean text format for quick Groww search & entry."""
        header = "--- GROWW 1-CLICK ORDER LIST (AMO / OFF-MARKET) ---" if execution_mode.upper() == "AMO" else "--- GROWW 1-CLICK ORDER LIST (LIVE SESSION) ---"
        lines = [header]
        if execution_mode.upper() == "AMO":
            lines.append("Note: Add to cart and submit order. Executes at 09:15 AM Market Open on Next Trading Session.")
        for item in order_basket:
            symbol = item.get("clean_symbol", item["ticker"].replace(".NS", ""))
            lines.append(f"• Buy {item['quantity']} qty of {symbol} ({item.get('name', symbol)})")
        return "\n".join(lines)


class ICICIDirectAdapter:
    """Generates ICICI Direct Breeze API parameters and Web Trade payloads."""

    @staticmethod
    def generate_breeze_payload(order_basket: List[Dict[str, Any]], execution_mode: str = "LIVE") -> List[Dict[str, Any]]:
        """Formats order items for ICICI Direct Breeze API."""
        is_amo = execution_mode.upper() == "AMO"
        breeze_items = []
        for item in order_basket:
            symbol = item.get("clean_symbol", item["ticker"].replace(".NS", ""))
            entry = {
                "stock_code": symbol,
                "exchange_code": "NSE",
                "action": "buy",
                "order_type": "market",
                "quantity": str(int(item["quantity"])),
                "product": "cash",
                "validity": "amo" if is_amo else "day"
            }
            breeze_items.append(entry)
        return breeze_items

    @classmethod
    def generate_web_trade_url(cls, primary_ticker: str) -> str:
        """Generates ICICI Direct quick order entry URL."""
        clean = primary_ticker.replace(".NS", "").replace(".BO", "")
        return f"https://secure.icicidirect.com/trade/equity?symbol={clean}"
