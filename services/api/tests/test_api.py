from io import BytesIO
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from civicfix.main import create_app
from civicfix.storage import DraftRow
from civicfix.contracts import ClassifierResult,DescriptionResult

ORIGIN='http://127.0.0.1:5173'
POINT={'latitude':29.645781879176276,'longitude':-82.30619912751014,'label':'SE 7th Avenue','source':'manual'}
def jpeg(mode='RGB'):
    out=BytesIO();Image.new(mode,(60,40),'white').save(out,'PNG' if mode=='RGBA' else 'JPEG');return out.getvalue()
@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path,mode='fixture')
    with TestClient(app) as c:
        session=c.post('/api/v1/session',headers={'Origin':ORIGIN}).json()
        c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':session['csrf_token']})
        yield c

def create(c):return c.post('/api/v1/drafts',json={}).json()['draft']
def mutate(c,d,path,body=None,method='post'):
    kw={'headers':{'If-Match':f'"{d["revision"]}"'}}
    if body is not None:kw['json']=body
    return getattr(c,method)(f'/api/v1/drafts/{d["id"]}'+path,**kw)
def inputs(c):
    d=create(c)
    r=c.put(f'/api/v1/drafts/{d["id"]}/photo',headers={'If-Match':f'"{d["revision"]}"'},files={'photo':('private.jpg',jpeg(),'image/jpeg')});assert r.status_code==200,r.text;d=r.json()['draft']
    d=mutate(c,d,'',{'location':POINT},'patch').json()['draft']
    return mutate(c,d,'/location/confirm',{'confirmed':True}).json()['draft']
