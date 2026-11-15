"""NASA access doctor: metadata and optional bounded HDF header, never a feed."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from earth_echo.paths import repo_root
from earth_echo.settings import get_settings
from earth_echo.storage.products import atomic_json
from earth_echo.tools.refresh_job import child_deadline
from earth_echo.connectors.nasa_access import discover,credentials_present,authenticated_session,EarthdataRangeSource,EarthdataAccessError


def probe(source_ids,*,verify_header=False,retain=False):
    records=[];files={};session=None;auth_attempted=False;auth_error=None
    for sid in source_ids:
        stamp=datetime.now(timezone.utc)
        try:
            info,raw=discover(sid);files[sid+'-cmr.json']=raw
            record={**info,'retrieved_at':stamp.isoformat(),'status':'metadata_only','credentials_present':credentials_present(),'science_header_verified':False,
                'remaining':'Authenticated numerical sample, units/quality/georeferencing decoding, persistence, API/UI and independent science-value check still required'}
            if verify_header:
                if not credentials_present():record.update(status='credentials_missing',requirement='EARTHDATA_USERNAME/EARTHDATA_PASSWORD or EARTHDATA_TOKEN, local only; manual DAAC authorization')
                else:
                    if not auth_attempted:
                        auth_attempted=True
                        try:session=authenticated_session()
                        except EarthdataAccessError as error:auth_error=str(error)
                    if auth_error:raise EarthdataAccessError(auth_error)
                    source=EarthdataRangeSource(sid,info['science_url'],session=session,max_bytes=131072,max_requests=1,deadline_seconds=30)
                    if source.read_at(0,8)!=b'\x89HDF\r\n\x1a\n':raise EarthdataAccessError('Science URL did not return a qualified HDF5 header; no values published')
                    files[sid+'-header.ranges.json']=source.archive({'scope':'header only; no scientific values qualified'})
                    record.update(status='header_only',science_header_verified=True,original_object_bytes=source.size,etag=source.etag,header_range_bytes=source.transferred)
            records.append(record)
        except Exception as error:
            # Never echo arbitrary SDK/request errors that can embed signed URLs.
            message=str(error) if isinstance(error,EarthdataAccessError) else f'{type(error).__name__}: metadata/probe unavailable'
            records.append({'source_id':sid,'retrieved_at':stamp.isoformat(),'status':'access_failed','error':message,'scientific_values_verified':False,'published_as_product':False})
    report={'scope':'access preparation only; not a connected source or scientific integration','records':records,
        'assets':{name:{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for name,raw in files.items()}}
    if retain:
        folder=repo_root()/'data/samples/nasa-access';folder.mkdir(parents=True,exist_ok=True)
        for name,raw in files.items():(folder/name).write_bytes(raw)
        atomic_json(folder/'readiness.json',report)
    return report


def main():
    get_settings();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',nargs='+',choices=['D02','D03'],default=['D02','D03'])
    parser.add_argument('--verify-header',action='store_true')
    parser.add_argument('--retain',action='store_true')
    args=parser.parse_args()
    with child_deadline(120):report=probe(args.only,verify_header=args.verify_header,retain=args.retain)
    print(json.dumps(report,ensure_ascii=True,indent=2))
    if any(r['status'] in {'access_failed','credentials_missing'} for r in report['records']):raise SystemExit(2)


if __name__=='__main__':main()
