# Acceptance checklist

No product acceptance result has been measured. Stage 0 is documentation/design work. Each later stage must attach actual commands, outputs, environment, date and evidence to the [tracker](IMPLEMENTATION_STATUS.md). Simulated runs never establish real integration, model quality or performance.

## Stage exits

- [x] **0:** main and dataset branch reconciled, original data/notebook/rights records preserved, README links resolve, canonical PRD and contracts/config example exist, compute/credential prerequisites and next task recorded. User approved PRD as Stage 0 requirements authority; original course document not checked.
- [ ] **1A:** Implement shared strict schemas, adapter interface/registry, configuration validation and deterministic fixtures. Test bad labels/malformed fields, unclear/unsupported results, timeouts, missing keys/config, simulation labels, stale-result boundaries, no silent fallback, and no SDK imports in routing/report logic.
- [ ] **1B:** Real self-hosted open source image inference; record exact model/revision, processor, runtime, quantization/license where used, peak memory, latency, outputs and validation failures. Observe no hosted inference egress in success/failure modes.
- [ ] **1C:** Optional native Gemini adapter and honest access status; same allowed example through two real model configurations including self-hosted open source, switched by configuration only. Two real open source configurations can prove switching while hosted live check stays unverified. Run common contract/failure checks for every adapter.
- [ ] **1D:** Save initial prompts/predictions before tuning; use 43 images as development only and add normal/blurry/unsupported cases. Compare errors, unsupported facts, invalid outputs, failures, latency and compute/cost with compatible budgets. Choose a provisional measured default; real switching evidence is required for full Stage 1 completion.
- [ ] **2:** Mobile upload/camera preview/replace, optional observations, GPS and manual input with explicit location confirmation, byte/decode/dimension limits, metadata-free private derivatives, disclosure, invalid/denied/interrupted recovery and cross-session access rejection.
- [ ] **3:** Connect real analysis via common contract; edit category/description/photo; preserve inputs on provider failure; unresolved results require correction; revision/in-flight tests prevent stale overwrites. Preparation blocked until routing exists.
- [ ] **4:** Every destination/rule has official sources, verification date and version; city/county/utility/road ownership handled explicitly. Test City, County, boundary, outside-area, missing-location and category-specific cases. Unknown ownership remains unresolved.
- [ ] **5:** Server current-revision review and preparation predicates; exact preparation wording; copy text and open verified form manually. Exercise wrong category/jurisdiction, missing fields, unresolved routes, post-review edits, repeated prepare and unavailable forms. No external submission/authority ID.
- [ ] **6:** Frozen independent evaluation, timing runs and walkthrough records; preserve original targets and explain any misses. No invented participants, independent review or passing metrics.
- [ ] **7:** Recheck pricing/quotas/deployment settings, reproduce startup and run app containers, observe deployed smoke flow/session isolation/upload validation/HTTPS/rate limits/safe logs; verify clear/cancel and 24-hour deletion including temp files/caches/backups. Separate provider retention disclosure. Obtain separate deployment approval.

## Original numerical and quality targets

| Requirement | Pass condition / evidence |
| --- | --- |
| Independent classification | At least 85/100 correct first predictions, 20 independently reviewed photos per category, no duplicates/related scenes from development; abstentions on valid supported cases count wrong. Publish confusion matrix and per-class outcomes. |
| Recovery cases | 20 additional unclear/unsupported/missing-location/uncertain-routing cases; score separately from five-class accuracy. |
| Evaluation freeze | Freeze provider/model revision/quantization, prompt, preprocessing and routing version before acceptance; keep comparisons separate. If test data affects tuning, retire it or relabel later evidence as development. |
| AI timing | Usable result within 10 seconds on >=95/100 requests at one active request, and separately >=95/100 at three concurrent requests. Include retries/errors, actual cold starts and environment; local and deployed evidence separate. |
| Workflow timing | Each of 10 clear-image walkthroughs under 60 seconds to prepared; show individual times and every miss. Record additional correction/form-failure recovery exercises separately if outside those 10 runs. |
| Description quality | Zero unsupported generated facts in each passing report; compare statements against photo and attributed user observations. |
| Model independence | Same validated app behavior across two real configurations including self-hosted open source; no business-logic changes or hidden export/fallback. |
| Routing/review | Official evidence or unresolved state; current editable fields and explicit revision-bound review enforced on server. |
| Submission boundary | **Prepare Report**, **Report Prepared**, and **Your report is ready for manual submission. It has not been sent to an authority.** No authority tracking ID or receipt claim. |
| Privacy | Private session ownership, minimum model data, metadata removal, safe logs, application clear/cancel deletion and expiry by creation +24 hours including retained app copies. Disclose provider retention independently. |
| Reproduction | Fresh documented app setup, version locks, actual app container build/run evidence and deployment resource/cleanup verification. |

Any changed target must retain the original value, new value, reason and evidence. Planned thresholds are not performance claims.
