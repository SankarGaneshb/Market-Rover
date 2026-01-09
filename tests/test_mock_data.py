import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.mock_data import MockDataGenerator

class TestMockData:
    def setup_method(self):
        self.generator = MockDataGenerator()
        self.sample_stocks = [
            {'Symbol': 'RELIANCE', 'Company Name': 'Reliance Industries'},
            {'Symbol': 'TCS', 'Company Name': 'Tata Consultancy Services'},
            {'Symbol': 'INFY', 'Company Name': 'Infosys'}
        ]

    def test_mock_report_generation(self):
        """Test report generation structure"""
        report = self.generator.generate_mock_report(self.sample_stocks)
        assert isinstance(report, str)
        assert "EXECUTIVE SUMMARY" in report
        assert "Reliance Industries" in report
        assert "Tata Consultancy Services" in report
        assert "Risk Level:" in report

    def test_sentiment_data_generation(self):
        """Test sentiment distribution logic"""
        data = self.generator.generate_sentiment_data(num_articles=100)
        assert isinstance(data, dict)
        assert 'positive' in data
        assert 'negative' in data
        assert 'neutral' in data
        assert sum(data.values()) == 100

    def test_stock_risk_data(self):
        """Test risk score generation"""
        risk_data = self.generator.generate_stock_risk_data(self.sample_stocks)
        assert len(risk_data) == 3
        
        first_stock = risk_data[0]
        assert 'risk_score' in first_stock
        assert 'sentiment' in first_stock
        assert 15 <= first_stock['risk_score'] <= 85
        assert first_stock['sentiment'] in ['positive', 'negative', 'neutral']

    def test_news_timeline(self):
        """Test news generation"""
        news = self.generator.generate_news_timeline(self.sample_stocks, days=5)
        assert isinstance(news, list)
        assert len(news) > 0
        
        item = news[0]
        assert 'date' in item
        assert 'title' in item
        assert 'stock' in item
