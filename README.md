# CivicFix

CivicFix is a local web application for preparing nonemergency reports for
the City of Gainesville, Florida. Users upload a photo, confirm the location,
review locally generated suggestions, correct the report details, and copy or
download the final report for submission through the appropriate official
channel.

CivicFix does not submit reports on a user's behalf. It does not require a
cloud account or API key, and photos are processed locally.

## Features

- Photo-based issue classification and description assistance
- Location confirmation with Gainesville boundary and road data
- Support for potholes, broken streetlights, damaged signs, leaking hydrants,
  and illegal dumping
- Manual editing and confirmation before a report is prepared
- Optional AI suggestion feedback and a 1–5 app rating during report review
- Printable PDF with the issue photo, plus plain-text copy and download options
- Local storage with automatic expiration of runtime drafts and photos
- Fixture mode for deterministic development and automated tests

## Requirements

- macOS on Apple Silicon for the local Qwen inference adapter
- Python 3.12
- Node.js and npm
- 24 GB of memory recommended when running both local models

The application can run in fixture mode without the local model environments.

## Quick start

From the repository root:

```sh
python3.12 -m venv .venv-api
.venv-api/bin/python -m pip install -r services/api/requirements.lock
cd apps/web
npm ci
cd ../..
.venv-api/bin/python scripts/civicfix.py dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

The development launcher starts the API on port `8000` and the Vite
development server on port `5173`. Press `Ctrl+C` to stop both processes.

To run without the development server:

```sh
cd apps/web
npm run build
cd ../..
.venv-api/bin/python scripts/civicfix.py start
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

For a deterministic local run without model services:

```sh
.venv-api/bin/python scripts/civicfix.py dev --fixture
```

## Local model setup

Real inference requires the pinned model environments and publicly available
model weights. Set them up explicitly:

```sh
python3.12 -m venv .venv-inference/clip
.venv-inference/clip/bin/python -m pip install \
  -r experiments/first_model_exploration/requirements-macos.lock
.venv-inference/clip/bin/python \
  -m experiments.first_model_exploration.setup_model

python3.12 -m venv .venv-inference/qwen
.venv-inference/qwen/bin/python -m pip install \
  -r experiments/description_evaluation/requirements-qwen-macos.lock
HF_HUB_DISABLE_XET=1 .venv-inference/qwen/bin/python \
  -m experiments.description_evaluation.setup_model
```

The CLIP and Qwen environments use separate lock files because their
dependencies are different. Model downloads occur during setup; application
inference uses the local weights.

## Docker

Docker Compose runs the web application and optional Prometheus and Grafana
services. The CLIP service runs natively on the host. See
[DOCKER.md](DOCKER.md) for setup, environment variables, health checks, and
troubleshooting.

Start the application stack after completing the Docker instructions:

```sh
docker compose up -d --build --wait
```

The application is available at
[http://127.0.0.1:8000](http://127.0.0.1:8000). Prometheus uses port `9090`
and Grafana uses port `3000`.

## Testing

Run the API and inference tests:

```sh
.venv-api/bin/python scripts/civicfix.py test
```

Run the frontend checks:

```sh
cd apps/web
npm run generate:types
npm run check:contracts
npm run typecheck
npm test
npm run build
```

Run browser tests after installing the Playwright browsers:

```sh
npx playwright install chromium webkit
npm run e2e
```

Return to the repository root with `cd ../..`.

### Real-model browser checks

The opt-in browser suite uploads a pothole photo, a NASA astronaut portrait,
and a deliberately blurred copy of the pothole photo. The portrait and blurred
photo must stop at classification. The clear photo must keep the model
suggestions and the entered observation in the downloaded report.

Prepare the two additional test images from the repository root.

```sh
mkdir -p .runtime/goal-photo-verification
curl -fL https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/astronaut.png \
  -o .runtime/goal-photo-verification/astronaut.png
.venv-api/bin/python - <<'PY'
from PIL import Image, ImageFilter

with Image.open('data/images/commons-0a68e3b438.jpg') as photo:
    photo.convert('RGB').filter(ImageFilter.GaussianBlur(32)).save(
        '.runtime/goal-photo-verification/blurred-pavement.jpg', quality=90)
PY
```

The [NASA portrait](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.astronaut)
is public domain. The [pothole photo by Thomas Booker](https://commons.wikimedia.org/wiki/File:A_photo_of_a_pothole_2021-07-11.jpg)
and its blurred derivative are CC BY-SA 4.0.

With the local models set up, run the application and browser suite in separate
terminals.

```sh
CIVICFIX_DATA_DIR=.runtime/real-e2e-app .venv-api/bin/python scripts/civicfix.py dev
```

```sh
CIVICFIX_E2E_REAL=1 CIVICFIX_E2E_BASE_URL=http://127.0.0.1:5173 \
  npm --prefix apps/web run e2e -- real.spec.ts --project=chromium
```

The suite uses a demonstration location in Gainesville and stops at the local
download. It makes no external submission.

## Configuration

Copy [config/app.example.toml](config/app.example.toml) and set
`CIVICFIX_CONFIG` to the copied file when custom settings are needed.

Useful environment variables include:

- `CIVICFIX_CONFIG`: path to an application configuration file
- `CIVICFIX_DATA_DIR`: directory for runtime data
- `CIVICFIX_MODE=fixture`: enable deterministic fixture behavior

Runtime data is stored in `.runtime/app/` by default. It is not intended for
source control.

## Data and model behavior

The repository includes a small curated image collection in
[data/images/](data/images/) with labels in
[data/labels.csv](data/labels.csv). The collection supports local development
and experimentation; it is not an official benchmark and does not establish
production accuracy.

Suggestions are advisory. Users must review and confirm the category,
description, location, and report text. A photograph alone cannot establish
facts such as streetlight ownership, illegal dumping, or the cause of a
problem. When the application cannot verify a required detail, it leaves the
detail unresolved rather than presenting an unsupported claim.

The classifier can reject an unrelated photo or request a clearer view before
generating a description. This decision uses model-specific similarity
thresholds and can miss valid issues. A rejected draft needs a replacement
photo before it can proceed.

Routing data, source records, and data-quality notes are available in
[routing/sources.json](routing/sources.json),
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md), and
[docs/DATA_QUALITY.md](docs/DATA_QUALITY.md).

## Repository layout

```text
apps/web/       React frontend
services/api/   FastAPI application
services/inference/
                Local inference adapters
contracts/      OpenAPI contract
config/         Example application configuration
data/           Curated images and labels
evaluation/     Evaluation and smoke-test scripts
docs/           Detailed technical and data documentation
```

## Limitations

- Only locations inside the supported Gainesville boundary are accepted.
- Road issue routing uses the bundled Gainesville street inventory. An off-road
  pin or conflicting maintenance records require a more precise roadway
  location. Pothole reports can be directed to the City, Alachua County, or
  FDOT when the inventory identifies the maintainer.
- Map tiles and browser GPS require the relevant browser permissions and,
  for tiles, network access.
- The external reporting service may require additional fields, authentication,
  or a separate photo upload.
- Runtime drafts and photos expire after 24 hours. Cleanup cannot run while
  the machine is powered off.
- Submitted feedback stays on this computer for 30 days and detaches from the
  draft when it is cleared or expires.

## License and attribution

Application code, data, and included photographs may have different terms.
Review the attribution and license records in
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) before redistributing the
repository or its images.
