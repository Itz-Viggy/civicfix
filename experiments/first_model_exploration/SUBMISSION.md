# Combined model exploration submission

Submit **[training_experiments.ipynb on main](https://github.com/Itz-Viggy/civicfix/blob/main/experiments/first_model_exploration/training_experiments.ipynb)**
with its repository support files. Both experiments, their configurations,
outputs, review examples and conclusions are in this one executed notebook.

## Classification

Pretrained OpenCLIP ViT-B-32/OpenAI was explored first because it runs locally
and fits the five-category labeled pool. Only the dumping prompts changed after
reviewing errors; the same 43 development photos were used.

| Run | Correct | Macro-F1 | Mean / p95 time |
| --- | --- | --- | --- |
| Baseline | 40/43 (93.02%) | 0.9101 | 39.65 / 50.81 ms |
| Dumping-prompt revision | 41/43 (95.35%) | 0.9304 | 39.25 / 48.47 ms |

Two errors were fixed and one introduced. Original classification cells and
outputs are preserved.

## Descriptions

Local Qwen3-VL-4B-Instruct (MLX 4-bit) generated descriptions for 20 frozen photos.
The existing OpenCLIP checkpoint scored alignment; a separate visual rubric
checked all factual assertions, clarity, specificity and missing details.

| Run | Attempts / valid / reviewed | Mean raw cosine | Zero unsupported claims | Mean / p95 time |
| --- | --- | --- | --- | --- |
| Baseline | 20 / 16 / 16 | 0.327345 | 8/16 | 8.148 / 10.283 s |
| One self-check prompt addition | 20 / 15 / 15 | 0.324122 | 7/15 | 7.868 / 10.022 s |

The change did not improve results: one fix and two regressions on 14 shared
reviewed cases. All failures remain accounted for. The notebook validates and
displays saved real Qwen runs; its optional helper can launch new inference.

These are reused development cases and agent visual reviews, not independent
human or held-out validation. Cosine is similarity, not factual accuracy or
confidence. Both experiments used owned hardware with $0 service charges;
application, concurrency and destination-routing acceptance are not claimed.
Private documents and weights remain ignored.

[Reproduce](README.md) · [Description support files](../description_evaluation/README.md) · [Short findings](../description_evaluation/FINDINGS.md)
