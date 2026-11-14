"""Regenerate the working matrix from the unchanged original catalogue and local evidence."""
import json
from earth_echo.paths import repo_root
from earth_echo.storage.products import all_products,atomic_json

OBS = {1,2,4,5,6,13,15,17,19,21,25,28,34}
SCI = {3,7,9,10,11,12,14,15,16,18,20,22,24,27,28,29,33,35,48}
HISTORY = {1,8,13,23,34,41,47,48}
STATIC = {23,26,30,31,32}
SERVICES = {25,36,37}
DOCS = {38,39,40,42,43,44,45,46}
BLOCKS = {
    **{f'D{i:02}':'Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada' for i in [1,2,3,17]},
    'D33':'NASA/NDMC publica NetCDF y TIFF globales sin cuenta; ejecutar d33-grace-global. No equivale a forecasts CONUS ni a otras colecciones Earthdata.',
    'D08':'ARCO ERA5 público permite una hora estable sin cuenta; ejecutar d08-era5-air-temperature. El cliente CDS y otras colecciones requieren CDSAPI_KEY/licencia y no están implementados por esa vía.', 'D09':'SEAS5 mensual público no comercial mediante Open-Meteo: d09-seas5-monthly. CDSAPI_KEY/licencia siguen necesarios para la ruta CDS, otros centros, miembros e hindcasts; no se confunden distribuciones.',
    'D10':'GloFAS familia v4 rolling público no comercial mediante Open-Meteo: d10-glofas-discharge. EWDSAPI_KEY/licencia para la ruta EWDS, GRIB nativo/ediciones e hindcasts; no se confunden distribuciones.', 'D11':'GWIS WMS público devuelve TIFF Float32, pero ceros de fondo oceánico no se distinguen de FWI=0: sin nodata/máscara científica. WCS no expone ecmwf.fwi y dos recortes nominalmente alineados no coincidieron; ciclo/remuestreo no resuelto. Evidencia real en data/samples/d11-gwis/evidence.json, sin publicar como producto. EWDSAPI_KEY y licencia permiten historia/estacionales CEMS-Fire; no acreditan ese forecast de tiempo real.',
    'D12':'CAMS global público no comercial mediante Open-Meteo: d12-cams-global. Ruta ADS, niveles/variables/ciclo nativo e historia requieren ADSAPI_KEY/licencia; no se confunden distribuciones.', 'D14':'SMOC nativo público por rangos HTTPS, d14-smoc-native: cuatro componentes y dos normas, subconjunto norte occidental. Otras distribuciones Toolbox requieren COPERNICUSMARINE_SERVICE_USERNAME/COPERNICUSMARINE_SERVICE_PASSWORD; no se confunden rutas ni se acredita todavía temperatura/salinidad.',
    'D16':'Resolver archivo numérico de perspectivas, sin inferir datos desde imagen',
    'D18':'Vibrio regional: servicio consultado publica imágenes, sin distribución numérica acreditada. Hipoxia Erie terminó temporada 07/10/2026; no hay forecast vigente conectado',
    'D19':'Resolver capa FAO exportable y términos; Schistocerca gregaria solamente',
    'D20':'Resolver exportación numérica/máscara agrícola; imagen no acredita valor',
    'D23':'WFS respondió HTTP 403; inventario no es precursor',
    'D24':'Resolver versión y archivo numérico LHASA', 'D25':'STAC público verificado con escena Sentinel-2 L2A real; metadatos científicos HTTPS respondieron 401. CDSE_CLIENT_ID/CDSE_CLIENT_SECRET para la ruta OAuth elegida; sin píxeles acreditados',
    'D26':'RGI 7 resuelto por DOI/CMR NSIDC-0770; distribución redirige a Earthdata. EARTHDATA_USERNAME/EARTHDATA_PASSWORD; no hay geometría descargada',
    'D30':'Seleccionar mosaico DSM/datum/licencia', 'D31':'Subconjunto GEBCO y Type Identifier Grid con datum',
    'D32':'Subconjunto y licencia HydroATLAS; no son caudales', 'D34':'Edición RAPID v2024-2 con URL directa pública oficial; ejecutar refresh para descargar. El formulario de correo no es la única distribución; una serie de sección no pronostica colapso',
    'D35':'Resolver productos, geometrias, cancelación y validez', 'D41':'CDSAPI_KEY + licencia GTSM',
    'D47':'Best tracks históricos, versión y agencia pendientes',
}

