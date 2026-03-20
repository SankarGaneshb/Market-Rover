import pytest
from src.data.scoring import calculate_skin_in_the_game, MOCK_HISTORICAL_DATA

def test_full_skin_no_pledge():
    # 75% holding, 0% pledge -> 100% skin
    res = calculate_skin_in_the_game(75.0, 0.0)
    assert res['final_skin_pct'] == 100.0

def test_sebi_cap_normalization():
    # 60% holding, 0% pledged -> 60/75 * 100 = 80.0%
    res = calculate_skin_in_the_game(60.0, 0.0)
    assert res['final_skin_pct'] == 80.0

def test_partial_pledge():
    # 60% holding, 20% pledged -> (40/60) * (60/75) * 100 -> 66.67 * 0.8 = 53.33
    res = calculate_skin_in_the_game(60.0, 20.0)
    assert res['final_skin_pct'] == 53.33

def test_psu_above_75():
    # 80% holding (PSU), 0% pledge
    res = calculate_skin_in_the_game(80.0, 0.0, is_psu=True)
    assert res['final_skin_pct'] == 100.0

def test_high_pledge():
    # 50% holding, 45% pledged -> (5/50) * (50/75) * 100 -> 10% * 0.666 = 6.67%
    res = calculate_skin_in_the_game(50.0, 45.0)
    assert res['final_skin_pct'] == 6.67

def test_zero_promoter():
    res = calculate_skin_in_the_game(0.0, 0.0, is_zero_promoter=True, insider_nee_pct=15.5)
    assert res['final_skin_pct'] == 15.5
    assert res['layer1_commitment'] == 100.0
