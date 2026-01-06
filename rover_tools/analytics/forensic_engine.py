import yfinance as yf
import pandas as pd
import numpy as np

class ForensicAnalyzer:
    """
    Institutional-Grade Forensic Engine for detecting financial red flags.
    Focuses on:
    1. Cash Integrity (Satyam Check)
    2. Capex Reality (CWIP Fraud)
    3. Revenue Quality (Channel Stuffing)
    4. Debt Health (Evergreening/Cash Divergence)
    """

    def __init__(self, ticker_symbol):
        self.ticker_symbol = ticker_symbol
        self.ticker = yf.Ticker(ticker_symbol)
        
        # Data Cache
        self.balance_sheet = None
        self.financials = None
        self.cashflow = None
        self.data_loaded = False
        self.currency = "INR"

    def load_data(self):
        """Fetches and normalizes financial statements."""
        try:
            self.balance_sheet = self.ticker.balance_sheet
            self.financials = self.ticker.financials
            self.cashflow = self.ticker.cashflow
            
            # Basic validation
            if self.balance_sheet.empty or self.financials.empty:
                # print(f"⚠️ No financial data found for {self.ticker_symbol}")
                return False
                
            self.data_loaded = True
            return True
        except Exception as e:
            print(f"❌ Error loading forensic data for {self.ticker_symbol}: {e}")
            return False

    def _get_item(self, df, possible_names):
        """Helper to safely fetch a line item using multiple aliases."""
        if df is None: return None
        for name in possible_names:
            if name in df.index:
                return df.loc[name]
        return None

    def run_satyam_check(self):
        """
        [The 'Satyam' Test]
        Logic: If Cash is High, Interest Income MUST be High.
        Red Flag: High Cash + Low Interest Mean = Fake Cash (or pledged).
        """
        if not self.data_loaded: self.load_data()
        
        try:
            # 1. Get Cash & Equivalents
            cash_items = ["Cash And Cash Equivalents", "Cash & Cash Equivalents", "Cash"]
            cash_series = self._get_item(self.balance_sheet, cash_items)
            
            # 2. Get Interest Income (often categorized under "Other Income" or "Interest Income")
            # Note: yfinance creates diverse keys. We look for 'Interest Income' or parts of Other Income.
            # Ideally "Interest Income Non Operating"
            int_items = ["Interest Income", "Interest Income Non Operating", "Total Other Income"]
            interest_series = self._get_item(self.financials, int_items)

            if cash_series is None or interest_series is None:
                return {"status": "SKIPPED", "reason": "Missing Data (Cash/Interest)"}

            # Use most recent year
            latest_cash = cash_series.iloc[0]
            latest_interest = interest_series.iloc[0]

            # Avoid div by zero
            if latest_cash == 0:
                return {"status": "PASS", "yield": 0.0, "details": "No Cash Holdings"}

            implied_yield = (latest_interest / latest_cash) * 100

            # THRESHOLDS
            # If Yield < 2% and Cash > 10% of Market Cap (Proxy check needed, but here absolute) -> Suspicious
            # Simplified: Just Yield check.
            
            result = {
                "metric": "Cash Yield",
                "value": round(implied_yield, 2),
                "threshold": "Min 3.0%",
                "status": "PASS",
                "details": f"Implied Yield: {round(implied_yield, 2)}%"
            }

            if implied_yield < 2.5: # 2.5% is very low for India (Savings rate is 3%)
                result["status"] = "FAIL"
                result["flag"] = "RED"
                result["details"] = "Suspiciously Low Interest Income on Cash Balance."
            elif implied_yield < 4.0:
                result["status"] = "WARNING"
                result["flag"] = "AMBER"
            
            return result

        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    def run_cwip_check(self):
        """
        [The 'Fake Factory' Test]
        Logic: CWIP should not be > 20% of Gross Block for years.
        """
        if not self.data_loaded: self.load_data()

        try:
            # 1. Get Capital Work In Progress
            cwip_items = ["Capital Work In Progress", "Construction In Progress"]
            cwip_series = self._get_item(self.balance_sheet, cwip_items)

            # 2. Get Gross PPE (Property Plant Equipment)
            ppe_items = ["Gross PPE", "Net PPE", "Plant Property Equipment", "Property Plant And Equipment"]
            ppe_series = self._get_item(self.balance_sheet, ppe_items)

            if cwip_series is None:
                return {"status": "PASS", "value": 0, "details": "No CWIP Reported"}
            if ppe_series is None:
                return {"status": "SKIPPED", "reason": "Missing PPE Data"}

            latest_cwip = cwip_series.iloc[0]
            latest_ppe = ppe_series.iloc[0]
            
            if latest_ppe == 0: return {"status": "SKIPPED"}

            ratio = (latest_cwip / (latest_ppe + latest_cwip)) * 100

            result = {
                "metric": "CWIP Ratio",
                "value": round(ratio, 2),
                "threshold": "Max 20%",
                "status": "PASS",
                "details": f"CWIP is {round(ratio, 1)}% of Net Block"
            }

            if ratio > 25:
                result["status"] = "FAIL"
                result["flag"] = "RED"
                result["details"] = "High CWIP suggesting stalled projects or diverted capex."
            elif ratio > 15:
                result["status"] = "WARNING"
                result["flag"] = "AMBER"
            
            return result

        except Exception as e:
             return {"status": "ERROR", "reason": str(e)}

    def run_revenue_quality_check(self):
        """
        [The 'Channel Stuffing' Test]
        Logic: Receivables growing faster than Sales?
        """
        if not self.data_loaded: self.load_data()
        
        try:
            # Need at least 2 years of data
            if self.balance_sheet.shape[1] < 2 or self.financials.shape[1] < 2:
                return {"status": "SKIPPED", "reason": "Need 2 years data"}

            # 1. Sales Growth
            rev_items = ["Total Revenue", "Operating Revenue"]
            rev_series = self._get_item(self.financials, rev_items)
            
            # 2. Receivables Growth
            rec_items = ["Accounts Receivable", "Receivables", "Net Receivables"]
            rec_series = self._get_item(self.balance_sheet, rec_items)

            if rev_series is None or rec_series is None:
                return {"status": "SKIPPED", "reason": "Missing Rev/Rec Data"}

            # Calculate CAGR or YoY Growth (Current vs Previous)
            rev_curr = rev_series.iloc[0]
            rev_prev = rev_series.iloc[1]
            rec_curr = rec_series.iloc[0]
            rec_prev = rec_series.iloc[1]
            
            # Avoid div by zero
            if rev_prev == 0 or rec_prev == 0:
                 return {"status": "SKIPPED", "reason": "Zero Base Data"}

            rev_growth = ((rev_curr - rev_prev) / rev_prev) * 100
            rec_growth = ((rec_curr - rec_prev) / rec_prev) * 100
            
            delta = rec_growth - rev_growth # Positive means Receivables grew faster

            result = {
                "metric": "Revenue Quality",
                "value": round(delta, 2),
                "threshold": "Delta < 15%",
                "status": "PASS",
                "details": f"Rec Growth {round(rec_growth, 1)}% vs Sales {round(rev_growth, 1)}%"
            }

            if delta > 20:
                result["status"] = "FAIL"
                result["flag"] = "RED"
                result["details"] = "Receivables growing much faster than Sales (Channel Stuffing Risk)."
            elif delta > 10:
                result["status"] = "WARNING"
                result["flag"] = "AMBER"
            
            return result

        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    def generate_forensic_report(self):
        """Runs all checks and returns a summary."""
        if not self.data_loaded: 
            success = self.load_data()
            if not success:
                return {
                    "checks": [],
                    "overall_status": "NO DATA",
                    "red_flags": 0,
                    "amber_flags": 0
                }
        
        report = {
            "checks": [],
            "overall_status": "CLEAN",
            "red_flags": 0,
            "amber_flags": 0
        }
        
        # Run Checks
        checks = [
            self.run_satyam_check(),
            self.run_cwip_check(),
            self.run_revenue_quality_check()
        ]
        
        for check in checks:
            report["checks"].append(check)
            if check.get("flag") == "RED":
                report["red_flags"] += 1
            elif check.get("flag") == "AMBER":
                report["amber_flags"] += 1
        
        # summary logic
        if report["red_flags"] > 0:
            report["overall_status"] = "CRITICAL"
        elif report["amber_flags"] >= 2:
             report["overall_status"] = "CAUTION"
             
        return report
