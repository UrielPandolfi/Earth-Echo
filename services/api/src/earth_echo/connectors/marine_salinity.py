"""Native CMEMS practical salinity; preserve1e-3, no mass-fraction conversion."""
from datetime import datetime,timedelta,timezone
import hashlib
import io
import json
import zipfile
from earth_echo.connectors.marine_currents import ROOT,DOC,LICENSE,UsedRanges
from earth_echo.connectors.marine_profiles import decode_profile
from earth_echo.connectors.ranges import RangeSource,ArchivedRangeSource
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish,read_product,products_root

COLLECTION='cmems_mod_glo_phy-so_anfc_0.083deg_PT6H-i_202406'
METHOD='cmems-native-so-caribbean-atlantic-1deg-v1'
ID='d14-so-surface'


def scientific_url(day):
    valid=day+timedelta(days=1)
    return ROOT+COLLECTION+f'/{valid:%Y/%m}/glo12_rg_6h-i_{valid:%Y%m%d}-00h_3D-so_fcst_R{day:%Y%m%d}.nc'


def decode(source,day):
    return decode_profile(source,day,expected_url=scientific_url(day),collection=COLLECTION,method=METHOD,variable='so')


def product_from_ranges(range_bytes,day,retrieved_at,now):
    source=UsedRanges(range_bytes)
    values,lons,lats,stamp,metadata=decode(source,day)
    source.cache={k:source.cache[k] for k in sorted(source.used)}
    native=source.archive(metadata)
    raw=pack_files({'so.ranges.json':native},{'schema_version':'1','method':METHOD,'native_metadata':metadata,'assets':{'so.ranges.json':{
        'url':source.url,'etag':source.etag,'last_modified':source.modified,'original_object_bytes':source.size,'retained_range_bytes':sum(map(len,source.cache.values())),
        'range_blocks':len(source.cache),'sha256':hashlib.sha256(native).hexdigest()}}},compression=zipfile.ZIP_DEFLATED)
    sha=hashlib.sha256(raw).hexdigest();present=[v for v in values if v is not None]
    product=ScientificProduct(id=ID,source_id='D14',title='Salinidad práctica marina · 0,494025m · Caribe/Atlántico',
        collection_id='GLOBAL_ANALYSISFORECAST_PHY_001_024 / '+COLLECTION,product_version=f'edition202406 / filename R{day:%Y%m%d} / ETag{source.etag} / CF1.6',
        variable='so / sea_water_salinity',unit='1e-3',native_unit='1e-3; unit_long Practical Salinity Unit; Float32 sin escala/offset',kind='forecast',representation='field',
        initialized_at=None,issued_at=None,observed_at=None,valid_from=stamp,valid_to=None,retrieved_at=retrieved_at,ingested_at=now,
        issue_time_basis='Campo instantáneo según título nativo; area:mean es promedio espacial. CF horas desde1950-01-01/gregorian, UTC predeterminado, coincide con nombre y decodificación independiente. R es día de producción, sin hora de inicialización/emisión acreditada: null. Last-Modified es modificación de distribución.',
        original_url=DOC,license_url=LICENSE,attribution='E.U. Copernicus Marine Service Information (CMEMS), Mercator Ocean; MERCATOR GLO12. Subconjunto nativo por rangos y selección de centros por Earth Echo.',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',scientific_checksum_sha256=hashlib.sha256(json.dumps({'etag':source.etag,'url':source.url,'values':values,'metadata':metadata},sort_keys=True).encode()).hexdigest(),
        coverage='Caribe y Atlántico tropical noroccidental, límites de vista5–27°N/90–45°O,45×22centros. Un instante previsto en primera capa0,494025m; no cobertura mundial o perfil vertical publicado.',cadence_seconds=86400,method_version=METHOD,
        grid=ScientificGrid(width=45,height=22,west=-90,east=-45,south=5,north=27,longitudes=lons,latitudes=lats,values=values,minimum=min(present) if present else None,maximum=max(present) if present else None,missing_cells=values.count(None),
            resolution='Nativo1/12°; vista1° (45×22centros)',sampling=metadata['sampling'],quality_mask='Relleno nativo9.969209968386869e36/no finito/fuera de valid_min0…valid_max50→missing transparente. Salinidad cero dentro de rango es válida, sin flags adicionales. No se conserva extremo entre centros.'),
        verification=Verification(method='829.440Float32/seis profundidades de un chunk cotejados bit a bit HDF5/h5py frente a chunks crudos zlib. Ejes1/12° con tolerancia de redondeo Float32≤2,1e−5°; CF1950/gregorian cotejado timedelta/netCDF4. Definición/unit_long/unidad/rango/profundidad conservados, sin conversión de salinidad.',original_url=source.url,checked_at=now,
            expected='6×256×540Float32 bitwise; sea_water_salinity, units1e-3/Practical Salinity Unit, profundidad0,494025m',actual=f'829440Float32 coincidentes; {len(present)} centros visibles válidos/{len(values)}; {stamp.isoformat()}',passed=True),
        limitation='Pronóstico físico de salinidad práctica según unit_long nativo, unidad CF1e-3 y valores originales sin multiplicar por0,001 o1000. No se convierte a salinidad absoluta g/kg, masa de sales, densidad o concentración de oxígeno. Primera capa modelada0,494025m, no medición de muestra. Un instante/sector; seis profundidades retenidas y comprobadas, sólo primera publicada. Sin tendencia, anomalía, estratificación de toda la columna, Vibrio, hipoxia, toxicidad, HAB o AMOC inferidos. Máscara de soporte no acredita calidad local; vista1° no conserva extremos entre centros. Inicialización/emisión null, ETag multipart no es SHA del objeto3D completo.')
    return product,raw


def fetch_marine_salinity(now):
    if now.tzinfo is None:raise ValueError('Marine salinity requires aware UTC timestamp')
    now=now.astimezone(timezone.utc)
    day=now.replace(hour=0,minute=0,second=0,microsecond=0)-(timedelta(days=1) if now.hour<12 else timedelta())
    source=RangeSource(scientific_url(day),max_bytes=8_388_608,max_requests=64,deadline_seconds=120)
    current=read_product(ID,products_root());retrieved_at=now
    if current:
        raw=(products_root()/current.raw_file).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=current.checksum_sha256:raise ValueError('Marine salinity archive checksum changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:previous=ArchivedRangeSource(archive.read('so.ranges.json'))
        if (previous.url,previous.size,previous.etag)==(source.url,source.size,source.etag):source.cache.update(previous.cache);retrieved_at=current.retrieved_at
    decode(source,day)
    product,raw=product_from_ranges(source.archive({}),day,retrieved_at,now)
    return publish(product,raw,'.zip')
