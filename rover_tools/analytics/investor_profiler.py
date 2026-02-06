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
                "description": "Capital Protection with Blue-chip Focus",
                "risk_level": "Low",
                "max_tickers": 3,
                "allocation": {"Equity": 100}, 
                "structure": {"Nifty 50 Bluechips": 3} 
            }
        elif persona == self.personas.DEFENDER:
             return {
                "description": "Blue-chip Safety + Dividend Income",
                "risk_level": "Conservative",
                "max_tickers": 3,
                "allocation": {"Equity": 100},
                "structure": {"Bluechips": 2, "Dividend Yield": 1}
            }
        elif persona == self.personas.COMPOUNDER:
            return {
                "description": "Balanced Growth (Core + Next 50)",
                "risk_level": "Moderate",
                "max_tickers": 4,
                "allocation": {"Equity": 100},
                "structure": {"Bluechips": 2, "Next 50": 2}
            }
        elif persona == self.personas.HUNTER:
             return {
                "description": "Aggressive Growth across Market Caps",
                "risk_level": "Aggressive",
                "max_tickers": 6,
                "allocation": {"Equity": 100},
                "structure": {"Growth Bluechips": 2, "Next 50": 2, "Midcap": 2}
            }
        return {}

    def generate_smart_portfolio(self, persona, user_picked_brands=[], user_growth_brands=[], user_alpha_brands=[]):
        """
        Generates a Model Portfolio using Persona-Specific Logic + User's Core Picks.
        
        Args:
            persona: InvestorPersona Enum
            user_picked_brands: List of ticker strings (e.g. ['RELIANCE.NS']) - mapped to Broad/Core
            user_growth_brands: List of ticker strings (e.g. ['SRF.NS']) - mapped to Mid/Growth (Next 50)
            user_alpha_brands: List of ticker strings (e.g. ['BEL.NS']) - mapped to Alpha/Midcap (Hunter only)
        """
        strategy = self.get_allocation_strategy(persona)
        holdings = []
        
        # 1. Fill Core Slots with User Picks (validated)
        # We respect user choice but clip to allocation
        core_weight = 0
        if persona == self.personas.PRESERVER: core_weight = 25
        elif persona == self.personas.DEFENDER: core_weight = 40 
        elif persona == self.personas.COMPOUNDER: core_weight = 30
        elif persona == self.personas.HUNTER: core_weight = 20 # Mapped to Sector Leaders
        
        # Distribute core weight among user picks
        if user_picked_brands:
            w = core_weight / len(user_picked_brands)
            for t in user_picked_brands:
                holdings.append({"Symbol": t, "Asset Class": "Equity_Core", "Weight (%)": w, "Strategy": "User Choice (Core)"})
        
        # 2. Handle Secondary/Growth Picks (Compounder/Hunter only)
        # These reduce the weight available for the AI 'Midcap/Alpha' generation
        # NOTE: user_growth_brands are passed directly to the strategy engines or added here if we want explicit control.
        # Let's add them here as "User Choice (Growth)" and pass them to sub-engines to avoid duplication.
        
        growth_picks_weight_used = 0
        
        if user_growth_brands and (persona == self.personas.COMPOUNDER or persona == self.personas.HUNTER):
             # For Compounder: Midcap (50% bucket). For Hunter: Midcap (40% bucket) or Alpha.
             # Let's assign them to the primary growth bucket.
             
             target_bucket = "Equity_Mid" if persona == self.personas.COMPOUNDER else "Equity_Mid"
             per_stock_w = 10 
             
             for t in user_growth_brands:
                 holdings.append({"Symbol": t, "Asset Class": target_bucket, "Weight (%)": per_stock_w, "Strategy": "User Choice (Growth)"})
                 growth_picks_weight_used += per_stock_w
        
        alpha_picks_weight_used = 0
        if user_alpha_brands and persona == self.personas.HUNTER:
             target_bucket = "Equity_Alpha"
             per_stock_w = 10
             
             for t in user_alpha_brands:
                 holdings.append({"Symbol": t, "Asset Class": target_bucket, "Weight (%)": per_stock_w, "Strategy": "User Choice (Alpha)"})
                 alpha_picks_weight_used += per_stock_w

        # 3. Run Specific AI Strategy to fill the rest
        if persona == self.personas.PRESERVER:
            holdings += self._generate_fortress(holdings)
        elif persona == self.personas.DEFENDER:
             holdings += self._generate_shield(holdings)
        elif persona == self.personas.COMPOUNDER:
             holdings += self._generate_compounder(holdings, growth_picks_weight_used)
        elif persona == self.personas.HUNTER:
             holdings += self._generate_shark(holdings, growth_picks_weight_used, alpha_picks_weight_used)
             
        # 4. Normalize Weights ensures total is 100
        total_w = sum([h['Weight (%)'] for h in holdings])
        if total_w > 0:
            factor = 100.0 / total_w
            for h in holdings:
                h['Weight (%)'] = round(h['Weight (%)'] * factor, 2)
                
        return holdings

    # --- HELPER LISTS FOR STYLE FACTORS ---
    # Proxies for specific Nifty 50 styles
    DIVIDEND_STOCKS = ["ITC.NS", "POWERGRID.NS", "COALINDIA.NS", "NTPC.NS", "ONGC.NS", "BPCL.NS", "HEROMOTOCO.NS"]
    GROWTH_STOCKS = ["TITAN.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "ADANIENT.NS", "APOLLOHOSP.NS", "TRENT.NS"] # TRENT is Nifty 50 now? It's often high growth.
    VALUE_STOCKS = ["ITC.NS", "COALINDIA.NS", "ONGC.NS", "NTPC.NS"] # Overlap with Dividend often

    # --- STRATEGY ENGINES (EQUITY ONLY REFACTOR) ---

    def _generate_fortress(self, current_holdings):
        """Preserver: 3 Blue-chips (Nifty 50)"""
        # Target: 3 Stocks Total. 
        # User defined picks are already in 'current_holdings'.
        # We need to fill the rest up to 3 with Low Volatility Nifty 50.
        
        additions = []
        current_count = len(current_holdings)
        needed = 3 - current_count
        
        if needed <= 0: return []
        
        # Low Volatility Proxies
        safe_picks = ["HUL.NS", "NESTLEIND.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS"]
        # Filter existing
        current_syms = [h['Symbol'] for h in current_holdings]
        valid_picks = [s for s in safe_picks if s not in current_syms]
        
        # Weight per stock (Remaining weight / needed)
        # Note: Weights are normalized at the end, so we can just assign equal shares here.
        w = 100 / 3 
        
        for i in range(needed):
            if i < len(valid_picks):
                additions.append({"Symbol": valid_picks[i], "Asset Class": "Equity_Core", "Weight (%)": w, "Strategy": "Low Volatility Leader"})
            
        return additions

    def _generate_shield(self, current_holdings):
        """Defender: 2 Blue-chips + 1 Dividend Yield (Nifty 50)"""
        additions = []
        current_syms = [h['Symbol'] for h in current_holdings]
        
        # We need 1 Dividend Stock explicitly if not present
        has_div = any(s in self.DIVIDEND_STOCKS for s in current_syms)
        
        # Slot 1: Dividend (Priority)
        if not has_div:
            # Pick one from list
            for d in self.DIVIDEND_STOCKS:
                if d not in current_syms:
                    additions.append({"Symbol": d, "Asset Class": "Equity_Div", "Weight (%)": 33, "Strategy": "High Yield"})
                    current_syms.append(d)
                    break
        
        # Fill rest to reach 3 Total (2 Bluechips + 1 Div)
        total_needed = 3
        current_total = len(current_holdings) + len(additions)
        needed = total_needed - current_total
        
        if needed > 0:
            # Fill with Standard Bluechips (e.g. Banks/Consumers)
            general_picks = ["ICICIBANK.NS", "INFY.NS", "LT.NS", "MARUTI.NS"]
            valid = [g for g in general_picks if g not in current_syms]
            
            w = 33
            for i in range(needed):
                if i < len(valid):
                    additions.append({"Symbol": valid[i], "Asset Class": "Equity_Core", "Weight (%)": w, "Strategy": "Core Defender"})
                    
        return additions

    def _generate_compounder(self, current_holdings, growth_picks_weight_used=0):
        """Compounder: 2 Blue-chips + 2 Next 50"""
        additions = []
        current_syms = [h['Symbol'] for h in current_holdings]
        
        # Total Targets: 4
        # Nifty 50: 2
        # Next 50: 2
        
        # 1. Check Nifty 50 Count (User mostly picks these)
        # We assume user picks are mostly Nifty 50.
        # Let's fill Next 50 requirement first.
        
        # Next 50 Proxies
        next50_pool = [
             "ZOMATO.NS", "DLF.NS", "HAL.NS", "SIEMENS.NS", 
             "VBL.NS", "TRENT.NS", "GODREJCP.NS", "PIDILITIND.NS"
        ]
        
        # Count current Next 50 (approx check or assume user picks are core)
        # We'll just force add 2 Next 50s if we have space, or fill to max 4.
        
        needed_total = 4
        current_len = len(current_holdings)
        remaining_slots = needed_total - current_len
        
        if remaining_slots <= 0: return []
        
        # Strategy: Prioritize filling Next 50 slots if user hasn't picked 4 items.
        # If user picked 2, we add 2 Next 50.
        # If user picked 1, we add 2 Next 50 + 1 Nifty 50.
        
        # Add up to 2 Next 50s
        added_next50 = 0
        w = 25
        
        for n in next50_pool:
            if n not in current_syms and added_next50 < 2 and remaining_slots > 0:
                additions.append({"Symbol": n, "Asset Class": "Equity_Next50", "Weight (%)": w, "Strategy": "Emerging Giant"})
                current_syms.append(n)
                added_next50 += 1
                remaining_slots -= 1
        
        # If still slots left, fill with Nifty 50 Bluechips
        if remaining_slots > 0:
             bluechips = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS"]
             for b in bluechips:
                 if b not in current_syms and remaining_slots > 0:
                     additions.append({"Symbol": b, "Asset Class": "Equity_Core", "Weight (%)": w, "Strategy": "Core Compounder"})
                     current_syms.append(b)
                     remaining_slots -= 1
                     
        return additions
        
    def _generate_shark(self, current_holdings, growth_picks_weight_used=0, alpha_picks_weight_used=0):
        """Hunter: 2 Bluechip Growth + 2 Next 50 + 2 Midcap"""
        additions = []
        current_syms = [h['Symbol'] for h in current_holdings]
        
        # Total: 6
        # 2 Growth Bluechip (Nifty 50 - Exclude Value/Div)
        # 2 Next 50
        # 2 Midcap
        
        # We fill buckets sequentially based on what's missing.
        # We assume USER picks might fall into any bucket.
        # For V1 simplicity, we just try to fill the specific buckets.
        
        w = 16.6 # 100/6
        
        # Bucket 1: Midcap (2)
        mid_pool = ["POLYCAB.NS", "PERSISTENT.NS", "TATACOMM.NS", "SRF.NS", "VOLTAS.NS"]
        added_mid = 0
        for m in mid_pool:
            if m not in current_syms and added_mid < 2:
                additions.append({"Symbol": m, "Asset Class": "Equity_Midcap", "Weight (%)": w, "Strategy": "Midcap Alpha"})
                current_syms.append(m)
                added_mid += 1

        # Bucket 2: Next 50 (2)
        next50_pool = ["ZOMATO.NS", "HAL.NS", "BEL.NS", "DLF.NS", "VBL.NS"]
        added_next = 0
        for n in next50_pool:
            if n not in current_syms and added_next < 2:
                additions.append({"Symbol": n, "Asset Class": "Equity_Next50", "Weight (%)": w, "Strategy": "Next50 Growth"})
                current_syms.append(n)
                added_next += 1
                
        # Bucket 3: Bluechip Growth (2)
        # Should exclude Value/Div logic
        growth_pool = self.GROWTH_STOCKS
        added_growth = 0
        
        # Check if we still have space (Max 6 total constraint)
        current_total_len = len(current_holdings) + len(additions)
        
        for g in growth_pool:
            if g not in current_syms and added_growth < 2 and current_total_len < 6:
                additions.append({"Symbol": g, "Asset Class": "Equity_Growth", "Weight (%)": w, "Strategy": "Bluechip Growth"})
                current_syms.append(g)
                added_growth += 1
                current_total_len += 1
             
        return additions
