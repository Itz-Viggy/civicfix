# Offline description evaluation (D0–D5)

This additional development experiment uses Qwen3-VL-4B-Instruct for structured
photo descriptions and the existing OpenCLIP ViT-B-32/OpenAI checkpoint for
image–description cosine similarity. It does not change the classification
experiment, application providers, routing, labels or final-test policy.

**Evaluation complete:** see [actual findings](FINDINGS.md) and
[machine-readable results](results.json). The single prompt intervention was a
negative result; generation failures and factuality regressions are retained.

The frozen [selection](selection.json) contains 20 of the existing 43 development
photos: 4 potholes, 4 streetlights, 4 signs, all 3 hydrants and 5 dumping photos.
Selection used category quotas and lexicographic IDs before examining generation
results. Source links, authors, individual licenses and pixel hashes are retained;
the photos remain in `data/images/`. Only those public, permitted benchmark photos
are used. Private planning documents remain ignored under `docs/`.

## Reproduce

Run from the repository root on Apple Silicon. The Qwen runtime is isolated from
the existing classification environment. The saved lock records its actual
dependencies, including transitive dependencies required by MLX-VLM. No server,
paid inference, account upgrade or remote inference fallback is used.

```sh
.venv-inference/clip/bin/python -m venv .venv-inference/qwen
.venv-inference/qwen/bin/python -m pip install -r experiments/description_evaluation/requirements-qwen-macos.lock
.venv-inference/qwen/bin/python -m pip check
HF_HUB_DISABLE_XET=1 .venv-inference/qwen/bin/python -m experiments.description_evaluation.setup_model
.venv-inference/clip/bin/python -m unittest experiments.description_evaluation.test_evaluation -v

.venv-inference/qwen/bin/python -m experiments.description_evaluation.run generate .runtime/description-runs/baseline-new
.venv-inference/clip/bin/python -m experiments.description_evaluation.run score .runtime/description-runs/baseline-new
```

The existing CLIP setup/environment is described in
[`first_model_exploration/README.md`](../first_model_exploration/README.md).
The selection is already frozen; do not rerun `prepare` to select convenient
examples after seeing outputs. `setup_model` verifies a pinned public artifact
and all Hub LFS checksums. It never overwrites a different artifact manifest.
Generation verifies every local model file before loading, disables Hub network
access and rejects Python socket connections. This guard is not an OS-wide audit.

Each new run directory contains an exclusive-create immutable configuration and
append/fsync JSONL first results, including errors. Existing runs cannot be
overwritten. There is one generation attempt per photo, no JSON repair and no
retries. Runtime settings, model file hashes, package versions, prompt text/hash,
data/split/schema/rubric hashes, implementation hashes, timing scope, and a
configuration identity hash bind every output. Sanitized PIL RGB pixels and the
fixed prompt are the entire adapter input: no ID, filename, label, source caption,
annotation, precise coordinates or user observation. `DescriptionGenerator` is
an experiment adapter protocol; it adds no required application inference call.
The generator receives an aspect-preserving image bounded to 768 pixels on its
long side before native Qwen preprocessing; there is no upscaling at that bound.
CLIP still receives the original stored image through its existing transform.

## Score and review separately

The scorer reuses `first_model_exploration.benchmark.Runtime` unchanged: the same
SHA-256-verified checkpoint, QuickGELU, native image transform, tokenizer, CPU
float32 and four threads. It encodes the original stored image and generated
`description` text alone, L2 normalizes each, then takes their dot product.
**This is raw cosine similarity, not official CLIPScore**, confidence or factual
accuracy. There is no text prefix, rescaling or automatic approval threshold.
The reused runtime retains its classifier capability metadata (`score_method`);
the scorer configuration's top-level `formula` records the direct-text operation
actually executed here. No category prototypes or classification prompts are used.
Native 77-token context occupancy is recorded so potential truncation is visible.
Failures and abstentions have null scores and remain in attempted denominators.

Review every image–output pair against [rubric.json](rubric.json), including
`visible_observations` and factual assertions in clarification fields. Reviewers
record atomic unsupported assertions, clarity, specificity, missing visible facts,
notes, identity/type/method/time and hashes binding the review to its output and
rubric. **Zero unsupported claims among reviewed outputs** is the sole factuality
passing condition. Missing details, generation coverage, scores and latency are
reported separately. Model self-reported `outcome` is not a review decision.
Agent visual review is explicitly identified; it is not independent human review.

Save reviews as `reviews.jsonl` using [schemas.json](schemas.json). Based on baseline
review only, change the `feature` string of the generator prompt once, preserving
the `base` text and all other model/data/decoding/scorer/rubric settings. Record the
hypothesis before rerunning. Use the same 20 IDs:

```sh
.venv-inference/qwen/bin/python -m experiments.description_evaluation.run generate .runtime/description-runs/revision-new --prompt experiments/description_evaluation/prompts/v2.json
.venv-inference/clip/bin/python -m experiments.description_evaluation.run score .runtime/description-runs/revision-new
# Visually re-review the saved outputs, then save revision reviews.jsonl.
.venv-inference/clip/bin/python -m experiments.description_evaluation.report .runtime/description-runs/baseline-new .runtime/description-runs/revision-new .runtime/description-runs/comparison-new.json
```

`report` validates identities and reviews, requires unchanged scorer settings and
exactly one prompt feature change, and computes paired changes including fixes and
regressions. It never writes reviews or infers factuality from similarity. Raw
model responses, weight files and intermediate runs stay ignored in `.runtime/`;
only inspected benchmark outputs and evidence are suitable for publication.

To recompute the published comparison without loading models, choose a new output
path (exclusive creation prevents overwriting earlier evidence):

```sh
.venv-inference/clip/bin/python -m experiments.description_evaluation.report experiments/description_evaluation/evidence/baseline experiments/description_evaluation/evidence/revision .runtime/comparison-recheck.json
cmp experiments/description_evaluation/results.json .runtime/comparison-recheck.json
```

Local latency includes decode/sanitization, preprocessing, completed synchronized
generation and strict parsing. It excludes download, model load and persistence.
Each run starts a fresh process; the first image is cold and included in mean/p95.
This measures sequential development inference, not application concurrency or
end-to-end service latency. No held-out or production acceptance claim is implied.
