# Description evaluation findings

The completed CLIP and Qwen experiments are submitted together in
[training_experiments.ipynb](../first_model_exploration/training_experiments.ipynb).
D0–D5 are complete; the description prompt change did not improve results.

Both runs used local Qwen3-VL-4B-Instruct (pinned MLX 4-bit), the existing verified
OpenCLIP ViT-B-32 checkpoint, and the same 20 frozen development photos.

| Run | Attempted / valid / reviewed | Mean raw cosine | Zero unsupported claims | Clarity / specificity | Mean / p95 generation time |
| --- | --- | --- | --- | --- | --- |
| Baseline v1 | 20 / 16 / 16 | 0.327345 | 8/16 | 1.94 / 1.75 | 8.148 / 10.283 s |
| One prompt change v2 | 20 / 15 / 15 | 0.324122 | 7/15 | 2.00 / 1.80 | 7.868 / 10.022 s |

One visual-evidence self-check instruction was added after baseline review.
On **14 shared reviewed cases**, zero-unsupported outputs fell from **7/14 to
6/14**: one fix and two regressions. Mean paired cosine changed by −0.001909.
Missing important facts occurred in 4/16 and 3/15 outputs, with no change on
shared cases. Failures increased from 4 to 5; all attempts remain accounted for.

The leaning-sign attachment claim was removed. Regressions included an invented
green indicator/operating status and unsupported serviceability/site designation.
The green-indicator case gained cosine similarity despite worse factuality.
String `"null"` values and excessive sentences caused contract failures; no output
was repaired or retried. The notebook includes all records, reviews and examples.

**Similarity is not factual accuracy or official CLIPScore.** Passing factuality
requires zero unsupported assertions across all reviewed fields. Reviews were
performed by an agent, not independently by a human. Timing includes all attempts
but excludes model loading; it does not establish application performance.

These previously inspected development photos do not establish held-out
reliability. Keep the experiment offline; do not promote v2 or use CLIP as an
approval threshold. Independent review and new test photos remain needed.
No application feature was added; private docs, raw runs and weights stay ignored.

[Reproduce](README.md) · [Exact results](results.json) · [Per-image evidence](evidence/)
