# CivicFix dataset playground

CivicFix plans to recognize Gainesville-area nonemergency issues from user photos with hosted Gemini inference, then use location and rules for routing and user review. This milestone prepares and inspects real images; it does not implement the application or measure model accuracy.

**[Executed playground.ipynb](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/playground.ipynb)** · **[Working branch](https://github.com/Itz-Viggy/civicfix/tree/dataset-playground)**

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

- Repository: [https://github.com/Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix), **private**.
- Dataset version: `v1`.
- Immutable dataset commit: [`8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4`](https://github.com/Itz-Viggy/civicfix/commit/8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4). This dataset commit was pushed before the notebook implementation; retrieval does not point at the later notebook commit.
- Manifest SHA-256: `98f8e250316df8c1517b381445d05dbc8a98813020930438a506e72e75dd28f9`.
- Remote retrieval is verified by the saved notebook's `github` status and 43 hash-validated images.

Sign in to GitHub with an account that can read this repository:

```sh
gh auth login --hostname github.com
```

Alternatively supply `GITHUB_TOKEN` (or `GH_TOKEN`) through the environment/secret manager with repository read access. Never paste credentials into notebook cells or committed files. The helper reads credentials into memory without printing or writing them. Private repository access must be granted before an instructor can clone, view the notebook or retrieve its data. No instructor account was identified and no invitation was sent.

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

Every included image has author, original title, original/file-page URL, selected download URL, source revision/version, license/version/URL, actual UTC retrieval timestamp, agent label evidence and stored-image checksum. [DATA_SOURCES](docs/DATA_SOURCES.md), [source_records.json](docs/source_records.json) and [candidate_review.csv](docs/candidate_review.csv) preserve attribution, permission checks, transformations and exclusions. Licenses are {'CC BY-SA 2.0': 17, 'CC BY-SA 4.0': 15, 'CC BY 2.0': 1, 'CC BY 4.0': 2, 'Public domain': 3, 'CC BY-SA 3.0': 1, 'CC0': 4}. Individual photo licenses remain in force, including the same-version share-alike terms for transformed CC BY-SA photos; no blanket project code license covers the photographs.

JPEG derivatives have EXIF/GPS removed and a maximum 1280-pixel side. Cached 330-pixel thumbnails were used for some small originals, with retained defect evidence reviewed after conversion. Other originals remain reachable only at their source sites. No sensitive originals, people/plate crops, credentials or temporary downloads were committed.

Coverage is uneven: leaking hydrants remain below the approximate ten-per-class target. Nonlocal convenience photos do not validate Gainesville routing. Agent interpretation needs independent review; lighting, weather, geography and capture dates are uneven or unrecorded. The notebook checks byte duplicates and screens near duplicates, but does not prove event independence. [DATA_QUALITY](docs/DATA_QUALITY.md) reports measured results and remaining gaps.

[MODEL_NOTES](docs/MODEL_NOTES.md) records the exact planned `gemini-2.5-flash-lite` API model, official terms and the current prior-user access restriction. No replacement model or accuracy result is claimed. [PROPOSAL_UPDATES](docs/PROPOSAL_UPDATES.md) provides targeted replacement text; no proposal document was supplied. [SUBMISSION](docs/SUBMISSION.md) contains links and the acceptance checklist.
