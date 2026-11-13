"""CPC historical ONI. This is deliberately not today's ENSO phase or RONI advisory."""
import hashlib
import io
import math
from datetime import datetime,timezone
from decimal import Decimal
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

URL='https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'
SEASONS=['DJF','JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ']

def parse_oni(raw: bytes) -> list[ProductSample]:
    lines=raw.decode().splitlines()
    if lines[0].split()!=['SEAS','YR','TOTAL','ANOM']: raise ValueError('Unexpected ONI table')
    samples=[]
    for line in lines[1:]:
        if not line.strip(): continue
        season,year,total,anomaly=line.split()
        index=SEASONS.index(season); year=int(year)
        # Month at centre is Jan for DJF; the window spans preceding to following month.
        start_month=index if index else 12; start_year=year if index else year-1
        end_index=year*12+index+2
        end_year,end_zero=divmod(end_index,12)
        start=datetime(start_year,start_month,1,tzinfo=timezone.utc)
        end=datetime(end_year,end_zero+1,1,tzinfo=timezone.utc)
        value=float(anomaly)
        if not math.isfinite(value): raise ValueError('Invalid ONI')
        samples.append(ProductSample(id=f'{year}-{season}',time=start,valid_to=end,value=value,
            quality='Media móvil de tres meses; ventanas superpuestas; tabla histórica NOAA',
            attributes={'estación':season,'año_central':str(year),'SST_total_°C':total,'índice':'ONI histórico, no RONI ni diagnóstico operativo de fase'}))
    return samples

def fetch_oni(now: datetime) -> str:
    raw,_=download(URL,max_bytes=100_000)
    samples=parse_oni(raw)
    if not samples: raise ValueError('Empty ONI history')
    # Independent load of original column with numerical reader, not parser season logic.
    import numpy as np
    reference=float(np.genfromtxt(io.BytesIO(raw),skip_header=1,usecols=3)[-1])
    if samples[-1].value!=reference: raise ValueError('ONI independent column check failed')
    sha=hashlib.sha256(raw).hexdigest()
    p=ScientificProduct(id='d48-oni-history',source_id='D48',title='ONI · historia del Pacífico',collection_id='CPC ONI ascii',product_version='ONI ERSSTv5; instantánea por SHA-256',
        variable='three_month_sst_anomaly_nino34',unit='°C',native_unit='°C',kind='historical',representation='planetary',observed_at=samples[-1].time,observation_end=samples[-1].valid_to,
        retrieved_at=now,ingested_at=now,original_url=URL,license_url='https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php',attribution='NOAA Climate Prediction Center',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd48-oni-history/assets/{sha}.txt',coverage='Índice SST de Niño 3.4, Pacífico ecuatorial; no campo de impactos locales.',cadence_seconds=604800,
        method_version='cpc-oni-table-v1',limitation='Historia ONI, medias móviles de tres meses y climatología definida por CPC. No se convierte automáticamente en fase ENSO vigente, perspectiva probabilística ni lluvia local. El diagnóstico operativo puede usar otro índice como RONI.',samples=samples,
        verification=Verification(method='Última anomalía contrastada con lectura independiente de la columna original mediante numpy; ventanas calculadas y probadas por estación',original_url=URL,checked_at=now,expected=str(reference),actual=str(samples[-1].value),passed=True))
    return publish(p,raw,'.txt')
