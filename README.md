# CivicFix

A local Gainesville, Florida, nonemergency report-preparation app. Upload a photo, confirm a location, get local CLIP/Qwen suggestions, correct the draft, review it, and prepare text/photo for manual entry in an official reporting form. CivicFix never submits a report.

## Local application

Tested runtime: Python 3.12.15, Node 26.10.0, Apple Silicon with Metal and 24 GB RAM. The Qwen MLX adapter requires Apple Silicon; deterministic test mode is separately labeled. No cloud account or API key is needed. The existing models use roughly 3.5 GB of disk; runtime photos stay in private `.runtime/app/` and expire after 24 hours. Cleanup runs while the app is running and on startup; a powered-off machine cannot delete on schedule.

From the repository root:

```sh
# Python 3.12 must be installed on a clean checkout.
python3.12 -m venv .venv-api
# On this existing checkout, .venv/bin/python can replace python3.12.
.venv-api/bin/python -m pip install -r services/api/requirements.lock
cd apps/web
npm ci
cd ../..
.venv-api/bin/python scripts/civicfix.py dev
```

Open [CivicFix locally](http://127.0.0.1:5173). Wait for both models to become ready. The launcher stops its API and model children on Ctrl+C. Default API port is 8000; UI is 5173. Optional `CIVICFIX_CONFIG` points to a copy of `config/app.example.toml`; `CIVICFIX_DATA_DIR` isolates runtime storage. `--fixture` on the launcher selects visibly simulated development mode; it is never an automatic fallback.

The checked-out model environments/artifacts are reused. On a new machine, create the two environments and explicitly download the public pinned models using the existing experiment setup commands below. Downloads happen only during setup; inference uses local verified weights. Preserve the separate CLIP/Qwen locks because their dependency versions differ.

```sh
.venv/bin/python -m venv .venv-inference/clip
.venv-inference/clip/bin/python -m pip install -r experiments/first_model_exploration/requirements-macos.lock
.venv-inference/clip/bin/python -m experiments.first_model_exploration.setup_model
.venv/bin/python -m venv .venv-inference/qwen
.venv-inference/qwen/bin/python -m pip install -r experiments/description_evaluation/requirements-qwen-macos.lock
HF_HUB_DISABLE_XET=1 .venv-inference/qwen/bin/python -m experiments.description_evaluation.setup_model
```

For a locally served built UI:

```sh
cd apps/web
npm run build
cd ../..
.venv-api/bin/python scripts/civicfix.py start
```

Open [the built application](http://127.0.0.1:8000).

## Checks

```sh
.venv-api/bin/python scripts/civicfix.py test
PYTHONPATH=services/api:. .venv-api/bin/python scripts/civicfix.py schema
cd apps/web
npm run generate:types
npm run check:contracts
npm run typecheck
npm test
npm run build
npx playwright install chromium webkit
npm run e2e
cd ../..
PYTHONPATH=services/api:. .venv-api/bin/python evaluation/run.py
PYTHONPATH=services/api:. .venv-api/bin/python evaluation/robustness.py
PYTHONPATH=services/api:. .venv-api/bin/python evaluation/api_smoke.py
# Explicit real-model browser smoke, after stopping other local servers:
cd apps/web
CIVICFIX_E2E_REAL=1 npm run e2e -- real.spec.ts --project=chromium
cd ../..
```

Evaluation runs use actual local models and write new private JSONL evidence under `.runtime/app-evaluation/`. They do not claim held-out accuracy or automatically certify factuality. Review generated assertions against the permitted photos; similarity scores are not confidence or factual accuracy. User observations stay separately attributed and are not model inputs.

## Scope and recovery

Only city-limit locations are accepted. The bundled boundary and road-maintenance geometry come from the official City of Gainesville GIS organization, with sources, checksums and terms in `routing/sources.json`. Road issues resolve only near an authoritative city-maintained segment. Unknown ownership stays unresolved. Streetlight ownership and a category-specific hydrant web form are not established by the bundled evidence; those cases show official guidance and allow draft copying, but cannot pretend to be form-ready.

Optional OpenStreetMap tiles require internet; GPS depends on browser permission/accuracy. Manual coordinates and the bundled boundary work without map tiles. No address-search service is used. A daylight photo cannot prove a streetlight outage, and debris does not prove illegal dumping.

If models are starting, wait and retry. Missing weights, bad hashes, crashes, uncertain predictions and invalid JSON have explicit errors; valid inputs remain saved, and the app offers explicit manual correction. No photo is silently exported to a hosted model. If copying is denied, select the displayed report text or download it. The external form may require its own fields, sign-in or photo upload; opening it does not send anything. Clear deletes app-owned copies; deleting/expiring a draft prevents late model results from restoring it.

## Preserved dataset and experiment documentation

## First Model Exploration homework

Submit the [combined executed notebook](experiments/first_model_exploration/training_experiments.ipynb): OpenCLIP classification on 43 development photos, followed by Qwen3-VL descriptions, OpenCLIP alignment scores and factual reviews on a frozen 20-photo subset.

Classification improved **40/43 → 41/43** after one dumping-prompt change. The description prompt change did not help: **16 → 15** valid outputs, **8/16 → 7/15** with zero unsupported claims under agent visual review. Both experiments use real local inference; similarity is separate from factuality, and no held-out/application acceptance is claimed.

[Submission note](experiments/first_model_exploration/SUBMISSION.md) · [Reproduce](experiments/first_model_exploration/README.md) · [Short description findings](experiments/description_evaluation/FINDINGS.md)

## Dataset playground

**[Executed playground.ipynb](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/playground.ipynb)** · **[Working branch](https://github.com/Itz-Viggy/civicfix/tree/dataset-playground)**

GitHub's notebook viewer returned a preview error during inspection. `docs/NOTEBOOK_PREVIEW.md` (local only) shows the actual grid and statistics in Markdown; the validated notebook retains its outputs for download/opening in Jupyter. `docs/VERIFICATION.md` (local only) distinguishes successful execution/file delivery from this rendering limitation.

The **CivicFix Commons Curated Collection v1** contains **43 photographs**, stored in `data/images/` with one record per image in `data/labels.csv`. This convenience sample is agent-reviewed, not independently human-validated and not an official benchmark. Actual image storage is **13,020,816 bytes (12.418 MiB)**. The small approved subset is sufficient for repository storage under the 25 MiB working budget. No external storage or paid infrastructure is required.

| Category | Images |
|---|---:|
| `pothole` | 10 |
| `broken_streetlight` | 10 |
| `damaged_sign` | 10 |
| `leaking_hydrant` | 3 |
| `illegal_dumping` | 10 |

## Install and run

Tested with **Python 3.12.15**, Apple M5 arm64, macOS, 24 GiB memory, CPU only. The dedicated environment uses the exact direct-package versions in `requirements.txt`; transitive dependencies resolve during installation. The original global Python 3.14 environment was left intact. Python 3.12.15 was obtained with `uv` for this task.

From the repository root with Python 3.12.15 installed:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python scripts/execute_notebook.py
```

The executor launches this environment's Python in a fresh kernel, stops on cell errors, and atomically saves the successful notebook with outputs. Run from the repository root. No Gemini key, GPU framework or model API call is needed.

## Immutable retrieval and private access

Default `github` mode downloads the manifest and only its listed images through the GitHub API into a new empty ignored `.cache/inspection-*` directory on each run. The retrieval helper validates safe relative paths, the manifest SHA-256, all image SHA-256 values and decoding, with three bounded network attempts and four download workers. It does not search for new images or overwrite tracked images, labels or acquisition dates.

- Repository: [https://github.com/Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix), **public** (visibility verified October 21, 2026; no setting changed).
- Dataset version: `v1`.
- Immutable dataset commit: [`8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4`](https://github.com/Itz-Viggy/civicfix/commit/8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4). This dataset commit was pushed before the notebook implementation; retrieval does not point at the later notebook commit.
- Manifest SHA-256: `98f8e250316df8c1517b381445d05dbc8a98813020930438a506e72e75dd28f9`.
- Remote retrieval is verified by the saved notebook's `github` status and 43 hash-validated images.

Sign in to GitHub with an account that can read this repository:

```sh
gh auth login --hostname github.com
```

Alternatively supply `GITHUB_TOKEN` (or `GH_TOKEN`) through the environment/secret manager with repository read access. Never paste credentials into notebook cells or committed files. The helper reads credentials into memory without printing or writing them. The pinned historical dataset retrieval configuration still requests authenticated access. GitHub currently reports the repository public, so the published notebook links are viewable without an invitation. Private planning documents remain local and untracked.

A documented offline/local mode copies the tracked collection from a clean clone and validates the same hashes. It proves local reproducibility, not GitHub download access:

```sh
CIVICFIX_DATA_MODE=local python scripts/execute_notebook.py
python -m unittest scripts.test_dataset_tools -v
```

The saved final notebook reports the tested remote mode. Cache directories are ignored and safe to remove after a run.

## Docker reproduction

Docker uses `python:3.12.15-slim`, pinned requirements and CPU execution. Its build context is restricted to the notebook runtime files. The container does not contain a GitHub credential and does not containerize or deploy the eventual CivicFix web app.

```sh
docker build -t civicfix-playground .
# Execute local data and save the notebook back into the host checkout.
docker run --rm -e CIVICFIX_DATA_MODE=local -v "$PWD:/workspace" civicfix-playground
```

For authenticated remote retrieval, provide `GITHUB_TOKEN` securely in the host environment and forward its name at run time:

```sh
docker run --rm -e GITHUB_TOKEN -e CIVICFIX_DATA_MODE=github -v "$PWD:/workspace" civicfix-playground
```

Docker CLI/daemon are unavailable on the development machine. The Dockerfile and commands were prepared and inspected, but image build and container execution are **unverified**. Local Python execution is verified independently.

## Provenance, rights and limitations

Every included image has author, original title, original/file-page URL, selected download URL, source revision/version, license/version/URL, actual UTC retrieval timestamp, agent label evidence and stored-image checksum. `docs/DATA_SOURCES.md` (local only), `docs/source_records.json` (local only) and `docs/candidate_review.csv` (local only) preserve attribution, permission checks, transformations and exclusions. Licenses are {'CC BY-SA 2.0': 17, 'CC BY-SA 4.0': 15, 'CC BY 2.0': 1, 'CC BY 4.0': 2, 'Public domain': 3, 'CC BY-SA 3.0': 1, 'CC0': 4}. Individual photo licenses remain in force, including the same-version share-alike terms for transformed CC BY-SA photos; no blanket project code license covers the photographs.

JPEG derivatives have EXIF/GPS removed and a maximum 1280-pixel side. Cached 330-pixel thumbnails were used for some small originals, with retained defect evidence reviewed after conversion. Other originals remain reachable only at their source sites. No sensitive originals, people/plate crops, credentials or temporary downloads were committed.

Coverage is uneven: leaking hydrants remain below the approximate ten-per-class target. Nonlocal convenience photos do not validate Gainesville routing. Agent interpretation needs independent review; lighting, weather, geography and capture dates are uneven or unrecorded. The notebook checks byte duplicates and screens near duplicates, but does not prove event independence. `docs/DATA_QUALITY.md` (local only) reports measured results and remaining gaps.

`docs/MODEL_NOTES.md` (local only) records the exact planned `gemini-2.5-flash-lite` API model, official terms and the current prior-user access restriction. No replacement model or accuracy result is claimed. `docs/PROPOSAL_UPDATES.md` (local only) provides targeted replacement text; no proposal document was supplied. `docs/SUBMISSION.md` (local only) contains links and the acceptance checklist.
