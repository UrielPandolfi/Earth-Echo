"""Extract tiny test fixtures from the actual retained provider responses. No network."""
import json
from earth_echo.storage.products import read_product,products_root
from earth_echo.paths import repo_root

def main():
    root=repo_root(); target=root/'data/samples/integrations'; target.mkdir(parents=True,exist_ok=True)
    fixtures={}
    for key in ['d29-sentry','d23-holocene-inventory','d27-tsunami-messages']:
        p=read_product(key); raw=(products_root()/p.raw_file).read_bytes(); body=json.loads(raw)
        if key=='d29-sentry': body['data']=body['data'][:2]; body['count']=2
        elif key=='d23-holocene-inventory': body['features']=body['features'][:2]; body['totalFeatures']=2
        else: body=body[0]['cap'][0]['xml']
        fixtures[key]={'original_url':p.original_url,'original_sha256':p.checksum_sha256,'excerpt':body}
    (target/'provider-excerpts.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p=read_product('d22-oaf-recent')
    (target/'usgs-oaf-us7000txrk.json').write_bytes((products_root()/p.raw_file).read_bytes())

if __name__=='__main__': main()
