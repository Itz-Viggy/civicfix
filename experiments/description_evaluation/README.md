# Description evaluation support files

Submit the **[combined CLIP + Qwen notebook](../first_model_exploration/training_experiments.ipynb)**.
It contains setup, frozen IDs, prompts, all outputs/failures, factual reviews,
paired results and visual examples. [Short findings](FINDINGS.md) · [Exact results](results.json).

The notebook's description section validates/replays the actual October 22 runs.
It preserves the original CLIP outputs and does not pretend replay is new inference.
Refresh that section from the repository root:

```sh
.venv-inference/clip/bin/python -m experiments.first_model_exploration.execute_notebook --descriptions-only
.venv-inference/clip/bin/python -m experiments.first_model_exploration.verify_submission
```

## Run new local inference

Apple Silicon, Python 3.12; no paid service or hosted fallback. CLIP uses its
existing environment/checkpoint; Qwen uses an isolated environment and pinned
public 4-bit artifact. Weight files remain ignored.

```sh
.venv-inference/clip/bin/python -m venv .venv-inference/qwen
.venv-inference/qwen/bin/python -m pip install -r experiments/description_evaluation/requirements-qwen-macos.lock
HF_HUB_DISABLE_XET=1 .venv-inference/qwen/bin/python -m experiments.description_evaluation.setup_model
.venv-inference/qwen/bin/python -m experiments.description_evaluation.run generate .runtime/description-runs/baseline-new
.venv-inference/clip/bin/python -m experiments.description_evaluation.run score .runtime/description-runs/baseline-new
```

Review the actual outputs against [rubric.json](rubric.json), saving new
`reviews.jsonl` records under [schemas.json](schemas.json). Reviews bind to exact
outputs; they cannot be reused for a fresh generation. After baseline review,
change one prompt feature and rerun the same IDs. To reproduce the existing v2:

```sh
.venv-inference/qwen/bin/python -m experiments.description_evaluation.run generate .runtime/description-runs/revision-new --prompt experiments/description_evaluation/prompts/v2.json
.venv-inference/clip/bin/python -m experiments.description_evaluation.run score .runtime/description-runs/revision-new
# Save fresh visual reviews before computing factuality metrics.
.venv-inference/clip/bin/python -m experiments.description_evaluation.report .runtime/description-runs/baseline-new .runtime/description-runs/revision-new .runtime/comparison-new.json
```

Existing run/configuration files cannot be overwritten. The 20 permitted images,
rights and hashes are fixed in [selection.json](selection.json); final-test data
is untouched. Qwen receives sanitized pixels bounded to 768 px, without source
captions/labels or identifying metadata. CLIP scores the original stored image
and generated description using native transforms and normalized cosine, with no
prefix/rescaling, confidence interpretation or automatic approval threshold.
The inherited classifier runtime metadata describes its capabilities; the scorer
configuration's top-level formula records the actual direct-text operation.

Generation failures and empty-description abstentions remain separate from
reviewed factuality. Latency includes all attempts and cold first images, but
excludes loading/persistence. Agent review is not independent human validation.
The replaceable adapter is experiment-only; no application changes are required.
Private `docs/`, raw runs and weights remain ignored. Code, checkpoint and
configuration hashes preserve the original experiment evidence.
