# Hora estable ERA5 por la distribución pública ARCO

`era5-arco.zip` conserva los bytes originales de un bloque de temperatura del aire a 2 m (721×1440, Float32 K) y sus metadatos/ejes CF, obtenidos por HTTPS público. Campo estable 30/06/2026 00 UTC, no ERA5T. El manifiesto contiene cada URL, SHA, tamaño y generación GCS. Es un archivo local de bloques, no el GRIB original ni una colección completa.

Fuente científica: C3S/ECMWF ERA5, doi:10.24381/cds.adbb2d47. Distribución ARCO de Google Research, Carver y Merose (2023): <https://github.com/google-research/arco-era5>. Archivo `ar/full_37-1h-0p25deg-chunk-1.zarr-v3`, formato Zarr **2**; v3 es edición del store. Licencia y descripción del producto original: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview>.

Se cotejaron todos los bytes descomprimidos con C-Blosc1 y C-Blosc2. Eje temporal comienza en 1900, aunque los datos calificados comienzan en 1940: índice real 1.108.824. Latitud 90…−90 y longitud 0…359,75°, paso 0,25°. Valor nativo −35°,−62°: 281,419677734375 K. Vista mundial de centros a 1°, NaN sigue null, K→°C con función probada y comprobación Decimal. No valida incertidumbre, un detector térmico ni un pronóstico; una sola hora no es serie/climatología/tendencia.
