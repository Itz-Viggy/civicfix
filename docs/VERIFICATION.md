# Execution and delivery verification

Checked on 2026-10-04 (America/New_York; UTC records fall on 2026-10-05). Machine-readable measured results are in [verification_results.json](verification_results.json). The acceptance checklist and submission note are in [SUBMISSION](SUBMISSION.md).

## Clean reproduction

A separate clean clone of branch `dataset-playground`, commit `30894ac82e478c7787f80e950e86691fc01f64ba`, received a new Python 3.12.15 virtual environment. Its requirements were installed with `pip install --no-cache-dir -r requirements.txt`, without using the development environment's installed packages. `pip check` reported no broken requirements.

From that clone's root, both commands completed successfully:

```sh
CIVICFIX_DATA_MODE=local .venv/bin/python scripts/execute_notebook.py
.venv/bin/python scripts/execute_notebook.py
.venv/bin/python -m unittest scripts.test_dataset_tools -v
.venv/bin/python -m pip check
```

Each notebook run started a fresh kernel and a newly created empty retrieval directory. Local mode copied the tracked data; default `github` mode downloaded the manifest and 43 image files from immutable dataset commit `8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4` using existing GitHub authentication. The manifest SHA-256 and every image SHA-256 matched in both modes. Acquisition timestamps and tracked data were not regenerated.

The notebook saved in this branch is the actual final **github** execution from that clean clone. Its 7 code cells have sequential execution counts 1–7, with zero error outputs. `nbformat.validate` passed. Actual outputs include metadata tables, first records, a ten-photo grid, all five class counts, the bar chart and measured quality checks. The grid uses an embedded JPEG to reduce notebook size; the chart remains an embedded PNG. This reduced the notebook from roughly 2.89 MB to 545,243 bytes without changing dataset images. The preview grid was visually inspected for readable IDs, labels, defect evidence and privacy.

Five regression checks passed: traversal rejection, nonempty-cache rejection, manifest-corruption rejection, image-checksum rejection and missing-private-access rejection. These exercise the retrieval boundary with the real manifest and tracked images. They do not validate label accuracy.

## Agreement and privacy

Programmatic comparison confirmed agreement among both run summaries, 43 manifest rows, 43 actual/tracked image files, 43 source records, the candidate ledger, notebook outputs, README, quality findings, proposal text and submission counts. Image bytes total 13,020,816 (12.418 MiB); category counts are 10/10/10/3/10 in specification order. Required values, decode failures, hash mismatches, exact duplicates, inconsistent hash labels, EXIF and GPS fields were zero. All included rows are agent-reviewed. The 71-candidate ledger records 43 included, 26 excluded and 2 not acquired. All included source/license check timestamps precede the first dataset commit.

Images were reviewed with their source captions before upload. Excluded originals stay in ignored temporary work, outside Git history and notebook outputs. All task commits, intended tracked text, staged files and saved notebook were screened for credential patterns and personal development paths. No matching credential/private-path material was found. Tracked files and the intended diff were inspected; environments, caches, acquisition scratch files and clean-clone artifacts are ignored. No unrelated preexisting work was present or overwritten.

## GitHub and visible output status

Authenticated GitHub checks confirm [Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix) is private with default branch `main`. Implementation is on [dataset-playground](https://github.com/Itz-Viggy/civicfix/tree/dataset-playground); it was pushed without merging or force-pushing. The approved dataset was committed/pushed before configuring its immutable retrieval version. Remote branch SHA and authenticated notebook-file checks verify delivery; the final branch commit contains this report and the saved clean-clone notebook.

The direct [playground.ipynb](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/playground.ipynb) URL was inspected while signed in through Chrome. GitHub displayed the correct private repository, branch, filename and pushed commit, but its notebook viewer returned **“Unable to render code block.”** The smaller, validated notebook was retried and received the same result. The cause was not established; successful native GitHub notebook rendering is **not claimed**.

[NOTEBOOK_PREVIEW](NOTEBOOK_PREVIEW.md) provides a Markdown fallback using images extracted from the actual saved outputs, the measured counts and per-image attribution. The notebook retains its outputs for download/opening in Jupyter. No private repository content was sent to a public notebook-viewing service, and repository visibility was preserved.

## Remaining external actions and data gaps

- **Instructor access: BLOCKED.** Authenticated collaborator checks show only the owner and zero pending invitations. No instructor account was identified/authorized, so no invitation was sent. The instructor needs access before these private submission links are usable.
- **Docker execution: unverified.** The CLI/daemon is unavailable. The CPU Dockerfile, restricted context and host-output commands exist; build/container testing still requires Docker.
- **GitHub notebook viewer: unresolved preview error.** Saved output validation and Markdown fallback are available; native notebook rendering remains unverified.
- **Data coverage:** only 3 hydrant examples, with 2 relying on source captions for invisible hydrant bodies; limited low light, unrecorded weather and no verified Gainesville routing coverage. Independent label validation and model accuracy/latency testing have not occurred.
- **Future model dependency:** the exact planned Gemini model's prior-user access restriction is documented in [MODEL_NOTES](MODEL_NOTES.md); account-level availability was not tested. This does not block the required notebook, which makes no model calls.
