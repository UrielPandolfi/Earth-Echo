"""NCEI provisional/best tracks, not an archive of issued forecasts."""
import csv
import hashlib
import io
import math
from datetime import datetime,timedelta,timezone
import numpy as np
from netCDF4 import Dataset,chartostring
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ProductSample,ProductTrack,Verification
from earth_echo.science.paths import split_dateline,path_extent
from earth_echo.storage.products import publish

BASE='https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/'
URL=BASE+'netcdf/IBTrACS.last3years.v04r01.nc'
CHECK_URL=BASE+'csv/ibtracs.ACTIVE.list.v04r01.csv'
AVERAGING={'hurdat_atl':'1 min','hurdat_epa':'1 min','atcf':'1 min','tokyo':'10 min','newdelhi':'3 min','reunion':'10 min','bom':'10 min','nadi':'10 min','wellington':'10 min'}

def number(value):
    return None if np.ma.is_masked(value) or not math.isfinite(float(value)) else float(value)

def decode_tracks(raw: bytes, now: datetime):
    samples=[];tracks=[]
    with Dataset('ibtracs',memory=raw) as ds:
        if not all(ds[k].units==u for k,u in [('lat','degrees_north'),('lon','degrees_east'),('wmo_wind','kts'),('wmo_pres','mb')]):
            raise ValueError('Unknown IBTrACS units')
        if 'version v04r01' not in ds.title: raise ValueError('Unknown IBTrACS version')
        ids=chartostring(ds['sid'][:]);names=chartostring(ds['name'][:]);types=chartostring(ds['track_type'][:])
        times=chartostring(ds['iso_time'][:]);agencies=chartostring(ds['wmo_agency'][:]);flags=chartostring(ds['iflag'][:]);nature=chartostring(ds['nature'][:])
        cutoff=now-timedelta(days=30)
        for index,sid in enumerate(ids):
            valid=[(j,datetime.fromisoformat(str(t)).replace(tzinfo=timezone.utc)) for j,t in enumerate(times[index]) if str(t).strip()]
            if not valid or max(t for _,t in valid)<cutoff: continue
            if len(tracks)>=30: raise ValueError('Recent IBTrACS track budget exceeded')
            own=[];segments=[];segment=[]
            for j,time in valid:
                if time>now: raise ValueError('Historical position lies in the future')
                lat,native_lon=number(ds['lat'][index,j]),number(ds['lon'][index,j])
                lon=None if native_lon is None else (native_lon+180)%360-180
                wind,pressure=number(ds['wmo_wind'][index,j]),number(ds['wmo_pres'][index,j])
                agency=str(agencies[index,j]).strip()
                sample=ProductSample(id=f'{sid}-{time:%Y%m%dT%H%M%SZ}',time=time,latitude=lat,longitude=lon,value=wind,
                    quality=f'{types[index]}; IFLAG={flags[index,j]}; viento ausente' if wind is None else f'{types[index]}; IFLAG={flags[index,j]}',
                    attributes={'SID':str(sid),'nombre':str(names[index]),'longitud_nativa':None if native_lon is None else str(native_lon),'WMO_AGENCY':agency or None,'promedio_viento':AVERAGING.get(agency.lower(),'No determinado; no se armonizan períodos'),
                        'presion_mb':None if pressure is None else str(pressure),'TRACK_TYPE':str(types[index]),'NATURE':str(nature[index,j]),'IFLAG':str(flags[index,j])})
                samples.append(sample);own.append(sample)
                if lat is None or lon is None:
                    if len(segment)>1: segments.extend(split_dateline(segment).coordinates)
                    segment=[]
                else: segment.append([lon,lat])
            if len(segment)>1: segments.extend(split_dateline(segment).coordinates)
            positions=[[s.longitude,s.latitude] for s in own if s.longitude is not None and s.latitude is not None]
            if len(positions)>1 and segments:
                tracks.append(ProductTrack(id=str(sid),name=str(names[index]),geometry={'type':'MultiLineString','coordinates':segments},extent=path_extent(positions),
                    sample_ids=[s.id for s in own],quality=f'{types[index]}; las líneas unen centros publicados. Cortes al antimeridiano interpolados solo para dibujo; no se agregan observaciones.'))
        if len(samples)>8000: raise ValueError('Recent IBTrACS sample budget exceeded')
    return samples,tracks

def check_csv(samples,raw):
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not rows or rows[0]['LAT']!='degrees_north' or rows[0]['WMO_WIND']!='kts': raise ValueError('Unknown CSV units')
    lookup={(s.attributes['SID'],s.time.strftime('%Y-%m-%d %H:%M:%S')):s for s in samples}
    count=0
    for row in rows[1:]:
        sample=lookup.get((row['SID'],row['ISO_TIME']))
        if sample is None: raise ValueError('CSV/NetCDF editions disagree on active positions')
        for column,value in [('LAT',sample.latitude),('LON',sample.longitude),('WMO_WIND',sample.value)]:
            original=None if not row[column].strip() else float(row[column])
            if column=='LON' and original is not None: original=(original+180)%360-180
            if (value is None)!=(original is None) or value is not None and not math.isclose(value,original,abs_tol=.00011):
                raise ValueError(f'Independent CSV disagrees on {sample.id}/{column}')
        if sample.attributes['WMO_AGENCY']!=(row['WMO_AGENCY'].strip() or None): raise ValueError('WMO agency differs')
        count+=1
    return count

def fetch_ibtracs(now: datetime) -> str:
    raw,_=download(URL,max_bytes=3_000_000)
    samples,tracks=decode_tracks(raw,now)
    check,_=download(CHECK_URL,max_bytes=500_000);checked=check_csv(samples,check)
    if not tracks or not checked: raise ValueError('No recent track can be independently verified')
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d47-cyclone-tracks',source_id='D47',title='Ciclones · trayectorias recientes IBTrACS',collection_id='IBTrACS.last3years',product_version='v04r01',variable='wmo_maximum_sustained_wind',
        unit='kt (período según agencia)',native_unit='kts',kind='historical',representation='tracks',observed_at=min(s.time for s in samples),observation_end=max(s.time for s in samples),
        retrieved_at=now,ingested_at=now,original_url=URL,license_url='https://www.ncei.noaa.gov/products/international-best-track-archive',attribution='NOAA NCEI IBTrACS y agencias WMO originales',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd47-cyclone-tracks/assets/{sha}.nc',coverage=f'{len(tracks)} trayectorias de sistemas con última posición en los últimos 30 días, sin recorte por cuenca. Original conserva tres años; no es cobertura exhaustiva.',
        cadence_seconds=86400,method_version='ibtracs-native-recent-tracks-v1',limitation='Historia compilada, incluida posición provisional. No es trayectoria futura ni archivo de pronósticos emitidos. Viento WMO en nudos sin armonizar promedios 1/3/10 minutos; cada registro conserva agencia, IFLAG, tipo y presión mb. Faltantes nativos siguen null. Se dibujan centros publicados, con cortes de visualización al antimeridiano; sin inventar observaciones en los bordes.',
        samples=samples,tracks=tracks,verification=Verification(method='Posición, viento, agencia y faltantes de todos los registros ACTIVE cotejados entre NetCDF y CSV independientes de NCEI',original_url=CHECK_URL,checked_at=now,expected=f'{checked} registros CSV',actual=f'{checked} coincidencias NetCDF',passed=True)),raw,'.nc')
