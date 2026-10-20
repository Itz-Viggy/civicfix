# Stage 0 baseline and prerequisites

Recorded October 20, 2026 (America/New_York). This is a design and repository stage, not app or inference execution evidence. See the [tracker](IMPLEMENTATION_STATUS.md).

## Repository reconciliation

| Item | Inspected baseline |
| --- | --- |
| App development parent | Local `main`, `aaacb067e92dd0681e77b2b5c090fb49326d1250` |
| Supporting documentation | Local `dataset-playground`, `6373875f2ec744f879ad593ec353830fdba5b578` |
| Stage 0 branch | `codex/stage-0-foundation` |
| Immutable dataset | `8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4` |
| Manifest SHA-256 | `98f8e250316df8c1517b381445d05dbc8a98813020930438a506e72e75dd28f9` |

Both local branches and their cached origin refs were inspected. No remote freshness claim is made. `dataset-playground` is already an ancestor of `main`; their content difference is the 13 missing documentation/preview/provenance files. All 13 ignored local files matched that branch byte for byte before edits. Track those existing bytes, remove the blanket `docs/` ignore, and restore README links without merging older app assumptions. This includes `verification_results.json`, previously removed on main but still required by the historical verification document. Its restored results remain dated historical evidence.

The notebook, notebook dependencies, Dockerfile, scripts, 43 JPEGs, labels, dataset configuration, source records, license text, and acquisition timestamps are preserved. The pinned data is development material, not an independent final test set. Supporting documentation retains historical wording and dates; the current PRD and contracts govern app development. The supplied draft stays locally ignored; [CIVICFIX_DEVELOPMENT_PRD.md](CIVICFIX_DEVELOPMENT_PRD.md) is its exact canonical copy.

No applicable `AGENTS.md` was found in the repository or its ancestor directories during inspection.

## Requirements authority

The user confirmed on October 20 that the PRD may serve as the Stage 0 source of truth. `Milestone3_Data_Collection_Revised.docx` v7 is not in this checkout and was not independently read. The course-document citation and section claims originate from the PRD. Reconcile against the original before changing course deliverables or claiming independent source verification.

The five existing category identifiers are fixed:

| ID | Reporting definition and evidence limit |
| --- | --- |
| `pothole` | Visible depression or missing pavement in a road surface; do not infer depth, cause, ownership, or vehicle damage. |
| `broken_streetlight` | Visible fixture/pole damage or a user-reported failure to illuminate; a daylight photo alone cannot establish an electrical fault. |
| `damaged_sign` | Visible damage, displacement, or obscuration of a traffic/street sign; do not infer an unseen missing sign or the responsible agency. |
| `leaking_hydrant` | A hydrant with visible escaping water, or a clearly attributed user observation; do not invent a hidden hydrant, leak origin, or severity. Caption-dependent development labels need independent review. |
| `illegal_dumping` | Debris/waste that may warrant a dumping report; describe visible material and attribute user claims. A photo does not establish illegality or who left it. |

The final action is **Prepare Report**, the final heading is **Report Prepared**, and the explanation is **Your report is ready for manual submission. It has not been sent to an authority.** Internal draft IDs never become authority tracking IDs. No authority submission, acceptance claim, external form automation, or repair-status workflow is included.

## Local inventory (observed, not inferred capacity)

