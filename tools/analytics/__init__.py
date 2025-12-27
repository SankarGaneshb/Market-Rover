from .core import AnalyticsCore
from .forecast import AnalyticsForecast
from .portfolio_engine import AnalyticsPortfolio

class MarketAnalyzer(AnalyticsCore, AnalyticsForecast, AnalyticsPortfolio):
    """
    Unified Market Analyzer inheriting capabilities from:
    - Core: Basic stats, volatility, outliers
    - Forecast: Scenarios, Monthly strategy, Monte Carlo
    - Portfolio: Correlation, Rebalancing, Risk Scores
    """
    def __init__(self):
        pass
