"""Private native HTTP entry point for the existing OpenCLIP worker."""
import asyncio
from contextlib import asynccontextmanager
import os
import secrets

from fastapi import FastAPI, HTTPException, Request
from starlette.requests import ClientDisconnect

from services.api.civicfix.images import MAX_FILE
from services.inference.manager import InferenceManager


async def wait_for_disconnect(request):
    while (await request.receive())['type'] != 'http.disconnect':
        pass


def create_app(manager=None):
    manager = manager if manager is not None else InferenceManager(classifier_only=True)
    slot = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app):
        token = os.environ.get('CIVICFIX_CLIP_TOKEN')
        if not token or not token.isascii():
            raise RuntimeError('CIVICFIX_CLIP_TOKEN must be set to an ASCII token')
        app.state.authorization = 'Bearer ' + token
        await manager.start()
        try:
            yield
        finally:
            await manager.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def authorize(request):
        supplied = request.headers.get('authorization', '').encode('latin-1')
        if not secrets.compare_digest(supplied, app.state.authorization.encode('ascii')):
            raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})

    @app.get('/health')
    async def health(request: Request):
        authorize(request)
        return manager.capabilities()['classifier']

    @app.post('/classify')
    async def classify(request: Request):
        authorize(request)
        if request.headers.get('content-type') != 'image/jpeg':
            raise HTTPException(415, 'JPEG body required')
        if slot.locked() or manager.capabilities()['classifier']['status'] != 'ready':
            raise HTTPException(503, 'Classifier unavailable or busy')
        async with slot:
            image = bytearray()
            try:
                async with asyncio.timeout(5):
                    async for chunk in request.stream():
                        if len(image) + len(chunk) > MAX_FILE:
                            raise HTTPException(413, 'Image too large')
                        image.extend(chunk)
            except TimeoutError:
                raise HTTPException(408, 'Image upload timed out') from None
            except ClientDisconnect:
                return
            if not image:
                raise HTTPException(400, 'Image required')

            prediction = asyncio.create_task(manager.analyze(image))
            disconnected = asyncio.create_task(wait_for_disconnect(request))
            try:
                await asyncio.wait((prediction, disconnected), return_when=asyncio.FIRST_COMPLETED)
                if prediction.done():
                    return prediction.result()['classifier']
            finally:
                prediction.cancel()
                disconnected.cancel()
                await asyncio.gather(prediction, disconnected, return_exceptions=True)

    return app


app = create_app()
