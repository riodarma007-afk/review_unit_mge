from backend.app.services.kpi_calculator import KpiCalculator

def test_calculate_kpi_from_aggs():
    # Scenario 1: Normal values
    result = KpiCalculator.calculate_kpi_from_aggs(
        sum_mohh=12.0,
        sum_downtime=2.0, # avail = 10
        sum_mech_downtime=1.0, 
        sum_wh=8.0, 
        sum_ritasi=16
    )
    
    assert result['pa_percent'] == 83.33 # (12-2)/12 * 100 = 10/12 = 83.333
    assert result['ma_percent'] == 91.67 # (12-1)/12 * 100 = 11/12 = 91.666
    assert result['ua_percent'] == 80.0  # 8 / (12-2) * 100 = 8/10 = 80
    assert result['eu_percent'] == 66.67 # 8 / 12 * 100 = 66.666
    assert result['total_ritasi'] == 16
    assert result['productivity_rit_per_hour'] == 2.0 # 16 / 8

def test_calculate_kpi_from_aggs_zero_division():
    # Scenario 2: WH = 0, MOHH = 0
    result = KpiCalculator.calculate_kpi_from_aggs(
        sum_mohh=0,
        sum_downtime=0, 
        sum_mech_downtime=0, 
        sum_wh=0, 
        sum_ritasi=0
    )
    
    assert result['pa_percent'] is None
    assert result['ma_percent'] is None
    assert result['ua_percent'] is None
    assert result['eu_percent'] is None
    assert result['productivity_rit_per_hour'] is None
    assert result['total_ritasi'] == 0
