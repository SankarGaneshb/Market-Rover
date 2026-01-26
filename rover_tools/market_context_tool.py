"""
Market Context Tool - Analyzes Nifty 50 and sector indices.
"""
import yfinance as yf
from typing import Dict
from crewai.tools import tool
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


@tool("Market Context Analyzer")
def analyze_market_context(portfolio_stocks: str = None) -> str:
    """
    Analyzes broader market context including Nifty 50, Bank Nifty,
    and relevant sectoral indices based on portfolio composition.
    Automatically detects sectors from portfolio stocks and analyzes
    the corresponding sector indices (IT, Banking, Auto, Pharma, FMCG, Metal, Energy).
    Helps determine if overall market sentiment is positive or negative.
    
    Args:
        portfolio_stocks: Comma-separated list of stock symbols (e.g., "TCS.NS,INFY.NS,HDFCBANK.NS")
        
    Returns:
        Market context analysis
    """
    def _get_index_performance(symbol: str, name: str) -> Dict:
        """Get performance data for an index."""
        try:
            index = yf.Ticker(symbol)
            hist = index.history(period="1mo")
            
            if hist.empty:
                return None
            
            current = hist['Close'].iloc[-1]
            week_ago = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
            month_ago = hist['Close'].iloc[0]
            
            week_change = ((current - week_ago) / week_ago) * 100
            month_change = ((current - month_ago) / month_ago) * 100
            
            return {
                'name': name,
                'current': current,
                'week_change': week_change,
                'month_change': month_change,
                'sentiment': 'Positive' if week_change > 0 else 'Negative'
            }
        except Exception as e:
            logger.debug(f"Index fetch failed for {symbol}: {e}")
            return None
    
    try:
        output = "Market Context Analysis:\n"
        output += "═" * 50 + "\n\n"
        
        # Nifty 50 (always included)
        nifty_data = _get_index_performance("^NSEI", "Nifty 50")
        if nifty_data:
            output += f"📊 {nifty_data['name']}\n"
            output += f"   Current: {nifty_data['current']:.2f}\n"
            output += f"   Week Change: {nifty_data['week_change']:+.2f}%\n"
            output += f"   Month Change: {nifty_data['month_change']:+.2f}%\n"
            output += f"   Sentiment: {nifty_data['sentiment']}\n\n"
        else:
            raise Exception("Critical Market Data (Nifty 50) is unavailable.")
        
        # Detect sectors from portfolio
        sectors_to_analyze = set()
        if portfolio_stocks:
            stocks = [s.strip() for s in portfolio_stocks.split(',')]
            
            for stock in stocks:
                try:
                    # Sanitize
                    stock = stock.replace("$", "").strip().upper()
                    if not stock.endswith(('.NS', '.BO')) and '^' not in stock:
                        stock += ".NS"
                    
                    ticker = yf.Ticker(stock)
                    info = ticker.info
                    sector = info.get('sector', '')
                    
                    # Map yfinance sectors to Nifty indices
                    sector_mapping = {
                        'Technology': 'IT',
                        'Financial Services': 'BANK',
                        'Financial': 'BANK',
                        'Consumer Cyclical': 'Auto',
                        'Automotive': 'Auto',
                        'Healthcare': 'Pharma',
                        'Consumer Defensive': 'FMCG',
                        'Basic Materials': 'Metal',
                        'Energy': 'Energy',
                    }
                    
                    if sector in sector_mapping:
                        sectors_to_analyze.add(sector_mapping[sector])
                except Exception as e:
                    logger.debug(f"Failed to detect sector for {stock}: {e}")
                    continue
        
        # Always include Bank Nifty (important index)
        bank_nifty = _get_index_performance("^NSEBANK", "Bank Nifty")
        if bank_nifty:
            # Highlight if banking stocks are in portfolio
            is_relevant = 'BANK' in sectors_to_analyze
            emoji = "🏦⭐" if is_relevant else "🏦"
            label = f"{bank_nifty['name']} (Portfolio Sector)" if is_relevant else bank_nifty['name']
            
            output += f"{emoji} {label}\n"
            output += f"   Current: {bank_nifty['current']:.2f}\n"
            output += f"   Week Change: {bank_nifty['week_change']:+.2f}%\n"
            output += f"   Month Change: {bank_nifty['month_change']:+.2f}%\n"
            output += f"   Sentiment: {bank_nifty['sentiment']}\n\n"
        
        # Sector-specific indices
        sector_indices = {
            'IT': ('^CNXIT', 'Nifty IT'),
            'Auto': ('^CNXAUTO', 'Nifty Auto'),
            'Pharma': ('^CNXPHARMA', 'Nifty Pharma'),
            'FMCG': ('^CNXFMCG', 'Nifty FMCG'),
            'Metal': ('^CNXMETAL', 'Nifty Metal'),
            'Energy': ('^CNXENERGY', 'Nifty Energy'),
        }
        
        # Analyze detected sectors
        for sector in sectors_to_analyze:
            if sector in sector_indices and sector != 'BANK':  # Bank already handled
                sector_symbol, sector_name = sector_indices[sector]
                sector_data = _get_index_performance(sector_symbol, sector_name)
                if sector_data:
                    output += f"📈 {sector_data['name']} (Portfolio Sector)\n"
                    output += f"   Current: {sector_data['current']:.2f}\n"
                    output += f"   Week Change: {sector_data['week_change']:+.2f}%\n"
                    output += f"   Month Change: {sector_data['month_change']:+.2f}%\n"
                    output += f"   Sentiment: {sector_data['sentiment']}\n\n"
        
        # Overall market sentiment
        if nifty_data:
            overall_sentiment = "POSITIVE 📈" if nifty_data['week_change'] > 0 else "NEGATIVE 📉"
            output += f"Overall Market Sentiment: {overall_sentiment}\n"
            
            if nifty_data['week_change'] > 2:
                output += "Market is showing strong positive momentum.\n"
            elif nifty_data['week_change'] > 0:
                output += "Market is showing cautious optimism.\n"
            elif nifty_data['week_change'] > -2:
                output += "Market is showing mild weakness.\n"
            else:
                output += "Market is under significant pressure.\n"
        
        # Summary of analyzed sectors
        if sectors_to_analyze:
            output += f"\n💡 Analyzed sectors based on portfolio: {', '.join(sorted(sectors_to_analyze))}\n"
        
        return output
        
    except Exception as e:
        return f"Error analyzing market context: {str(e)}"
