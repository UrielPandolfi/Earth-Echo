# Fixture científica D16

`nmme-oct2026-ranges.json` contiene13rangos binarios auténticos del NetCDF NOAA PSL `NMME_prob90_latest.nc`, corrida octubre2026, conservados del activo local original. No construye un NetCDF nuevo ni altera probabilidades. Incluye metadatos/ejes/índice HDF5 y un chunk espacial (todas sus anticipaciones), unos2,27MB con base64. `evidence.json` acredita SHA, tamaño, recuperación, URL y cuatro probes; el SHA del contenedor reducido difiere del activo padre completo retenido.

Las pruebas abren esos rangos sin red, leen coordenadas/tiempo/NaN con h5py y cotejan las tres probabilidades con `struct.unpack` de los bytes del chunk. En −67°,17°: noviembre0,8870967626571655; diciembre0,9435483813285828; enero0,9112903475761414. Son valores de esta corrida; no constantes de la aplicación. El probe−75°,10° es NaN en el original. Cero real se comprueba en otra celda del mismo chunk.

Variante con tendencia retenida; evento mensual p90 estacional, referencia1991–2020. Documentación primaria: https://psl.noaa.gov/marine-heatwaves/ . No verifica habilidad predictiva ni daño biológico. Esta fixture de desarrollo está fuera del almacén científico operativo512MB; no hay descarga por clic.
