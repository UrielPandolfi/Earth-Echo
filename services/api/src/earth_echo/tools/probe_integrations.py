"""Small public discovery requests; never uses credentials or downloads collections."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from earth_echo.paths import repo_root

URLS = {
    'crw-sst': 'https://coastwatch.noaa.gov/erddap/info/noaacrwsstDaily/index.json',
    'crw-hotspot': 'https://coastwatch.noaa.gov/erddap/search/index.json?page=1&itemsPerPage=10&searchFor=hotspot',
    'crw-dhw': 'https://coastwatch.noaa.gov/erddap/info/noaacrwdhwDaily/index.json',
    'oisst': 'https://coastwatch.pfeg.noaa.gov/erddap/search/index.json?page=1&itemsPerPage=5&searchFor=oisst',
    'modis-dates': 'https://modis.ornl.gov/rst/api/v1/MOD13Q1/dates?latitude=-3&longitude=-60',
    'modis-bands': 'https://modis.ornl.gov/rst/api/v1/MOD13Q1/bands',
    'lst-dates': 'https://modis.ornl.gov/rst/api/v1/MOD11A2/dates?latitude=-3&longitude=-60',
    'firms': 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv',
    'ecmwf': 'https://data.ecmwf.int/forecasts/',
    'cneos': 'https://ssd-api.jpl.nasa.gov/sentry.api',
    'gvp': 'https://volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=1.0.0&request=GetCapabilities',
    'tsunami': 'https://www.tsunami.gov/events/xml/PAAQAtom.xml',
    'enso': 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt',
}

def probe(item):
    name, url = item
    try:
        with urlopen(Request(url, headers={'User-Agent': 'EarthEcho/0.2', 'Accept': 'application/json'}), timeout=25) as response:
            body = response.read(4_000_001)
            if len(body) > 4_000_000:
                return name, {'url': url, 'error': 'over 4 MB; not retained'}
            path = repo_root() / 'data/operational/discovery' / (name + '.txt')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            return name, {'url': url, 'status': response.status, 'bytes': len(body), 'sample': body[:120].decode(errors='replace')}
    except Exception as error:
        return name, {'url': url, 'error': str(error)}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as executor:
        for name, result in executor.map(probe, URLS.items()):
            print(name, json.dumps(result))
