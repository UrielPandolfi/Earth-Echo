# Accesos del catálogo

Comprobación local: 13 de noviembre de 2026. No se encontraron credenciales configuradas. Los secretos van exclusivamente en `.env` de la raíz (ignorado por Git), o en las variables de entorno del proceso servidor. Copiar `.env.example` a `.env`, completar localmente y reiniciar API/worker. Nunca usar `VITE_` ni enviar claves al chat.

| Proveedor / fuentes | Cuenta o permiso | Variables del servidor | Desbloquea |
| --- | --- | --- | --- |
| [NASA Earthdata](https://urs.earthdata.nasa.gov/users/new), D01–D05, D17, D33 | Registro gratuito y autorización de la aplicación DAAC correspondiente en Earthdata; SMAP/GES DISC/LAADS/OB.DAAC son distribuciones distintas | `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD`; alternativamente `.netrc` local para clientes compatibles | Archivos IMERG Early V07, SMAP SPL3SMP_E, GLDAS_NOAH025_3H, mosaicos MOD13Q1/MOD11A2, Ocean Color y GRACE. Una cuenta no confirma aún una descarga o decodificación. |
| [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/map_key/), D06 | MAP_KEY gratuita; respetar cuota y consultar disponibilidad | `FIRMS_MAP_KEY` | Consulta CSV por área/fecha/sensor. El CSV público masivo es otra vía y se verifica por separado. |
| [CDS](https://cds.climate.copernicus.eu/how-to-api), D08, D09, D41 | Registro y aceptación manual de términos de CADA dataset | `CDSAPI_URL=https://cds.climate.copernicus.eu/api`, `CDSAPI_KEY` | ERA5, estacionales, GTSM. También admite archivo local `.cdsapirc` según instrucciones oficiales. |
| [CEMS Early Warning Data Store](https://ewds.climate.copernicus.eu/how-to-api), D10, D11 | Cuenta ECMWF y aceptación manual de términos del producto CEMS | `EWDSAPI_URL=https://ewds.climate.copernicus.eu/api`, `EWDSAPI_KEY` | Caudal GloFAS y productos numéricos de peligro de fuego disponibles en el catálogo CEMS. Se debe resolver la colección vigente; un WMS no alcanza. |
| [ADS](https://ads.atmosphere.copernicus.eu/how-to-api), D12 | Registro y licencia CAMS aceptada manualmente | `ADSAPI_URL=https://ads.atmosphere.copernicus.eu/api`, `ADSAPI_KEY` | CAMS por variable, nivel, corrida y plazo. |
| [Copernicus Marine](https://data.marine.copernicus.eu/register), D14 | Cuenta gratuita, términos del servicio | `COPERNICUSMARINE_SERVICE_USERNAME`, `COPERNICUSMARINE_SERVICE_PASSWORD` | Subconjuntos de física oceánica con Toolbox. No hay descarga acreditada sin cuenta en este incremento. |
| [Copernicus Data Space](https://documentation.dataspace.copernicus.eu/Registration.html), D25, D30 | Catálogo público; descarga/procesamiento según servicio con cuenta y cuota | `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET` para cliente OAuth del servicio elegido; no se presuponen equivalentes al usuario/contraseña | Descargas Sentinel/DEM cuando se implemente el flujo autorizado. InSAR requiere procesamiento científico adicional. |

Las variables CDS/ADS/EWDS/CDSE se reservan y documentan para el acceso; no se declara implementado un conector por tenerlas en el ejemplo. Ningún script crea cuentas, acepta términos ni activa servicios pagos.

Acceso sin cuenta comprobado con datos: ERDDAP CRW (SST, HotSpot, DHW), USGS FDSN/OAF, SWPC observado/previsto, MODIS ORNL (subconjuntos locales), ECMWF Open Data IFS, NCEI OISST, CNEOS Sentry, CPC ONI, CAP de NTWC/PTWC, Smithsonian GVP, NOAA PSL MHW, NASA LHASA y GLO-90 público en AWS. GVP usa `webservices.volcano.si.edu/geoserver/GVP-VOTW/ows`; el 403 inicial correspondía a otro host. FIRMS CSV respondió con cabecera y cero filas: no acredita detecciones.

D30 ya dispone de una tesela GLO-90 pública sin cuenta AWS/CDSE. Las credenciales CDSE de la tabla corresponden a otras rutas de descarga y a Sentinel, no bloquean esa tesela. D24 y D16 usan rangos HTTPS conservados y comprobados; no descargan las colecciones completas. [RAPID](https://rapid.ac.uk/rapidmoc/rapid_data/datadl.php), D34, solicita correo y consentimiento para descargar: se deja al usuario ese paso, sin enviar información personal ni aceptar condiciones.

La documentación de [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) publica un subconjunto gratuito por HTTPS, bajo CC BY 4.0 y términos ECMWF: no necesita cuenta CDS para esa distribución. La historia ERA5 y los ensembles estacionales siguen siendo vías diferentes.

La confianza TLS usa el almacén de certificados del sistema mediante `truststore`. No se desactiva la comprobación de certificados. Los resultados de descubrimiento no cuentan como productos integrados.