def main():
    root = repo_root()
    c = json.loads((root/'Earth_Echo_Catalogo.json').read_text(encoding='utf-8'))
    products = all_products()
    matrix = []
    for s in c['sources']:
        n = int(s['id'][1:])
        kinds = [label for ids,label in [(OBS,'Fuente de observaciones'),(SCI,'Pronóstico o producto científico existente'),
            (HISTORY,'Dataset histórico'),(STATIC,'Geometría o contexto estático'),(SERVICES,'Servicio de descubrimiento o visualización'),
            (DOCS,'Documentación, método o referencia científica')] if n in ids]
        evidence = [f'/v1/products/{p.id}' for p in products if p.source_id == s['id']]
        if s['id'] == 'D21': evidence = ['/v1/layers/d21-events']
        if s['id'] == 'D28': evidence = ['/v1/layers/d28-kp','/v1/forecasts/d28-kp']
        service_status=None
        if s['id']=='D36':
            service_status='visualization_only'
            evidence=['apps/web/src/globe/createCesiumGlobe.ts','docs/integraciones/real-hydroatlas-1672x941.jpg']
        if s['id']=='D37':
            service_status='discovery_only'
            evidence=['data/samples/d02-smap/cmr-granule.json','data/samples/d02-smap/retrieval.json']
        connected_products=[p for p in products if p.source_id==s['id']]
        next_step = ' | '.join(dict.fromkeys(p.limitation for p in connected_products)) if connected_products else BLOCKS.get(s['id'],'Consultar producto real; descubrimiento no cuenta como integración')
        if s['id']=='D36':next_step='Base GIBS Blue Marble comprobada como visualización estática; no observación del día ni valores científicos nuevos'
        if s['id']=='D37':next_step='CMR público devolvió metadatos auténticos de SMAP; discovery verificado, HDF científico todavía no descargado'
        matrix.append({'id':s['id'],'name':s['name'],'classification':kinds, 'official_url':s['url'],
            'status':service_status or ('connected_for_scope' if evidence else 'reference_only' if n in DOCS else 'pending'),
            'evidence':evidence,'blocker_or_next_step':next_step,
            'limits':s['limits']})
    (root/'data/operational/integration_matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    text = '# Matriz de integraciones reales\n\nGenerada desde los 48 IDs originales con `python -m earth_echo.tools.integration_report`. Estado y evidencia son del alcance efectivamente descargado, no del proveedor entero. Accesos: [accesos.md](accesos.md).\n\n| ID | Fuente | Clasificación | Estado / evidencia | Bloqueo o siguiente paso |\n| --- | --- | --- | --- | --- |\n'
    for item in matrix:
        evidence = item['status']+': '+', '.join(item['evidence']) if item['evidence'] else item['status']
        text += f"| {item['id']} | {item['name']} | {'; '.join(item['classification'])} | {evidence} | {item['blocker_or_next_step'].replace('|',';')} |\n"
    from earth_echo.catalog.capabilities import capability_matrix
    text+='\n## Capacidades de los 31 fenómenos\n\nObservación puede ser parcial; un dato de contexto no habilita un detector. «specified», «blocked» o «research» no son capacidades operativas. «partial» describe exactamente el alcance indicado en la API.\n\n| ID | Fenómeno | Observación | Indicador | Tendencia | Pronóstico externo | Modelo propio |\n| --- | --- | --- | --- | --- | --- | --- |\n'
    for m in capability_matrix().phenomena:
        statuses={o.kind:o.status for o in m.outputs}
        text+=f"| {m.id} | {m.name} | "+' | '.join(statuses[k] for k in ['observation','indicator','trend','forecast','experimental_model'])+' |\n'
    (root/'docs/integraciones.md').write_text(text,encoding='utf-8')
    overlay_path=root/'data/operational/source_integration.json'
    overlay=json.loads(overlay_path.read_text(encoding='utf-8'))
    for sid in {p.source_id for p in products}:
        own=[p for p in products if p.source_id==sid]
        overlay['sources'][sid]={'integration_status':'connected','sample_kind':'verified_scientific_product','sample_path':'data/real/products/'+own[0].id+'/current.json','credential_variables':[],
            'detail':'; '.join(p.title+' ('+p.coverage+')' for p in own)}
    if (root/'data/real/feeds/d21-events.json').exists():
        overlay['sources']['D21']={'integration_status':'connected','sample_kind':'retained_live_feed','sample_path':'data/real/feeds/d21-events.json','credential_variables':[],
            'detail':'USGS FDSN con ventana, umbral y máximo configurables; query original, UTC, magnitud/revisión y datos retenidos. La capa /v1/layers/d21-events consulta el archivo actualizado, no la muestra inicial de 20 eventos. No probabilidades de réplica.'}
    if (root/'data/real/feeds/d28-kp.json').exists():
        overlay['sources']['D28']={'integration_status':'connected','sample_kind':'retained_observation_and_forecast','sample_path':'data/real/feeds/d28-kp.json','credential_variables':[],
            'detail':'Kp planetario observado y forecast SWPC de filas predicted, actualización separada de observación/validez. Emisión e inicialización no proporcionadas quedan null; recuperación no las sustituye. Sin intensidad local ni validación de modelo propio.'}
    atomic_json(overlay_path,overlay)

if __name__ == '__main__':
    main()
