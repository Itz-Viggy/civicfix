# Description evaluation findings — October 22, 2026

**D0–D5 are complete. The description evaluation is complete as a development
experiment. The prompt change did not improve the result.** Completion means
the experiment was executed and evaluated, not that every generation passed or
that the application is accepted for use.

## Actual results

Both runs used **Qwen3-VL-4B-Instruct, pinned MLX community 4-bit conversion**
`2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b`, MLX-VLM 0.3.12 on Apple M5 Metal,
24 GiB memory, greedy generation, 384-token limit, seed 6216 and the same ordered
20 development photos. Full versions, prompt text, model hashes, source hashes
and settings are in each immutable configuration. [results.json](results.json)
contains the unrounded metrics and all 20 paired status records.

| Run | Model + prompt version | Attempted / valid generated / reviewed | Mean image–text score | Zero unsupported claims / reviewed | Clarity / specificity (0–2) | Mean / p95 generation latency |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | Qwen3-VL-4B-Instruct, MLX 4-bit; description-v1 | 20 / 16 / 16 | 0.327345 raw cosine, N=16 | 8 / 16 (50.0%) | 1.9375 / 1.7500 | 8.148 / 10.283 s, N=20 |
| One prompt change | Same model/runtime; description-v2 | 20 / 15 / 15 | 0.324122 raw cosine, N=15 | 7 / 15 (46.7%) | 2.0000 / 1.8000 | 7.868 / 10.022 s, N=20 |

The scorer protocol is `openclip-vit-b32-openai-native-raw-cosine-v1`: existing
OpenAI ViT-B-32 weights and native OpenCLIP transform/tokenizer, direct normalized
image–description dot product, no prefix or rescaling. **These are similarities,
not probabilities, factual accuracy percentages or official CLIPScore.** Median
cosines were 0.325933 and 0.325605. Maximum text token occupancies were 35 and 34
of 77, so no context truncation was indicated. There were no CLIP execution
errors; 4 baseline and 5 revised records were skipped because generation failed.

All output fields were reviewed against the fixed visual rubric, including
observations and factual assertions in clarification reasons. Reviews were made
by the Codex primary agent viewing photos, not independently by a human. They
were not blinded to run/prompt identity. Zero unsupported claims is the sole
factuality passing condition among reviewed outputs; a passing output can still
omit information. These judgments are not an independently validated accuracy
measurement. Atomic assertions, rationale and reviewer provenance are saved for
each reviewed case so another reviewer can challenge them.

The baseline had 11 unsupported atomic claims across 16 reviews; the revision had
12 across 15. Missing important visible facts occurred in 4/16 and 3/15 outputs.
Neither lower missing-fact count nor higher aggregate specificity proves an
improvement because the successful-case sets differ. Abstentions were zero in
both runs; invalid structured outputs were counted as failures, not abstentions
or factuality passes. Model-reported `outcome` is not the review result.
Here an abstention means a valid output with an empty description. The baseline
also had one nonempty output with self-reported `outcome: unsupported`; it was
retained for scoring/review rather than automatically treated as correct or
discarded. The model's own label does not determine factuality.

## Controlled comparison

After baseline visual review, one feature was added: **“Before returning JSON,
check every proposed assertion against the visible pixels and delete any
assertion that is not directly observable.”** The base prompt was preserved
verbatim. The hypothesis and potential regressions were
[registered before revised inference](evidence/prompt_change_before_revision.json).
Model/artifact, quantization, implementation, ordered image IDs, preprocessing,
decoding, scorer and rubric stayed unchanged; the comparison guard passed.

On the **14 jointly valid, jointly reviewed cases**, zero-unsupported outputs
fell from **7/14 to 6/14**, with **one fix and two regressions**. Unsupported claim
count increased by 2 on these pairs. Mean paired cosine change was **−0.001909**
(median 0), clarity changed by +0.071429, specificity by 0, and missing-important-
fact count by 0. All 20 cases remain in status and latency comparisons. There
were two newly invalid outputs, one recovered valid output and three failures
in both runs. This is a negative development result; v2 is not recommended over v1.

| Case | Baseline → revision | Interpretation |
| --- | --- | --- |
| [Leaning road sign](../../data/images/commons-04258228ae.jpg), `commons-04258228ae` | 1 → 0 unsupported claims | Removed an unsupported attachment to a fence post; retained the visible bent/leaning condition. Factuality fix. |
| [Displaced globe light](../../data/images/commons-2409b4bbcb.jpg), `commons-2409b4bbcb` | 0 → 2 unsupported claims; cosine **+0.013173** | Revision invented an illuminated green indicator from a green surface patch and inferred operating status. Higher similarity accompanied worse factuality. |
| [Objects beside a fence](../../data/images/commons-0f02ab33ca.jpg), `commons-0f02ab33ca` | 0 → 2 unsupported claims | Revision inferred lack of serviceability and ruled out utility-area designation. Visible discarded-looking items do not establish these facts. |
| [Hidden water source](../../data/images/commons-1b000da556.jpg), `commons-1b000da556` | 0 → 0 unsupported claims | Both descriptions state visible water from the ground, without claiming a visible hydrant body or an accidental leak cause. The tentative category is not confirmation. |
| [Road-name panel below STOP sign](../../data/images/commons-1be7ba9610.jpg), `commons-1be7ba9610` | 2 → 1 unsupported claims; important omission persists | Removing the graffiti guess helps partially, but both runs focus on the STOP sign and miss the stripped road-name panel. Still not a factuality pass. |

