
# Common NSE/BSE Tickers for Autocomplete
# Categorized for filtering

NIFTY_50 = [
    "RELIANCE.NS - Reliance Industries Ltd",
    "TCS.NS - Tata Consultancy Services Ltd",
    "HDFCBANK.NS - HDFC Bank Ltd",
    "ICICIBANK.NS - ICICI Bank Ltd",
    "INFY.NS - Infosys Ltd",
    "SBIN.NS - State Bank of India",
    "BHARTIARTL.NS - Bharti Airtel Ltd",
    "ITC.NS - ITC Ltd",
    "KOTAKBANK.NS - Kotak Mahindra Bank Ltd",
    "LT.NS - Larsen & Toubro Ltd",
    "HINDUNILVR.NS - Hindustan Unilever Ltd",
    "AXISBANK.NS - Axis Bank Ltd",
    "BAJFINANCE.NS - Bajaj Finance Ltd",
    "MARUTI.NS - Maruti Suzuki India Ltd",
    "ASIANPAINT.NS - Asian Paints Ltd",
    "HCLTECH.NS - HCL Technologies Ltd",
    "TITAN.NS - Titan Company Ltd",
    "SUNPHARMA.NS - Sun Pharmaceutical Industries Ltd",
    "ULTRACEMCO.NS - UltraTech Cement Ltd",
    "TATASTEEL.NS - Tata Steel Ltd",
    "NTPC.NS - NTPC Ltd",
    "POWERGRID.NS - Power Grid Corporation of India Ltd",
    "BAJAJFINSV.NS - Bajaj Finserv Ltd",
    "TATAMOTORS.NS - Tata Motors Ltd",
    "M&M.NS - Mahindra & Mahindra Ltd",
    "ADANIENT.NS - Adani Enterprises Ltd",
    "ADANIPORTS.NS - Adani Ports and Special Economic Zone Ltd",
    "ONGC.NS - Oil and Natural Gas Corporation Ltd",
    "JSWSTEEL.NS - JSW Steel Ltd",
    "WIPRO.NS - Wipro Ltd",
    "COALINDIA.NS - Coal India Ltd",
    "GRASIM.NS - Grasim Industries Ltd",
    "HINDALCO.NS - Hindalco Industries Ltd",
    "DRREDDY.NS - Dr. Reddy's Laboratories Ltd",
    "TECHM.NS - Tech Mahindra Ltd",
    "DIVISLAB.NS - Divi's Laboratories Ltd",
    "CIPLA.NS - Cipla Ltd",
    "SBILIFE.NS - SBI Life Insurance Company Ltd",
    "BPCL.NS - Bharat Petroleum Corporation Ltd",
    "BRITANNIA.NS - Britannia Industries Ltd",
    "EICHERMOT.NS - Eicher Motors Ltd",
    "HDFCLIFE.NS - HDFC Life Insurance Company Ltd",
    "TATACONSUM.NS - Tata Consumer Products Ltd",
    "NESTLEIND.NS - Nestle India Ltd",
    "HEROMOTOCO.NS - Hero MotoCorp Ltd",
    "APOLLOHOSP.NS - Apollo Hospitals Enterprise Ltd",
    "UPL.NS - UPL Ltd",
    "INDUSINDBK.NS - IndusInd Bank Ltd",
    "BAJAJ-AUTO.NS - Bajaj Auto Ltd",
    "LTIM.NS - LTIMindtree Ltd"
]