| Resource | Observation | Consequence |
| --- | --- | --- |
| Machine | Apple M5, arm64, 10 CPU cores, 10 GPU cores, Metal, 24 GB unified memory; macOS 26.6.2 | Apple GPU exists; no CUDA/GPU-host assumption. Model fit and latency unmeasured. |
| Disk | Approximately 199 GiB available when inspected | Not a model download or capacity guarantee. |
| Notebook Python | `.venv/bin/python` 3.12.15, root `.python-version` 3.12.15 | Preserve this environment and existing requirements. `pip check` passes. |
| Global tools | Python 3.14.7; Node 26.10.0; npm 11.19.1 | App backend will use a separate Python 3.12 environment. Pin/test app Node runtime during Stage 2. |
| Commands on PATH | No `docker`, `ollama`, `vllm`, `uv`, or `python3.12` | Existing venv works; Docker execution and model serving remain unverified. |
| Notebook packages | No MLX/MLX-VLM, torch, transformers, vLLM, FastAPI, Pydantic, HTTPX, Uvicorn, or google-genai installed | Do not add app/inference packages to notebook requirements. Other environments were not exhaustively inventoried. |
| Credentials/config | No nonempty `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `HF_TOKEN`, `CIVICFIX_INFERENCE_PROVIDER`, `CIVICFIX_INFERENCE_BASE_URL`, or `DATABASE_URL` in this process | No account access, database, or remote compute verified. Secret values were not printed; credential stores were not searched. |

## Dependency decisions

Only notebook dependencies are installed/tested today. The following registry snapshot is a candidate set, not a tested dependency lock. Metadata was read from public registries on October 20; no packages were installed. Freeze direct versions and transitive locks in their own environments when the relevant stage starts, and record any version changes with the reason.

| Component | Candidate/version or policy | First validation task |
| --- | --- | --- |
| Backend | Python 3.12.15; FastAPI 0.152.0; Pydantic 2.14.1; HTTPX 0.28.1 | 1A: install schemas/config and test; 2: FastAPI API skeleton. FastAPI/Pydantic metadata require Python >=3.10; HTTPX >=3.8. |
| ASGI server | Uvicorn 0.54.0 (Python >=3.10) | 2: startup smoke test. |
| Frontend | Next.js 16.4.2; React 19.3.1; matching React DOM; TypeScript | 2: resolve peer compatibility, pin exact versions/runtime and commit npm lock. Registry metadata for matching React DOM and TypeScript not yet checked. |
| Node | Minimum >=20.9.0 per Next metadata/docs; prefer a supported LTS at setup | 2: installed Node 26.10.0 is observed, not claimed as a tested app runtime. |
| Image/API upload | Pillow plus python-multipart, exact app pins at setup | 2: verify decoder limits/metadata removal; no HEIC support assumed. |
| Database | PostgreSQL; driver, migration tool, and exact server version selected with Stage 2 persistence design | No database provisioned. Require migrations, TLS, bounded connections, deletion, and expiry. |
| Hosted SDK | Optional `google-genai`, exact pin in 1C | Only its adapter imports the native SDK. |
| Local serving | Separate environment/host; no runtime selected or installed | 1B must pin model, revision, processor, runtime, and any quantization artifact after compatibility check. |

Metadata sources: [Next](https://registry.npmjs.org/next/latest), [React](https://registry.npmjs.org/react/latest), [FastAPI](https://pypi.org/pypi/fastapi/json), [Pydantic](https://pypi.org/pypi/pydantic/json), [HTTPX](https://pypi.org/pypi/httpx/json), [Uvicorn](https://pypi.org/pypi/uvicorn/json). Supporting guidance: [Next installation](https://nextjs.org/docs/app/getting-started/installation), [FastAPI version pinning](https://fastapi.tiangolo.com/deployment/versions/), [Node release schedule](https://nodejs.org/en/about/previous-releases).

## Inference prerequisites and handling

Start with `Qwen/Qwen3-VL-4B-Instruct`. The [official model card](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) lists image/text support and Apache 2.0. This does not establish CivicFix accuracy, actual memory fit, third-party quantization rights, or performance. The publisher's serving examples and [vLLM GPU installation requirements](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/) must be matched to real hardware; a Linux GPU command is not a Mac setup.

For this Mac, [MLX-VLM's maintainer documentation](https://github.com/Blaizzy/mlx-vlm) includes Qwen3-VL and server examples. It is a candidate to verify in 1B, not an installed or tested runtime. Check the exact release/commit, image endpoint behavior, processor and model artifact, license/quantization provenance, memory peak, latency and persistence/caches. Disable photo/prompt logging and persistent prompt caches or include them in verified deletion. Alternatively identify an authorized private compatible GPU endpoint. Keep weights out of Git and keep inference dependencies separate from the app and notebook.

Gemini remains optional. The [current model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite) still limits 2.5 access to prior active users; account eligibility is unknown. [Gemini terms](https://ai.google.dev/gemini-api/terms) distinguish unpaid inputs/outputs used for improvement and possible human review from paid processing. Paid processing is not a zero-retention guarantee. Before 1C live calls, verify the account, applicable terms and image rights; before real-user photos, document retention and disclosures. Do not use sensitive or personal content on unpaid services. Use permitted non-sensitive development examples and send the minimum necessary data. Exact coordinates stay in deterministic routing.

There is no silent provider fallback. Local failures cannot export photos to Gemini. Real integration proof needs two actual configurations, including a self-hosted open source model; deterministic fixtures do not count. No weights were downloaded and no inference or paid call was made in Stage 0.

## Hosting, database and retention requirements

Vercel frontend + Render API/PostgreSQL remains a proposed deployment shape, not provisioned infrastructure. API uploads go directly to the API origin with restricted credentialed CORS/session/CSRF controls; they must not depend on a frontend function forwarding large payloads. [Vercel Functions](https://vercel.com/docs/functions/limitations) currently cap request/response payloads at 4.5 MB. The app contract proposes a 10 MiB photo limit. A cross-origin production session must be tested in real browsers; prefer same-site custom domains where available.

[Render's free plan](https://render.com/docs/free) sleeps after 15 idle minutes, loses local files across restarts, has no free persistent disk, and expires free PostgreSQL after 30 days (1 GB, no backups). Cold starts conflict with a blanket 10-second inference promise. Do not claim durable drafts or dependable cleanup scheduling from an ephemeral filesystem or sleeping process. The database needs durable metadata, and photos need private storage with authenticated reads and verified deletion. A separate scheduler must enforce expiry despite API idleness. Choose storage/backup policies that can meet deletion within 24 hours; long-lived content backups would violate that promise unless explicitly resolved.

The [Vercel price page](https://vercel.com/pricing) lists Hobby at $0/month and Pro at $20/month plus applicable usage; [Render pricing](https://render.com/pricing) separates compute, database and workspace charges. These are planning references, not a selected quote or budget. No free deployment promise is made. Stage 7 must recheck selected regional SKU prices, quotas, TLS, storage, backup retention, cleanup scheduling, private model connectivity and spend controls before deployment approval. Self-hosted inference compute is a separate measured resource; a small API host is not presumed capable of serving the model.

Application content expires at creation +24 hours; preparation does not extend it. Clear/cancel/delete removes app-owned content and derivatives. Expired content must immediately be inaccessible and physically removed by the deadline. Provider-side retention is disclosed separately and cannot be described as deleted merely because application deletion succeeded. See [API contract](APP_CONTRACT.md).

## Stage 0 verification

Actual check outcomes and the next task are recorded in the [tracker](IMPLEMENTATION_STATUS.md). Historical notebook execution and rights review remain in [VERIFICATION.md](VERIFICATION.md); Stage 0 does not repeat or relabel those as new model, Docker, or human-review results.
