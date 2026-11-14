"""Derive fields from retained IFS assets; never download them again per phenomenon."""
import hashlib
import math
from datetime import datetime
from decimal import Decimal,localcontext
import eccodes as ec
from earth_echo.contracts.products import ScientificProduct,ScientificCalculation,CalculationInput,Verification
from earth_echo.science.meteorology import wind_speed,vapour_pressure_deficit,relative_humidity
from earth_echo.storage.products import read_product,products_root,publish

FAO='https://www.fao.org/4/x0490e/x0490e07.htm'

def derive_ifs_fields(now: datetime):
    results=[]
    for name,parameters,function,unit,title,formula in [
        ('wind10',('10u','10v'),wind_speed,'m/s','Rapidez del viento a 10 m','sqrt(u10² + v10²)'),
        ('vpd',('2t','2d'),vapour_pressure_deficit,'kPa','Déficit de presión de vapor a 2 m','e_s(T)-e_s(Td); e_s(x)=0.6108*exp(17.27*x/(x+237.3)), x en °C'),
        ('rh',('2t','2d'),relative_humidity,'%','Humedad relativa del aire a 2 m','100*e_s(Td)/e_s(T); e_s(x)=0.6108*exp(17.27*x/(x+237.3)), x en °C'),
    ]:
        inputs=[read_product(f'd07-ifs-{param}-24h') for param in parameters]
        if any(p is None or p.grid is None for p in inputs): raise ValueError('Retained IFS inputs unavailable; no synthetic field')
        first,second=inputs
        if first.initialized_at!=second.initialized_at or first.valid_from!=second.valid_from or first.grid.longitudes!=second.grid.longitudes or first.grid.latitudes!=second.grid.latitudes:
            raise ValueError('IFS cycle, validity or coordinates do not align')
        if (first.unit,second.unit)!=(('m/s','m/s') if name=='wind10' else ('°C','°C')): raise ValueError('Unexpected derived-field input units')
        values=[function(a,b) for a,b in zip(first.grid.values,second.grid.values,strict=True)]
        present=[v for v in values if v is not None]
        if not present: raise ValueError('No cell lies within method applicability')
        index=next(i for i,v in enumerate(values) if v is not None)
        lat=first.grid.latitudes[index//first.grid.width];lon=first.grid.longitudes[index%first.grid.width]
        originals=[];native=[]
        for p in inputs:
            raw=(products_root()/p.raw_file).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=p.checksum_sha256: raise ValueError('Retained input checksum differs')
            originals.append(raw);handle=ec.codes_new_from_message(raw)
            try: native.append(ec.codes_grib_find_nearest(handle,lat,lon)[0]['value'])
            finally:ec.codes_release(handle)
        if name=='wind10':expected=math.sqrt(native[0]**2+native[1]**2)
        else:
            with localcontext() as ctx:
                ctx.prec=40
                t,td=[Decimal(str(v))-Decimal('273.15') for v in native]
                def pressure(x):return Decimal('.6108')*(Decimal('17.27')*x/(x+Decimal('237.3'))).exp()
                expected=float(100*pressure(td)/pressure(t) if name=='rh' else pressure(t)-pressure(td))
        if not math.isclose(expected,values[index],rel_tol=1e-9,abs_tol=1e-8): raise ValueError('Independent native calculation disagrees')
        grid=first.grid.model_copy(update={'values':values,'minimum':min(present),'maximum':max(present),'missing_cells':values.count(None),
            'sampling':'Cálculo por centro muestreado de los campos IFS de 1°, ejes/ciclo/plazo idénticos; sin interpolar entradas ausentes. El GRIB conservado contiene ambos mensajes nativos completos.',
            'quality_mask':'Faltante si falta cualquier componente.'+(' RH se define aquí solo sobre agua líquida con 0 ≤ Td ≤ T ≤ 50 °C; hielo/supersaturación/fuera del dominio permanecen ausentes, sin recorte a 0/100%.' if name=='rh' else ' VPD se define aquí solo con 0 ≤ Td ≤ T ≤ 50 °C; hielo/supersaturación/fuera del dominio permanecen ausentes, sin recorte a cero.' if name=='vpd' else '')})
        raw=b''.join(originals);sha=hashlib.sha256(raw).hexdigest();key=f'd07-ifs-{name}-24h'
        calculation=ScientificCalculation(method_version=f'ifs-{name}-v1',formula=formula,
            parameters={'a_kPa':.6108,'b':17.27,'c_degC':237.3,'minimum_degC':0,'maximum_degC':50,**({'percentage_factor':100} if name=='rh' else {})} if name!='wind10' else {},
            inputs=[CalculationInput(product_id=p.id,variable=p.variable,unit=p.unit,checksum_sha256=p.checksum_sha256) for p in inputs],reference_url=FAO if name!='wind10' else 'https://codes.ecmwf.int/grib/param-db/207',
            reference_period='Instante de validez +24 h de IFS; sin climatología ni período de anomalía. No es media diaria de RH.' if name=='rh' else 'Instante de validez +24 h de IFS; sin climatología ni período de anomalía. No es media diaria de VPD.',
            applicability='Magnitud de vector horizontal a 10 m.' if name=='wind10' else 'Ecuaciones 10/11/14 de FAO-56: razón de vapor real/saturación sobre agua líquida, expresada como porcentaje. Dominio conservador 0–50 °C, Td≤T; no se extrapola a hielo o humedad del suelo.' if name=='rh' else 'Ecuaciones 11/14 de FAO-56 para saturación sobre agua líquida. Dominio conservador de implementación 0–50 °C, Td≤T; no se extrapola a hielo ni a demanda/estrés del cultivo.')
        product=ScientificProduct(id=key,source_id='D07',title=title+' · IFS +24 h · calculado',collection_id='IFS oper fc 0p25 / Earth Echo derived field',product_version=first.product_version,
            variable='wind_speed_10m' if name=='wind10' else 'relative_humidity_2m' if name=='rh' else 'vapour_pressure_deficit_2m',unit=unit,native_unit='m/s (u10,v10)' if name=='wind10' else 'K (T2m,Td2m), convertidos a °C con función probada',kind='forecast',representation='field',
            initialized_at=first.initialized_at,issued_at=None,issue_time_basis=first.issue_time_basis,valid_from=first.valid_from,valid_to=first.valid_to,retrieved_at=min(p.retrieved_at for p in inputs),ingested_at=now,
            original_url=first.original_url,license_url=first.license_url,attribution='ECMWF IFS Open Data · cálculo físico Earth Echo, no producto oficial nuevo ni modelo entrenado',checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.grib2',
            coverage='Malla IFS mundial de visualización 1°; '+('solo centros dentro del dominio líquido conservador del método RH.' if name=='rh' else 'solo centros dentro del dominio líquido conservador del método VPD.' if name=='vpd' else 'máscara conjunta de componentes nativas.'),cadence_seconds=43200,method_version=calculation.method_version,
            limitation='Variable física derivada de un pronóstico externo; no detector ni probabilidad de tormenta, granizo, ignición o sequía. '+('Humedad relativa del aire a 2 m, instantánea y respecto a agua líquida; no humedad del suelo/combustible, FWI, estrés agrícola o probabilidad. Dominio 0 ≤ Td ≤ T ≤ 50 °C; huecos por hielo/supersaturación no se rellenan ni recortan. Comparte el original T/Td de VPD, sin nueva descarga.' if name=='rh' else 'VPD es instantáneo sobre agua líquida en el dominio declarado; no evapotranspiración, humedad del suelo o estrés agrícola confirmado.' if name=='vpd' else 'Rapidez a 10 m, sin ráfaga máxima, cizalladura vertical ni umbral de impacto.'),
            grid=grid,calculation=calculation,verification=Verification(method='Componentes consultadas por coordenada desde los GRIB nativos retenidos; '+('norma sqrt independiente de hypot' if name=='wind10' else 'aritmética Decimal de 40 dígitos independiente del cálculo float'),original_url=first.original_url,checked_at=now,expected=str(expected),actual=str(values[index]),passed=True))
        results.append(publish(product,raw,'.grib2'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
