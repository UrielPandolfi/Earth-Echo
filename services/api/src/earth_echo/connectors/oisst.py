"""One recent original daily OISST file (about 1.5 MB), with native data preserved."""
import hashlib
import math
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import netCDF4
import numpy as np
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificGrid, ScientificProduct, Verification
from earth_echo.storage.products import publish

BASE='https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/'

def fetch_oisst(now: datetime) -> str:
    reference = now-timedelta(days=1)
    listing_url=BASE+reference.strftime('%Y%m/')
    listing,_=download(listing_url,max_bytes=100_000)
    files = sorted(set(re.findall(r'oisst-avhrr-v02r01\.(\d{8})(_preliminary)?\.nc',listing.decode())))
    files = [f for f in files if datetime.strptime(f[0],'%Y%m%d').replace(tzinfo=timezone.utc) <= reference]
    if not files: raise ValueError('No recent OISST daily file in official listing')
    date,provisional=files[-1]
    name=f'oisst-avhrr-v02r01.{date}{provisional}.nc'
    url=listing_url+name
    raw,_=download(url,max_bytes=3_000_000)
    with netCDF4.Dataset('oisst.nc',memory=raw) as ds:
        sst=ds.variables['sst']
        if sst.units!='Celsius' or sst.shape!=(1,1,720,1440): raise ValueError('Unexpected OISST units or grid')
        times=ds.variables['time']
        t=netCDF4.num2date(times[0],times.units,only_use_cftime_datetimes=False)
        observed=datetime(t.year,t.month,t.day,t.hour,t.minute,t.second,tzinfo=timezone.utc)
        if observed.strftime('%Y%m%d') != date: raise ValueError('OISST date disagrees with independent listing')
        lats_native=np.asarray(ds.variables['lat'][:]); lons_native=np.asarray(ds.variables['lon'][:])
        rows=list(range(2,720,4))[::-1]
        columns=sorted(range(2,1440,4),key=lambda c:(float(lons_native[c])+180)%360-180)
        # Decode at scientific native resolution. Preserve err/ice/anom in retained original.
        native=sst[0,0,:,:]
        values=[None if np.ma.is_masked(native[r,c]) else float(native[r,c]) for r in rows for c in columns]
        lats=[float(lats_native[r]) for r in rows]; lons=[(float(lons_native[c])+180)%360-180 for c in columns]
        index=next(i for i,v in enumerate(values) if v is not None)
        r,c=rows[index//360],columns[index%360]
        scale,offset=float(sst.scale_factor),float(sst.add_offset)
        sst.set_auto_maskandscale(False)
        encoded=int(sst[0,0,r,c])
        expected=float(Decimal(str(encoded))*Decimal(str(scale))+Decimal(str(offset)))
        actual=values[index]
        if not math.isclose(expected,actual,abs_tol=2e-5): raise ValueError('OISST automatic scaling disagrees with encoded short')
        version=str(getattr(ds,'version','v2.1'))+(' preliminary' if provisional else ' final')
        present=[v for v in values if v is not None]
        dx=lons[1]-lons[0]; dy=lats[0]-lats[1]
        grid=ScientificGrid(width=360,height=180,west=max(-180,lons[0]-dx/2),east=min(180,lons[-1]+dx/2),
            south=max(-90,lats[-1]-dy/2),north=min(90,lats[0]+dy/2),longitudes=lons,latitudes=lats,values=values,
            minimum=min(present),maximum=max(present),missing_cells=values.count(None),resolution='Nativa 0,25°; visualización 1°',
            sampling='Cada cuarto centro nativo, sin promedio de área; longitud 0–360 normalizada a -180–180 y filas norte→sur. El NetCDF conserva SST/anomalía/error/hielo a resolución nativa.',
            quality_mask='Relleno y valid_range del short nativo; tierra transparente. Se conserva el campo de error de interpolación en el original; zonas de hielo pueden usar SST proxy, según NOAA.')
    sha=hashlib.sha256(raw).hexdigest()
    p=ScientificProduct(id='d13-oisst-global',source_id='D13',title='SST · OISST mundial',collection_id='NOAA OISST AVHRR v2.1',product_version=version,
        variable='sst',unit='°C',native_unit='Celsius (short escalado)',kind='observation',representation='field',observed_at=observed,
        retrieved_at=now,ingested_at=now,original_url=url,license_url='https://www.ncei.noaa.gov/products/optimum-interpolation-sst',attribution='NOAA/NCEI OISST',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd13-oisst-global/assets/{sha}.nc',coverage='Océanos mundiales; tierra ausente; extensión exacta en grid.',cadence_seconds=86400,
        method_version='oisst-native-stride-v1',limitation='SST analizada e interpolada, preliminar cuando así lo identifica NOAA. No es temperatura del aire, un evento de calor marino ni diagnóstico ENSO.',grid=grid,
        verification=Verification(method=f'Fecha contra listado oficial; short[{r},{c}]={encoded} y escala decimal contra decodificación automática NetCDF4',original_url=listing_url,
            checked_at=now,expected=str(expected),actual=str(actual),passed=True))
    return publish(p,raw,'.nc')
