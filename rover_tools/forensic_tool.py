from langchain.tools import tool
from rover_tools.analytics.forensic_engine import ForensicAnalyzer

@tool("Check Accounting Fraud")
def check_accounting_fraud(ticker_symbol: str):
    """
    Performs a Forensic Audit on the company's Balance Sheet (Satyam Check, CWIP, Revenue Quality).
    Useful for detecting accounting red flags before investing.
    
    Args:
        ticker_symbol (str): The stock ticker (e.g., 'TCS.NS').
        
    Returns:
        str: A summary of the audit. Returns "CLEAN" if no flags, otherwise details the Red Flags.
    """
    try:
        analyzer = ForensicAnalyzer(ticker_symbol)
        report = analyzer.generate_forensic_report()
        
        status = report.get("overall_status", "UNKNOWN")
        
        if status == "CLEAN":
            return f"FORENSIC AUDIT PASSED ({ticker_symbol}): No accounting red flags detected."
            
        # Compile warnings
        details = []
        for check in report.get("checks", []):
            if check.get("flag") in ["RED", "AMBER"]:
                details.append(f"- {check['metric']}: {check['details']} ({check['flag']})")
                
        if not details:
            return f"FORENSIC AUDIT PASSED ({ticker_symbol}): Minor data gaps but no active red flags."
            
        flag_summary = "\n".join(details)
        return f"FORENSIC AUDIT WARNING ({ticker_symbol}) - Status: {status}\n{flag_summary}"

    except Exception as e:
        return f"Forensic Audit Error for {ticker_symbol}: {str(e)}"
