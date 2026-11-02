import asyncio
import pytest
from services.inference.manager import InferenceManager,validate

def test_fixture_pipeline():
    async def scenario():
        m=InferenceManager('fixture');await m.start();r=await m.analyze(b'pixels')
        assert validate('classifier',r['classifier'])['result']['predicted_category']=='pothole'
        assert validate('description',r['description'])['result']['outcome']=='supported'
        assert r['description']['metadata']['simulated'];await m.close()
    asyncio.run(scenario())

def test_inconsistent_classifier_rejected():
    r={'status':'ok','result':{'predicted_category':'damaged_sign','scores':dict(zip(['pothole','broken_streetlight','damaged_sign','leaking_hydrant','illegal_dumping'],[.8,.1,.2,0,.1])),'top1_margin':.6}}
    with pytest.raises(AssertionError):validate('classifier',r)

def test_supported_without_observations_rejected():
    with pytest.raises(AssertionError):validate('description',{'status':'ok','result':{'category_suggestion':'pothole','outcome':'supported','suggested_description':'A hole.','visible_observations':[],'clarification_reasons':[]}})

def test_cancellation_reaps_compute_before_return():
    import sys
    async def scenario():
        m=InferenceManager('real')
        async def no_restart(kind):m.states[kind]='unavailable'
        m._load=no_restart
        p=await asyncio.create_subprocess_exec(sys.executable,'-c','import sys,time; sys.stdin.readline(); time.sleep(300)',stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE)
        m.workers['classifier']=p;m.states={'classifier':'ready','description':'unavailable'}
        task=asyncio.create_task(m.analyze(b'pixels'))
        await asyncio.sleep(.05);await m.cancel()
        assert task.cancelled() and p.returncode is not None
        await m.close()
    asyncio.run(scenario())
