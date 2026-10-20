# CivicFix implementation status

Updated October 20, 2026 (America/New_York). Scope of this change: **Stage 0 only**. Status values: `not_started`, `in_progress`, `blocked`, `complete`. All tasks began `not_started`; Stage 0 moved to `in_progress` for reconciliation and to `complete` after the checks below. No later stage has started.

| Task | Depends on | Status | Evidence / review | Blocker or prerequisite | Next action |
| --- | --- | --- | --- | --- | --- |
| 0 | None | complete | [Baseline](STAGE_0_BASELINE.md), [app contract](APP_CONTRACT.md), [inference contract](INFERENCE_CONTRACT.md), [checklist](ACCEPTANCE_CHECKLIST.md), checks below; local branch `codex/stage-0-foundation`, no PR opened | No Stage 0 blocker; user accepts PRD as requirements authority. Original course document not independently checked. | Review Stage 0, then request 1A. |
| 1 (aggregate) | 0, 1A–1D | not_started | No real inference evidence | Full exit needs real open source integration, switching proof and benchmark | Execute substages separately. |
| 1A | 0 | not_started | [Contract](INFERENCE_CONTRACT.md), [configuration example](../config/inference.example.toml) are design inputs only | No credential/GPU prerequisite | Implement strict schemas, interface, registry, config validation and simulated fixtures/tests. |
| 1B | 1A + runnable compute | not_started | [Compute inventory](STAGE_0_BASELINE.md) | Mac runtime/artifact and private serving must be verified; no installed runtime or remote compute confirmed | Verify MLX-VLM compatibility for this Mac or an authorized private GPU host, then real Qwen3-VL-4B inference. |
| 1C | 1A + two real configurations for proof | not_started | Hosted documentation checked, no account/live call | No configured Gemini key or verified prior-user access; second real configuration absent | Implement optional native adapter; document live availability and configuration-only switching evidence. |
| 1D | At least one real backend; Stage 1 exit needs switching | not_started | Development dataset only | Real outputs and independent label review absent | Save initial predictions, benchmark allowed development examples, select measured default. |
| 2 | 0 + shared draft contract | not_started | [API/fields/layout](APP_CONTRACT.md) | Package install/lock, persistence implementation and production storage topology pending | Build web/API input skeleton and session-restricted drafts. Independent of blocked live inference after shared contract foundations. |
| 3 | 1A + 2 + real backend | not_started | No app | Inputs and real inference pending | Connect editable analysis and stale-result protection. |
| 4 | 0 + location contract | not_started | Route shape defined, no jurisdiction rule claimed | Official boundary/ownership/source research pending | Verify deterministic routing rules and expected cases; can proceed independently of live inference. |
| 5 | 3 + 4 | not_started | Preparation predicates and wording defined | Integrated analysis/routing pending | Implement reviewed preparation and separate manual handoff. |
| 6 | 5 + independent test data + full Stage 1 release evidence | not_started | [Acceptance targets](ACCEPTANCE_CHECKLIST.md) | 100 independent supported photos +20 recovery cases and label review absent | Freeze config and run actual classification/timing/walkthrough evaluation. |
| 7 | 6 + verified resources | not_started | [Hosting requirements](STAGE_0_BASELINE.md), notebook Docker only | No Docker CLI, verified hosting/storage/cleanup/database plan or deployment approval | Recheck resources/costs, validate app containers and operations, then request deployment approval. |

## Stage 0 evidence

