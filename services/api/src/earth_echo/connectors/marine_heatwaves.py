"""NOAA PSL NMME monthly MHW probabilities from one retained, bounded cycle."""
import hashlib
import math
import struct
from datetime import datetime,timedelta,timezone
import h5py
import numpy as np
from earth_echo.connectors.ranges import RangeSource
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish

URL='https://downloads.psl.noaa.gov/Datasets/marinehw/NMME_prob90_latest.nc'

def month_window(initial: datetime, lead: float):
    offset=round(lead-.5)
    if not math.isclose(lead,offset+.5): raise ValueError('Unknown monthly lead convention')
    absolute=initial.year*12+initial.month-1+offset
    year,zero=divmod(absolute,12); next_year,next_zero=divmod(absolute+1,12)
    return datetime(year,zero+1,1,tzinfo=timezone.utc),datetime(next_year,next_zero+1,1,tzinfo=timezone.utc)

def fetch_mhw(now: datetime, source=None) -> str:
    source=source or RangeSource(URL,max_requests=60)
    products=[]
    with source.open() as stream,h5py.File(stream,'r') as ds:
        time=ds['start_time']; leads=ds['lead_time'][:]; data=ds['mhw_probability']
        if bytes(time.attrs['units']).decode()!='days since 2021-01-01 00:00:00' or data.shape[:3]!=(12,181,360):
            raise ValueError('Unknown MHW coordinates or time origin')
        initial=datetime(2021,1,1,tzinfo=timezone.utc)+timedelta(days=int(time[-1]))
        time_index=data.shape[3]-1
        lats_native=ds['lat'][:];lons_native=ds['lon'][:]
        rows=sorted(range(1,len(lats_native)-1),key=lambda r:float(lats_native[r]),reverse=True) # masked poles omitted
        cols=sorted(range(len(lons_native)),key=lambda c:(float(lons_native[c])+180)%360-180)
        lats=[float(lats_native[r]) for r in rows];lons=[(float(lons_native[c])+180)%360-180 for c in cols]
        candidates=[i for i,lead in enumerate(leads) if month_window(initial,float(lead))[1]>now][:3]
        if not candidates: raise ValueError('No unexpired monthly MHW forecast')
        for slot,lead_index in enumerate(candidates,1):
            native=data[lead_index,:,:,time_index]
            values=[None if not math.isfinite(float(native[r,c])) else float(native[r,c]) for r in rows for c in cols]
            present=[v for v in values if v is not None]
            if not present or min(present)<0 or max(present)>1: raise ValueError('MHW probabilities are not fractions in [0,1]')
            index=next(i for i,v in enumerate(values) if v is not None and 0<v<1)
            r,c=rows[index//len(cols)],cols[index%len(cols)]
            # Independent numeric decoder of the actual uncompressed HDF5 chunk bytes.
            if data.compression is not None or data.dtype.itemsize!=4: raise ValueError('Unknown HDF5 numeric encoding')
            chunk=data.id.get_chunk_info_by_coord((lead_index,r,c,time_index))
            local=np.ravel_multi_index((lead_index%data.chunks[0],r%data.chunks[1],c%data.chunks[2],0),data.chunks)
            encoded=source.read_at(chunk.byte_offset+int(local)*4,4)
            expected=struct.unpack('<f' if data.dtype.byteorder in {'<','='} else '>f',encoded)[0]
            if expected!=values[index]: raise ValueError('MHW native chunk check disagrees with HDF5 decoder')
            start,end=month_window(initial,float(leads[lead_index]))
            grid=ScientificGrid(width=len(cols),height=len(rows),west=max(-180,lons[0]-.5),east=min(180,lons[-1]+.5),south=lats[-1]-.5,north=lats[0]+.5,
                longitudes=lons,latitudes=lats,values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),
                resolution='NMME, malla de 1° mensual; polos enmascarados excluidos',sampling='Valores mensuales nativos; longitud normalizada a -180–180, filas norte→sur. Sin convertir celdas en eventos.',
                quality_mask='NaN del proveedor como faltante (tierra/hielo/sin salida). Cero es probabilidad publicada válida, no ausencia.')
            products.append((slot,start,end,float(leads[lead_index]),grid,expected,values[index]))
        models=bytes(ds.attrs['model_use']).decode()
        metadata={'variable':'mhw_probability','start_time_index':time_index,'initialized_at':initial.isoformat(),'leads':[p[3] for p in products],
            'models':models,'shape':list(data.shape),'chunks':list(data.chunks),'definition_url':'https://psl.noaa.gov/marine-heatwaves/'}
    raw=source.archive(metadata);sha=hashlib.sha256(raw).hexdigest()
    total=sum(len(b) for b in source.cache.values())
    results=[]
    for slot,start,end,lead,grid,expected,actual in products:
        key=f'd16-mhw-month-{slot}'
        p=ScientificProduct(id=key,source_id='D16',title=f'MHW · NMME {start:%Y-%m}',collection_id='NOAA PSL NMME_prob90_latest (with trend)',
            product_version=f'cycle={initial:%Y-%m}; ETag={source.etag}',variable='mhw_probability',unit='1 (probabilidad definida)',native_unit='fracción [0,1]',kind='forecast',representation='field',
            initialized_at=initial,issued_at=None,issue_time_basis='start_time define inicialización mensual; publicación no codificada; HTTP Last-Modified no se sustituye por emisión.',valid_from=start,valid_to=end,
            retrieved_at=now,ingested_at=now,original_url=URL,license_url='https://psl.noaa.gov/marine-heatwaves/',attribution='NOAA Physical Sciences Laboratory / NMME',
            checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.json',coverage='Océanos de la malla NMME de ~1°, con máscara; la habilidad cambia por región y plazo.',cadence_seconds=86400,
            method_version='psl-nmme-range-cycle-v1',
            limitation=f'Producto externo experimental de investigación. Probabilidad mensual de SST sobre umbral estacional percentil 90 de 1991–2020, con tendencia retenida; lead={lead} meses (centro del mes). Modelos: {models}. No representa un evento diario Hobday ni una probabilidad de daño biológico. {total} bytes retenidos en {len(source.cache)} rangos de un archivo de {source.size}; no se descargó toda la historia.',grid=grid,
            verification=Verification(method='Valor HDF5 cotejado con lectura numérica independiente struct.unpack de los bytes del chunk original; ejes y origen temporal verificados',original_url=URL,
                checked_at=now,expected=str(expected),actual=str(actual),passed=True))
        results.append(publish(p,raw,'.json'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
