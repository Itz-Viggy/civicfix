"""HTTP integration smoke. Run inside app; state survives app recreation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import httpx

p = argparse.ArgumentParser()
p.add_argument('phase', choices=['create', 'verify', 'delete'])
mode = p.add_mutually_exclusive_group()
mode.add_argument('--fixture', action='store_true')
mode.add_argument('--clip-only', action='store_true')
args = p.parse_args()
state = Path(os.getenv('CIVICFIX_DATA_DIR', '/var/lib/civicfix')) / '.docker-smoke.json'
c = httpx.Client(base_url='http://127.0.0.1:8000', headers={'Origin':'http://127.0.0.1:8000'}, timeout=30)
def call(method, path, **kw):
    r = c.request(method, path, **kw)
    r.raise_for_status()
    return r.json() if r.content and 'json' in r.headers.get('content-type','') else r.content

deadline=time.monotonic()+650
while True:
    try:
        if call('GET','/api/v1/health/live')['status']=='ok': break
    except httpx.TransportError:
        if time.monotonic()>=deadline: raise
    time.sleep(1)

if args.phase == 'create':
    assert call('GET','/')
    caps = call('GET','/api/v1/capabilities')
    assert caps['simulated'] == args.fixture
    if args.clip_only:
        assert caps['classifier']['status'] == 'ready' and caps['description']['status'] == 'unavailable'
    else:
        assert caps['ready']
    token = call('POST','/api/v1/session')['csrf_token']
    c.headers['X-CSRF-Token'] = token
    d = call('POST','/api/v1/drafts',json={})['draft']
    base = '/api/v1/drafts/' + d['id']
    def mutate(method, path, **kw):
        global d
        value = call(method,base+path,headers={'If-Match':f'"{d["revision"]}"'},**kw)
        if 'draft' in value: d = value['draft']
        return value
    image = Path('/workspace/data/images/commons-0a68e3b438.jpg').read_bytes()
    mutate('PUT','/photo',files={'photo':('test.jpg',image,'image/jpeg')})
    mutate('PATCH','',json={'location':{'latitude':29.645781879176276,'longitude':-82.30619912751014,'label':'SE 7th Avenue test location','source':'manual'}})
    mutate('POST','/location/confirm',json={'confirmed':True})
    started = time.monotonic()
    mutate('POST','/analysis',json={'acknowledged':True,'disclosure_version':'local-v1'})
    while True:
        d = call('GET',base)['draft']
        if d['analysis']['status'] != 'running': break
        assert time.monotonic()-started < 1050, 'Analysis deadline'
        time.sleep(1)
    from civicfix.contracts import ClassifierResult, DescriptionResult
    analysis = d['analysis']
    classifier = analysis['classifier']
    assert classifier['status'] == 'ok' and classifier['metadata']['simulated'] == args.fixture, analysis
    ClassifierResult.model_validate(classifier['result'])
    if args.clip_only:
        from services.inference.manager import real_clip_duration
        assert real_clip_duration(classifier) is not None
        assert analysis['status'] == 'failed' and analysis['reason_codes'] == ['description_failed'], analysis
        assert analysis['description']['error']['code'] == 'model_unavailable'
        print(f"Real CLIP prediction verified: {classifier['result']['predicted_category']}; manual description required")
    else:
        description = analysis['description']
        assert analysis['status'] == 'succeeded', analysis
        assert description['status'] == 'ok' and description['metadata']['simulated'] == args.fixture, description
        DescriptionResult.model_validate(description['result'])
        print(f'Both model stages verified; simulated={args.fixture}; elapsed={time.monotonic()-started:.1f}s')
    mutate('PATCH','',json={'category':'pothole','description':'A hole with broken pavement is visible beside a square metal cover.'})
    mutate('POST','/manual-resolution',json={'reason':'Reviewed the test photo and corrected uncertain details.','acknowledged':True})
    mutate('POST','/destination',json={})
    mutate('POST','/review',json={'confirmed':True,'nonemergency_confirmed':True})
    prepared=mutate('POST','/prepare',json={})
    assert 'has not been sent' in prepared['message']
    photo=call('GET',base+'/photo/download')
    prepared_text = call('GET', base+'/prepared.txt')
    assert prepared_text
    state.write_text(json.dumps({'id': d['id'], 'cookie': c.cookies.get('civicfix_session'), 'csrf': token,
                                 'photo_sha256': hashlib.sha256(photo).hexdigest(),
                                 'text_sha256': hashlib.sha256(prepared_text).hexdigest()}))
    state.chmod(0o600)
    print('Report prepared; persistence probe saved')
else:
    saved=json.loads(state.read_text())
    c.cookies.set('civicfix_session',saved['cookie'])
    c.headers['X-CSRF-Token']=saved['csrf']
    base='/api/v1/drafts/'+saved['id']
    d=call('GET',base)['draft']
    assert d['state']=='prepared'
    assert hashlib.sha256(call('GET',base+'/photo/download')).hexdigest()==saved['photo_sha256']
    prepared_text = call('GET', base+'/prepared.txt')
    assert prepared_text
    if 'text_sha256' in saved:
        assert hashlib.sha256(prepared_text).hexdigest() == saved['text_sha256']
    print('Persisted session, prepared draft, text and photo verified')
    if args.phase=='delete':
        call('DELETE',base)
        assert c.get(base).status_code==404
        assert c.get(base+'/photo').status_code==404
        state.unlink()
        print('Test draft and photo access deleted')
