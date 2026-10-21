# Original assignment verification

Checked against the original uploaded **EGN 6216, Fall 2026, Homework: First Model Exploration**, including all six steps, “Keep Your Evaluation Honest,” “Commit and Document,” “What to Submit,” and all seven final checklist items. [source_verification.json](source_verification.json) records the original source hashes; the source documents remain private. Requirements come from the assignment; the unrelated example-model rows and old PRD kickoff prompts are not additional implementation requests.

| Requirement | Evidence | Result |
| --- | --- | --- |
| Dedicated organized notebook | `training_experiments.ipynb`: Setup, Data preparation, Candidate/model configuration, Inference, Evaluation, Error analysis, Targeted change, Results/conclusion | Pass |
| Step 1: 2–3 sentence AI role; inputs/outputs | Candidate/model configuration: photo → five-category suggestion and cosine scores | Pass |
| Candidates and first-choice rationale | CLIP B/32 first; SigLIP, B/16, Qwen later; CPU, labeled pool, no weight training | Pass |
| Identify/test deterministic responsibilities as needed | Taxonomy round-trip/unknown rejection in notebook; arithmetic/split tests; app routing and preparation remain deferred | Pass |
| Step 2: Milestone 3 data, shapes, labels, balance, missingness | Data preparation outputs: 43 RGB JPEGs, dimensions, 10/10/10/3/10, missing metadata, license counts, duplicate screening | Pass |
| Document filled/dropped/unchanged | None filled or dropped; labels and missing optional metadata unchanged | Pass |
| Section 6.5 separation; no test leakage | Independently read completed original: all 43 designated development. Explicit IDs/source hash in `split.json`; no final test cases present or consumed | Pass |
| Learned preprocessing fitted only on training | No fitting, augmentation, fine-tuning or learned CivicFix transform; native frozen CLIP preprocessing only | Pass |
| Step 3: simplest real candidate end to end | First real `[1,3,224,224]` tensor → `[1,512]` embedding → five finite scores and category | Pass |
| Freeze configuration before tuning | New immutable config before image inference; checkpoint/tokenizer hashes, package versions, prompts, transforms, IDs, seed, CPU precision, budget | Pass |
| Document pretrained budget and seed | No weight training; seed 6216; deterministic torch algorithms | Pass |
| Step 4: relevant metrics, score and N | 40/43 then 41/43; accuracy, macro-F1, per-class precision/recall/F1/support; confusion matrices; failures counted | Pass |
| Save readable evaluation visualization; preliminary qualification | Both confusion-matrix plots embedded; small reused development set explicitly qualified | Pass |
| Step 5: 5–10 errors/weak outputs if available | All three baseline errors plus four weak/sparse cases, seven total; expected/predicted, observations, margins and likely causes | Pass |
| Confidently incorrect outputs where applicable | Largest wrong margin inspected; no calibrated confidence/probability asserted | Pass |
| Practical constraint and Section 2.1 comparison | Measured batch-1 sequential CPU latency, separate setup/first image; compared with 10-second 95/100 target without claiming load-test success | Pass |
| Step 6: one evidence-driven change and expected benefit | Before-run hypothesis; only three dumping descriptions changed; four other prompt sets unchanged | Pass |
| Same examples, metrics and scoring | Exact ordered 43 IDs and configuration guard; same accuracy/F1 procedure; startup/timing differences disclosed | Pass |
| Record whether change helped, hurt or unclear | Net +1 correct, +2.33 percentage points accuracy; two fixes, one regression; no claim of generalization | Pass |
| No technical failure disguised as result | Initial loader incompatibility documented and fixed before predictions; zero inference failures in completed runs | Pass |
| Model source/license and data permissions | `model.json`, README source/license notes, unchanged per-photo attribution/rights manifest | Pass |
| Save visible outputs; exclude credentials/large files | All code cells executed; two embedded plots; raw runs/weights ignored; only safe configs, aggregates and neutral-ID observations exported | Pass |
| Push descriptive commit and actual link/identifier | Actual published experiment commit and notebook link recorded in `SUBMISSION.md`; verified during H6 | Pass — remote commit and notebook blob verified |
| Submission: short note, one row per run, initial stage/why | `SUBMISSION.md` includes candidate, initial result, limitation, change/effect, two-row configuration/score/N/runtime/cost table and stage rationale | Pass |
| Prepare Section 7 role/candidates/config/results/next steps | Private local `docs/FIRST_MODEL_EXPLORATION_SECTION_7.md` draft | Pass locally; intentionally untracked |

H0–H6 cover this homework only. App Stage 0 remains complete; main-app Stages 1A–7, hosted HF verification and final product acceptance remain pending. Repository visibility was independently checked during H6: public. No invitation is required to view the safe submission; no visibility setting was changed.
