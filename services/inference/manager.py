"""Replaceable local inference orchestration, with process-level cancellation."""
import asyncio, base64, json, math, time, hashlib
from pathlib import Path
from contextlib import suppress
ROOT=Path(__file__).resolve().parents[2]
CATEGORIES=['pothole','broken_streetlight','damaged_sign','leaking_hydrant','illegal_dumping']

def error(code):
    return {'status':'error','error':{'code':code,'message':{'timeout':'Model exceeded its time budget.','model_unavailable':'Local model is unavailable.','invalid_output':'Model response failed validation.'}.get(code,'Model processing stopped.')}}

def validate(kind,value):
    if value.get('status')!='ok': return value
    r=value['result']
    if kind=='classifier':
        scores=r['scores']; assert set(scores)==set(CATEGORIES)
        assert all(isinstance(v,(float,int)) and math.isfinite(v) and -1.00001<=v<=1.00001 for v in scores.values())
        order=sorted(CATEGORIES,key=lambda c:-scores[c])
        assert r['predicted_category']==order[0]
        assert abs(r['top1_margin']-(scores[order[0]]-scores[order[1]]))<1e-5
    else:
        assert set(r)=={'category_suggestion','outcome','visible_observations','suggested_description','clarification_reasons'}
        assert r['category_suggestion'] in [None,*CATEGORIES]
        assert r['outcome'] in ['supported','unclear','unsupported']
        obs=r['visible_observations']; text=r['suggested_description']; reasons=r['clarification_reasons']
        assert isinstance(obs,list) and len(obs)<=10 and all(isinstance(x,str) and 0<len(x.strip())<=500 for x in obs)
        assert isinstance(text,str) and len(text)<=2000 and len(text.split())<=60
        import re
        assert len(re.findall(r'[.!?](?:\s|$)',text))<=2
        assert isinstance(reasons,list) and len(reasons)<=10
        codes={'poor_image_quality','no_supported_issue','multiple_issues','insufficient_visual_evidence','operating_status_not_visible','other_uncertainty'}
        assert all(isinstance(x,dict) and set(x)<= {'code','detail'} and x.get('code') in codes and isinstance(x.get('detail',''),str) and len(x.get('detail',''))<=500 for x in reasons)
        if r['outcome']=='supported': assert r['category_suggestion'] and text.strip() and obs and not reasons
        else: assert reasons
        if r['outcome']=='unsupported': assert r['category_suggestion'] is None
    return value

class InferenceManager:
    def __init__(self,mode='real'):
        self.mode=mode; self.workers={}; self.states={k:'starting' for k in ['classifier','description']}; self.start_tasks=[]; self.active=None
    async def start(self):
        if self.mode=='fixture': self.states={k:'ready' for k in self.states}; return
        self.start_tasks=[asyncio.create_task(self._load(k)) for k in self.states]
    async def _load(self,kind):
        self.states[kind]='starting'
        exe=ROOT/f'.venv-inference/{"clip" if kind=="classifier" else "qwen"}/bin/python'
        try:
            p=await asyncio.create_subprocess_exec(str(exe),str(ROOT/'services/inference/worker.py'),kind,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,limit=65537)
            self.workers[kind]=p
            msg=json.loads(await asyncio.wait_for(p.stdout.readline(),120))
            if not msg.get('ready'): raise RuntimeError()
            self.states[kind]='ready'
        except Exception:
            await self._stop(kind); self.states[kind]='unavailable'
    def capabilities(self):
        config_digest=hashlib.sha256(b''.join((ROOT/p).read_bytes() for p in ['services/inference/description_prompt.txt','experiments/first_model_exploration/model.json','experiments/first_model_exploration/prompts/categories.v2.json','experiments/description_evaluation/settings.json'])+self.mode.encode()).hexdigest()
        return {'config_digest':config_digest,'ready':all(s=='ready' for s in self.states.values()),'simulated':self.mode=='fixture','classifier':{'status':self.states['classifier'],'model_id':'OpenCLIP ViT-B-32'},'description':{'status':self.states['description'],'model_id':'Qwen3-VL-4B-Instruct (MLX 4-bit)'}}
    async def _stop(self,kind):
        p=self.workers.pop(kind,None)
        if p and p.returncode is None:
            with suppress(ProcessLookupError): p.terminate()
            try: await asyncio.wait_for(p.wait(),2)
            except asyncio.TimeoutError:
                with suppress(ProcessLookupError): p.kill()
                await p.wait()
    async def analyze(self,image_bytes,on_stage=None):
        self.active=asyncio.current_task(); out={}; started=time.monotonic()
        try:
            for kind,budget in [('classifier',10),('description',45)]:
                if on_stage:
                    v=on_stage(kind)
                    if hasattr(v,'__await__'): await v
                if self.mode=='fixture':
                    await asyncio.sleep(.05)
                    result=({'predicted_category':'pothole','scores':dict(zip(CATEGORIES,[.8,.1,.2,.0,.15])),'top1_margin':.6,'mode':'closed_set','score_kind':'cosine_similarity'} if kind=='classifier' else {'category_suggestion':'pothole','outcome':'supported','visible_observations':['Missing pavement is visible.'],'suggested_description':'A section of pavement is missing from the road surface.','clarification_reasons':[]})
                    out[kind]={'status':'ok','result':result,'metadata':{'simulated':True,'model_id':'fixtures-v1'}}; continue
                if self.states[kind]!='ready': out[kind]=error('model_unavailable'); continue
                raw=None
                try:
                    p=self.workers[kind]
                    p.stdin.write((json.dumps({'image':base64.b64encode(image_bytes).decode()})+'\n').encode()); await p.stdin.drain()
                    timeout=min(budget,60-(time.monotonic()-started))
                    raw=await asyncio.wait_for(p.stdout.readline(),max(.01,timeout))
                    out[kind]=validate(kind,json.loads(raw))
                except asyncio.TimeoutError:
                    out[kind]=error('timeout'); await self._stop(kind); self.start_tasks.append(asyncio.create_task(self._load(kind)))
                except Exception:
                    out[kind]=error('invalid_output')
                    if raw is None or not raw:
                        await self._stop(kind);self.start_tasks.append(asyncio.create_task(self._load(kind)))
            return out
        except asyncio.CancelledError:
            loaders=[t for t in self.start_tasks if not t.done()]
            for t in loaders:t.cancel()
            await asyncio.gather(*loaders,return_exceptions=True)
            await asyncio.gather(*(self._stop(k) for k in self.workers.copy()))
            if self.mode!='fixture': self.start_tasks.extend(asyncio.create_task(self._load(k)) for k in self.states)
            raise
        finally: self.active=None
    async def cancel(self):
        task=self.active
        if task and task is not asyncio.current_task():
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
    async def close(self):
        await self.cancel()
        for t in self.start_tasks: t.cancel()
        await asyncio.gather(*self.start_tasks,return_exceptions=True)
        await asyncio.gather(*(self._stop(k) for k in self.workers.copy()))
