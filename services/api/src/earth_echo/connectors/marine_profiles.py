"""Common native GLO12 geometry/time/chunk checks for two qualified profiles."""
from datetime import datetime,timedelta,timezone
import h5py
import netCDF4
import numpy as np
from earth_echo.connectors.hdf_native import native_window
from earth_echo.connectors.marine_currents import attr

_FIELDS={
    'thetao':('sea_water_potential_temperature','degrees_C','Degrees Celsius',(-10,40),'native_valid_range_C'),
    'so':('sea_water_salinity','1e-3','Practical Salinity Unit',(0,50),'native_valid_range'),
}


def decode_profile(source,day,*,expected_url,collection,method,variable):
    standard,unit,unit_long,valid_range,range_key=_FIELDS[variable]
    if source.url!=expected_url or not source.etag or source.etag.startswith('W/'):
        raise ValueError('Marine profile native URL/strong object version missing')
    with source.open() as reader,h5py.File(reader,'r') as ds:
        if attr(ds.attrs.get('Conventions'))!='CF-1.6' or attr(ds.attrs.get('source'))!='MERCATOR GLO12' or attr(ds.attrs.get('product'))!='GLOBAL_ANALYSISFORECAST_PHY_001_024' or attr(ds.attrs.get('title'))!='Instantaneous fields for product GLOBAL_ANALYSISFORECAST_PHY_001_024':
            raise ValueError('Marine profile native collection/time meaning changed')
        lon,lat,depth,time=[ds[k][...] for k in ('longitude','latitude','depth','time')]
        if lon.shape!=(4320,) or lat.shape!=(2041,) or attr(ds['longitude'].attrs.get('units'))!='degrees_east' or attr(ds['latitude'].attrs.get('units'))!='degrees_north' or np.max(abs(lon-(-180+np.arange(4320)/12)))>2.1e-5 or np.max(abs(lat-(-80+np.arange(2041)/12)))>1.1e-5:
            raise ValueError('Marine profile independent native CF axes changed')
        if depth.shape!=(50,) or attr(ds['depth'].attrs.get('units'))!='m' or attr(ds['depth'].attrs.get('positive'))!='down' or depth[0]!=np.float32(.494025) or not np.all(np.diff(depth)>0):
            raise ValueError('Marine profile native depth changed')
        units=attr(ds['time'].attrs.get('units'))
        if time.shape!=(1,) or units!='hours since 1950-01-01' or attr(ds['time'].attrs.get('calendar'))!='gregorian':
            raise ValueError('Marine profile CF time encoding changed')
        stamp=datetime(1950,1,1,tzinfo=timezone.utc)+timedelta(hours=float(time[0]))
        independent=netCDF4.num2date(time[0],units,calendar='gregorian',only_use_cftime_datetimes=False,only_use_python_datetimes=True).replace(tzinfo=timezone.utc)
        if stamp!=independent or stamp!=day+timedelta(days=1):raise ValueError('Marine profile native time and file identity disagree')
        v=ds[variable]
        if v.shape!=(1,50,2041,4320) or v.dtype!=np.dtype('<f4') or v.chunks!=(1,6,256,540) or attr(v.attrs.get('standard_name'))!=standard or attr(v.attrs.get('units'))!=unit or attr(v.attrs.get('unit_long'))!=unit_long or attr(v.attrs.get('cell_methods'))!='area: mean' or float(v.attrs.get('scale_factor',1))!=1 or float(v.attrs.get('add_offset',0))!=0:
            raise ValueError('Marine profile units/layout/meaning changed')
        low,high,fill=[float(np.asarray(v.attrs[k]).item()) for k in ('valid_min','valid_max','_FillValue')]
        if (low,high)!=valid_range or not np.isfinite(fill) or low<=fill<=high:raise ValueError('Marine profile native quality metadata changed')
        surface=None
        for z in range(6):
            manual=native_window(v,(0,z),1024,1280,1080,1620);library=v[0,z,1024:1280,1080:1620]
            if not np.array_equal(manual.view('u4'),library.view('u4')):raise ValueError('Marine profile raw DEFLATE and HDF5 disagree bitwise')
            if z==0:surface=manual
        rows=np.array([int(np.argmin(abs(lat-y))) for y in np.arange(26.5,5.4,-1)])
        cols=np.array([int(np.argmin(abs(lon-x))) for x in np.arange(-89.5,-45,1)])
        field=surface[np.ix_(rows-1024,cols-1080)]
        values=[None if not np.isfinite(x) or x==fill or x<low or x>high else float(x) for x in field.ravel()]
        metadata={'collection':collection,'CF':'1.6','native_depths_m':depth[:6].tolist(),'published_depth_m':float(depth[0]),'native_values_bitwise_checked':829440,
            'native_fill':fill,range_key:[low,high],'time_units':units,'calendar':'gregorian','time_coordinate':stamp.isoformat(),'temporal_statistic':'instantaneous',
            'production_day_from_filename':day.date().isoformat(),'initialized_at':None,'issued_at':None,'native_axis_rounding_tolerance_degrees':{'lon':2.1e-5,'lat':1.1e-5},
            'sampling':'One exact native1/12-degree center every12steps; 45x22view, Caribbean/tropical northwest Atlantic only. No spatial average or interpolation. Native Float32 coordinates retained.','method':method}
        if variable=='so':metadata.update(native_variable=variable,native_unit=unit,native_unit_long=unit_long)
        return values,lon[cols].tolist(),lat[rows].tolist(),stamp,metadata