## Failures and timing

There was exactly one attempt per image per run, with no retries, JSON repairs or
caption substitutions. All 40 status/timing records and 31 real cosine scores
are published. The first contract errors were:

- Baseline: two outputs returned the string `"null"` instead of JSON `null`, and
  two descriptions exceeded two sentences: **4/20 failures, 80% valid coverage**.
- Revision: three string-`"null"` errors and two sentence-limit errors:
  **5/20 failures, 75% valid coverage**. Some invalid outputs violate more than
  one constraint; diagnostics report the first validation error.

[Baseline diagnostics](evidence/baseline/failure_diagnostics.jsonl) and
[revision diagnostics](evidence/revision/failure_diagnostics.jsonl) retain the
returned category/description and response hashes. Full raw responses remain
ignored locally. Failures were never scored or counted as factuality passes.

Latency is local sequential wall time from decode/sanitization through completed,
synchronized generation and parsing, including failed attempts. Downloads, model
load and persistence are excluded. Cold first-image times were 13.137 and 9.402 s;
model loads were separately measured at 2.389 and 2.017 s. p95 uses linear
interpolation on all 20 attempts. Runs were sequential and unrandomized, with no
repeated timing trials; the measured −0.281 s mean difference does not establish
a causal latency improvement or an application SLA.

## Evidence, verification and boundaries

See [runnable instructions](README.md), [selection/provenance](selection.json),
[fixed rubric](rubric.json), [baseline evidence](evidence/baseline), and
[revised evidence](evidence/revision). Published records contain only inspected,
permitted benchmark outputs. Individual photo rights/attributions are retained
in the selection and original manifest. Weights, private documents and raw run
files remain ignored. Each inference/scoring process reported **zero denied
Python socket connection attempts**; this is not an OS-wide network audit.
No paid inference or hosted fallback was used. Service charges were $0; owned
hardware and electricity costs were not priced.

The public artifact download initially stalled through Xet and succeeded through
HTTP with `HF_HUB_DISABLE_XET=1`; all LFS hashes were checked. The processor first
required Torch/Torchvision, then loaded after installing the same pinned versions
as the classifier into the isolated Qwen environment. A direct processor probe
also needed a `Path` argument rather than a string; the actual adapter's normal
loader worked. One local review-writing helper initially lacked `PYTHONPATH=.`,
failed before writing evidence, and was rerun successfully. No such setup error
is presented as a successful test or a model result.

Executed verification: **9 description harness tests**, **13 existing classifier/
dataset tests**, the existing saved-submission verifier, both environment
dependency checks, Python compilation, and recomputation from published evidence
with a byte-for-byte matching results JSON. The classifier notebook was read and
its saved evidence verified; classification inference was not rerun. The completed
classification experiment, original data/labels, split, model contract, application
configuration and dependencies were preserved. `docs/` is ignored and untracked.

No execution blocker remains for D0–D5. Each stage's exit evidence is recorded in
[stage_status.json](evidence/stage_status.json). Evaluation completion includes
properly accounted failures; it does not require every attempt to succeed.

## Limits and integration recommendation

These 20 photos come from 43 already inspected development examples, with sparse
hydrants and uneven scene coverage. There is no held-out performance claim,
statistical significance test, independent human review, production concurrency
test or application acceptance claim. Review judgments about subtle damage,
lettering and qualifiers can vary. Some apparent issue identities are caption-
supported in the original dataset, but captions and labels were not passed to
Qwen and were not treated as visible evidence during review. The community
conversion identifies its upstream model, but does not pin that upstream source
commit; its exact converted artifact is pinned and verified here. Results apply
to this quantized configuration, not necessarily upstream full precision.

Keep this as offline development evidence. Do not promote the revised prompt
or add CLIP as a required production call or acceptance threshold. Any later
description integration should preserve the replaceable adapter and require
user review, especially for hidden water sources, operating status, disposal
authorization and sign text. Independent review and new held-out data are still
needed before drawing reliability conclusions. No application feature, routing,
submission, database or deployment work was implemented.

## Section 7-ready finding

We extended the completed classifier experiment with local Qwen3-VL-4B-Instruct
description generation and existing OpenCLIP image–text cosine scoring on 20
frozen development photos. Baseline generation yielded 16 valid outputs; 8/16 had
zero unsupported claims under agent visual review. One evidence-self-check prompt
addition yielded 15 valid outputs and 7/15 zero-unsupported outputs. On 14 shared
reviewed cases, there was one fix and two regressions; mean cosine decreased by
0.001909. Similarity and factuality were evaluated separately, including a case
where cosine increased while unsupported claims appeared. The intervention was
not an improvement, and these reused development cases do not establish unseen-
photo reliability or application acceptance.
