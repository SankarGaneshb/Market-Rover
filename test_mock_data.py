"""
Test Script for Market-Rover 2.0
Run this to validate functionality without hitting API rate limits
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from utils.mock_data import mock_generator
import pandas as pd


def test_mock_report_generation():
    """Test mock report generation"""
    print("=" * 80)
    print("TEST 1: Mock Report Generation")
    print("=" * 80)
    
    # Sample portfolio
    stocks = [
        {'Symbol': 'INFY', 'Company Name': 'Infosys Ltd'},
        {'Symbol': 'TCS', 'Company Name': 'Tata Consultancy Services'},
        {'Symbol': 'WIPRO', 'Company Name': 'Wipro Ltd'}
    ]
    
    # Generate report
    report = mock_generator.generate_mock_report(stocks)
    
    print(report)
    print("\n✅ Mock report generated successfully!")
    return True


def test_sentiment_data():
    """Test sentiment data generation"""
    print("\n" + "=" * 80)
    print("TEST 2: Sentiment Data Generation")
    print("=" * 80)
    
    sentiment_data = mock_generator.generate_sentiment_data(15)
    
    print(f"Positive: {sentiment_data['positive']}")
    print(f"Negative: {sentiment_data['negative']}")
    print(f"Neutral: {sentiment_data['neutral']}")
    print(f"Total: {sum(sentiment_data.values())}")
    
    assert sum(sentiment_data.values()) == 15, "Total should be 15"
    print("\n✅ Sentiment data generated successfully!")
    return True


def test_risk_data():
    """Test risk score generation"""
    print("\n" + "=" * 80)
    print("TEST 3: Risk Score Generation")
    print("=" * 80)
    
    stocks = [
        {'Symbol': 'INFY', 'Company Name': 'Infosys Ltd'},
        {'Symbol': 'TCS', 'Company Name': 'Tata Consultancy Services'}
    ]
    
    risk_data = mock_generator.generate_stock_risk_data(stocks)
    
    for stock in risk_data:
        print(f"{stock['symbol']}: Risk={stock['risk_score']}, Sentiment={stock['sentiment']}")
    
    print("\n✅ Risk data generated successfully!")
    return True


def test_news_timeline():
    """Test news timeline generation"""
    print("\n" + "=" * 80)
    print("TEST 4: News Timeline Generation")
    print("=" * 80)
    
    stocks = [
        {'Symbol': 'INFY', 'Company Name': 'Infosys Ltd'},
        {'Symbol': 'TCS', 'Company Name': 'Tata Consultancy Services'}
    ]
    
    news_data = mock_generator.generate_news_timeline(stocks, days=7)
    
    print(f"Generated {len(news_data)} news items:")
    for item in news_data[:5]:  # Show first 5
        print(f"  - {item['date'].strftime('%Y-%m-%d')}: {item['stock']} - {item['title'][:50]}...")
    
    print("\n✅ News timeline generated successfully!")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 MARKET-ROVER 2.0 MOCK DATA TESTS")
    print("=" * 80 + "\n")
    
    tests = [
        test_mock_report_generation,
        test_sentiment_data,
        test_risk_data,
        test_news_timeline
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
