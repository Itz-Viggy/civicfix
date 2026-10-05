# CivicFix dataset submission

Repository: [https://github.com/Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix) (private)
Working branch: [dataset-playground](https://github.com/Itz-Viggy/civicfix/tree/dataset-playground)
Direct notebook: [playground.ipynb](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/playground.ipynb)
Immutable dataset commit: [`8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4`](https://github.com/Itz-Viggy/civicfix/commit/8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4)

## Short submission note

I used the CivicFix Commons Curated Collection v1, with 43 photographs with documented reuse rights stored in my private GitHub repository under data/images/. The notebook retrieves the pinned dataset and shows its actual outputs. I found only 3 suitable leaking-hydrant photographs, compared with ten in each other category, so hydrant coverage is still limited.

## Actual image counts

| Category | Images |
|---|---:|
| `pothole` | 10 |
| `broken_streetlight` | 10 |
| `damaged_sign` | 10 |
| `leaking_hydrant` | 3 |
| `illegal_dumping` | 10 |

Image storage: 13,020,816 bytes (12.418 MiB). Labels and review are agent-curated; the note does not claim personal photography or independent human review.

## Acceptance checks

| Acceptance item | Status | Evidence |
|---|---|---|
| Real dataset obtained | PASS | 43 tracked real JPEGs and matching complete manifest/source records. |
| Permission checked before upload | PASS | Individual file-page/license checks and attribution/change notices in DATA_SOURCES and source_records.json. |
| Coverage accurately reported | PASS | All five counts shown; hydrant and condition gaps explicitly recorded. |
| Data retrievable | PASS | Clean authenticated github retrieval; 43 image hashes and manifest hash validated. |
| Dataset information displayed | PASS | Saved rows, fields, types, bytes, dimensions, formats, color modes and example grid. |
| Quality assessed | PASS | Executed integrity/duplicate/label/metadata checks, agent visual review and documented limitations. |
| Notebook reproducible | PASS | Fresh kernel and initially empty retrieval directory; Python 3.12.15; no manual cells or model key. |
| Dependencies recorded | PASS | Exact directly used installed versions in requirements.txt; clean environment installation and pip check. |
| Docker prepared | PASS | CPU Dockerfile, restricted build context and host-output commands. |
| Docker execution tested | BLOCKED | Docker CLI/daemon unavailable; build and container execution unverified. |
| Proposal changes documented | PASS | Targeted proposed text for 2.3–2.7; no original proposal document existed. |
| Sensitive content excluded | PASS | Image/privacy review, metadata stripping and task-file/history scan; unsafe originals excluded. |
| Outputs saved | PASS | Notebook JSON validated; all code cells executed; embedded real JPEG/PNG previews; zero error outputs. |
| GitHub work available | PASS | Branch pushed; remote file and SHA checks verified. See delivery verification below. |
| Native GitHub notebook rendering | BLOCKED | Browser viewer returned “Unable to render code block”; actual saved-output Markdown fallback provided in NOTEBOOK_PREVIEW.md. |
| Instructor access | BLOCKED | Private repository; no identified/authorized instructor account and no instructor invitation configured. |

## Remaining actions and limits

Instructor access is not confirmed. Supply the instructor's GitHub account and authorize an invitation before submission of private links; do not assume the instructor can view them. Docker execution needs a machine with Docker. Hydrant, nighttime, weather and Gainesville-specific coverage remain data gaps; independent label validation and model evaluation have not been performed. The current Gemini prior-user restriction remains a proposal dependency, not a notebook execution blocker.

Delivery verification is recorded in [VERIFICATION](VERIFICATION.md). Native GitHub notebook rendering remains blocked by a preview error; [NOTEBOOK_PREVIEW](NOTEBOOK_PREVIEW.md) shows the actual saved grid and statistics. Successful execution and remote file delivery are verified independently.
