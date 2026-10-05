# Targeted proposal updates: Sections 2.3–2.7

The repository initially contained the specification only; no original proposal or Word document was present. The text below is **proposed replacement/addition text based on that specification**, not an edit already applied to the proposal. Preserve unrelated sections when applying it.

## 2.3 Hardware — proposed replacement

Data inspection was executed locally on an Apple M5 arm64 Mac with 24 GiB RAM, using the CPU. The notebook performs image decoding, metadata inspection and plotting; no GPU or model training was required. Hosted inference remains a separate planned service.

## 2.4 Software — proposed replacement

The dataset milestone uses tested Python 3.12.15 with the exact pandas, Pillow, matplotlib, NumPy, requests and Jupyter execution-tool versions in `requirements.txt`. The executed root `playground.ipynb` runs without a Gemini key. Docker is included for final deployment planning and reproducible environments, replacing the prior statement that Docker was not planned. The supplied CPU Dockerfile reproduces this notebook; the web application's deployment image and actual container execution are not yet validated. Docker was unavailable on this machine.

The exact planned model remains the hosted Gemini API ID `gemini-2.5-flash-lite`. Official documentation checked on 2026-10-04 now restricts 2.5 access to prior active users. Account-level availability must be established before inference implementation; no silent substitution was made. Applicable API terms, not an invented open-weight license, govern use. See `MODEL_NOTES.md`.

## 2.5 Cloud and storage — proposed replacement

The curated dataset is stored in the private GitHub repository [https://github.com/Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix), on branch `dataset-playground`, under `data/images/` and `data/labels.csv`. Its 43 approved image derivatives occupy 13,020,816 bytes (12.418 MiB). Access requires a permitted GitHub account; instructor access is pending identification and authorization of an instructor account. All image license/attribution records accompany the dataset. Private access does not override third-party reuse terms.

This small licensed collection fits the 25 MiB working storage budget. Notebook retrieval uses immutable dataset commit `8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4` and validates hashes. This is experimental dataset storage, not application hosting, a runtime reporting database or a public-photo upload service. Those infrastructure choices remain separate.

## 2.6 Scale — limited addition

The actual milestone collection contains 43 photographs with uneven categories (counts below). It supports initial inspection only. Keep existing prototype scale assumptions: no real inference latency, concurrent-load or deployment experiment was run, so this milestone supplies no evidence to revise them. It does not establish the planned 85% classification target.

| Category | Images |
|---|---:|
| `pothole` | 10 |
| `broken_streetlight` | 10 |
| `damaged_sign` | 10 |
| `leaking_hydrant` | 3 |
| `illegal_dumping` | 10 |

## 2.7 Decision record — proposed addition

**Decision:** store the small approved evaluation collection in the existing user's private GitHub account and retrieve a pinned dataset commit.

**Rationale:** 12.418 MiB of images is inexpensive to clone, review and reproduce alongside labels and attribution; it avoids credentials for another storage service and paid infrastructure. Source rights were checked before upload.

**Trade-off:** private GitHub access must be granted to instructors; Git is unsuitable for a much larger or sensitive user-photo collection. The subset is nonlocal, agent-reviewed and has a hydrant shortfall.

**Reconsideration trigger:** reconsider storage when curated image bytes exceed 25 MiB, frequent image replacements materially inflate Git history, or permissions/privacy require restricted external storage. Evaluate that change explicitly and implement authorized retrieval/access controls before moving data. Reassess hosted-model choice separately if the exact planned model is unavailable to this account.
