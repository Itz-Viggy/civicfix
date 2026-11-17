import asyncio

from services.inference.host_clip import create_app


def test_private_worker_cancels_on_http_disconnect(monkeypatch):
    monkeypatch.setenv('CIVICFIX_CLIP_TOKEN', 'test-token')

    async def scenario():
        started = asyncio.Event()
        cancelled = asyncio.Event()

        class Worker:
            async def start(self):
                pass

            async def close(self):
                pass

            def capabilities(self):
                return {'classifier': {'status': 'ready'}}

            async def analyze(self, image):
                assert image == b'jpeg'
                started.set()
                try:
                    await asyncio.Future()
                finally:
                    cancelled.set()

        app = create_app(Worker())
        scope = {
            'type': 'http', 'path': '/classify', 'method': 'POST', 'query_string': b'',
            'headers': [(b'content-type', b'image/jpeg')],
        }
        messages = []

        async def send(message):
            messages.append(message)

        incoming = asyncio.Queue()
        async with app.router.lifespan_context(app):
            await app(scope, incoming.get, send)
            assert messages[0]['status'] == 401

            scope = {**scope, 'headers': [*scope['headers'], (b'authorization', b'Bearer test-token')]}
            incoming.put_nowait({'type': 'http.request', 'body': b'jpeg', 'more_body': False})
            request = asyncio.create_task(app(scope, incoming.get, send))
            await asyncio.wait_for(started.wait(), 1)
            incoming.put_nowait({'type': 'http.disconnect'})
            await asyncio.wait_for(request, 1)
            assert cancelled.is_set()

    asyncio.run(scenario())
