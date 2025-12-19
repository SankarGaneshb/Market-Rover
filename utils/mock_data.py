"""
Mock data generator for testing Market-Rover 2.0 without API calls
Simulates realistic analysis results for testing UI and workflows
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List


class MockDataGenerator:
    """Generate realistic mock data for testing"""
    
    def __init__(self):
        """Initialize with sample data"""
        self.sample_news_titles = [
            "{company} reports strong quarterly earnings, beats estimates",
            "{company} announces new product launch in key market",
            "Analysts upgrade {company} stock to 'buy' rating",
            "{company} faces regulatory scrutiny over recent practices",
            "Market volatility impacts {company} stock performance",
            "{company} CEO announces strategic restructuring plan",
            "Competition heats up for {company} in key segments",
            "{company} expands operations to new geographic regions",
            "Insider trading allegations surface at {company}",
            "{company} stock reaches 52-week high on strong demand"
        ]
        
        self.sentiments = ['positive', 'negative', 'neutral']
        self.sentiment_weights = [0.4, 0.3, 0.3]  # 40% positive, 30% negative, 30% neutral
    
    def generate_mock_report(self, stocks: List[Dict]) -> str:
        """
        Generate a complete mock analysis report.
        
        Args:
            stocks: List of stock dictionaries with 'Symbol' and 'Company Name'
            
        Returns:
            Mock report text
        """
        report_lines = []
        
        # Executive Summary
        report_lines.append("=" * 80)
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("Overall Portfolio Health: MODERATE")
        report_lines.append("Market Sentiment This Week: NEUTRAL TO POSITIVE")
        report_lines.append("")
        report_lines.append("Top 3 Most Important News Stories:")
        for i, stock in enumerate(stocks[:3], 1):
            news_title = random.choice(self.sample_news_titles).format(company=stock['Company Name'])
            report_lines.append(f"{i}. {news_title}")
        report_lines.append("")
        
        # Stock-by-Stock Analysis
        report_lines.append("=" * 80)
        report_lines.append("STOCK-BY-STOCK ANALYSIS")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for stock in stocks:
            symbol = stock['Symbol']
            company = stock['Company Name']
            
            # Generate mock price
            mock_price = random.uniform(500, 3500)
            
            report_lines.append(f"### {symbol} - {company}")
            report_lines.append(f"Current Price: ₹{mock_price:.2f}")
            report_lines.append("")
            
            # Generate 2-3 news items
            num_news = random.randint(2, 3)
            report_lines.append("Key News Stories:")
            for i in range(num_news):
                sentiment = random.choices(self.sentiments, self.sentiment_weights)[0]
                news_title = random.choice(self.sample_news_titles).format(company=company)
                emoji = "📈" if sentiment == "positive" else "📉" if sentiment == "negative" else "➡️"
                report_lines.append(f"  {emoji} {news_title} (Sentiment: {sentiment.upper()})")
            
            report_lines.append("")
            
            # Risk assessment
            risk_level = random.choice(['LOW', 'MEDIUM', 'HIGH'])
            risk_emoji = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
            report_lines.append(f"Risk Level: {risk_emoji} {risk_level}")
            
            # Recommendation
            recommendation = random.choice(['WATCH', 'HOLD', 'CONCERN'])
            report_lines.append(f"Recommendation: **{recommendation}**")
            report_lines.append("")
            report_lines.append("-" * 80)
            report_lines.append("")
        
        # Risk Highlights
        report_lines.append("=" * 80)
        report_lines.append("RISK HIGHLIGHTS")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Pick 1-2 stocks with negative sentiment
        risky_stocks = random.sample(stocks, min(2, len(stocks)))
        report_lines.append("Stocks Requiring Attention:")
        for stock in risky_stocks:
            report_lines.append(f"  • {stock['Symbol']} - {stock['Company Name']}: Market volatility concerns")
        report_lines.append("")
        
        # Market Context
        report_lines.append("Market-Wide Risks:")
        report_lines.append("  • Global economic uncertainty affecting IT sector")
        report_lines.append("  • Banking sector facing regulatory headwinds")
        report_lines.append("")
        
        # Flag for Review
        report_lines.append("=" * 80)
        report_lines.append("FLAG FOR REVIEW")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("No items flagged for manual review in this analysis.")
        report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_sentiment_data(self, num_articles: int = 15) -> Dict[str, int]:
        """
        Generate mock sentiment distribution.
        
        Args:
            num_articles: Total number of articles
            
        Returns:
            Dictionary with sentiment counts
        """
        sentiments = random.choices(
            ['positive', 'negative', 'neutral'],
            weights=[0.4, 0.3, 0.3],
            k=num_articles
        )
        
        return {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': sentiments.count('neutral')
        }
    
    def generate_stock_risk_data(self, stocks: List[Dict]) -> List[Dict]:
        """
        Generate mock risk scores for stocks.
        
        Args:
            stocks: List of stock dictionaries
            
        Returns:
            List of stock data with risk scores
        """
        stock_data = []
        
        for stock in stocks:
            sentiment = random.choices(self.sentiments, self.sentiment_weights)[0]
            risk_score = random.randint(15, 85)
            
            stock_data.append({
                'symbol': stock['Symbol'],
                'company': stock['Company Name'],
                'risk_score': risk_score,
                'sentiment': sentiment
            })
        
        return stock_data
    
    def generate_news_timeline(self, stocks: List[Dict], days: int = 7) -> List[Dict]:
        """
        Generate mock news timeline data.
        
        Args:
            stocks: List of stock dictionaries
            days: Number of days to generate news for
            
        Returns:
            List of news articles with dates
        """
        news_data = []
        
        for stock in stocks:
            # Generate 2-4 news items per stock
            num_news = random.randint(2, 4)
            
            for i in range(num_news):
                date = datetime.now() - timedelta(days=random.randint(0, days))
                sentiment = random.choices(self.sentiments, self.sentiment_weights)[0]
                title = random.choice(self.sample_news_titles).format(company=stock['Company Name'])
                
                news_data.append({
                    'date': date,
                    'title': title,
                    'sentiment': sentiment,
                    'stock': stock['Symbol']
                })
        
        return sorted(news_data, key=lambda x: x['date'])


def simulate_analysis_delay(progress_callback=None):
    """
    Simulate the time taken for analysis with progress updates.
    
    Args:
        progress_callback: Optional callback function(percentage, stock_name, status)
    """
    import time
    
    stages = [
        (10, "Loading portfolio data", None),
        (20, "Scraping news articles", "INFY"),
        (40, "Analyzing sentiment", "HDFCBANK"),
        (60, "Evaluating market context", "SBIN"),
        (80, "Generating intelligence report", None),
        (100, "Complete", None)
    ]
    
    for percentage, message, stock in stages:
        if progress_callback:
            progress_callback(percentage, stock or "All Stocks", "processing")
        time.sleep(2)  # Simulate work


# Singleton instance
mock_generator = MockDataGenerator()
