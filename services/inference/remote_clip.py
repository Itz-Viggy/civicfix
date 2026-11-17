"""Use the native CLIP worker without loading model runtimes into the API."""
import asyncio
from contextlib import suppress
from hashlib import sha256

import httpx

from services.inference.manager import ROOT, error, real_clip_duration, validate


class RemoteClipManager:
    def __init__(self, url, token):
        self.url = httpx.URL(url)
        if self.url.scheme not in ('http', 'https') or not self.url.host or self.url.userinfo:
            raise ValueError('CIVICFIX_CLIP_URL must be an HTTP(S) URL without credentials')
        if not token or not token.isascii():
            raise ValueError('CIVICFIX_CLIP_TOKEN must be set to an ASCII token')
        self.headers = {'Authorization': 'Bearer ' + token}
        assets = ROOT / 'experiments/first_model_exploration'
        self.config_digest = sha256(
            b'host-clip-v1' + (assets / 'model.json').read_bytes()
            + (assets / 'prompts/categories.v2.json').read_bytes()
        ).hexdigest()
        self.status = 'starting'
        self.active = None

    async def start(self):
        self.client = httpx.AsyncClient(
            base_url=self.url, headers=self.headers, trust_env=False,
            timeout=httpx.Timeout(65, connect=2),
        )
        self.health_task = asyncio.create_task(self.check_health())

    async def check_health(self):
        while True:
            try:
                async with asyncio.timeout(2):
                    response = await self.client.get('health')
                    response.raise_for_status()
                    status = response.json()['status']
                self.status = status if status in ('starting', 'ready', 'unavailable') else 'unavailable'
            except (httpx.HTTPError, TimeoutError, ValueError, TypeError, KeyError):
                self.status = 'unavailable'
            await asyncio.sleep(2)

    def capabilities(self):
        return {
            'config_digest': self.config_digest, 'ready': False, 'simulated': False,
            'classifier': {'status': self.status, 'model_id': 'OpenCLIP ViT-B-32'},
            'description': {'status': 'unavailable'},
        }

    async def analyze(self, image_bytes, on_stage=None):
        self.active = asyncio.current_task()
        try:
            if on_stage:
                await on_stage('classifier')
            result = await self.classify(image_bytes)
            return {'classifier': result, 'description': error('model_unavailable')}
        finally:
            self.active = None

    async def classify(self, image_bytes):
        try:
            async with asyncio.timeout(65):
                response = await self.client.post(
                    'classify', content=image_bytes, headers={'Content-Type': 'image/jpeg'},
                )
                response.raise_for_status()
            result = response.json()
            if result.get('status') == 'error':
                code = result.get('error', {}).get('code')
                return error(code if code in ('timeout', 'model_unavailable') else 'invalid_output')
            if real_clip_duration(result) is None:
                return error('invalid_output')
            return validate('classifier', result)
        except (httpx.TimeoutException, TimeoutError):
            return error('timeout')
        except httpx.HTTPError:
            return error('model_unavailable')
        except (ValueError, KeyError, TypeError, AttributeError, AssertionError):
            return error('invalid_output')

    async def cancel(self):
        task = self.active
        if task and task is not asyncio.current_task():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def close(self):
        await self.cancel()
        self.health_task.cancel()
        with suppress(asyncio.CancelledError):
            await self.health_task
        await self.client.aclose()
