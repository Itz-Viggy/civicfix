# First Model Exploration submission

I explored CivicFix's image-classification stage first using pretrained OpenCLIP ViT-B-32 with OpenAI weights. It fits the five-category labeled collection and runs on owned CPU hardware without weight training or paid APIs. Qwen photo descriptions/clarification, destination routing and report preparation remain separate future application work.

The baseline scored **40/43 (93.02%)**, macro-F1 **0.9101**. One error was a leaking-hydrant label on a wet-lane photo with no visible hydrant; its caption-supported label cannot be established from the pixels alone. I visually inspected all three baseline errors and four additional weak/sparse cases. After observing two dumping errors, I changed only the dumping text prompts to cover single appliances and scattered garden waste. On the **same 43 development images**, the revision scored **41/43 (95.35%)**, macro-F1 **0.9304**: two errors were fixed and one rubble image regressed to damaged sign. This helped on reused development cases, with no claim of unseen-data improvement.

The original completed Milestone 3 Section 6.5 explicitly treats all 43 already-inspected photos as development examples; separate final evaluation photos are still needed. The split/source hash and exact IDs are recorded. No final test examples were used, and labels/images were unchanged. Three hydrants, agent-curated labels, mostly daylight/nonlocal scenes and unknown pretraining overlap limit the results. Cosine scores are relative similarities, not calibrated confidence.

| Run | Fixed model/settings | Single change | Correct/N; accuracy | Macro-F1 | N; failures | Mean / p95 per image | Service charge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | ViT-B-32/openai; CPU fp32; native transforms; batch 1; 4 threads; v1 | none | 40/43; 93.02% | 0.9101 | 43; 0 | 0.03965 / 0.05081 s | $0 |
| Revision | ViT-B-32/openai; CPU fp32; native transforms; batch 1; 4 threads; v2-dumping-visual-coverage | dumping text only | 41/43; 95.35% | 0.9304 | 43; 0 | 0.03925 / 0.04847 s | $0 |

Timing used an Apple M5 Mac with 24 GiB unified memory and Python 3.12.15. Sequential per-image wall time includes file read/decode, preprocessing, image encoder, cosine scoring and result extraction; model loading and text prototypes are measured separately in the notebook. The first baseline image was not pre-warmed, and revision shared the loaded model. Both runs completed 43/43 below 10 seconds; this does **not** verify Section 2.1's 95/100-request target at one and three concurrent requests, or the full workflow. Electricity and owned hardware were not priced. No hosted HF allocation, remote image processing or paid resource was used.

Full prompts, model/checkpoint/tokenizer hashes, package pins, configurations, per-class metrics, confusion matrices, case analysis and visible real outputs are in the [executed notebook](training_experiments.ipynb) and [aggregate results](results.json). The first baseline and full-notebook verification produced identical categories and cosine scores. An initial TorchScript loader incompatibility was resolved before scoring; there is no remaining technical blocker. Raw first predictions/configs/hypothesis remain locally ignored; only safe results and neutral-ID observations are committed. The [assignment checklist](ASSIGNMENT_CHECKLIST.md) was checked against the original assignment; a Section 7 draft is kept privately.

The original OpenAI CLIP artifact and OpenCLIP use MIT notices; the [model card](https://github.com/openai/CLIP/blob/main/model-card.md) describes research intended use and deployment limitations. Individual image rights/attribution remain in the unchanged dataset manifest. See [reproduction and source notes](README.md).

## Repository hand-in

Publication details will be filled only after the actual experiment commit is created and its remote branch is verified. GitHub reports the repository public (verified during H6); no visibility change or invitation was made. Private course documents and raw run artifacts remain local. H0–H6 complete this homework only, not the full app.
