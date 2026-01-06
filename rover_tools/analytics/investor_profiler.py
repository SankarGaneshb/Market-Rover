import pandas as pd
from enum import Enum
from rover_tools.analytics.forensic_engine import ForensicAnalyzer
from rover_tools.shadow_tools import detect_silent_accumulation, analyze_sector_flow
from rover_tools.analytics.portfolio_engine import AnalyticsPortfolio
from rover_tools.ticker_resources import NIFTY_50_SECTOR_MAP, ASSET_PROXIES, NIFTY_MIDCAP, NIFTY_SMALLCAP

class InvestorPersona(Enum):
    PRESERVER = "The Preserver"     # Minimal Risk, FD Beating
    DEFENDER = "The Defender"       # Conservative, Inflation Protection
    COMPOUNDER = "The Compounder"   # Moderate, Wealth Creation
    HUNTER = "The Hunter"           # Aggressive, Alpha Seeker

class PortfolioValidator:
    """
    Guardrail Engine: Runs Forensic, Shadow, and Correlation checks.
    """
    def __init__(self):
        self.pf_engine = AnalyticsPortfolio()

    def validate_holdings(self, holdings_list):
        """
        Runs comprehensive health check on a list of tickers.
        Returns a dict of flags: {ticker: {status: 'RED/AMBER/GREEN', reason: '...'}}
        """
        flags = {}
        tickers = [h['Symbol'] for h in holdings_list if "BEES" not in h['Symbol'] and "LIQUID" not in h['Symbol']]
        
        # 1. Forensic Check
        for ticker in tickers:
            analyzer = ForensicAnalyzer(ticker)
            report = analyzer.generate_forensic_report()
            
            if report['overall_status'] == "CRITICAL":
                flags[ticker] = {"status": "RED", "reason": f"Forensic Alert: {report['red_flags']} Red Flags"}
            elif report['overall_status'] == "CAUTION":
                flags[ticker] = {"status": "AMBER", "reason": "Forensic Warning (Check details)"}
            else:
                flags[ticker] = {"status": "GREEN", "reason": "Forensic Clean"}
                
        # 2. Shadow Check (For Alpha/Hunter validation)
        for ticker in tickers:
            try:
                shadow = detect_silent_accumulation(ticker)
                score = shadow.get('score', 0)
                if score > 60:
                     msg = f"Shadow Score: {score}/100 (Accumulation Detected)"
                     # Append to reasoning, don't overwrite if Red
                     if flags[ticker]['status'] != 'RED':
                         flags[ticker]['reason'] += f" | {msg}"
            except:
                pass

        # 3. Correlation Check (Portfolio Level)
        # Check if any pair > 0.8
        corr_matrix = self.pf_engine.calculate_correlation_matrix(tickers)
        if not corr_matrix.empty:
            for i in range(len(corr_matrix.columns)):
                for j in range(i):
                    val = corr_matrix.iloc[i, j]
                    if val > 0.85:
                        t1 = corr_matrix.columns[i]
                        t2 = corr_matrix.columns[j]
                        # Add warning to both
                        msg = f"High Correlation ({val:.2f}) with {t2}"
                        if t1 in flags: flags[t1]['reason'] += f" | {msg}"
                        else: flags[t1] = {"status": "AMBER", "reason": msg}

        return flags