SENSEX = [
    "RELIANCE.NS - Reliance Industries Ltd",
    "TCS.NS - Tata Consultancy Services Ltd",
    "HDFCBANK.NS - HDFC Bank Ltd",
    "ICICIBANK.NS - ICICI Bank Ltd",
    "INFY.NS - Infosys Ltd",
    "SBIN.NS - State Bank of India",
    "BHARTIARTL.NS - Bharti Airtel Ltd",
    "ITC.NS - ITC Ltd",
    "KOTAKBANK.NS - Kotak Mahindra Bank Ltd",
    "LT.NS - Larsen & Toubro Ltd",
    "HINDUNILVR.NS - Hindustan Unilever Ltd",
    "AXISBANK.NS - Axis Bank Ltd",
    "BAJFINANCE.NS - Bajaj Finance Ltd",
    "MARUTI.NS - Maruti Suzuki India Ltd",
    "ASIANPAINT.NS - Asian Paints Ltd",
    "HCLTECH.NS - HCL Technologies Ltd",
    "TITAN.NS - Titan Company Ltd",
    "SUNPHARMA.NS - Sun Pharmaceutical Industries Ltd",
    "ULTRACEMCO.NS - UltraTech Cement Ltd",
    "TATASTEEL.NS - Tata Steel Ltd",
    "NTPC.NS - NTPC Ltd",
    "POWERGRID.NS - Power Grid Corporation of India Ltd",
    "BAJAJFINSV.NS - Bajaj Finserv Ltd",
    "TATAMOTORS.NS - Tata Motors Ltd",
    "M&M.NS - Mahindra & Mahindra Ltd",
    "INDUSINDBK.NS - IndusInd Bank Ltd",
    "BAJAJ-AUTO.NS - Bajaj Auto Ltd",
    "WIPRO.NS - Wipro Ltd",
    "JSWSTEEL.NS - JSW Steel Ltd",
    "TECHM.NS - Tech Mahindra Ltd"
]

BANK_NIFTY = [
    "HDFCBANK.NS - HDFC Bank Ltd",
    "ICICIBANK.NS - ICICI Bank Ltd",
    "SBIN.NS - State Bank of India",
    "AXISBANK.NS - Axis Bank Ltd",
    "KOTAKBANK.NS - Kotak Mahindra Bank Ltd",
    "INDUSINDBK.NS - IndusInd Bank Ltd",
    "AUBANK.NS - AU Small Finance Bank Ltd",
    "FEDERALBNK.NS - The Federal Bank Ltd",
    "IDFCFIRSTB.NS - IDFC First Bank Ltd",
    "BANDHANBNK.NS - Bandhan Bank Ltd",
    "PNB.NS - Punjab National Bank",
    "BANKBARODA.NS - Bank of Baroda"
]

POPULAR_OTHERS = [
    "ZOMATO.NS - Zomato Ltd",
    "PAYTM.NS - One97 Communications Ltd",
    "NYKAA.NS - FSN E-Commerce Ventures Ltd",
    "POLICYBZR.NS - PB Fintech Ltd",
    "LICI.NS - Life Insurance Corporation of India",
    "IRCTC.NS - Indian Railway Catering and Tourism Corp",
    "HAL.NS - Hindustan Aeronautics Ltd",
    "BEL.NS - Bharat Electronics Ltd",
    "VBL.NS - Varun Beverages Ltd",
    "TRENT.NS - Trent Ltd",
    "VEDL.NS - Vedanta Ltd",
    "SIEMENS.NS - Siemens Ltd",
    "DLF.NS - DLF Ltd",
    "PIDILITIND.NS - Pidilite Industries Ltd",
    "GODREJCP.NS - Godrej Consumer Products Ltd",
    "SHREECEM.NS - Shree Cement Ltd",
    "HAVELLS.NS - Havells India Ltd",
    "DABUR.NS - Dabur India Ltd",
    "ABB.NS - ABB India Ltd",
    "AMBUJACEM.NS - Ambuja Cements Ltd",
    "GAIL.NS - GAIL (India) Ltd",
    "BOSCHLTD.NS - Bosch Ltd"
]

def get_common_tickers(category="All"):
    """
    Returns tickers based on category.
    """
    if category == "Nifty 50":
        return sorted(NIFTY_50)
    elif category == "Sensex":
        return sorted(SENSEX)
    elif category == "Bank Nifty":
        return sorted(BANK_NIFTY)
    else:
        # Combine all unique tickers
        all_tickers = list(set(NIFTY_50 + SENSEX + BANK_NIFTY + POPULAR_OTHERS))
        return sorted(all_tickers)
