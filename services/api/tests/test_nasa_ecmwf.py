import math
import pytest
from earth_echo.connectors.nasa_subsets import good_vi, reproject_subset
from earth_echo.science.units import kelvin_to_celsius, metres_to_mm

def test_physical_units_do_not_turn_absence_into_zero():
    assert kelvin_to_celsius(273.15) == 0
    assert kelvin_to_celsius(None) is None
    assert metres_to_mm(.001) == 1
    assert metres_to_mm(None) is None

def test_modis_cloud_water_and_snow_are_rejected():
    good = 1<<11  # MODLAND=0, usefulness=0, land=1; reliability=0
    assert good_vi(good,0)
    assert not good_vi(good,3)
    for bad in [good|1,good|(1<<8),good|(1<<10),good|(1<<14),good|(1<<15),0]:
        assert not good_vi(bad,0)

def test_sinusoidal_reprojection_preserves_native_order_and_missing():
    # At equator, 1 km sinusoidal square has independently known angular size.
    body = {'ncols':2,'nrows':2,'cellsize':1000,'xllcorner':0,'yllcorner':0}
    grid = reproject_subset(body,[1,None,3,4],'test')
    assert grid.west == pytest.approx(0)
    assert grid.north == pytest.approx(math.degrees(2000/6371007.181))
    assert grid.values == [1,None,3,4]
    assert grid.missing_cells == 1

def test_live_product_metadata_is_consistent_when_retained():
    from earth_echo.storage.products import all_products
    for p in all_products():
        if p.source_id=='D07':
            assert p.initialized_at is not None and p.valid_from is not None
            assert p.issued_at is None  # no invented emission
            assert p.grid.width == 360 and p.grid.height == 180
        if p.source_id in {'D04','D05'}:
            assert p.observation_end > p.observed_at
            assert 'proc_date=' in p.product_version
