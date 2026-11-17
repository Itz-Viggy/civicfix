import asyncio
import hashlib
import json
import sys
import pytest
from services.inference import initialize, settings
from services.inference.manager import InferenceManager

def test_verified_atomic_download_reuse_and_repair(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'weights')
    target=tmp_path/'models/weights';digest=hashlib.sha256(b'weights').hexdigest()
    initialize.download(source.as_uri(),target,digest)
    source.unlink()
    initialize.download(source.as_uri(),target,digest)  # Verified cache is offline-safe.
    target.write_bytes(b'corrupt')
    with pytest.raises(ValueError):initialize.verify(target.parent,{'weights':digest})
    source.write_bytes(b'weights')
    initialize.download(source.as_uri(),target,digest)
    assert target.read_bytes()==b'weights' and not target.with_suffix('.partial').exists()

def test_bad_download_never_publishes(tmp_path,monkeypatch):
    monkeypatch.setattr(initialize.time,'sleep',lambda _:None)
    source=tmp_path/'source';source.write_bytes(b'corrupt')
    target=tmp_path/'model'
    with pytest.raises(ValueError):initialize.download(source.as_uri(),target,'0'*64)
    assert not target.exists()

def test_backend_defaults_and_digest(monkeypatch):
    monkeypatch.delenv('CIVICFIX_QWEN_BACKEND',raising=False)
    native=InferenceManager().capabilities()
    assert settings.backend()=='mlx'
    monkeypatch.setenv('CIVICFIX_QWEN_BACKEND','transformers')
    cpu=InferenceManager().capabilities()
    assert native['config_digest']!=cpu['config_digest']
    assert 'CPU' in cpu['description']['model_id']
    monkeypatch.setenv('CIVICFIX_QWEN_BACKEND','invalid')
    with pytest.raises(ValueError):InferenceManager()

def test_stage_timeout_reaps_worker(monkeypatch):
    monkeypatch.setenv('CIVICFIX_CLASSIFIER_TIMEOUT','.01')
    async def scenario():
        manager=InferenceManager()
        async def no_restart(kind):manager.states[kind]='unavailable'
        manager._load=no_restart
        worker=await asyncio.create_subprocess_exec(sys.executable,'-c','import sys,time;sys.stdin.readline();time.sleep(300)',stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE)
        manager.workers['classifier']=worker
        manager.states={'classifier':'ready','description':'unavailable'}
        result=await manager.analyze(b'pixels')
        assert result['classifier']['error']['code']=='timeout'
        assert worker.returncode is not None
        await manager.close()
    asyncio.run(scenario())
