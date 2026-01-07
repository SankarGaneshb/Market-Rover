"""
Portfolio Tool - Reads and validates stock portfolio from CSV.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict
from crewai.tools import tool
from config import ensure_nse_suffix, PORTFOLIO_FILE, PROJECT_ROOT


@tool("Portfolio Reader")
def read_portfolio(portfolio_file: str = None) -> str:
    """
    Reads the user's stock portfolio from a CSV file.
    Returns a list of stocks with their symbols (with .NS suffix for NSE),
    company names, quantities, and average prices.
    
    Args:
        portfolio_file: Path to portfolio CSV file (optional)
        
    Returns:
        String representation of portfolio stocks
    """
    try:
        # Use provided file or default from config
        file_path = portfolio_file or PORTFOLIO_FILE
        
        # Handle relative paths
        if not Path(file_path).is_absolute():
            file_path = PROJECT_ROOT / file_path
        
        # Check if file exists
        if not Path(file_path).exists():
            return f"Error: Portfolio file not found at {file_path}"
        
        # Read CSV
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip() # Remove whitespace from headers
        
        # Validate required columns
        required_cols = ['Symbol', 'Company Name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return f"Error: Missing required columns: {missing_cols}"
        
        # Ensure NSE suffix on all symbols
        df['Symbol'] = df['Symbol'].apply(ensure_nse_suffix)
        
        # Format output
        portfolio_list = []
        for _, row in df.iterrows():
            stock_info = {
                'symbol': row['Symbol'],
                'company': row['Company Name'],
                'quantity': row.get('Quantity', 'N/A'),
                'avg_price': row.get('Average Price', 'N/A')
            }
            portfolio_list.append(stock_info)
        
        # Create readable output
        output = f"Portfolio contains {len(portfolio_list)} stocks:\n\n"
        for stock in portfolio_list:
            output += f"- {stock['symbol']} ({stock['company']})"
            if stock['quantity'] != 'N/A':
                output += f" - Qty: {stock['quantity']}, Avg Price: ₹{stock['avg_price']}"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"Error reading portfolio: {str(e)}"