1. Inspected `main` at `aaacb067e92dd0681e77b2b5c090fb49326d1250` and `dataset-playground` at `6373875f2ec744f879ad593ec353830fdba5b578`. These are local refs matching cached origin refs; no fresh remote inspection claimed. Created isolated local branch `codex/stage-0-foundation` from main.
2. All 13 recovered supporting docs, previews, source/rights records and historical results match dataset-playground byte for byte. Removed blanket docs ignore; copied the supplied PRD exactly to [CIVICFIX_DEVELOPMENT_PRD.md](CIVICFIX_DEVELOPMENT_PRD.md). Original draft retained locally.
3. User explicitly approved the PRD's five categories and manual report-preparation boundary as Stage 0 authority. Original course `.docx` is unavailable and was not independently verified.
4. Defined request/result/error/metadata contracts, explicit provider configuration and simulation labels, draft fields/API/session/revision/invalidation rules, folder layout, privacy and acceptance criteria. No schema/API/adapter implementation is claimed.
5. Recorded observed hardware, tools, environment variable presence (names only), missing inference runtime/keys, public dependency metadata and official provider/hosting guidance in [baseline](STAGE_0_BASELINE.md). No model download, account provisioning, inference, paid call or deployment occurred.
6. `.venv/bin/python -m unittest scripts.test_dataset_tools -v`: **5/5 passed**. `.venv/bin/python -m pip check`: **no broken requirements**. Existing notebook environment used without modification; pip emitted an unwritable cache warning and disabled its cache.
7. Fresh temporary local retrieval through `retrieve_dataset(..., mode="local")` validated manifest SHA-256 and all **43 image hashes and decodes**. `inspect_images` measured **13,020,816 bytes**, category counts **10/10/10/3/10**, and zero EXIF/GPS. Temporary inspection copies were removed. No remote retrieval or notebook execution rerun is claimed.
8. Byte comparisons with main confirm unchanged notebook, labels, data configuration, requirements, Python pin and notebook Dockerfile; Git diff confirms no dataset/script edits. Byte comparisons with dataset-playground cover all 13 restored files. Canonical PRD exactly matches supplied draft. Python `tomllib` parses the config example, which explicitly selects deterministic fixtures and no fallback.
9. Final audit confirms all **54 local Markdown file links target tracked files**, and `git diff --check` / staged diff checks pass. All 22 staged files are restricted to Stage 0 documentation/configuration scope. External source URLs were inspected through the official pages where relevant; the audit checks local file existence, not every external link/anchor or private GitHub access. See the reproduction commands below.

Checks establish repository/document integrity only. They do not establish label accuracy, model integration, numerical performance, Docker operation, access by an instructor or production privacy/cleanup. Historical dataset evidence keeps its original dates.

## Recheck the documentation boundary

Run from the repository root with the existing notebook environment. The audit intentionally checks file targets (not heading fragments or every external URL).

```sh
.venv/bin/python -m unittest scripts.test_dataset_tools -v
.venv/bin/python -m pip check
git diff --check
```

```python
from pathlib import Path
import re
import tomllib
from urllib.parse import unquote, urlsplit

root = Path.cwd()
for doc in [root / "README.md", *sorted((root / "docs").glob("*.md"))]:
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", doc.read_text()):
        link = urlsplit(target.split()[0].strip("<>"))
        if not link.scheme and link.path:
            assert (doc.parent / unquote(link.path)).exists(), (doc, target)
example = tomllib.loads((root / "config/inference.example.toml").read_text())
assert example["provider"] == "deterministic"
assert example["fallback_policy"] == "none"
```

## Exact next runnable task

After Stage 0 review, request **Stage 1A only**:

> Read the PRD, tracker, app and inference contracts. In a separate Python 3.12 API environment, implement strict request/result/error schemas, the provider adapter interface and registry, validated configuration, and deterministic fixtures labeled simulated. Cover supported/unclear/unsupported cases, malformed outputs, unknown labels, deadlines, missing configuration/keys, no fallback and no provider SDK dependency in report/routing logic. Pin installed dependencies and record actual checks. No model weights, paid calls, UI scaffold, deployment, or Stage 1B work in this task.

Stage 1A can run on this machine without model credentials or a serving runtime. If later real integrations are blocked, update that specific substage to `blocked` when attempted, preserve honest unmet exits, and select only independently authorized work. Do not advance automatically.
