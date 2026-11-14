import math
import pytest
from earth_echo.science.meteorology import wind_speed,saturation_vapour_pressure,vapour_pressure_deficit,relative_humidity

def test_vector_speed_keeps_missing_and_native_units():
    assert wind_speed(-3,4)==5
    assert wind_speed(0,0)==0
    assert wind_speed(None,4) is None
    assert wind_speed(math.nan,4) is None

def test_fao56_published_example_and_conservative_liquid_domain():
    # FAO-56 chapter 3, example 3, equation 11: 24.5°C -> 3.075 kPa; 15°C -> 1.705 kPa.
    assert saturation_vapour_pressure(24.5)==pytest.approx(3.075,abs=.0005)
    assert saturation_vapour_pressure(15)==pytest.approx(1.705,abs=.0005)
    assert vapour_pressure_deficit(24.5,15)==pytest.approx(1.370,abs=.001)
    assert vapour_pressure_deficit(15,15)==0
    assert vapour_pressure_deficit(10,11) is None
    assert vapour_pressure_deficit(-5,-10) is None
    assert vapour_pressure_deficit(51,20) is None
    assert vapour_pressure_deficit(20,None) is None


def test_relative_humidity_native_percentage_and_no_supersaturation_clipping():
    assert relative_humidity(24.5,15)==pytest.approx(100*1.705/3.075,abs=.02)
    assert relative_humidity(15,15)==100
    for t,td in [(10,11),(-5,-10),(51,20),(20,None),(20,float('nan'))]:
        assert relative_humidity(t,td) is None
