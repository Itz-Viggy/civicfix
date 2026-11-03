#!/usr/bin/env python3
"""Local launcher; no deployment, hosted services, or automatic model downloads."""
import argparse,os,signal,subprocess,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('command',choices=['dev','start','test','setup','schema']);p.add_argument('--fixture',action='store_true');args=p.parse_args()
api=ROOT/'.venv-api/bin/python'
env={**os.environ,'PYTHONPATH':str(ROOT/'services/api')+os.pathsep+str(ROOT),'CIVICFIX_MODE':'fixture' if args.fixture else 'real'}
def run(cmd,**kw):return subprocess.run(cmd,cwd=ROOT,env=env,check=True,**kw)
if args.command=='setup':
    if not api.exists():
        bootstrap=shutil.which('python3.12') or str(ROOT/'.venv/bin/python')
        if not Path(bootstrap).exists():p.error('Install Python 3.12 before setup.')
        run([bootstrap,'-m','venv',str(ROOT/'.venv-api')])
    run([str(api),'-m','pip','install','-r','services/api/requirements.lock'])
    subprocess.run(['npm','ci'],cwd=ROOT/'apps/web',check=True)
elif args.command=='test':run([str(api),'-m','pytest','services/api/tests','services/inference/tests','-q'])
elif args.command=='schema':
    import json
    sys.path[:0]=[str(ROOT/'services/api'),str(ROOT)]
    from civicfix.main import app
    (ROOT/'contracts').mkdir(exist_ok=True)
    (ROOT/'contracts/openapi.json').write_text(json.dumps(app.openapi(),indent=2)+'\n')
else:
    children=[]
    def stop(*_):
        for c in children:
            if c.poll() is None:c.send_signal(signal.SIGTERM)
        for c in children:
            try:c.wait(timeout=5)
            except subprocess.TimeoutExpired:c.kill()
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    try:
        children.append(subprocess.Popen([str(api),'-m','uvicorn','civicfix.main:app','--host','127.0.0.1','--port','8000','--no-access-log'],cwd=ROOT,env=env))
        if args.command=='dev':children.append(subprocess.Popen(['npm','run','dev','--','--host','127.0.0.1'],cwd=ROOT/'apps/web',env=env))
        print('CivicFix: http://127.0.0.1:'+('5173' if args.command=='dev' else '8000'),flush=True)
        while all(c.poll() is None for c in children):time.sleep(.25)
    finally:stop()
