# 🔍 Market Rover - Stock Intelligence System

A multi-agent AI system powered by CrewAI that monitors your stock portfolio, scrapes financial news, performs sentiment analysis, and generates weekly intelligence reports.

## ✨ Features

- **📊 Portfolio Monitoring**: Tracks your NSE stocks from a simple CSV file
- **📰 News Scraping**: Uses Newspaper3k to scrape recent news from Moneycontrol
- **🧠 Sentiment Analysis**: AI-powered classification of news as Positive/Negative/Neutral
- **📈 Market Context**: Analyzes Nifty 50 and sector trends for broader market understanding
- **📝 Weekly Reports**: Generates comprehensive intelligence briefings with risk highlights
- **💰 Cost-Effective**: Affordable for small portfolios using OpenAI's free tier ($5 credit)

## 🏗️ Architecture

Market Rover uses **5 specialized AI agents** orchestrated by CrewAI:

1. **Portfolio Manager Agent**: Reads and validates your stock portfolio
2. **News Scraper Agent**: Scrapes Moneycontrol using News Paper3k
3. **Sentiment Analyzer Agent**: Classifies news sentiment
4. **Market Context Agent**: Analyzes Nifty 50 and sector trends
5. **Report Generator Agent**: Creates final intelligence report

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (get $5 free credit from [OpenAI Platform](https://platform.openai.com/api-keys))

### Installation

1. **Clone or navigate to the project directory**:
```bash
cd Market-Rover
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
```

4. **Prepare your portfolio**:
   - Edit `Portfolio.csv` (or use `portfolio_example.csv` as a template)
   - Format: Symbol, Company Name, Quantity, Average Price
   - Symbols will automatically get .NS suffix for NSE

### Usage

Run the weekly analysis:
```bash
python main.py
```

The system will:
1. Read your portfolio
2. Scrape news from Moneycontrol for each stock
3. Analyze sentiment and market context
4. Generate a comprehensive report in the `reports/` directory

## 📋 Portfolio File Format

Create a `Portfolio.csv` file with this structure:

```csv
Symbol,Company Name,Quantity,Average Price
RELIANCE,Reliance Industries Ltd,10,2450.50
TCS,Tata Consultancy Services,5,3550.00
INFY,Infosys Ltd,15,1450.75
```

- **Symbol**: Stock symbol (without .NS suffix - it will be added automatically)
- **Company Name**: Full company name
- **Quantity**: Number of shares you own (optional)
- **Average Price**: Your average purchase price (optional)

## ⚙️ Configuration

Edit `config.py` or set environment variables in `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ITERATIONS` | 15 | Maximum iterations for each agent |
| `LOOKBACK_DAYS` | 7 | How many days back to search for news |
| `PORTFOLIO_FILE` | Portfolio.csv | Path to your portfolio file |
| `CONVERT_TO_CRORES` | true | Convert amounts to Crores |

## 📊 Sample Report Structure

```
═══════════════════════════════════════════
    MARKET ROVER INTELLIGENCE REPORT
═══════════════════════════════════════════

EXECUTIVE SUMMARY
- Overall portfolio health
- Market sentiment this week
- Top 3 most important news stories

STOCK-BY-STOCK ANALYSIS
For each stock:
- Current price and change
- Key news with sentiment
- Risks/opportunities
- Recommendation: WATCH/HOLD/CONCERN

RISK HIGHLIGHTS
- Stocks needing attention
- Market-wide risks
- Flagged items for human review
```

## 💰 Cost Breakdown

### Current Setup (OpenAI with Free Tier)
- **LLM**: OpenAI GPT-3.5-turbo
- **Free credit**: $5 (25-50 runs)
- **Data**: yfinance + Newspaper3k (both free)
- **Infrastructure**: Run locally
- **Cost per run**: ~$0.10-0.20

### Monthly Estimates
- **3 stocks, weekly**: ~$0.60/month (after free credit)
- **10 stocks, weekly**: ~$1.50/month
- **20 stocks, daily**: ~$12/month

See OpenAI pricing: https://openai.com/api/pricing/

## 🛠️ Technology Stack

- **CrewAI**: Multi-agent orchestration framework
- **OpenAI GPT-3.5-turbo**: Large Language Model for reasoning
- **yfinance**: Free NSE/BSE stock data
- **Newspaper3k**: Web scraping for news articles
- **NSEPython**: Data verification (optional)
- **Pandas**: Data manipulation

## 📁 Project Structure

```
Market-Rover/
├── main.py                 # Application entry point
├── agents.py               # Agent definitions
├── tasks.py                # Task definitions
├── crew.py                 # Crew orchestration
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── Portfolio.csv           # Your stock portfolio
├── portfolio_example.csv   # Example portfolio
├── tools/
│   ├── portfolio_tool.py      # Portfolio reader
│   ├── news_scraper_tool.py   # Moneycontrol scraper
│   ├── stock_data_tool.py     # Stock data fetcher
│   └── market_context_tool.py # Market analyzer
└── reports/                # Generated reports
```

## 🔧 Troubleshooting

### "No module named 'crewai'"
```bash
pip install -r requirements.txt
```

### "GOOGLE_API_KEY not found"
1. Create a `.env` file in the project root
2. Add: `GOOGLE_API_KEY=your_key_here`
3. Get a free key from: https://makersuite.google.com/app/apikey

### "No news found for stock"
- Check if the stock symbol is correct
- Try running again (Moneycontrol may have rate limits)
- Some stocks may have less news coverage

### News scraping fails
- Newspaper3k may need additional dependencies on Windows:
```bash
pip install lxml lxml_html_clean
```

## 🎯 User Rules Compliance

- ✅ All NSE stocks automatically get `.NS` suffix
- ✅ All financial figures converted to Crores
- ✅ Uses Newspaper3k for Moneycontrol scraping (Agent B)
- ✅ Implements ReAct (Reasoning + Acting) strategy
- ✅ Max 15 iterations with safeguards
- ✅ "Flag for Review" feature for uncertain sentiments

## 📝 License

This project is for personal use. Ensure compliance with data source terms of service.

## 🤝 Contributing

This is a personal portfolio intelligence tool. Feel free to modify for your own needs.

## ⚠️ Disclaimer

This tool provides information only and is not financial advice. Always do your own research before making investment decisions.

---

**Market Rover** - Your intelligent stock portfolio companion 🚀
