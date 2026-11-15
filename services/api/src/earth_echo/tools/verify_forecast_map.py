"""Verify retained originals -> versioned API -> points/highlights, without HTTP providers.

Integration evidence only. No Brier, calibration, causal or predictive skill claim.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime,timedelta,timezone
from urllib.parse import urlparse
from urllib.request import urlopen
import h5py
import numpy as np
import eccodes as ec
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.storage.products import read_product,products_root,atomic_json
from earth_echo.paths import repo_root
from earth_echo.queries.predictions import identity
from earth_echo.contracts.predictions import ForecastCatalog,ForecastField,ForecastPoint,ForecastHighlights,PlanetaryForecast
from earth_echo.contracts.types import parse_utc
from earth_echo.ingest.feeds import feeds_dir


def verify(base='http://127.0.0.1:8000'):
    target=urlparse(base)
    if target.scheme!='http' or target.hostname not in {'127.0.0.1','localhost','::1'} or target.username or target.password:
        raise ValueError('Use a local API without credentials')
    def get(path):
        with urlopen(base.rstrip('/')+path,timeout=30) as response:
            raw=response.read(16_000_001)
        if len(raw)>16_000_000:raise ValueError('Verification response exceeded16MB')
        return raw
    catalog=ForecastCatalog.model_validate_json(get('/v1/forecasts/catalog'))
    entries={e.id:e for e in catalog.forecasts}
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Native/API fidelity; not forecast skill','default_d16_id':catalog.default_d16_id,'d16':[],'ifs':[]}
    for slot in range(1,4):
        p=read_product(f'd16-mhw-month-{slot}')
        if p is None:continue
        raw=(products_root()/p.raw_file).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==p.checksum_sha256
        assert 'with trend' in p.collection_id
        source=ArchivedRangeSource(raw)
        with source.open() as stream,h5py.File(stream,'r') as ds:
            assert bytes(ds['start_time'].attrs['units']).decode()=='days since 2021-01-01 00:00:00'
            initial=datetime(2021,1,1,tzinfo=timezone.utc)+timedelta(days=float(ds['start_time'][-1]))
            assert initial==p.initialized_at
            offset=(p.valid_from.year-initial.year)*12+p.valid_from.month-initial.month
            li=int(np.flatnonzero(ds['lead_time'][:]==offset+.5)[0])
            native=ds['mhw_probability'][li,:,:,-1]
            assert np.isnan(native[0,:]).all() and np.isfinite(native[-1,:]).all()
            lon=(ds['lon'][:]+180)%360-180;order=np.argsort(lon)
            expected=native[::-1,:][:,order]
            decoded=np.asarray(p.grid.values,dtype=float).reshape(expected.shape)
            assert np.array_equal(expected,decoded,equal_nan=True)
            assert np.array_equal(lon[order],p.grid.longitudes)
            assert np.array_equal(ds['lat'][:][::-1],p.grid.latitudes)
        key=identity(p);assert key in entries
        field=ForecastField.model_validate_json(get(f'/v1/forecasts/fields/{key}'))
        assert field.grid.model_dump(exclude={'west','east','south','north'})==p.grid.model_dump(exclude={'west','east','south','north'})
        assert (field.grid.west,field.grid.east,field.grid.south,field.grid.north)==(-180,180,-90,90)
        assert field.forecast.original_sha256==p.checksum_sha256
        point=ForecastPoint.model_validate_json(get(f'/v1/forecasts/fields/{key}/point?longitude=-67&latitude=17'))
        r=p.grid.latitudes.index(17);c=p.grid.longitudes.index(-67)
        assert point.probability==float(expected[r,c]) and point.value is None and point.forecast.issued_at is None
        assert point.cell.extent.west==-67.5 and point.cell.extent.south==16.5
        land=ForecastPoint.model_validate_json(get(f'/v1/forecasts/fields/{key}/point?longitude=-75&latitude=10'))
        assert land.status=='no_coverage' and land.probability is None
        csv_rows=list(csv.DictReader(io.StringIO(get(f'/v1/forecasts/fields/{key}/point.csv?longitude=-67&latitude=17').decode())))
        assert float(csv_rows[0]['probability'])==point.probability and csv_rows[0]['forecast_id']==key
        highlighted=ForecastHighlights.model_validate_json(get(f'/v1/forecasts/fields/{key}/highlights?probability_filter=0.7'))
        # Compare the exact decoded Float32 value to the decimal display filter
        # in float64. NumPy would otherwise round scalar0.7 down to Float32,
        # admitting values0.699999988... that the API correctly keeps below it.
        assert highlighted.matching_cells==int(np.count_nonzero(expected.astype(np.float64)>=.7))
        for area in highlighted.areas:
            cell=area.representative.cell
            served=ForecastPoint.model_validate_json(get(f'/v1/forecasts/fields/{key}/point?longitude={cell.longitude}&latitude={cell.latitude}'))
            assert served==area.representative and served.probability==area.probability_max
        # The scientific original endpoint is version-pinned, not the rotating slot.
        served_hash=hashlib.sha256(get(f'/v1/forecasts/fields/{key}/original')).hexdigest()
        assert served_hash==p.checksum_sha256
        report['d16'].append({'id':key,'product_id':p.id,'valid_from':p.valid_from.isoformat(),'valid_to':p.valid_to.isoformat(),
            'original_sha256':p.checksum_sha256,'native_positions_checked':expected.size,'valid_cells':int(np.isfinite(expected).sum()),'masked_cells':int(np.isnan(expected).sum()),
            'probe_probability':point.probability,'masked_probe':[-75,10],'areas_p_ge_0_7':highlighted.total_areas,'shown_areas':highlighted.returned_areas,'native_axes_masks_and_values_equal':True,'api_csv_and_representatives_equal':True})
    for variable in ('2t','wind10','tp'):
        p=read_product(f'd07-ifs-{variable}-24h')
        if p is None:report['ifs'].append({'variable':variable,'status':'missing_input'});continue
        raw=(products_root()/p.raw_file).read_bytes();assert hashlib.sha256(raw).hexdigest()==p.checksum_sha256
        n=int.from_bytes(raw[8:16],'big');messages=[raw[:n]]+([raw[n:]] if variable=='wind10' else [])
        native=[]
        for message in messages:
            handle=ec.codes_new_from_message(message)
            try:
                probe=ec.codes_grib_find_nearest(handle,17.5,-67.5)[0]
                assert probe['lat']==17.5 and (probe['lon']+180)%360-180==-67.5
                native.append(float(probe['value']))
            finally:ec.codes_release(handle)
        expected=native[0]-273.15 if variable=='2t' else math.sqrt(native[0]**2+native[1]**2) if variable=='wind10' else native[0]*1000
        key=identity(p)
        point=ForecastPoint.model_validate_json(get(f'/v1/forecasts/fields/{key}/point?longitude=-67.5&latitude=17.5'))
        assert point.probability is None and math.isclose(point.value,expected,abs_tol=1e-9)
        report['ifs'].append({'id':key,'variable':p.variable,'native_values':native,'converted_value':point.value,'unit':point.unit,'valid_from':p.valid_from.isoformat(),'valid_to':p.valid_to.isoformat() if p.valid_to else None,
            'temporal_state':point.forecast.temporal_state,'issued_at':None,'original_sha256':p.checksum_sha256,'native_grib_matches':True})
    kp=PlanetaryForecast.model_validate_json(get('/v1/forecasts/planetary/d28-kp'))
    if kp.forecast:
        raw=get(kp.forecast.original_download)
        assert hashlib.sha256(raw).hexdigest()==kp.forecast.original_sha256
        native=json.loads(raw)
        predicted={parse_utc(row['time_tag'] if '+' in row['time_tag'] or row['time_tag'].endswith('Z') else row['time_tag']+'Z'):row['kp'] for row in native if row['observed']=='predicted'}
        for w in kp.windows:
            assert predicted[w.valid_from]==w.value and w.valid_to-w.valid_from==timedelta(hours=3)
        assert kp.forecast.issued_at is None and kp.forecast.initialized_at is None and kp.probability is None
        report['kp']={'id':kp.forecast.id,'native_windows_equal':True,'windows':len(kp.windows),'valid_from':kp.forecast.valid_from.isoformat(),'valid_to':kp.forecast.valid_to.isoformat(),'spatial_support':'planetary','issued_at':None,'probability':None}
    else:report['kp']={'status':kp.status,'reason':kp.reason}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--api-base',default='http://127.0.0.1:8000');parser.add_argument('--retain',action='store_true');parser.add_argument('--prior-catalog',help='Saved catalog from before restarting the API');args=parser.parse_args()
    report=verify(args.api_base)
    if args.prior_catalog:
        before=ForecastCatalog.model_validate_json(open(args.prior_catalog,encoding='utf-8-sig').read())
        with urlopen(args.api_base.rstrip('/')+'/v1/forecasts/catalog',timeout=30) as response:after=ForecastCatalog.model_validate_json(response.read(2_000_000))
        after_by_id={f.id:f for f in after.forecasts}
        checked=[]
        for original in before.forecasts:
            if original.source_id!='D16':continue
            current=after_by_id[original.id]
            for name in ('initialized_at','issued_at','retrieved_at','processed_at','first_seen_at','valid_from','valid_to','original_sha256','adapter_version'):
                assert getattr(current,name)==getattr(original,name),(original.id,name)
            checked.append(original.id)
        assert checked
        report['restart_check']={'identities_and_scientific_times_unchanged':checked,'scope':'D16 versions retained across an actual local API process-tree restart; retrieval/first_seen did not become issue time.'}
    if args.retain:atomic_json(repo_root()/'data/operational/forecast_map_evidence.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
