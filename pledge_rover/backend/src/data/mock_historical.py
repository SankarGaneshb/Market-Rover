from typing import Dict, Any
from .scoring import calculate_skin_in_the_game, survival_score

# 8-Quarter Time Series Mock Data for the 5 target companies
# This replaces the missing BSE historical data for Phase 2 validation

MOCK_HISTORICAL_DATA: Dict[str, Dict[str, Any]] = {
    "LLOYDSME": {
        "company_name": "Lloyds Metals And Energy Limited",
        "current_metrics": {
            "promoter_holding_pct": 65.5,
            "pledged_pct": 12.4, # 12.4% of total shares
            "is_psu": False,
            "is_zero_promoter": False
        },
        "time_series_8q": {
            "pledge_qoq_change": 4.5,
            "price_pledge_pearson_8q": -0.4, # Slight inverse corr
            "pledgee_tier": "NBFC",
            "ocf_trend": "flat",
            "pledge_std_dev_8q": 3.2,
            "release_create_ratio": 0.6
        }
    },
    "DEEPAKFERT": {
        "company_name": "Deepak Fertilizers And Petrochemicals",
        "current_metrics": {
            "promoter_holding_pct": 48.0,
            "pledged_pct": 34.5, 
            "is_psu": False,
            "is_zero_promoter": False
        },
        "time_series_8q": {
            "pledge_qoq_change": 0.0,
            "price_pledge_pearson_8q": 0.8, # Positive corr (Growth)
            "pledgee_tier": "Tier1Bank",
            "ocf_trend": "positive",
            "pledge_std_dev_8q": 1.1,
            "release_create_ratio": 1.2
        }
    },
    "NOCIL": {
        "company_name": "NOCIL Limited",
        "current_metrics": {
            "promoter_holding_pct": 33.8,  # Minority Family
            "pledged_pct": 4.1, 
            "is_psu": False,
            "is_zero_promoter": False
        },
        "time_series_8q": {
            "pledge_qoq_change": -1.2,
            "price_pledge_pearson_8q": 0.1,
            "pledgee_tier": "Tier1Bank",
            "ocf_trend": "positive",
            "pledge_std_dev_8q": 0.5,
            "release_create_ratio": 2.5
        }
    },
    "AJANTPHARM": {
        "company_name": "Ajanta Pharma",
        "current_metrics": {
            "promoter_holding_pct": 66.2, 
            "pledged_pct": 0.0, # Clean
            "is_psu": False,
            "is_zero_promoter": False
        },
        "time_series_8q": {
            "pledge_qoq_change": 0.0,
            "price_pledge_pearson_8q": 0.0,
            "pledgee_tier": "Tier1Bank",
            "ocf_trend": "positive",
            "pledge_std_dev_8q": 0.0,
            "release_create_ratio": 1.0
        }
    },
    "CAMLINFINE": {
        "company_name": "Camlin Fine Sciences",
        "current_metrics": {
            "promoter_holding_pct": 48.0, 
            "pledged_pct": 18.9, 
            "is_psu": False,
            "is_zero_promoter": False
        },
        "time_series_8q": {
            "pledge_qoq_change": 8.5, # Sudden jump
            "price_pledge_pearson_8q": -0.85, # Strong inverse (price crashed, pledge rose)
            "pledgee_tier": "RelatedParty",
            "ocf_trend": "negative",
            "pledge_std_dev_8q": 6.8,
            "release_create_ratio": 0.1 # No releases, all creations
        }
    }
}

def get_enriched_promoter_data(symbol: str) -> Dict[str, Any]:
    """Computes all intelligent metrics to send to frontend & AI Council."""
    sym = symbol.upper()
    if sym not in MOCK_HISTORICAL_DATA:
        return None
    
    data = MOCK_HISTORICAL_DATA[sym]
    
    # Calculate 3-Layer Skin in the Game
    skin_metrics = calculate_skin_in_the_game(**data["current_metrics"])
    
    # Calculate 8-Quarter Survival Score
    survival_metrics = survival_score(data["time_series_8q"])
    
    # Map legacy static values for Dashboard compatibility until fully updated
    legacy_map = {
        "LLOYDSME": {"gov": 3.8, "shares": 504.6},
        "DEEPAKFERT": {"gov": 6.2, "shares": 126.9},
        "NOCIL": {"gov": 8.5, "shares": 166.6},
        "AJANTPHARM": {"gov": 9.1, "shares": 126.0},
        "CAMLINFINE": {"gov": 4.5, "shares": 167.5}
    }
    legacy = legacy_map.get(sym, {"gov": 5.0, "shares": 100.0})

    # Return a unified dictionary
    return {
        "symbol": sym,
        "company_name": data["company_name"],
        "holding_pct": data["current_metrics"]["promoter_holding_pct"],
        "pledged_pct": data["current_metrics"]["pledged_pct"],
        "skin_in_the_game": skin_metrics["final_skin_pct"],
        "skin_layer1": skin_metrics["layer1_commitment"],
        "skin_layer2": skin_metrics["layer2_concentration"],
        "survival_score": survival_metrics["score_0_to_100"],
        "intent_label": survival_metrics["intent_label"],
        "trust_signal": survival_metrics["trust_signal"],
        "release_create_ratio": survival_metrics["release_create_ratio"],
        "governance_score": legacy["gov"],
        "total_shares": legacy["shares"]
    }

def get_all_enriched_promoters():
    """Returns a list of all enriched promoters"""
    return [get_enriched_promoter_data(sym) for sym in MOCK_HISTORICAL_DATA.keys()]
