import pandas as pd
from enum import Enum
from rover_tools.analytics.forensic_engine import ForensicAnalyzer

class InvestorPersona(Enum):
    PRESERVER = "The Preserver"     # Minimal Risk, FD Beating
    DEFENDER = "The Defender"       # Conservative, Inflation Protection
    COMPOUNDER = "The Compounder"   # Moderate, Wealth Creation
    HUNTER = "The Hunter"           # Aggressive, Alpha Seeker

class InvestorProfiler:
    """
    Behavioral Finance Engine to map users to profiles and generate
    Asset Allocation Strategies with strict ticker limits.
    """
    
    def __init__(self):
        self.personas = InvestorPersona

    def get_profile(self, q1_score, q2_score, q3_score):
        """
        Calculates profile based on 3-Question 'Sleep Test'.
        Q1 (Panic): A=1, B=2, C=3
        Q2 (Time): A=1, B=2, C=3
        Q3 (Capacity): A=1, B=2, C=3
        Total Score -> Profile
        """
        total_score = q1_score + q2_score + q3_score
        
        # Mapping Logic
        if total_score <= 4:
            return self.personas.PRESERVER
        elif total_score <= 6:
            return self.personas.DEFENDER
        elif total_score <= 7:
            return self.personas.COMPOUNDER
        else:
            return self.personas.HUNTER

    def get_allocation_strategy(self, persona):
        """Returns the specific Asset Allocation & Ticker Constraints."""
        
        if persona == self.personas.PRESERVER:
            # 75% Safety, 25% Equity
            return {
                "description": "Capital Protection + FD Beating Returns",
                "risk_level": "Low",
                "max_tickers": 4,
                "allocation": {
                    "Equity_LargeCap": 25,
                    "Safety_Liquid": 50,
                    "Safety_Gold": 25
                },
                "structure": {
                    "Large Cap": 2, # Tickers
                    "Liquid ETF": 1,
                    "Gold ETF": 1
                }
            }
            
        elif persona == self.personas.DEFENDER:
            # 50% Large, 20% Div, 10% Gold, 10% REIT, 10% Bond
            return {
                "description": "Inflation Protection + Regular Income",
                "risk_level": "Conservative",
                "max_tickers": 6,
                "allocation": {
                    "Equity_LargeCap": 50,
                    "Equity_Dividend": 20,
                    "Asset_Gold": 10,
                    "Asset_REIT": 10,
                    "Asset_Bond": 10
                },
                "structure": {
                    "Large/Div Stocks": 3,
                    "Gold ETF": 1,
                    "REIT": 1,
                    "Bond ETF": 1
                }
            }
            
        elif persona == self.personas.COMPOUNDER:
             # 40% Large, 30% Mid, 10% Gold, 10% REIT, 10% Bond
            return {
                "description": "Wealth Creation (Growth at Reasonable Price)",
                "risk_level": "Moderate",
                "max_tickers": 8,
                "allocation": {
                    "Equity_LargeCap": 40,
                    "Equity_MidCap": 30,
                    "Asset_Gold": 10,    # Satellite
                    "Asset_REIT": 10,
                    "Asset_Bond": 10
                },
                "structure": {
                    "Large Cap Stock": 3,
                    "Mid Cap Stock": 2,
                    "Gold ETF": 1,
                    "REIT": 1,
                    "Bond ETF": 1
                }
            }
            
        elif persona == self.personas.HUNTER:
             # 40% Large, 30% Mid, 10% Small, 10% REIT, 10% Asset (Gold/Bond)
            return {
                "description": "Alpha Generation (Aggressive High Conviction)",
                "risk_level": "High (Aggressive)",
                "max_tickers": 10,
                "allocation": {
                    "Equity_LargeCap": 40,
                    "Equity_MidCap": 30,
                    "Equity_SmallCap": 10,
                    "Asset_REIT": 10,
                    "Asset_Hedge": 10
                },
                "structure": {
                    "Large Cap Stock": 3,
                    "Mid Cap Stock": 3,
                    "Small Cap Stock": 2,
                    "REIT": 1,
                    "Gold/Bond ETF": 1
                }
            }
        return {}

    def run_forensic_audit_on_portfolio(self, ticker_list):
        """
        Runs the Forensic Integrity Shield on a list of proposed stocks.
        Returns a 'Risk Report'.
        """
        report = {}
        for ticker in ticker_list:
            # Skip ETFs for forensic (basic logic)
            if "BEES" in ticker or "NIFTY" in ticker:
                continue
                
            analyzer = ForensicAnalyzer(ticker)
            audit_result = analyzer.generate_forensic_report()
            report[ticker] = audit_result
            
        return report

    def get_benchmark_proxies(self):
        """
        Returns the benchmark ticker for each asset bucket.
        Used for Composite Benchmark calculation.
        """
        return {
            "Equity_LargeCap": "^NSEI",         # Nifty 50
            "Equity_MidCap": "MID150BEES.NS",   # Nifty Midcap 150 ETF
            "Equity_SmallCap": "BSE-SML",       # BSE Smallcap (using proxy if needed, or ^CNXSC)
            "Equity_Dividend": "DIVOPPBEES.NS", # Dividend Opportunities
            "Safety_Liquid": "LIQUIDBEES.NS",   # Liquid Fund
            "Safety_Gold": "GOLDBEES.NS",       # Gold ETF
            "Asset_Gold": "GOLDBEES.NS",        # Duplicate for consistency
            "Asset_REIT": "EMBASSY.RR.NS",      # REIT Proxy
            "Asset_Bond": "NIFTYGS10YR.NS",     # Long Term G-Sec
            "Asset_Hedge": "GOLDBEES.NS"        # Hedge Proxy (Gold)
        }

    def generate_model_portfolio(self, persona):
        """
        Generates a Model Portfolio (list of holdings) based on the Persona.
        Uses static logic to pick high-quality tickers from resources.
        """
        strategy = self.get_allocation_strategy(persona)
        allocation = strategy['allocation']
        structure = strategy['structure'] # e.g. {"Large Cap": 2}
        
        # Import resources inside method to avoid circular imports if any
        from rover_tools.ticker_resources import NIFTY_50, NIFTY_MIDCAP, NIFTY_SMALLCAP
        
        holdings = []
        
        # Helper to pick top N stocks
        def pick_stocks(source_list, count):
            # source_list format: "SYMBOL.NS - Name"
            # We just want the symbol
            clean_symbols = [s.split(' - ')[0] for s in source_list]
            return clean_symbols[:count] # Naive Top N selection (usually by market cap)

        # 1. Large Cap Bucket
        if "Equity_LargeCap" in allocation:
            target_count = structure.get("Large Cap", 0) or structure.get("Large/Div Stocks", 0) or structure.get("Large Cap Stock", 0)
            picks = pick_stocks(NIFTY_50, target_count)
            weight_per_stock = allocation["Equity_LargeCap"] / max(1, len(picks))
            for stock in picks:
                holdings.append({"Symbol": stock, "Asset Class": "Equity_LargeCap", "Weight (%)": weight_per_stock})
                
        # 2. Mid Cap Bucket
        if "Equity_MidCap" in allocation:
            target_count = structure.get("Mid Cap Stock", 0)
            picks = pick_stocks(NIFTY_MIDCAP, target_count)
            weight_per_stock = allocation["Equity_MidCap"] / max(1, len(picks))
            for stock in picks:
                holdings.append({"Symbol": stock, "Asset Class": "Equity_MidCap", "Weight (%)": weight_per_stock})

        # 3. Small Cap Bucket
        if "Equity_SmallCap" in allocation:
            target_count = structure.get("Small Cap Stock", 0)
            picks = pick_stocks(NIFTY_SMALLCAP, target_count)
            weight_per_stock = allocation["Equity_SmallCap"] / max(1, len(picks))
            for stock in picks:
                holdings.append({"Symbol": stock, "Asset Class": "Equity_SmallCap", "Weight (%)": weight_per_stock})
                
        # 4. Dividend / Safety / Asset Buckets (Mapped to ETFs)
        for bucket, name in [("Safety_Liquid", "LIQUIDBEES.NS"), 
                             ("Safety_Gold", "GOLDBEES.NS"),
                             ("Asset_Gold", "GOLDBEES.NS"),
                             ("Asset_Bond", "NIFTYGS10YR.NS"),
                             ("Asset_REIT", "EMBASSY.RR.NS"),
                             ("Asset_Hedge", "GOLDBEES.NS"),
                             ("Equity_Dividend", "ITC.NS")]: # Using ITC as Div Proxy if no ETF
            
            if bucket in allocation:
                 # Check if this bucket is actually used in allocation
                 w = allocation[bucket]
                 holdings.append({"Symbol": name, "Asset Class": bucket, "Weight (%)": w})

        return holdings
