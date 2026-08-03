import math
from typing import Dict, Any

def calculate_terp(pre_issue_price: float, rights_price: float, old_ratio: int, new_ratio: int) -> float:
    """
    Theoretical Ex-Rights Price (TERP)
    Formula: [(Pre-Issue Price * Old Shares) + (Rights Price * New Shares)] / (Old Shares + New Shares)
    """
    total_value_old = pre_issue_price * old_ratio
    total_value_new = rights_price * new_ratio
    terp = (total_value_old + total_value_new) / (old_ratio + new_ratio)
    return round(terp, 2)

def calculate_re_intrinsic_value(current_price: float, rights_price: float) -> float:
    """
    Intrinsic value of the Rights Entitlement.
    If the current price is less than rights price, RE is effectively worthless.
    """
    return max(0.0, current_price - rights_price)

def calculate_fractional_entitlement(holdings: int, old_ratio: int, new_ratio: int) -> Dict[str, Any]:
    """
    Calculates fractional shares and the whole shares entitled.
    """
    raw_entitlement = (holdings / old_ratio) * new_ratio
    whole_shares = math.floor(raw_entitlement)
    fraction = raw_entitlement - whole_shares

    return {
        "raw_entitlement": raw_entitlement,
        "whole_shares": whole_shares,
        "fractional_shares": round(fraction, 4),
        "fraction_warning": "Fractions will be rounded down. The company may sell consolidated fractions and credit cash to your bank account." if fraction > 0 else ""
    }

def calculate_subscription_pl(
    holdings: int,
    market_price: float,
    rights_price: float,
    old_ratio: int,
    new_ratio: int,
    additional_shares: int = 0
) -> Dict[str, Any]:
    """
    Calculates capital required, total investment value, and new average cost.
    """
    entitlement_info = calculate_fractional_entitlement(holdings, old_ratio, new_ratio)
    entitled_shares = entitlement_info["whole_shares"]

    total_applied = entitled_shares + additional_shares
    capital_required = total_applied * rights_price

    current_value = holdings * market_price
    total_cost_basis = current_value + capital_required
    total_shares = holdings + total_applied

    new_average_cost = total_cost_basis / total_shares if total_shares > 0 else 0

    # Calculate paper profit based on TERP
    terp = calculate_terp(market_price, rights_price, old_ratio, new_ratio)
    post_issue_value = total_shares * terp
    paper_profit = post_issue_value - total_cost_basis

    return {
        "entitled_shares": entitled_shares,
        "additional_shares_applied": additional_shares,
        "total_shares_applied": total_applied,
        "capital_required": capital_required,
        "new_total_holdings": total_shares,
        "new_average_cost": round(new_average_cost, 2),
        "projected_terp": terp,
        "projected_paper_profit": round(paper_profit, 2)
    }

def calculate_additional_allotment_probability(
    is_undersubscribed: bool,
    promoter_renunciation_pct: float
) -> str:
    """
    Heuristic-based probability for retail investors getting extra shares.
    """
    if is_undersubscribed or promoter_renunciation_pct > 50.0:
        return "HIGH (80-95%) - Strong chance of firm allotment due to institutional/promoter undersubscription."
    elif promoter_renunciation_pct > 10.0:
        return "MEDIUM (40-60%) - Pro-rata allotment likely, partial additional shares expected."
    else:
        return "LOW (10-20%) - Heavy oversubscription expected. Funds will likely be unblocked on refund date."
