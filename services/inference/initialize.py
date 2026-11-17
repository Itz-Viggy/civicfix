"""Download pinned public artifacts atomically; verify before reuse and loading."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import time
from services.inference.settings import ROOT, models

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def verify(path, files):
    for name, digest in files.items():
        if sha256(path / name) != digest:
            raise ValueError(f'Model checksum mismatch: {name}')

def download(url, target, digest):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256(target) == digest:
        return
    partial = target.with_name(target.name + '.partial')
    for attempt in range(3):
        try:
            print(f'Downloading {target.name}', flush=True)
            with urllib.request.urlopen(url, timeout=120) as source, partial.open('wb') as dest:
                while block := source.read(1024 * 1024):
                    dest.write(block)
            if sha256(partial) != digest:
                raise ValueError(f'Model checksum mismatch: {target.name}')
            os.replace(partial, target)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def main():
    if os.getenv('CIVICFIX_MODE', 'real') == 'fixture':
        print('Explicit fixture mode: no models required', flush=True)
        return
    cfg = json.loads((ROOT/'experiments/first_model_exploration/model.json').read_text())
    download(cfg['source_url'], models()/'clip/ViT-B-32.pt', cfg['sha256'])
    manifest = json.loads((ROOT/'services/inference/qwen_cpu_artifact.json').read_text())
    path = models()/'qwen3-vl-4b-cpu'
    for name, digest in manifest['files'].items():
        download(f"https://huggingface.co/{manifest['artifact_id']}/resolve/{manifest['revision']}/{name}", path/name, digest)
    verify(path, manifest['files'])
    print('All model artifacts verified', flush=True)

if __name__ == '__main__':
    main()