class InvestorProfiler:
    """
    Behavioral Finance Engine to map users to profiles and generate
    Asset Allocation Strategies with strict ticker limits.
    """
    
    def __init__(self):
        self.personas = InvestorPersona
        self.validator = PortfolioValidator()

    def get_profile(self, q1_score, q2_score, q3_score):
        """Calculates profile based on 3-Question 'Sleep Test'."""
        total_score = q1_score + q2_score + q3_score
        if total_score <= 4: return self.personas.PRESERVER
        elif total_score <= 6: return self.personas.DEFENDER
        elif total_score <= 7: return self.personas.COMPOUNDER
        else: return self.personas.HUNTER

    def get_allocation_strategy(self, persona):
        """Returns the specific Asset Allocation & Ticker Constraints."""
        if persona == self.personas.PRESERVER:
            return {
                "description": "Capital Protection + FD Beating Returns (Fortress Strategy)",
                "risk_level": "Low",
                "max_tickers": 5,
                "allocation": {"Equity": 25, "Gold": 25, "Debt": 50}, 
                "structure": {"Best Brands (Nifty 50)": 2, "Gold ETF": 1, "Liquid/G-Sec": 2} # Slots
            }
        elif persona == self.personas.DEFENDER:
             return {
                "description": "Inflation Protection + Regular Income (Dividend Shield)",
                "risk_level": "Conservative",
                "max_tickers": 7,
                "allocation": {"Equity": 60, "REIT": 15, "Gold": 15, "Debt": 10},
                "structure": {"Dividend Brands": 3, "REITs": 1, "Gold ETF": 1, "Corp Bond": 1}
            }
        elif persona == self.personas.COMPOUNDER:
            return {
                "description": "Wealth Creation (Quality Compounder Strategy)",
                "risk_level": "Moderate",
                "max_tickers": 10,
                "allocation": {"Equity_Large": 30, "Equity_Mid": 50, "Gold": 20},
                "structure": {"Core Brands": 3, "Growth Midcaps": 4, "Gold ETF": 1}
            }
        elif persona == self.personas.HUNTER:
             return {
                "description": "Alpha Generation (Momentum Shark Strategy)",
                "risk_level": "Aggressive",
                "max_tickers": 12,
                "allocation": {"Equity_Small": 40, "Equity_Mid": 40, "Sector_Ldr": 20},
                "structure": {"Sector Leaders": 3, "Hidden Gems": 5, "Turnaround": 2}
            }
        return {}

    def generate_smart_portfolio(self, persona, user_picked_brands=[]):
        """
        Generates a Model Portfolio using Persona-Specific Logic + User's Core Picks.
        
        Args:
            persona: InvestorPersona Enum
            user_picked_brands: List of ticker strings (e.g. ['RELIANCE.NS', 'TCS.NS'])
        """
        strategy = self.get_allocation_strategy(persona)
        holdings = []
        
        # 1. Fill Core Slots with User Picks (validated)
        # We respect user choice but clip to allocation
        core_weight = 0
        if persona == self.personas.PRESERVER: core_weight = 25
        elif persona == self.personas.DEFENDER: core_weight = 40 # Part of 60% equity
        elif persona == self.personas.COMPOUNDER: core_weight = 30
        elif persona == self.personas.HUNTER: core_weight = 20
        
        # Distribute core weight among user picks
        if user_picked_brands:
            w = core_weight / len(user_picked_brands)
            for t in user_picked_brands:
                holdings.append({"Symbol": t, "Asset Class": "Equity_Core", "Weight (%)": w, "Strategy": "User Choice (Core)"})
        else:
            # Fallback if user picked mainly nothing
            pass 

        # 2. Run Specific AI Strategy to fill the rest
        if persona == self.personas.PRESERVER:
            holdings += self._generate_fortress(holdings)
        elif persona == self.personas.DEFENDER:
             holdings += self._generate_shield(holdings)
        elif persona == self.personas.COMPOUNDER:
             holdings += self._generate_compounder(holdings)
        elif persona == self.personas.HUNTER:
             holdings += self._generate_shark(holdings)
             
        # 3. Normalize Weights ensures total is 100
        total_w = sum([h['Weight (%)'] for h in holdings])
        if total_w > 0:
            factor = 100.0 / total_w
            for h in holdings:
                h['Weight (%)'] = round(h['Weight (%)'] * factor, 2)
                
        return holdings

    # --- STRATEGY ENGINES ---

    def _generate_fortress(self, current_holdings):
        """Preserver: Safety First (Gold + Bonds)"""
        additions = []
        
        # 1. Add Gold (25%)
        additions.append({"Symbol": ASSET_PROXIES['Gold'], "Asset Class": "Safety_Gold", "Weight (%)": 25, "Strategy": "Hedge"})
        
        # 2. Add Debt (50%) -> Split Liquid and G-Sec
        additions.append({"Symbol": ASSET_PROXIES['Liquid'], "Asset Class": "Safety_Cash", "Weight (%)": 25, "Strategy": "Liquidity"})
        additions.append({"Symbol": ASSET_PROXIES['G-Sec Bond'], "Asset Class": "Safety_Bond", "Weight (%)": 25, "Strategy": "Sovereign Guarantee"})
        
        return additions

    def _generate_shield(self, current_holdings):
        """Defender: Income Focus (REITs + Div Stocks)"""
        additions = []
        
        # 1. Add REIT (15%)
        additions.append({"Symbol": ASSET_PROXIES['REIT'], "Asset Class": "Income_REIT", "Weight (%)": 15, "Strategy": "Rental Income"})

        # 2. Add Gold (15%)
        additions.append({"Symbol": ASSET_PROXIES['Gold'], "Asset Class": "Safety_Gold", "Weight (%)": 15, "Strategy": "Inflation Hedge"})
        
        # 3. Add High Dividend Stock (Automatic Pick) - e.g. ITC or POWERGRID if not in user picks
        # Simple Logic: Check if ITC is in user picks. If not, add it.
        # Ideally we scan specifically for Yield, but hardcoding high-quality proxies is safer for V1
        div_proxy = "ITC.NS"
        if not any(h['Symbol'] == div_proxy for h in current_holdings):
             additions.append({"Symbol": div_proxy, "Asset Class": "Equity_Div", "Weight (%)": 10, "Strategy": "Dividend Aristocrat"})
             
        return additions

    def _generate_compounder(self, current_holdings):
        """Compounder: Growth at Reasonable Price (Midcaps)"""
        additions = []
        
        # 1. Add Gold (20%)
        additions.append({"Symbol": ASSET_PROXIES['Gold'], "Asset Class": "Safety_Gold", "Weight (%)": 20, "Strategy": "Hedge"})
        
        # 2. Pick High Quality Midcaps (50% Allocation)
        # Scan Nifty Midcap list -> Filter Forensic Safe -> Pick.
        # For efficiency V1, we pick diversified top names known for growth
        # In a real engine, we'd run 'rover_tools.analytics.forensic_engine' live here.
        # We will pick 2 distinct sectors.
        midcap_picks = ["TRENT.NS", "BEL.NS", "LTIM.NS"] 
        w = 50 / len(midcap_picks)
        for m in midcap_picks:
             # Basic duplicate check
             if not any(h['Symbol'] == m for h in current_holdings):
                 additions.append({"Symbol": m, "Asset Class": "Equity_Midcap", "Weight (%)": w, "Strategy": "Quality Growth"})
                 
        return additions
        
    def _generate_shark(self, current_holdings):
        """Hunter: Momentum + Shadow Score"""
        additions = []
        
        # 1. Sector Rotation Check (Live)
        # We try to get top sector
        try:
             sector_df = analyze_sector_flow()
             if not sector_df.empty:
                 top_sector = sector_df.iloc[0]['Sector'] # e.g. "Nifty Auto"
                 # Map sector to a Proxy ETF or Stock?
                 # For now, we add a general "Alpha" name. 
                 # Let's say we pick a proxy from Smallcap
                 pass
        except:
             pass

        # 2. Shadow Score Winners (Simulated for V1 speed, or use specific known high-beta names)
        # We allocate to Smallcap & Momentum
        alpha_picks = ["ZOMATO.NS", "KPITTECH.NS", "BSE.NS", "SUZLON.NS"]
        w = 80 / len(alpha_picks) # Remaining weight roughly
        
        for a in alpha_picks:
             additions.append({"Symbol": a, "Asset Class": "Equity_Alpha", "Weight (%)": w, "Strategy": "Momentum/Shadow"})
             
        return additions
