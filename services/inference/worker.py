"""Private persistent model process: pixels in, bounded JSON out. No report metadata."""
import base64, contextlib, io, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
from services.inference.settings import backend, models
wire = sys.stdout

def send(value):
    data = json.dumps(value, allow_nan=False)
    if len(data.encode()) > 65536:
        data = json.dumps({'status':'error','error':{'code':'invalid_output','message':'Model output exceeded limit.'}})
    wire.write(data+'\n'); wire.flush()

kind = sys.argv[1]
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from PIL import Image
        if kind == 'classifier':
            from experiments.first_model_exploration.benchmark import Runtime, load_prompts
            cfg = json.loads((ROOT/'experiments/first_model_exploration/model.json').read_text())
            runtime = Runtime(models()/'clip/ViT-B-32.pt', cfg['sha256'])
            runtime.set_prompts(load_prompts(ROOT/'experiments/first_model_exploration/prompts/categories.v2.json'))
            metadata = {'adapter':'openclip_local','model_id':'ViT-B-32','checkpoint_sha256':cfg['sha256'],'prompt_version':'v2-dumping-visual-coverage','simulated':False}
        else:
            settings = json.loads((ROOT/'experiments/description_evaluation/settings.json').read_text())
            if backend()=='mlx':
                from experiments.description_evaluation.runtime import MLXGenerator
                runtime = MLXGenerator(models()/'qwen3-vl-4b-4bit', settings, json.loads((ROOT/'experiments/description_evaluation/qwen_artifact.json').read_text()))
            if backend()=='transformers':
                from services.inference.cpu import CPUGenerator
                manifest=json.loads((ROOT/'services/inference/qwen_cpu_artifact.json').read_text())
                runtime=CPUGenerator(models()/'qwen3-vl-4b-cpu', settings, manifest)
            prompt = (ROOT/'services/inference/description_prompt.txt').read_text()
            metadata = {'adapter':'qwen_mlx_local','model_id':settings['artifact_id'],'revision':settings['artifact_revision'],'prompt_version':'app-description-v1','simulated':False}
    if kind != 'classifier' and backend()=='transformers':
        metadata.update(adapter='qwen_transformers_cpu',model_id=manifest['artifact_id'],revision=manifest['revision'],device='cpu',runtime='transformers-float32')
    send({'ready':True,'metadata':metadata})
except Exception as exc:
    print(f'Model {kind} initialization failed ({type(exc).__name__})', file=sys.stderr, flush=True)
    send({'ready':False,'error':'model_unavailable'}); sys.exit(1)
while True:
    line=sys.stdin.readline(8*1024*1024+1)
    if not line: break
    if len(line) > 8*1024*1024: break
    started=time.monotonic()
    try:
        data=json.loads(line)
        image=Image.open(io.BytesIO(base64.b64decode(data['image'],validate=True))).convert('RGB')
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if kind=='classifier': result=runtime.classify(image)[0]
            else:
                raw=runtime.generate(image,prompt).strip()
                if raw.startswith('```json\n') and raw.endswith('\n```'): raw=raw[8:-4]
                result=json.loads(raw)
        send({'status':'ok','result':result,'metadata':{**metadata,'duration_seconds':time.monotonic()-started,'preprocessing_version':'rgb-jpeg-1280-v1'}})
    except Exception as exc:
        print(f'Model {kind} generation failed ({type(exc).__name__})', file=sys.stderr, flush=True)
        send({'status':'error','error':{'code':'invalid_output','message':'The model could not produce a valid result.'}})
