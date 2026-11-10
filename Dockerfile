# syntax=docker/dockerfile:1
FROM node:26.10.0-bookworm-slim AS web-dependencies
WORKDIR /workspace/apps/web
COPY apps/web/package*.json ./
RUN npm ci
FROM web-dependencies AS web
COPY apps/web/ ./
COPY contracts/ /workspace/contracts/
RUN npm run build
FROM web AS web-test
RUN npm test && npm run check:contracts
CMD ["npm", "test"]
FROM web-dependencies AS browser-test
RUN npx playwright install --with-deps chromium webkit
COPY apps/web/playwright.config.ts ./
COPY apps/web/e2e/ ./e2e/
COPY data/ /workspace/data/
ENV CIVICFIX_E2E_BASE_URL=http://127.0.0.1:8000
CMD ["npm", "run", "e2e"]

FROM python:3.12.15-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /workspace
FROM python-base AS api-dependencies
COPY services/api/requirements.lock /tmp/api.lock
RUN python -m venv /opt/api && /opt/api/bin/pip install --no-cache-dir -r /tmp/api.lock

FROM python-base AS model-dependencies
COPY docker/requirements-clip.lock docker/requirements-qwen.lock /tmp/
RUN python -m venv /opt/clip && /opt/clip/bin/pip install --no-cache-dir -r /tmp/requirements-clip.lock
RUN python -m venv /opt/qwen && /opt/qwen/bin/pip install --no-cache-dir -r /tmp/requirements-qwen.lock

FROM python-base AS playground
ENV MPLBACKEND=Agg
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY playground.ipynb ./
CMD ["python", "scripts/execute_notebook.py"]

FROM python-base AS app-base
RUN groupadd --gid 10001 civicfix && useradd --uid 10001 --gid civicfix --create-home civicfix \
    && install -d -o civicfix -g civicfix /var/lib/civicfix
COPY --from=api-dependencies /opt/api/ /opt/api/
COPY services/ ./services/
COPY experiments/ ./experiments/
COPY scripts/ ./scripts/
COPY routing/ ./routing/
COPY data/ ./data/
COPY config/ ./config/
COPY docker/ ./docker/
COPY --from=web /workspace/apps/web/dist/ ./apps/web/dist/
ENV PATH=/opt/api/bin:$PATH PYTHONPATH=/workspace/services/api:/workspace CIVICFIX_DATA_DIR=/var/lib/civicfix
USER civicfix
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "civicfix.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]

FROM app-base AS application
USER root
RUN install -d -o civicfix -g civicfix /var/lib/civicfix-models
COPY --from=model-dependencies /opt/ /opt/
ENV CIVICFIX_QWEN_BACKEND=transformers CIVICFIX_MODEL_DIR=/var/lib/civicfix-models \
    CIVICFIX_CLIP_PYTHON=/opt/clip/bin/python CIVICFIX_QWEN_PYTHON=/opt/qwen/bin/python \
    CIVICFIX_MODEL_LOAD_TIMEOUT=600 CIVICFIX_CLASSIFIER_TIMEOUT=60 \
    CIVICFIX_DESCRIPTION_TIMEOUT=900 CIVICFIX_ANALYSIS_TIMEOUT=1020
USER civicfix
HEALTHCHECK --interval=15s --timeout=5s --start-period=650s --retries=3 CMD ["python", "docker/healthcheck.py"]
FROM application AS api-test
CMD ["python", "-m", "pytest", "services/api/tests", "services/inference/tests", "-q", "-o", "cache_dir=/tmp/pytest-cache"]
FROM application AS runtime

FROM app-base AS module8
ENV CIVICFIX_CLIP_URL=http://host.docker.internal:8001 CIVICFIX_ANALYSIS_TIMEOUT=75
HEALTHCHECK --interval=5s --timeout=4s --start-period=15s --retries=3 CMD ["python", "docker/healthcheck.py", "--live-only"]
