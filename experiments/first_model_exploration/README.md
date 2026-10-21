# CivicFix First Model Exploration

Real OpenCLIP `ViT-B-32` / `openai` inference, independent of the application. Start with the [executed notebook](training_experiments.ipynb), [submission note](SUBMISSION.md), [results](results.json), and [assignment checklist](ASSIGNMENT_CHECKLIST.md).

The original Milestone 3 Section 6.5 designates all 43 existing photos as development cases. [split.json](split.json) pins their IDs and the original document hash. There are no held-out test cases in this pool. Separate final evaluation data is still needed. Images, original labels and the existing playground remain unchanged.

## Reproduce

Tested on Python 3.12.15, macOS arm64, Apple M5, 24 GiB unified RAM. CPU float32, batch size 1, four torch threads. MPS is available but was not used. No paid service or remote inference is configured. The root notebook environment and dependencies are preserved.

From the repository root, using Python 3.12.15 (the existing `.venv/bin/python` also works to create the isolated environment):

```sh
python3.12 -m venv .venv-inference/clip
.venv-inference/clip/bin/python -m pip install -r experiments/first_model_exploration/requirements-macos.lock
.venv-inference/clip/bin/python -m pip check
.venv-inference/clip/bin/python -m experiments.first_model_exploration.setup_model
.venv-inference/clip/bin/python -m experiments.first_model_exploration.execute_notebook
.venv-inference/clip/bin/python -m unittest experiments.first_model_exploration.test_benchmark -v
.venv-inference/clip/bin/python -m experiments.first_model_exploration.verify_submission
```

The lock includes transitive versions for the tested Mac environment; Linux/container execution is unverified. Exact direct versions are also recorded in `requirements.txt`. `setup_model` downloads only the original public OpenAI checkpoint (353,976,522 bytes) and verifies the pinned SHA-256 in [model.json](model.json). It does not create an endpoint or upload data. Weights stay ignored under `.runtime/models/clip/`. The original artifact is TorchScript: `weights_only=False` is required by its loader and is used only after the known public artifact's hash is verified. OpenAI-native QuickGELU and preprocessing are explicitly preserved.

The notebook uses a fresh kernel, disables Hugging Face network operations, and rejects external Python socket connections during inference. Loopback remains available for Jupyter; this is a Python-level check, not an OS-wide network audit. Zero external attempts were observed. Only pixels and the same fixed taxonomy reach the model; labels and source captions are joined after predictions are saved. All errors remain in attempted-case accounting.

Each execution creates a new ignored `.runtime/clip-runs/exploration-*` directory, containing the frozen configuration, append-only first predictions, metrics, hypothesis and a safe aggregate summary. Existing run artifacts are never overwritten. To refresh the tracked aggregate after reviewing a rerun, copy that run's `safe_summary.json` to this folder's `results.json`; keep raw run records local. Timing can vary while identical configurations should reproduce classifications on the tested environment. Unit-test fixtures are synthetic and excluded from inference evidence.

## Evidence and limits

Baseline: 40/43, accuracy 93.02%, macro-F1 0.9101. Revision: 41/43, accuracy 95.35%, macro-F1 0.9304. Only dumping text descriptions changed; the full prompts and exact configurations are saved. The revision corrected two errors and introduced one regression. Seven baseline errors/weak cases were visually inspected, including all three hydrants; the regression was inspected afterward.

Per-image wall timing includes file read/decode, RGB conversion, native preprocessing, image encoding, cosine scoring and result extraction. Model loading/text encoding are reported separately. CPU runs were sequential, without retries; the first image was not pre-warmed. Revision uses the same loaded model. These measurements exclude the full application, transfer and queues; they cannot verify the Section 2.1 target of 95/100 requests below 10 seconds at each concurrency load. There are no API charges; electricity and owned hardware costs were not priced.

The labels are agent-curated, three hydrants are sparse, two hydrants depend on captions, and nonlocal/daylight scenes dominate. A forced-choice CLIP score is not a calibrated probability or validation that an issue exists. Unknown exposure to CLIP's original pretraining data also limits interpretation. No independent final-test, irrelevant-image rejection, hosted HF API, Qwen report generation or application acceptance is claimed.

[OpenCLIP](https://github.com/mlfoundations/open_clip) and [OpenAI CLIP](https://github.com/openai/CLIP) publish MIT licenses; consult their notices and [CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md) for research intended-use guidance and deployment limits. The original OpenAI weight source/hash is pinned in `model.json`; no weight file is redistributed here. Photos retain their individual licenses, authors and source links in `data/labels.csv`. The private course sources and PRD are represented only by hashes and narrow requirements summaries; `docs/` remains ignored and untracked.

GitHub reported this repository public during H6 (October 21, 2026); a grader can use the published links without a private-repository invitation. No visibility setting was changed. Private documents, weights and raw run artifacts remain ignored and untracked. Docker and hosted service reproduction remain unverified and are outside this homework.
