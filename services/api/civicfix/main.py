"""Local private report workflow. All authoritative transitions happen here."""
from __future__ import annotations
import asyncio, hashlib, json, math, os, secrets, time, uuid
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartParser
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select,delete
from pydantic import ValidationError
from prometheus_client import (CollectorRegistry, Counter, Histogram, CONTENT_TYPE_LATEST,
                               disable_created_metrics, generate_latest)
from services.inference.manager import InferenceManager, real_clip_duration
from .contracts import (CATEGORIES,DraftCreate,DraftPatch,Confirm,Analyze,Resolve,Review,Empty,DraftResponse,ClassifierResult,DescriptionResult)
from .contracts import ClassificationFeedback, ExperienceFeedback, FeedbackInput, FeedbackState
from .config import load_config,ROOT
from .feedback import (FEEDBACK_MAX_REQUEST, FEEDBACK_QUOTA, FEEDBACK_RETENTION, FEEDBACK_WINDOW,
                       FeedbackCollector, feedback_analysis, feedback_state)
from .storage import Store,SessionRow,DraftRow,PhotoRow,JobRow,FeedbackRow
from .images import sanitize,ImageFailure,MAX_FILE,MAX_REQUEST
from .report_pdf import render_pdf

# Entire requests are bounded before parsing; originals never spill to OS temp.
MultiPartParser.spool_max_size=MAX_REQUEST
disable_created_metrics()

MESSAGE='Your report is ready for manual submission. It has not been sent to an authority.'
def uid(): return str(uuid.uuid4())
def stamp(t=None):
    from datetime import datetime,timezone
    return datetime.fromtimestamp(time.time() if t is None else t,timezone.utc).isoformat().replace('+00:00','Z')
def digest(value): return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def encode(value): return json.dumps(value,allow_nan=False,separators=(',',':'))
class Problem(Exception):
    def __init__(self,status,code,message=None,reasons=None,retry_after=2):
        self.status=status;self.code=code;self.message=message or code.replace('_',' ').capitalize();self.reasons=reasons
        self.retry_after=retry_after

def invalidate(d,manual=True,route=False):
    d['review_revision']=d['reviewed_at']=d['prepared_revision']=d['prepared_at']=None
    if manual: d['manual_resolution']=None
    if route: d['route']=None

def changed(d): d['revision']+=1;d['updated_at']=stamp()
def active(d): return d.get('analysis',{}).get('status')=='running' if d.get('analysis') else False
def photo_rejected(d): return (d.get('analysis') or {}).get('status') == 'rejected'

def require_replacement_if_rejected(d):
    if photo_rejected(d):
        raise Problem(409, 'photo_rejected', 'Upload a replacement photo that clearly shows one supported issue.',
                      reasons=d['analysis']['reason_codes'])

def validated_execution(execution, validator):
    if isinstance(execution, dict):
        if execution.get('status') == 'ok':
            allowed = {'adapter','model_id','revision','checkpoint_sha256','prompt_version','prompt_sha256',
                       'preprocessing_version','duration_seconds','simulated','runtime','device'}
            metadata = execution.get('metadata')
            safe_metadata = {k: v for k, v in metadata.items()
                             if k in allowed and isinstance(v, (str, int, float, bool, type(None)))} if isinstance(metadata, dict) else {}
            try:
                return {'status': 'ok', 'result': validator.model_validate(execution['result']).model_dump(),
                        'metadata': safe_metadata}
            except (ValidationError, KeyError, ValueError):
                return {'status': 'error', 'error': {'code': 'invalid_output',
                        'message': 'The model output did not match the report schema.'}}
        if execution.get('status') == 'error':
            safe_codes = ('model_unavailable','invalid_output','timeout','worker_crash','cancelled','interrupted')
            issue = execution.get('error')
            code = issue.get('code') if isinstance(issue, dict) else None
            return {'status': 'error', 'error': {'code': code if code in safe_codes else 'invalid_output',
                    'message': 'Local model analysis needs retry or manual correction.'}}
    return {'status': 'error', 'error': {'code': 'invalid_output',
            'message': 'The model output was incomplete.'}}

def text(d,prepared=False):
    label='Report Prepared' if prepared else 'Draft — not submitted'
    loc=d.get('location') or {}
    lines=[label, MESSAGE if prepared else 'This draft has not been sent to an authority.','',f"Category: {(d.get('category') or 'Not selected').replace('_',' ')}",f"Location: {loc.get('label','Not confirmed')}"]
    if 'latitude' in loc: lines.append(f"Coordinates: {loc['latitude']}, {loc['longitude']}")
    lines += ['',d.get('description','')]
    if d.get('user_observations'): lines += ['', 'User observation: '+d['user_observations']]
    if d.get('route',{}): lines += ['','Destination: '+(d['route'].get('destination_name') or 'Unresolved')]
    return '\n'.join(lines)

