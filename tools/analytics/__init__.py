from tools.analytics.core import AnalyticsCore
from tools.analytics.forecast import AnalyticsForecast
from tools.analytics.portfolio_engine import AnalyticsPortfolio

class AnalyzersUnified(AnalyticsCore, AnalyticsForecast, AnalyticsPortfolio):
    """
    Unified Market Analyzer inheriting capabilities from:
    - Core: Basic stats, volatility, outliers
    - Forecast: Scenarios, Monthly strategy, Monte Carlo
    - Portfolio: Correlation, Rebalancing, Risk Scores
    """
    def __init__(self):
        pass