def analyzed(c,d):
    r=mutate(c,d,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'});assert r.status_code==202,r.text
    for _ in range(60):
        d=c.get(f'/api/v1/drafts/{d["id"]}').json()['draft']
        if d['analysis']['status']!='running':return d
        time.sleep(.02)
    pytest.fail('Analysis did not finish')
def prepare(c,d):
    d=mutate(c,d,'/destination',{}).json()['draft']
    r=mutate(c,d,'/review',{'confirmed':True,'nonemergency_confirmed':True});assert r.status_code==200,r.text;d=r.json()['draft']
    r=mutate(c,d,'/prepare',{});assert r.status_code==200,r.text
    return d,r.json()

def test_complete_real_storage_flow(client):
    d=analyzed(client,inputs(client));assert d['analysis']['status']=='succeeded'
    d,p=prepare(client,d)
    assert p['destination']['status']=='resolved'
    assert 'It has not been sent to an authority.' in p['message']
    assert mutate(client,d,'/prepare',{}).json()['prepared_at']==p['prepared_at']
    assert client.get(f'/api/v1/drafts/{d["id"]}/prepared.txt').status_code==200
    assert client.get(f'/api/v1/drafts/{d["id"]}/photo/download').headers['content-type']=='image/jpeg'
    d=mutate(client,d,'',{'description':'A visible section of pavement is missing.'},'patch').json()['draft']
    assert d['prepared_revision'] is None
    assert mutate(client,d,'/prepare',{}).status_code==409

def test_ownership_csrf_and_uniform_deletion(client):
    d=inputs(client)
    assert client.patch(f'/api/v1/drafts/{d["id"]}',json={'description':'bad'},headers={'X-CSRF-Token':'bad'}).status_code==403
    assert client.post('/api/v1/drafts',json={},headers={'Origin':'https://evil.example'}).status_code==403
    old=client.cookies.get('civicfix_session');client.cookies.clear()
    assert client.get(f'/api/v1/drafts/{d["id"]}').status_code==401
    token=client.post('/api/v1/session').json()['csrf_token'];client.headers['X-CSRF-Token']=token
    assert client.get(f'/api/v1/drafts/{d["id"]}').status_code==404
    assert client.get(f'/api/v1/drafts/{d["id"]}/photo').status_code==404
    assert client.delete(f'/api/v1/drafts/{d["id"]}').status_code==204
    client.cookies.clear();client.cookies.set('civicfix_session',old)
    assert client.get(f'/api/v1/drafts/{d["id"]}').status_code==200

def test_revision_validation_and_review_bypass(client):
    d=create(client)
    assert client.patch(f'/api/v1/drafts/{d["id"]}',json={'description':'x'}).status_code==428
    assert mutate(client,d,'',{'state':'prepared'},'patch').status_code==422
    assert mutate(client,d,'',{'location':{**POINT,'confirmed':True}},'patch').status_code==422
    assert mutate(client,d,'/prepare',{}).status_code==409
    newer=mutate(client,d,'',{'description':'Draft description'},'patch').json()['draft']
    assert mutate(client,d,'',{'description':'stale'},'patch').status_code==409
    assert mutate(client,newer,'',{'description':'Draft description'},'patch').json()['draft']['revision']==newer['revision']

def test_upload_validation_preserves_previous_photo(client):
    d=inputs(client);photo=d['photo']['id']
    for raw,mime,expected in [(b'junk','image/jpeg',422),(jpeg(),'image/png',415),(b'<svg/>','image/svg+xml',415),(b'x'*(10*1024*1024+1),'image/jpeg',413)]:
        r=client.put(f'/api/v1/drafts/{d["id"]}/photo',headers={'If-Match':f'"{d["revision"]}"'},files={'photo':('bad',raw,mime)})
        assert r.status_code==expected,r.text
    assert client.get(f'/api/v1/drafts/{d["id"]}').json()['draft']['photo']['id']==photo
    r=client.put(f'/api/v1/drafts/{d["id"]}/photo',headers={'If-Match':f'"{d["revision"]}"'},files={'photo':('rgba.png',jpeg('RGBA'),'image/png')});assert r.status_code==200
    image=Image.open(BytesIO(client.get(f'/api/v1/drafts/{d["id"]}/photo').content));assert image.mode=='RGB';assert not image.getexif()

def test_manual_unresolved_and_copy(client):
    d=analyzed(client,inputs(client))
    d=mutate(client,d,'',{'category':'leaking_hydrant','description':'Water is visible beside the hydrant.','user_observations':'I saw water flowing.'},'patch').json()['draft']
    d=mutate(client,d,'/manual-resolution',{'reason':'I confirmed these details.','acknowledged':True}).json()['draft']
    d=mutate(client,d,'/destination',{}).json()['draft'];assert d['route']['status']=='unresolved'
    assert mutate(client,d,'/prepare',{}).status_code==409
    response=client.get(f'/api/v1/drafts/{d["id"]}/draft.txt');assert 'Draft — not submitted' in response.text;assert 'User observation: I saw water flowing.' in response.text
    assert client.get(f'/api/v1/drafts/{d["id"]}/prepared.txt').status_code==409

def test_location_confirmation_and_accuracy_invalidation(client):
    d=inputs(client);assert d['location']['confirmed']
    d=mutate(client,d,'',{'location':{**POINT,'accuracy':100000,'source':'browser'}},'patch').json()['draft']
    assert not d['location']['confirmed'];assert not d['eligibility']['can_analyze']
    assert mutate(client,d,'/location/confirm',{'confirmed':True}).status_code==409
    r=mutate(client,d,'',{'location':{**POINT,'latitude':91}},'patch');assert r.status_code==422

def test_expiry_delete_and_files(client):
    d=inputs(client);s=client.app.state.store
    with s.session() as db,db.begin():db.get(DraftRow,d['id']).expires=0
    assert client.get(f'/api/v1/drafts/{d["id"]}').status_code==404
    client.portal.call(client.app.state.cleanup)
    assert list(s.photos.iterdir())==[]
    assert client.delete(f'/api/v1/drafts/{d["id"]}').status_code==204

def test_restart_persistence(tmp_path):
    with TestClient(create_app(tmp_path,mode='fixture')) as c:
        session=c.post('/api/v1/session',headers={'Origin':ORIGIN}).json();c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':session['csrf_token']});d=inputs(c);cookie=c.cookies.get('civicfix_session')
    with TestClient(create_app(tmp_path,mode='fixture')) as c:
        c.cookies.set('civicfix_session',cookie)
        assert c.get(f'/api/v1/drafts/{d["id"]}').json()['draft']['photo']['id']==d['photo']['id']

def test_model_contracts():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):ClassifierResult(predicted_category='pothole',scores={x:.2 for x in ['pothole']},top1_margin=0)
    with pytest.raises(ValidationError):DescriptionResult(category_suggestion='pothole',outcome='supported',visible_observations=[],suggested_description='There is damage.',clarification_reasons=[])

class ControlledManager:
    def __init__(self):
        import threading
        self.release=threading.Event();self.cancelled=False
    async def start(self):pass
    async def close(self):pass
    def capabilities(self):return {'simulated':True,'classifier':{'status':'ready'},'description':{'status':'ready'}}
    async def cancel(self):self.cancelled=True;self.release.set()
    async def analyze(self,image_bytes,on_stage=None):
        import asyncio
        from services.inference.manager import InferenceManager
        while not self.release.is_set():await asyncio.sleep(.01)
        m=InferenceManager('fixture');return await m.analyze(image_bytes,on_stage)

def controlled(tmp_path):
    manager=ControlledManager();app=create_app(tmp_path,mode='fixture',manager=manager)
    c=TestClient(app);c.__enter__()
    token=c.post('/api/v1/session',headers={'Origin':ORIGIN}).json()['csrf_token']
    c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':token})
    return c,manager