def create_app(data_dir=None,mode=None,manager=None):
    cfg=load_config(data_dir,mode)
    if manager is None:
        if cfg.mode == 'real' and cfg.clip_url:
            from services.inference.remote_clip import RemoteClipManager
            manager = RemoteClipManager(cfg.clip_url, os.getenv('CIVICFIX_CLIP_TOKEN'))
        else:
            manager=InferenceManager(mode=cfg.mode)
    store=Store(cfg.data_dir)
    registry = CollectorRegistry()
    predictions = Counter('civicfix_classification_predictions_total',
                          'Committed real CLIP classifications by predicted category.',
                          ['category'], registry=registry)
    for category in CATEGORIES:
        predictions.labels(category)
    durations = Histogram('civicfix_classification_duration_seconds',
                          'CLIP worker image decode, preprocessing and scoring time in seconds.',
                          buckets=(.05, .1, .25, .5, 1, 2.5, 5, 10, 30, 60), registry=registry)
    lock=asyncio.Lock(); tasks={}; active_job=None
    app=FastAPI(title='CivicFix local API',version='1.0.0')
    app.state.store=store;app.state.manager=manager;app.state.clock=time.time;app.state.cleanup_issue=False
    def safe_unlink(path):
        try:path.unlink(missing_ok=True)
        except OSError:app.state.cleanup_issue=True
    def now(): return app.state.clock()
    registry.register(FeedbackCollector(store, now))
    def routing():
        from . import routing as rules
        return rules
    def config_digest():
        cap=manager.capabilities()
        return str(cap.get('config_digest',digest('local-v1:'+cfg.mode)))
    def owned(db,id,owner):
        row=db.get(DraftRow,id)
        if not row or row.owner!=owner or row.expires<=now(): raise Problem(404,'draft_unavailable')
        d=json.loads(row.content)
        current=config_digest()
        if d.get('_config')!=current:
            d['_config']=current; d['analysis']=None;d['processing_acknowledgement']=None
            invalidate(d);changed(d); row.content=encode(d)
        if d.get('route'):
            old=d['route']
            rules = routing()
            if (old.get('rules_version'), old.get('boundary_version')) != (rules.RULES_VERSION, rules.BOUNDARY_VERSION):
                invalidate(d,manual=False,route=True);changed(d);row.content=encode(d)
        return row,d
    def save(row,d): row.content=encode(d)
    def reasons(d):
        errors=[]
        if not d['photo']: errors.append('missing_photo')
        l=d.get('location')
        if not l: errors.append('missing_location')
        elif not l.get('confirmed'):errors.append('unconfirmed_location')
        if l and (boundary_status := routing().boundary(l)) != 'inside':errors.append(boundary_status)
        if not d.get('category'):errors.append('missing_category')
        if not d.get('description','').strip():errors.append('missing_description')
        if active(d):errors.append('analysis_in_progress')
        a=d.get('analysis')
        if photo_rejected(d) or not d.get('manual_resolution'):
            if not a:errors.append('analysis_required')
            elif a.get('status')!='succeeded' or a.get('reason_codes'): errors.extend(a.get('reason_codes') or ['analysis_needs_correction'])
        route=d.get('route')
        if not route or route.get('status')!='resolved':errors.extend((route or {}).get('reason_codes') or ['destination_unresolved'])
        return list(dict.fromkeys(errors))
    def view(d):
        result={k:v for k,v in d.items() if not k.startswith('_')}
        missing=reasons(d)
        l=d.get('location') or {}
        can_analyze=bool(d['photo'] and l.get('confirmed') and routing().boundary(l)=='inside' and not active(d) and not photo_rejected(d))
        result['eligibility']={'can_analyze':can_analyze,'can_review':not missing,'can_prepare':not missing and d['review_revision']==d['revision'],'reason_codes':missing}
        result['state']='prepared' if d['prepared_revision']==d['revision'] and not missing else 'analyzing' if active(d) else 'ready_for_review' if not missing else 'needs_correction' if d['photo'] else 'draft'
        return result
    def response(d,status=200,**extra):
        return JSONResponse({'draft':view(d),**extra},status_code=status,headers={'ETag':f'"{d["revision"]}"'})
    def require_match(request,d):
        tag=request.headers.get('if-match')
        if tag is None:raise Problem(428,'revision_required')
        if tag != f'"{d["revision"]}"':raise Problem(409,'revision_conflict')
    def session(request,db):
        secret=request.cookies.get('civicfix_session','')
        row=db.get(SessionRow,digest(secret)) if secret else None
        if not row or row.expires<=now():raise Problem(401,'session_required')
        return row
    def origin(request):
        if request.headers.get('origin') not in cfg.allowed_origins:raise Problem(403,'origin_rejected')
    def authorize(request,db,mutate=False):
        row=session(request,db)
        if mutate:
            origin(request)
            if not secrets.compare_digest(request.headers.get('x-csrf-token',''),row.csrf):raise Problem(403,'csrf_rejected')
        return row.id
    async def stop_job(db,d,status='cancelled'):
        nonlocal active_job
        a=d.get('analysis')
        if not a or a.get('status')!='running':return
        job_id=a['job_id'];a['status']=status
        job=db.get(JobRow,job_id)
        if job:
            value=json.loads(job.content);value['status']=status;value['finished_at']=stamp(now());job.content=encode(value)
        if job_id in tasks:
            await manager.cancel()
            tasks.pop(job_id).cancel()
        if active_job==job_id:active_job=None
    def remove_files(db,id):
        for p in db.scalars(select(PhotoRow).where(PhotoRow.draft_id==id)).all():
            safe_unlink(store.photos/p.key);db.delete(p)
        db.execute(delete(JobRow).where(JobRow.draft_id==id))
    async def cleanup():
        async with lock:
            with store.session() as db,db.begin():
                for row in db.scalars(select(DraftRow).where(DraftRow.expires<=now())).all():
                    d=json.loads(row.content);await stop_job(db,d,'cancelled');remove_files(db,row.id);db.delete(row)
                db.execute(delete(SessionRow).where(SessionRow.expires<=now()))
                db.execute(delete(FeedbackRow).where(FeedbackRow.created_at <= now() - FEEDBACK_RETENTION))
                for photo in db.scalars(select(PhotoRow)).all():
                    parent=db.get(DraftRow,photo.draft_id)
                    current=json.loads(parent.content).get('photo') if parent else None
                    if not current or current['id']!=photo.id:
                        safe_unlink(store.photos/photo.key);db.delete(photo)
                db.flush()
                keys=set(db.scalars(select(PhotoRow.key)).all())
                for file in store.photos.iterdir():
                    if file.name not in keys:safe_unlink(file)
            store.checkpoint()
    async def cleanup_loop():
        while True:
            await asyncio.sleep(cfg.cleanup_interval)
            try:await cleanup()
            except OSError:app.state.cleanup_issue=True
    @asynccontextmanager
    async def lifespan(_):
        with store.session() as db,db.begin():
            for row in db.scalars(select(DraftRow)).all():
                d=json.loads(row.content)
                if active(d):
                    d['analysis']['status']='interrupted';d['analysis']['reason_codes']=['analysis_interrupted'];invalidate(d);changed(d);save(row,d)
            for job in db.scalars(select(JobRow)).all():
                j=json.loads(job.content)
                if j['status']=='running':j['status']='interrupted';job.content=encode(j)
        await cleanup()
        await manager.start()
        cleaner=asyncio.create_task(cleanup_loop())
        try:yield
        finally:
            cleaner.cancel()
            await manager.close()
            for task in tasks.values():task.cancel()
            with suppress(asyncio.CancelledError):await cleaner
            await cleanup()
            store.engine.dispose()
    app.router.lifespan_context=lifespan
    @app.exception_handler(Problem)
    async def problem_handler(request,error):
        headers={'Retry-After':str(error.retry_after)} if error.status==429 else {}
        return JSONResponse({'error':{'code':error.code,'message':error.message,'retryable':error.status in (409,429,503),'reason_codes':error.reasons or []},'request_id':uid()},status_code=error.status,headers=headers)
    @app.exception_handler(StarletteHTTPException)
    async def http_failure(request,error):
        return await problem_handler(request,Problem(error.status_code,'invalid_request' if error.status_code<500 else 'service_error'))
    @app.exception_handler(RequestValidationError)
    async def validation(request,error):
        return JSONResponse({'error':{'code':'invalid_fields','message':'Check the highlighted input fields.','retryable':False,'field_errors':[{'field':'.'.join(str(v) for v in e['loc']),'message':e['msg']} for e in error.errors()]},'request_id':uid()},status_code=422)
    @app.middleware('http')
    async def guard(request,call_next):
        host = request.headers.get('host','').split(':')[0]
        internal_scrape = host == 'app' and request.method == 'GET' and request.url.path == '/metrics'
        if host not in ('127.0.0.1','localhost','testserver') and not internal_scrape:
            return JSONResponse({'error':{'code':'host_rejected','message':'Local host required','retryable':False}},status_code=403)
        if request.url.path.startswith('/api/') and request.method in ('POST','PATCH','PUT','DELETE'):
            try:
                origin(request)
                if request.url.path!='/api/v1/session':
                    with store.session() as db:authorize(request,db,True)
            except Problem as e:return await problem_handler(request,e)
        feedback_post = (request.method == 'POST' and request.url.path.startswith('/api/v1/drafts/')
                         and request.url.path.rstrip('/').endswith('/feedback'))
        limit = FEEDBACK_MAX_REQUEST if feedback_post else MAX_REQUEST
        limit_message = 'Feedback request limit is 8 KiB' if feedback_post else 'Request limit is 11 MiB'
        length = request.headers.get('content-length', '').lstrip('0')
        if length and (len(length) > len(str(limit)) or not length.isascii() or not length.isdecimal() or int(length) > limit):
            return JSONResponse({'error':{'code':'request_too_large','message':limit_message,'retryable':False}},status_code=413)
        if request.url.path.startswith('/api/') and request.method in ('POST','PUT','PATCH'):
            chunks=[];total=0
            async for chunk in request.stream():
                total+=len(chunk)
                if total>limit:return JSONResponse({'error':{'code':'request_too_large','message':limit_message,'retryable':False}},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        result=await call_next(request)
        result.headers['Cache-Control']='no-store';result.headers['X-Content-Type-Options']='nosniff';result.headers['Referrer-Policy']='no-referrer'
        return result
    @app.post('/api/v1/session')
    async def init_session(request:Request):
        origin(request)
        secret=request.cookies.get('civicfix_session')
        with store.session() as db,db.begin():
            row=db.get(SessionRow,digest(secret)) if secret else None
            if not row or row.expires<=now():
                secret=secrets.token_urlsafe(32);row=SessionRow(id=digest(secret),csrf=secrets.token_urlsafe(32),expires=now()+86400);db.add(row)
            result=JSONResponse({'csrf_token':row.csrf,'expires_at':stamp(row.expires)})
            result.set_cookie('civicfix_session',secret,httponly=True,samesite='lax',max_age=86400,path='/')
            return result
    @app.get('/api/v1/health/live')
    async def live():return {'status':'ok','cleanup_issue':app.state.cleanup_issue}
    @app.get('/metrics', include_in_schema=False)
    async def metrics():
        return Response(generate_latest(registry), headers={'Content-Type': CONTENT_TYPE_LATEST})
    @app.get('/api/v1/capabilities')
    async def capabilities():
        cap=manager.capabilities()
        return {**cap,'taxonomy':CATEGORIES,'disclosure_version':'local-v1','limits':{'photo_bytes':MAX_FILE,'request_bytes':MAX_REQUEST,'pixels':20_000_000,'max_side':1280}}
    @app.get('/api/v1/boundary')
    async def boundary_geometry():
        for name in ('city-limits.geojson','gainesville.geojson','gainesville-city-limits.geojson'):
            path=ROOT/'routing'/name
            if path.is_file():return JSONResponse(json.loads(path.read_text()))
        raise Problem(503,'boundary_unavailable')
    @app.post('/api/v1/drafts',response_model=DraftResponse,status_code=201)
    async def create(request:Request,body:DraftCreate):
        async with lock:
            with store.session() as db,db.begin():
                owner=authorize(request,db,True);s=db.get(SessionRow,owner);s.expires=now()+86400
                d={'id':uid(),'revision':1,'state':'draft','created_at':stamp(now()),'updated_at':stamp(now()),'expires_at':stamp(now()+86400),'photo':None,'location':None,'user_observations':body.user_observations,'category':None,'description':'','field_sources':{'category':None,'description':None},'analysis':None,'processing_acknowledgement':None,'manual_resolution':None,'route':None,'review_revision':None,'reviewed_at':None,'prepared_revision':None,'prepared_at':None,'_config':config_digest(),'_generation':0,'_edits':{'category':0,'description':0}}
                db.add(DraftRow(id=d['id'],owner=owner,expires=now()+86400,content=encode(d)))
                result=response(d,201)
                result.set_cookie('civicfix_session',request.cookies['civicfix_session'],httponly=True,samesite='lax',max_age=86400,path='/')
                return result
    @app.get('/api/v1/drafts/{id}',response_model=DraftResponse)
    async def get(id:str,request:Request):
        with store.session() as db,db.begin():
            _,d=owned(db,id,authorize(request,db));return response(d)
    @app.patch('/api/v1/drafts/{id}',response_model=DraftResponse)
    async def patch(id:str,request:Request,body:DraftPatch):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                data=body.model_dump(exclude_unset=True);dirty=False
                for key,value in data.items():
                    if key=='location':
                        old=d.get('location'); oldinput={k:old.get(k) for k in ('latitude','longitude','label','source','accuracy')} if old else None
                        if oldinput==value:continue
                        d['location']=None if value is None else {**value,'confirmed':False,'confirmed_at':None,'boundary_status':routing().boundary(value)}
                        invalidate(d,manual=False,route=True);dirty=True
                    elif d.get(key)!=value or (key in ('category','description') and d['field_sources'].get(key)!='user'):
                        if value is None and key in ('description','user_observations'):raise Problem(422,'invalid_fields')
                        d[key]=value;dirty=True;invalidate(d,route=key=='category')
                        if key in ('category','description'):d['field_sources'][key]='user';d['_edits'][key]=d['revision']+1
                if dirty:changed(d);save(row,d)
                return response(d)
    async def photo_change(id,request,remove=False):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                if remove:data=None
                else:
                    form=await request.form(max_files=1,max_fields=0,max_part_size=MAX_FILE)
                    try:
                        entries=list(form.multi_items())
                        if len(entries)!=1 or entries[0][0]!='photo' or not hasattr(entries[0][1],'read'):raise Problem(422,'one_photo_required')
                        upload=entries[0][1];raw=await upload.read(MAX_FILE+1)
                        try:data,size=sanitize(raw,upload.content_type)
                        except ImageFailure as e:raise Problem(e.status,e.code)
                    finally:await form.close()
                await stop_job(db,d,'stale')
                previous=d.get('photo');key=uid()+'.jpg' if data else None
                if data:
                    target=store.photos/key
                    with target.open('xb') as f:f.write(data)
                    os.chmod(target,0o600)
                    info={'id':key[:-4],'mime_type':'image/jpeg','width':size[0],'height':size[1],'bytes':len(data),'preprocessing_version':'rgb-jpeg-1280-v1','preview_url':f'/api/v1/drafts/{id}/photo','download_url':f'/api/v1/drafts/{id}/photo/download'}
                    db.add(PhotoRow(id=info['id'],draft_id=id,key=key));d['_photo_digest']=digest(data)
                else:info=None;d['_photo_digest']=None
                d['photo']=info;d['_generation']+=1;d['analysis']=None;d['processing_acknowledgement']=None
                for field in ('category','description'):
                    if d['field_sources'][field]!='user':d[field]=None if field=='category' else '';d['field_sources'][field]=None
                invalidate(d,route=True);changed(d);save(row,d)
            # Commit first. A cleanup pass removes either orphan if interrupted here.
            if previous:
                with store.session() as db,db.begin():
                    p=db.get(PhotoRow,previous['id'])
                    if p:safe_unlink(store.photos/p.key);db.delete(p)
            return response(d)
    @app.put('/api/v1/drafts/{id}/photo',response_model=DraftResponse)
    async def upload(id:str,request:Request):return await photo_change(id,request)
    @app.delete('/api/v1/drafts/{id}/photo',response_model=DraftResponse)
    async def remove_photo(id:str,request:Request):return await photo_change(id,request,True)
    def read_photo(db, draft):
        if not draft['photo']:
            raise Problem(404, 'photo_unavailable')
        row = db.get(PhotoRow, draft['photo']['id'])
        path = store.photos / row.key if row and row.draft_id == draft['id'] else None
        if not path or path.is_symlink() or not path.is_file():
            raise Problem(404, 'photo_unavailable')
        try:
            return path.read_bytes()
        except FileNotFoundError:
            raise Problem(404, 'photo_unavailable') from None

    @app.get('/api/v1/drafts/{id}/photo')
    @app.get('/api/v1/drafts/{id}/photo/download')
    async def photo(id:str,request:Request):
        with store.session() as db:
            _,d=owned(db,id,authorize(request,db))
            return Response(read_photo(db,d),media_type='image/jpeg',headers={'Content-Disposition':'attachment; filename="civicfix-photo.jpg"'} if request.url.path.endswith('/download') else {})
    @app.post('/api/v1/drafts/{id}/location/confirm',response_model=DraftResponse)
    async def confirm(id:str,request:Request,body:Confirm):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d);l=d.get('location')
                if not l or not l['label'].strip():raise Problem(409,'location_not_confirmable')
                status = routing().boundary(l)
                if status == 'boundary_lookup_failed':
                    raise Problem(503, 'boundary_unavailable', 'CivicFix could not check the Gainesville boundary. Try confirming the location again.')
                if status != 'inside':raise Problem(409,'location_not_confirmable')
                if not l['confirmed']:
                    l['confirmed']=True;l['confirmed_at']=stamp(now());l['boundary_status']=status
                    invalidate(d,manual=False,route=True);changed(d);save(row,d)
                return response(d)
    async def run_analysis(id,job_id,owner,generation,edits,image):
        nonlocal active_job
        async def on_stage(stage):
            async with lock:
                with store.session() as db,db.begin():
                    job=db.get(JobRow,job_id)
                    if job:
                        value=json.loads(job.content)
                        if value['status']=='running':value['stage']=stage;job.content=encode(value)
        c = v = rejection = None
        status = 'failed'
        try:
            result=await asyncio.wait_for(manager.analyze(image,on_stage=on_stage),timeout=cfg.analysis_timeout)
            c = validated_execution(result.get('classifier'), ClassifierResult)
            outcome = c.get('result', {}).get('outcome')
            if outcome in ('unsupported', 'unclear'):
                rejection = f'classification_{outcome}'
                status = 'rejected'
            else:
                if outcome == 'supported' or 'description' in result:
                    v = validated_execution(result.get('description'), DescriptionResult)
                if c['status'] == 'ok' and v and v['status'] == 'ok':
                    status = 'succeeded'
        except asyncio.CancelledError:return
        except asyncio.TimeoutError:
            await manager.cancel();status='timed_out'
        except Exception:
            status='failed'
        async with lock:
            try:
                with store.session() as db,db.begin():
                    row,d=owned(db,id,owner)
                    job=db.get(JobRow,job_id)
                    if not job or not active(d) or d['analysis']['job_id']!=job_id or d['_generation']!=generation:return
                    a=d['analysis'];a.update(status=status,classifier=c,description=v,reason_codes=[])
                    if rejection:
                        a['reason_codes'].append(rejection)
                        for field, blank in (('category', None), ('description', '')):
                            if d['field_sources'][field] != 'user':
                                d[field] = blank
                                d['field_sources'][field] = None
                        d['route'] = None
                    if not c or c['status']!='ok':a['reason_codes'].append('classification_failed')
                    if v and v['status']!='ok':a['reason_codes'].append('description_failed')
                    if v and v['status']=='ok':
                        vr=v['result']
                        if vr['outcome']!='supported':a['reason_codes'].extend([x['code'] for x in vr['clarification_reasons']])
                        if c and c['status']=='ok' and vr['category_suggestion'] and vr['category_suggestion']!=c['result']['predicted_category']:a['reason_codes'].append('category_disagreement')
                        if d['_edits']['description']==edits['description'] and d['field_sources']['description']!='user':d['description']=vr['suggested_description'];d['field_sources']['description']='qwen'
                    if c and c['status']=='ok' and not rejection and d['_edits']['category']==edits['category'] and d['field_sources']['category']!='user':d['category']=c['result']['predicted_category'];d['field_sources']['category']='clip';d['route']=None
                    invalidate(d);changed(d);save(row,d)
                    j=json.loads(job.content);j.update(status=status,stage='finished',finished_at=stamp(now()),classifier=c,description=v,reason_codes=a['reason_codes']);job.content=encode(j)
                if cfg.mode == 'real' and c:
                    duration = real_clip_duration(c)
                    if duration is not None:
                        if not rejection:
                            predictions.labels(c['result']['predicted_category']).inc()
                        durations.observe(duration)
            except Problem:pass
            finally:
                if active_job==job_id:active_job=None
                tasks.pop(job_id,None)
    @app.post('/api/v1/drafts/{id}/analysis')
    async def analyze(id:str,request:Request,body:Analyze):
        nonlocal active_job
        async with lock:
            with store.session() as db,db.begin():
                owner=authorize(request,db,True);row,d=owned(db,id,owner);require_match(request,d)
                require_replacement_if_rejected(d)
                if active(d):raise Problem(409,'analysis_in_progress')
                if active_job:raise Problem(429,'analysis_busy')
                if not d['photo'] or not (d.get('location') or {}).get('confirmed'):raise Problem(409,'analysis_inputs_required')
                status = routing().boundary(d['location'])
                if status == 'boundary_lookup_failed':
                    raise Problem(503, 'boundary_unavailable', 'CivicFix could not check the Gainesville boundary. Try again.')
                if status != 'inside':raise Problem(409,'analysis_inputs_required')
                caps=manager.capabilities()
                states=[caps.get(k,{}).get('status') for k in ('classifier','description')]
                if any(x in ('starting','loading') for x in states):raise Problem(503,'model_not_ready')
                job_id=uid();job={'id':job_id,'job_id':job_id,'status':'running','stage':'classifying','created_at':stamp(now()),'classifier':None,'description':None,'reason_codes':[]}
                d['analysis']={'job_id':job_id,'status':'running','classifier':None,'description':None,'reason_codes':[]}
                d['processing_acknowledgement']={'disclosure_version':body.disclosure_version,'acknowledged_at':stamp(now()),'config_digest':d['_config']}
                invalidate(d);changed(d);save(row,d);db.add(JobRow(id=job_id,draft_id=id,content=encode(job)))
                p=db.get(PhotoRow,d['photo']['id']);image=(store.photos/p.key).read_bytes()
                active_job=job_id
                # Task does not run until this transaction returns to the event loop.
                tasks[job_id]=asyncio.create_task(run_analysis(id,job_id,owner,d['_generation'],dict(d['_edits']),image))
                return response(d,202,job=job)
    @app.get('/api/v1/drafts/{id}/analysis/{job_id}')
    async def job_status(id:str,job_id:str,request:Request):
        with store.session() as db,db.begin():
            _,d=owned(db,id,authorize(request,db));job=db.get(JobRow,job_id)
            if not job or job.draft_id!=id:raise Problem(404,'job_unavailable')
            return {'draft_revision':d['revision'],'job':json.loads(job.content),'current':bool(d.get('analysis') and d['analysis']['job_id']==job_id)}
    @app.post('/api/v1/drafts/{id}/analysis/{job_id}/cancel')
    async def cancel_job(id:str,job_id:str,request:Request,body:Empty):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));job=db.get(JobRow,job_id)
                if not job or job.draft_id!=id:raise Problem(404,'job_unavailable')
                if active(d) and d['analysis']['job_id']==job_id:
                    await stop_job(db,d);invalidate(d);changed(d);save(row,d)
                return response(d,job=json.loads(job.content))

    @app.get('/api/v1/drafts/{id}/feedback', response_model=FeedbackState)
    async def get_feedback(id: str, request: Request):
        async with lock:
            with store.session() as db, db.begin():
                _, draft = owned(db, id, authorize(request, db))
                job_id, executions = feedback_analysis(db, draft)
                return feedback_state(db, id, job_id, executions)

    @app.post('/api/v1/drafts/{id}/feedback', response_model=FeedbackState, status_code=201,
              responses={200: {'model': FeedbackState, 'description': 'Identical feedback already saved'}})
    async def submit_feedback(id: str, request: Request, body: FeedbackInput, reply: Response):
        async with lock:
            with store.session() as db, db.begin():
                owner = authorize(request, db, True)
                _, draft = owned(db, id, owner)
                job_id, executions = feedback_analysis(db, draft)
                values = {'kind': body.kind, 'created_at': now(), 'simulated': cfg.mode == 'fixture'}
                if isinstance(body, ExperienceFeedback):
                    target = FeedbackRow.draft_id == id
                    values['draft_id'] = id
                    payload = {'rating': body.rating, 'comment': body.comment or None}
                else:
                    if body.job_id != job_id:
                        raise Problem(409, 'feedback_target_changed', 'The analysis has changed. Review the current suggestions.')
                    execution = executions.get(body.kind)
                    if execution is None:
                        raise Problem(409, 'feedback_unavailable', 'This analysis has no result to rate for this feedback.')
                    target = FeedbackRow.job_id == job_id
                    metadata = execution.get('metadata') or {}
                    result = execution['result']
                    values.update(job_id=job_id, model_id=metadata.get('model_id'),
                                  model_revision=metadata.get('revision') or metadata.get('checkpoint_sha256'),
                                  prompt_version=metadata.get('prompt_version'),
                                  simulated=values['simulated'] or metadata.get('simulated') is True
                                  or result.get('simulated') is True)
                    payload = {'verdict': body.verdict}
                    if isinstance(body, ClassificationFeedback):
                        if body.suggested_category == result['predicted_category']:
                            raise Problem(422, 'invalid_fields', 'Choose a category different from the original prediction.')
                        values['predicted_category'] = result['predicted_category']
                        payload['suggested_category'] = body.suggested_category

                existing = db.scalar(select(FeedbackRow).where(target, FeedbackRow.kind == body.kind))
                if existing is not None:
                    if not all(getattr(existing, field) == value for field, value in payload.items()):
                        raise Problem(409, 'feedback_already_submitted', 'Feedback for this item is already saved.')
                    reply.status_code = 200
                    return feedback_state(db, id, job_id, executions)

                owner_session = db.get(SessionRow, owner)
                submitted_at = values['created_at']
                start = owner_session.feedback_window_start
                if start is None or submitted_at >= start + FEEDBACK_WINDOW:
                    owner_session.feedback_window_start = submitted_at
                    owner_session.feedback_count = 0
                elif owner_session.feedback_count >= FEEDBACK_QUOTA:
                    raise Problem(429, 'feedback_rate_limited', 'Feedback limit reached. Try again after the current 24-hour window.',
                                  retry_after=max(1, math.ceil(start + FEEDBACK_WINDOW - submitted_at)))
                owner_session.feedback_count += 1
                db.add(FeedbackRow(**values, **payload))
                return feedback_state(db, id, job_id, executions)

    @app.post('/api/v1/drafts/{id}/manual-resolution',response_model=DraftResponse)
    async def manual(id:str,request:Request,body:Resolve):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                require_replacement_if_rejected(d)
                if active(d) or not d['photo'] or not d['category'] or not d['description'].strip():raise Problem(409,'manual_fields_required')
                caps=manager.capabilities()
                if not d.get('analysis') and not any(caps.get(k,{}).get('status')=='unavailable' for k in ('classifier','description')):raise Problem(409,'analysis_attempt_required')
                d['manual_resolution']={'reason':body.reason,'corrected_at':stamp(now()),'resolved_reason_codes':(d.get('analysis') or {}).get('reason_codes',['analysis_required'])}
                d['field_sources']={'category':'user','description':'user'}
                for k in d['_edits']:d['_edits'][k]=d['revision']+1
                invalidate(d,manual=False);changed(d);save(row,d);return response(d)
    @app.post('/api/v1/drafts/{id}/destination',response_model=DraftResponse)
    async def destination(id:str,request:Request,body:Empty):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                route=routing().resolve(d.get('location'),d.get('category'))
                if d.get('route')!=route:d['route']=route;invalidate(d,manual=False);changed(d);save(row,d)
                return response(d)
    @app.post('/api/v1/drafts/{id}/review',response_model=DraftResponse)
    async def review(id:str,request:Request,body:Review):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                if missing:=reasons(d):raise Problem(409,'not_ready_for_review',reasons=missing)
                d['review_revision']=d['revision'];d['reviewed_at']=stamp(now());d['_nonemergency_confirmed']=True;save(row,d);return response(d)
    def preparation(d):
        return {'draft_id':d['id'],'prepared_revision':d['prepared_revision'],'prepared_at':d['prepared_at'],'expires_at':d['expires_at'],'photo':d['photo'],'location':d['location'],'category':d['category'],'description':d['description'],'field_sources':d['field_sources'],'user_observations':d['user_observations'],'destination':d['route'],'report_text':text(d,True),'message':MESSAGE}
    def require_prepared(d):
        if d['prepared_revision'] != d['revision'] or reasons(d):
            raise Problem(409, 'preparation_unavailable')
    @app.post('/api/v1/drafts/{id}/prepare')
    async def prepare(id:str,request:Request,body:Empty):
        async with lock:
            with store.session() as db,db.begin():
                row,d=owned(db,id,authorize(request,db,True));require_match(request,d)
                missing=reasons(d)
                if d['review_revision']!=d['revision']:missing.append('review_required')
                if missing:raise Problem(409,'not_ready_to_prepare',reasons=missing)
                if d['prepared_revision']!=d['revision']:d['prepared_revision']=d['revision'];d['prepared_at']=stamp(now());save(row,d)
                return JSONResponse(preparation(d),headers={'ETag':f'"{d["revision"]}"'})
    @app.get('/api/v1/drafts/{id}/draft.txt')
    @app.get('/api/v1/drafts/{id}/prepared.txt')
    async def download_text(id:str,request:Request):
        with store.session() as db,db.begin():
            _,d=owned(db,id,authorize(request,db));prepared=request.url.path.endswith('/prepared.txt')
            require_replacement_if_rejected(d)
            if prepared:require_prepared(d)
            return PlainTextResponse(text(d,prepared),headers={'Content-Disposition':'attachment; filename="civicfix-report.txt"'})
    @app.get('/api/v1/drafts/{id}/prepared.pdf', response_class=Response,
             responses={200: {'content': {'application/pdf': {'schema': {'type': 'string', 'format': 'binary'}}}}})
    async def download_pdf(id: str, request: Request):
        with store.session() as db, db.begin():
            _, draft = owned(db, id, authorize(request, db))
            require_replacement_if_rejected(draft)
            require_prepared(draft)
            report = preparation(draft)
            image = read_photo(db, draft)
        pdf = await run_in_threadpool(render_pdf, report, image)
        return Response(pdf, media_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="civicfix-report.pdf"'})
    @app.delete('/api/v1/drafts/{id}',status_code=204)
    async def delete_draft(id:str,request:Request):
        async with lock:
            with store.session() as db,db.begin():
                owner=authorize(request,db,True);row=db.get(DraftRow,id)
                if row and row.owner==owner:
                    d=json.loads(row.content);await stop_job(db,d);remove_files(db,id);db.delete(row)
            store.checkpoint()
            return Response(status_code=204)
    @app.exception_handler(Exception)
    async def unexpected(request,error):
        return JSONResponse({'error':{'code':'internal_error','message':'The local service could not complete this operation. Please retry.','retryable':True},'request_id':uid()},status_code=500)
    dist=ROOT/'apps/web/dist'
    if dist.is_dir():
        app.mount('/',StaticFiles(directory=dist,html=True),name='web')
    app.state.cleanup=cleanup
    return app

app=create_app()
