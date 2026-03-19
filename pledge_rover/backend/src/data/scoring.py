import math

SEBI_MAX_PROMOTER_HOLDING = 75.0  # SEBI LODR minimum public float = 25%

def calculate_skin_in_the_game(
    promoter_holding_pct: float, 
    pledged_pct: float,
    is_psu: bool = False,
    is_zero_promoter: bool = False,
    insider_nee_pct: float = 0.0
) -> dict:
    """
    Returns the comprehensive Skin in the Game assessment.
    
    Layer 1: Commitment (0-100%) -> Of what they OWN, how much is unencumbered?
    Layer 2: Concentration (0.0-1.0) -> How meaningful is their control position relative to the 75% cap?
    Final Skin = Layer 1 * Layer 2
    """
    
    # ── Handle Zero-Promoter Edge Case (e.g. ITC, ICICI Bank) ──
    if is_zero_promoter or promoter_holding_pct == 0:
        return {
            "type": "Professionally Managed Entity",
            "layer1_commitment": 100.0,
            "layer2_concentration": 0.0,
            "final_skin_pct": insider_nee_pct,  # Use ISS NEE for insiders
            "description": f"Zero-promoter (Board aligned). Insider NEE: {insider_nee_pct}%"
        }

    # ── Normal Promoter Calculation ──
    # PSU exception: govt can hold > 75%, so effective ceiling is max(actual_holding, 75)
    effective_ceiling = max(promoter_holding_pct, SEBI_MAX_PROMOTER_HOLDING) if is_psu else min(promoter_holding_pct, SEBI_MAX_PROMOTER_HOLDING)
    
    if effective_ceiling <= 0:
        return {"final_skin_pct": 0.0}

    # 1. Commitment Layer
    unpledged_pct = max(promoter_holding_pct - pledged_pct, 0.0)
    commitment = (unpledged_pct / promoter_holding_pct) * 100.0 if promoter_holding_pct > 0 else 0.0
    
    # 2. Concentration Layer
    # How much of the 75% maximum allowed do they hold?
    effective_ceiling = max(promoter_holding_pct, SEBI_MAX_PROMOTER_HOLDING) if is_psu else SEBI_MAX_PROMOTER_HOLDING
    concentration = min(promoter_holding_pct, effective_ceiling) / effective_ceiling

    # Final Combined
    final_skin = commitment * concentration
    
    return {
        "type": "PSU" if is_psu else "Promoter Controlled",
        "layer1_commitment": round(commitment, 2),
        "layer2_concentration": round(concentration, 2),
        "final_skin_pct": round(min(final_skin, 100.0), 2),
        "description": "Computed via 3-Layer SEBI Normalization Framework"
    }

def survival_score(ts_data: dict) -> dict:
    """
    Calculates the 'Survival Score' (0-100) based on 8-Quarter Time Series Data.
    Higher score = More likely survival pledging (bad).
    Lower score = Growth pledging / neutral (good).
    
    Expected ts_data keys:
    - pledge_qoq_change (float): Latest quarter over quarter % change in pledging
    - price_pledge_pearson_8q (float): Correlation between stock price and pledge % (-1 to 1)
    - pledgee_tier (str): 'Tier1Bank', 'NBFC', 'RelatedParty'
    - ocf_trend (str): 'positive', 'flat', 'negative'
    - pledge_std_dev_8q (float): Standard deviation of pledge % over 8Q
    - release_create_ratio (float): Ratio of pledge releases to creations over 8Q
    """
    score = 0
    breakdown = {}

    # 1. Pledge Velocity QoQ (+30 max) - Higher jump = more stress
    v = ts_data.get('pledge_qoq_change', 0)
    pts = min(30, int((v / 5.0) * 30)) if v > 0 else 0
    breakdown['velocity'] = pts
    score += pts

    # 2. Price-Pledge Correlation (+25 max) - Inverse correlation is bad (pledging as stock falls)
    corr = ts_data.get('price_pledge_pearson_8q', 0)
    pts = int(max(0, -corr) * 25)
    breakdown['price_correlation'] = pts
    score += pts

    # 3. Pledgee Quality (+20 max) - Obscure lenders = desperation
    quality = ts_data.get('pledgee_tier', 'Tier1Bank')
    pts = {'Tier1Bank': 0, 'NBFC': 15, 'RelatedParty': 20}.get(quality, 10)
    breakdown['pledgee_quality'] = pts
    score += pts

    # 4. Operating Cash Flow Trend (+15 max)
    cf_trend = ts_data.get('ocf_trend', 'positive')
    pts = {'positive': 0, 'flat': 7, 'negative': 15}.get(cf_trend, 7)
    breakdown['cashflow'] = pts
    score += pts

    # 5. Pledge Oscillation (+10 max) - Rolling/churning debt
    std = ts_data.get('pledge_std_dev_8q', 0)
    pts = min(10, int((std / 5.0) * 10))
    breakdown['oscillation'] = pts
    score += pts

    # Classification Label
    if score < 30:
        label = 'Growth'
    elif score < 60:
        label = 'Uncertain'
    else:
        label = 'Survival'

    # Trust Meter: Release to Create Ratio
    r_c_ratio = ts_data.get('release_create_ratio', 1.0)
    trust_signal = 'Positive' if r_c_ratio > 1.0 else 'Neutral' if r_c_ratio == 1.0 else 'Warning'

    return {
        "intent_label": label,
        "score_0_to_100": score,
        "trust_signal": trust_signal,
        "release_create_ratio": r_c_ratio,
        "breakdown": breakdown
    }
