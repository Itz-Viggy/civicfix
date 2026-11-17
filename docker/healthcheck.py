"""Check API liveness and, for the legacy runtime, both model workers."""
import json
import sys
import urllib.request

def check(live_only=False):
    def get(path):
        with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/'+path, timeout=3) as response:
            return json.load(response)
    assert get('health/live')['status'] == 'ok'
    if not live_only:
        cap = get('capabilities')
        assert cap['ready'] and all(cap[k]['status']=='ready' for k in ('classifier','description'))

if __name__ == '__main__':
    check(live_only='--live-only' in sys.argv[1:])
