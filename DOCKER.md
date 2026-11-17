# CivicFix Module 8 with Docker

Docker Compose runs the existing React/FastAPI app, Prometheus, and Grafana. The app image uses SQLite and contains only application dependencies. OpenCLIP runs on the same Mac in the native environment. The demo accepts real CLIP suggestions and uses the existing manual confirmation flow for descriptions.

## Start on macOS with Docker Desktop

Run from the repository root. Use the API and native CLIP environments in [README](README.md#local-application). On an existing checkout, refresh the API environment for the metrics dependency.

```sh
.venv-api/bin/python -m pip install -r services/api/requirements.lock
docker info
```

Generate the local token once and start native CLIP in the first terminal.

```sh
mkdir -p .runtime/module8
if [ ! -s .runtime/module8/clip.env ]; then
  (umask 077; printf 'CIVICFIX_CLIP_TOKEN=%s\n' "$(openssl rand -hex 32)" > .runtime/module8/clip.env)
fi
set -a
. ./.runtime/module8/clip.env
set +a
CIVICFIX_CLASSIFIER_TIMEOUT=60 .venv-api/bin/python -m uvicorn \
  services.inference.host_clip:app --host 127.0.0.1 --port 8001 --workers 1 --no-access-log
```

Start the stack in a second terminal.

```sh
docker compose --env-file .runtime/module8/clip.env up -d --build --wait
docker compose --env-file .runtime/module8/clip.env ps
curl -fsS http://127.0.0.1:8000/api/v1/health/live
curl -fsS http://127.0.0.1:8000/api/v1/capabilities
```

- **CivicFix** at [127.0.0.1:8000](http://127.0.0.1:8000). Wait for `classifier.status` to be `ready`. Select **Analyze photo** after uploading a JPEG and confirming a location inside Gainesville. **Original AI suggestions** displays the CLIP category. With Qwen unavailable, enter a factual description and use **Confirm my category and description** before proceeding to review.
- **Prometheus** at [127.0.0.1:9090/targets](http://127.0.0.1:9090/targets). It scrapes `app:8000/metrics` every 15 seconds. Target **UP** confirms scraping. The classifier status is separate.
- **Grafana** at [127.0.0.1:3000/d/civicfix-module8/civicfix-module-8](http://127.0.0.1:3000/d/civicfix-module8/civicfix-module-8). This loopback instance has anonymous Viewer access to the provisioned dashboard. The category panel counts real committed predictions. The processing-time panel shows the cumulative mean CLIP worker duration in seconds.

Compose reaches the host listener at `host.docker.internal:8001` by default. Use the same runtime token for the native service and Compose. The browser uses the app's existing same-origin API and never calls the native listener. To diagnose missing classifier readiness, check the host wrapper logs and verify Docker can reach that address. Keep the listener private.

## Verify and restart

```sh
compose() { docker compose --env-file .runtime/module8/clip.env "$@"; }
compose exec -T app python docker/smoke.py create --clip-only
compose restart app
compose up -d --wait
compose exec -T app python docker/smoke.py verify
compose down
compose up -d --wait
compose exec -T app python docker/smoke.py verify
compose exec -T app python docker/smoke.py delete
```

The smoke uses one real CLIP result and manual report details. Verification checks the same unexpired session, draft, prepared text, and photo. The named `app-data` volume retains SQLite and photos across normal restarts and `down`. Drafts still expire after 24 hours. `down -v` deletes the app data. App metric counters start at zero after an app restart, so keep the app running through both demo batches.

For the labeled fixture browser suite, stop the main stack first to free port 8000. Use an isolated project.

```sh
CIVICFIX_MODE=fixture docker compose -p civicfix-fixture up -d --build --wait app
CIVICFIX_MODE=fixture docker compose -p civicfix-fixture --profile test \
  run --rm browser-test npm run e2e -- workflow.spec.ts
docker compose -p civicfix-fixture down
```

Fixture predictions leave both monitoring metrics unchanged. Stop the demo with `compose down` and stop the native wrapper with Ctrl+C.

## Prior verification of the legacy Docker runtime

Verified on Linux arm64 in Docker Desktop: production image build; isolated CPU runtime imports; all 27 API/inference tests; all 6 frontend unit tests; frontend type/build/contract checks; all 6 Chromium/mobile-WebKit browser scenarios against the built frontend; simulated HTTP preparation/download/deletion; and SQLite/session/photo persistence across container restart and recreation. Linux amd64 dependency resolution was checked, but an amd64 image was not executed.

Public models downloaded into a fresh named volume and passed the pinned hash checks. Cache reuse also passed with networking disabled and the model volume mounted read-only. Both real workers reached readiness with networking disabled. Real CLIP classified the existing pothole photo successfully. With Docker allocated 20 GiB on this 24-GiB Mac, Qwen was killed during generation; the container's `memory.events` reported `oom_kill=1`. **The full real description/report workflow has not passed on this machine.** Successful simulated tests do not establish real inference success. This historical result applies to the legacy two-model runtime.
