"""Actual local models through HTTP workflow, including correction and preparation."""
import json,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'services/api')]
from fastapi.testclient import TestClient
from civicfix.main import create_app

def main():
    out=ROOT/'.runtime/app-evaluation'/('api-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as data:
        started=time.monotonic()
        with TestClient(create_app(data_dir=data,mode='real')) as c:
            c.headers['origin']='http://127.0.0.1:8000'
            c.headers['x-csrf-token']=c.post('/api/v1/session').json()['csrf_token']
            while any(c.get('/api/v1/capabilities').json().get(k,{}).get('status')=='starting' for k in ['classifier','description']):
                if time.monotonic()-started>125:raise RuntimeError('Readiness deadline')
                time.sleep(.25)
            cold=time.monotonic()-started
            d=c.post('/api/v1/drafts',json={}).json()['draft'];base='/api/v1/drafts/'+d['id']
            def cmd(method,path,**kw):
                nonlocal d
                response=c.request(method,base+path,headers={'if-match':f'"{d["revision"]}"'},**kw)
                assert response.status_code in [200,202],response.text
                payload=response.json()
                if 'draft' in payload:d=payload['draft']
                return payload
            cmd('PUT','/photo',files={'photo':('photo.jpg',(ROOT/'data/images/commons-0a68e3b438.jpg').read_bytes(),'image/jpeg')})
            cmd('PATCH','',json={'location':{'latitude':29.645781879176276,'longitude':-82.30619912751014,'label':'SE 7th Avenue test location','source':'manual'}})
            cmd('POST','/location/confirm',json={'confirmed':True})
            records=[]
            for i in range(10):
                t=time.monotonic();cmd('POST','/analysis',json={'acknowledged':True,'disclosure_version':'local-v1'})
                while True:
                    d=c.get(base).json()['draft']
                    if d['analysis']['status']!='running':break
                    time.sleep(.1)
                records.append({'run':i,'seconds':time.monotonic()-t,'analysis':d['analysis']});print(i,records[-1]['seconds'],d['analysis']['status'],flush=True)
            cmd('PATCH','',json={'category':'pothole','description':'A hole with broken pavement is visible beside a square metal cover.'})
            cmd('POST','/manual-resolution',json={'reason':'Reviewed photograph and removed uncertain details from the suggestion.','acknowledged':True})
            cmd('POST','/destination',json={});assert d['route']['status']=='resolved'
            cmd('POST','/review',json={'confirmed':True,'nonemergency_confirmed':True})
            prep=cmd('POST','/prepare',json={});assert 'has not been sent' in str(prep)
            assert c.get(base+'/prepared.txt').status_code==200
            assert c.get(base+'/photo/download').status_code==200
            assert c.delete(base).status_code==204 and c.get(base).status_code==404
            (out/'results.json').write_text(json.dumps({'cold_readiness_seconds':cold,'runs':records,'prepared_then_deleted':True,'external_submission':False},indent=2))
            print('API real-model workflow verified',flush=True)
if __name__=='__main__':main()