def test_job_busy_cancel_delete_and_no_resurrection(tmp_path):
    c,m=controlled(tmp_path)
    try:
        d=inputs(c);r=mutate(c,d,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'});assert r.status_code==202;d=r.json()['draft'];job=r.json()['job']
        assert mutate(c,d,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'}).status_code==409
        other=inputs(c);assert mutate(c,other,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'}).status_code==429
        assert c.delete(f'/api/v1/drafts/{d["id"]}').status_code==204;assert m.cancelled
        time.sleep(.2)
        assert c.get(f'/api/v1/drafts/{d["id"]}').status_code==404
        assert c.get(f'/api/v1/drafts/{d["id"]}/analysis/{job["id"]}').status_code==404
    finally:c.__exit__(None,None,None)

def test_pending_location_and_user_edits_are_preserved(tmp_path):
    c,m=controlled(tmp_path)
    try:
        d=inputs(c);r=mutate(c,d,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'});d=r.json()['draft']
        d=mutate(c,d,'',{'location':{**POINT,'label':'Corrected location label'},'description':'My own factual description.'},'patch').json()['draft']
        m.release.set()
        for _ in range(60):
            d=c.get(f'/api/v1/drafts/{d["id"]}').json()['draft']
            if d['analysis']['status']!='running':break
            time.sleep(.02)
        assert d['analysis']['status']=='succeeded'
        assert d['description']=='My own factual description.'
        assert not d['location']['confirmed']
    finally:c.__exit__(None,None,None)

def test_invalid_model_output_requires_manual_completion(tmp_path):
    class Invalid(ControlledManager):
        async def analyze(self,*args,**kwargs):return {'classifier':{'status':'ok','result':{'predicted_category':'invented'}},'description':{'status':'error','error':{'code':'timeout','message':'Timed out'}}}
    with TestClient(create_app(tmp_path,mode='fixture',manager=Invalid())) as c:
        token=c.post('/api/v1/session',headers={'Origin':ORIGIN}).json()['csrf_token'];c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':token})
        d=analyzed(c,inputs(c));assert d['analysis']['status']=='failed';assert d['analysis']['classifier']['error']['code']=='invalid_output';assert not d['eligibility']['can_review']
        d=mutate(c,d,'',{'category':'pothole','description':'A section of pavement is missing.'},'patch').json()['draft']
        d=mutate(c,d,'/manual-resolution',{'reason':'I checked the photo and corrected the fields.','acknowledged':True}).json()['draft']
        d,p=prepare(c,d);assert p['field_sources']=={'category':'user','description':'user'}

def test_manual_completion_cannot_skip_ready_models(client):
    d=inputs(client)
    d=mutate(client,d,'',{'category':'pothole','description':'Pavement is missing.'},'patch').json()['draft']
    r=mutate(client,d,'/manual-resolution',{'reason':'I inspected it.','acknowledged':True})
    assert r.status_code==409 and r.json()['error']['code']=='analysis_attempt_required'

def test_failed_physical_delete_still_revokes_access(client,monkeypatch):
    from pathlib import Path
    d=inputs(client);photos=client.app.state.store.photos
    original=Path.unlink
    def failing(path,*args,**kwargs):
        if path.parent==photos:raise PermissionError('simulated private file lock')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'unlink',failing)
    assert client.delete(f'/api/v1/drafts/{d["id"]}').status_code==204
    assert client.get(f'/api/v1/drafts/{d["id"]}/photo').status_code==404
    assert client.get('/api/v1/health/live').json()['cleanup_issue']
    monkeypatch.setattr(Path,'unlink',original)
    client.portal.call(client.app.state.cleanup)
    assert not list(photos.iterdir())

def test_extra_multipart_is_safe_error(client):
    d=create(client)
    r=client.put(f'/api/v1/drafts/{d["id"]}/photo',headers={'If-Match':f'"{d["revision"]}"'},files=[('photo',('one.jpg',jpeg(),'image/jpeg')),('photo',('two.jpg',jpeg(),'image/jpeg'))])
    assert r.status_code==400
    assert r.json()['error']['code']=='invalid_request'

def test_expired_pending_job_cannot_commit(tmp_path):
    c,m=controlled(tmp_path)
    try:
        d=inputs(c);r=mutate(c,d,'/analysis',{'acknowledged':True,'disclosure_version':'local-v1'});assert r.status_code==202
        with c.app.state.store.session() as db,db.begin():db.get(DraftRow,d['id']).expires=0
        m.release.set();time.sleep(.2)
        assert c.get(f'/api/v1/drafts/{d["id"]}').status_code==404
        c.portal.call(c.app.state.cleanup)
        assert not list(c.app.state.store.photos.iterdir())
    finally:c.__exit__(None,None,None)
