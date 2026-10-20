# CivicFix development PRD

Draft v0.2 | October 20, 2026 | Owner: Vignesh Sundararajan

Status: Updated for model independence and staged Codex execution. Product decisions remain reviewable. The kickoff prompt below starts Stage 0 only when given to the coding agent; this PRD update does not itself build or deploy the app.

## 1. Goal

Build a mobile friendly app that turns a photo, a confirmed location, and optional user details into a report the user can review, correct, and prepare for separate manual submission.

The first complete version supports the five existing issue categories in the Gainesville area. It identifies a likely issue, writes a short description, checks the responsible authority, and gives the user the appropriate reporting destination.

The semester prototype ends at report preparation. The final action is **Prepare Report**. The final screen says **Report Prepared** and **Your report is ready for manual submission. It has not been sent to an authority.** It must show no authority tracking ID or acceptance claim. This follows the revised course document, which supersedes older submission language.

## 2. Verified starting point

Repository inspected: [Itz-Viggy/civicfix](https://github.com/Itz-Viggy/civicfix).

| Area | Evidence and current state |
| --- | --- |
| Data | 43 photos, approximately 12.42 MiB, with labels and provenance records. |
| Categories | 10 potholes, 10 broken streetlights, 10 damaged signs, 3 leaking hydrants, 10 illegal dumping examples. |
| Playground | Saved notebook output records successful image decoding, hashes, and metadata checks. These are recorded prior results, not checks rerun for this PRD. |
| Data limits | Agent labels need independent review. Hydrant examples are sparse; two depend on source captions without a visible hydrant body. Local, night, and weather coverage is weak or missing. |
| AI | No model accuracy or inference timing has been measured. |
| App | The inspected `main` tree contains the dataset and notebook tooling, with no frontend, API, or runtime reporting database. |
| Branch mismatch | `main` README links supporting `docs/` files that are absent from its tree. Those files are available on `dataset-playground`. Reconcile before extending the project. |
| Docker | A notebook Dockerfile exists. Its build and execution were unverified in the previous work. It does not deploy the web application. |

Do not treat the 43 development examples as an independent final test set. Keep the pinned dataset and its rights records intact.

## 3. Scope and product behavior

### Included

1. Take or upload a photo and preview or replace it.
2. Enter a location manually or request browser location, then confirm the issue location.
3. Add optional observations, such as a streetlight being off at night.
4. Suggest a supported category and a short description using a configured hosted or self-hosted vision model.
5. Request clarification when the evidence is unclear or unsupported.
6. Determine the reporting destination using confirmed location, issue type, and verified local rules.
7. Review and edit the photo, location, category, description, and destination.
8. Mark a valid reviewed report prepared, copy its text, and open the verified government form for manual submission.
9. Clear the draft and delete retained application copies under the retention rule.

### Deferred

Automated authority submission, external form automation, authority tracking, repair status, duplicate detection, public feeds, account profiles, other cities, and custom model training.

Opening a form does not mean the authority received a report. External form prefilling can be reconsidered separately after the preparation workflow works.

### Important category limits

The category is a reporting suggestion. A photo alone cannot always establish an electrical fault, the legality of dumping, or the cause or severity of damage. Descriptions must distinguish visible observations from user supplied claims. For example, write that debris is visible and label a user claim about dumping; do not invent who placed it or whether it violates a law.

## 4. Technical direction

| Component | Proposed approach | Review or implementation condition |
| --- | --- | --- |
| Frontend | Next.js and React, mobile first | Confirm and pin supported versions during setup. Do not copy unverified version numbers from the old proposal. |
| Backend | Python 3.12 and FastAPI | Keep the existing notebook environment reproducible while adding app dependencies separately. |
| AI | Provider independent interface with interchangeable hosted and self-hosted vision backends | Implement a shared contract and a real open source integration. Configure the provider and model without changing UI or report logic. Original Gemini choice becomes a comparison candidate. |
| Database | PostgreSQL, consistent with the latest written hosting plan | No runtime database exists in the inspected tree. Confirm the deployment service and retention needs before provisioning. |
| Hosting | Existing plan names Vercel and Render | Verify current limits, costs, persistence, and cleanup support before deployment. No free hosting guarantee is assumed. |
| Routing | Verified boundaries plus a small versioned category/destination lookup | AI must not invent departments, portal URLs, or jurisdiction. |
| Photos | Temporary private application storage, with session restricted access | Never place runtime user uploads in the dataset repository or serve them at public URLs. |
| Reproduction | Separate app containers and documented startup | Retain the existing notebook Dockerfile; validate the app containers independently. |

Google documentation checked for this draft still restricts 2.5 model access to prior active users. This affects that optional hosted candidate only; it must not block building the provider independent core or using an open source backend. Provider handling and current terms must also be checked before using real user photos. Send the minimum needed data; exact coordinates should remain in deterministic routing unless a documented model input need justifies them.

### Model independence is a required feature

The app must call a single internal operation such as `analyze_issue(request) -> AnalysisResult`. Provider SDKs, wire formats, image encodings, and model specific prompt wrappers belong inside adapters. No provider response objects may leak into the frontend, report workflow, routing rules, or database business logic.

The shared result contains a supported category or null, an outcome (`supported`, `unclear`, or `unsupported`), visible observations, suggested description, and clarification reasons. Execution metadata separately records provider/model/revision, prompt version, preprocessing, duration, and errors. A provider outage is a typed execution error, not an unsupported-photo classification.

Required adapters:

1. **Self-hosted vision endpoint:** run an actual open source vision-language model behind a private endpoint. Start with Qwen3-VL-4B-Instruct. Use a verified compatible serving option for the available hardware, such as vLLM on a supported GPU host. A Mac requires a separately verified compatible runtime; do not assume the Linux GPU command works there.
2. **Hosted provider:** implement the original Gemini integration as an optional comparison backend when access and credentials permit. Keep its native protocol inside its adapter. Additional providers can be added later without changing the app contract.
3. **Deterministic test adapter:** use fixed responses for offline development and failure tests. Label these runs as simulated; they never count as model-quality or real-integration evidence.

Configuration must select provider, exact model ID, private base URL where applicable, request timeout, output limit, prompt version, and optional model revision/quantization. Secrets stay server side. Use validated deployment configuration, not arbitrary user supplied endpoint URLs. Missing keys or unsupported image capabilities produce an explicit setup error.

The protocol is an adapter detail: an OpenAI-compatible local endpoint is not a promise that every hosted API uses that protocol. Providers with native JSON-schema support may use it, while all providers must pass the same application validation. Never assume identical sampling controls, token accounting, reasoning parameters, or image formats.

Keep local-model inference dependencies and weights separate from the lightweight web app and existing notebook environment. Pin the tested model revision, tokenizer/processor, serving runtime, and quantization artifact where used. Model weights must not be committed to the repository. Check the exact artifact license, including any third-party quantization.

No silent fallback from local processing to a hosted service is allowed. Fail clearly or use a separately configured and disclosed fallback policy. A failed local request must not unexpectedly send a photo to another provider.

**Required proof:** run the same allowed example through two real model configurations, including a self-hosted open source configuration, and demonstrate that selection changes through configuration only. Validate common fields and app behavior, not identical generated wording. If compute or credentials are missing, implement and test the available portions and mark the real comparison blocked; do not call the stage fully complete.

### Candidate models for CivicFix itself

These are initial benchmark candidates, not claims of CivicFix accuracy.

| Candidate | Proposed role | Selection condition |
| --- | --- | --- |
| `Qwen/Qwen3-VL-4B-Instruct` | First open source baseline and local integration | Official image-text model card lists Apache 2.0. Measure fit, memory, output validity, and latency on actual hardware. |
| `Qwen/Qwen3-VL-8B-Instruct` | Larger open source comparison | Official card also lists Apache 2.0. Test only when compute permits; keep it only if measured quality justifies the extra resources. |
| `gemini-2.5-flash-lite` | Optional hosted baseline from the original proposal | Check account access and applicable handling before calls. Its availability does not determine the application architecture. |

Use one selected vision model to classify and draft the description initially. Routing and preparation checks use deterministic code. Separate judge models or additional generation calls are not required. Human review and labeled test cases provide the acceptance evidence.

The recommendation to begin with 4B and then compare 8B is an implementation choice based on starting with a smaller model. It does not establish which one is more accurate for these five issue types. Self-hosting removes provider per-call fees but does not make compute, storage, or public hosting free. The under-10-second target remains unchanged and must be measured for each deployment profile.

### Processing responsibilities

The browser collects inputs and shows the draft. The API validates the upload, removes metadata, calls the image model, validates the returned fields, resolves routing, and manages draft access and deletion. The model proposes the category and description. The routing rules supply the destination. The user confirms the final report.

### Proposed API and data contract

These names are a starting contract to finalize in Stage 0:

| Operation | Required behavior |
| --- | --- |
| Create/update draft | Accept photo, location, optional observations; validate and assign an internal draft ID. |
| Analyze draft | Return category or clarification status, visible observations, suggested description, and reasons clarification is needed. |
| Resolve destination | Return verified route ID, jurisdiction, portal URL, evidence source/version, and resolved or unresolved status. |
| Review/update draft | Store edits and rerun affected checks. Location or category edits invalidate the old route; content edits invalidate earlier review. |
| Prepare draft | Check current revision, required fields, resolved routing, and explicit review on the server before preparing. |
| Delete draft | Remove draft content and photo copies; make subsequent reads fail. |

Store the latest input and edited fields, route/version, review revision, lifecycle state, and expiry time. Record model ID, prompt version, result status, and timing in restricted evaluation records without retaining photos or precise locations in logs. Internal IDs must never be presented as authority tracking numbers.

Suggested states: draft, analyzing, needs correction, ready for review, prepared, and deleted/expired. Service failure preserves previously entered information within the retention window. Repeated prepare requests do not create external actions. Use bounded retries within the documented analysis timeout.

## 5. Implementation stages

Each stage should have a small implementation PR, relevant checks, a short demo, and a note describing what remains incomplete. Review the result before starting the next stage. Stages 3 and 4 join in Stage 5.

### Stage 0: Reconcile the repository and confirm dependencies

1. Inspect both branches and preserve the notebook, pinned dataset, labels, and license records.
2. Bring the missing documentation into the chosen app development baseline and repair README links. Record the branch/commit used.
3. Confirm the five category definitions and the report preparation boundary from the latest course document.
4. Define the provider independent contract and configuration. Inventory available compute and serving runtimes without assuming a GPU, API key, or prior Gemini access.
5. Check provider handling, current dependencies, and hosting/database requirements. Record model/compute prerequisites as later integration tasks; continue repository and contract work when they are absent.
6. Finalize the draft fields, API contract, folder structure, and acceptance checklist. Create the stage tracker and record the next runnable task.

**Done when:** the baseline is clear, documentation links resolve, the provider independent contract and stage tracker exist, and compute/credential prerequisites are documented. A live model call is not required for Stage 0.

### Stage 1: Build interchangeable inference and establish a baseline

Execute these as separate reviewable chunks:

**1A. Shared contract and offline checks**

1. Implement request/result schemas, adapter interface, provider registry, and validated configuration.
2. Add the deterministic test adapter and tests for unsupported labels, malformed output, unclear photos, timeouts, and missing provider configuration.
3. Confirm that routing and report validation have no dependency on a provider SDK.

**Exit:** the shared interface works without an API key, and simulated runs are clearly labeled.

**1B. Real open source inference**

1. Inspect available hardware, choose a compatible runtime, and document the exact setup.
2. Implement the private self-hosted endpoint adapter and run Qwen3-VL-4B-Instruct on permitted non-sensitive development images.
3. Record the model revision, runtime, processor, quantization if any, peak memory, latency, failures, and actual output validity. Use 8B only if resources permit a comparison.
4. Verify that local mode has no hosted-provider calls or unexpected external image uploads.

**Exit:** a real local/self-hosted model returns validated results. If hardware is unavailable, record the specific blocker and finish independent code work; simulated responses do not satisfy this exit.

**1C. Hosted adapter and switching check**

1. Implement the optional Gemini adapter, isolating its native request/response format.
2. Check access and credentials before calling the original planned model. If unavailable, document the blocker rather than changing providers silently.
3. Demonstrate a configuration-only switch between two real model configurations, including one self-hosted open source model. Two runnable open source configurations can prove switching when hosted access is unavailable; the hosted live check remains explicitly unverified.
4. Run common contract and failure tests against every implemented adapter.

**Exit:** configuration switching works without business-logic changes, and real versus simulated integration evidence is clearly recorded.

**1D. Development benchmark**

1. Use the existing 43 photos for initial development experiments. Save initial prompts and first predictions before tuning.
2. Review category errors and descriptions against visible evidence, especially hydrants, electrical faults, and dumping claims.
3. Add development examples for normal scenes, blurry photos, and unsupported objects.
4. Compare available candidates using the same development cases and compatible input/output budgets. Record preprocessing and provider-specific wrappers.
5. Report category accuracy, unsupported facts, invalid outputs, end-to-end latency, failures, and cost or compute usage per configuration. Do not compare provider token counts as if their units were identical.
6. Choose a provisional default using measured quality, latency, resources, and handling. Keep alternate adapters usable.

**Done when:** the real open source integration and switching checks have evidence, development results are reproducible, and a provisional default is documented. Development accuracy is not final evaluation accuracy. If a real integration is blocked, identify the unfinished substage and continue only independent app work.

### Stage 2: Build photo and location input

1. Create the frontend/backend skeleton and session restricted draft handling.
2. Add upload/camera input, preview, replacement, and optional user observations.
3. Add location permission, manual entry, and explicit location confirmation. Device location must not silently become the issue location.
4. Validate actual file decoding, allowed types, byte/dimension limits, and coordinates. Publish the chosen limits in the API contract.
5. Strip EXIF/GPS from stored application derivatives. Explain what will be sent to the AI provider before analysis.
6. Add clear errors for invalid files, denied location, and interrupted requests.

**Done when:** valid inputs reach the API; invalid uploads are rejected; manual entry works when GPS is denied; and another session cannot read or change the draft.

### Stage 3: Connect analysis and editable report review

1. Connect the configured inference adapter to the draft workflow. Demonstrate that both hosted and self-hosted result shapes are handled through the same contract; clearly label any simulated backend.
2. Show the suggested category, description, and evidence limitations.
3. Add edit, replace photo, retry, and manual correction paths.
4. Keep unclear/unsupported results visibly unresolved until corrected. Do not display a model generated confidence number as a measured probability.
5. Preserve entered inputs during provider failure, rate limits, or timeout. Record failures honestly.
6. Add server checks that edits invalidate the appropriate prior analysis, route, and review state.

**Done when:** a real user can analyze, inspect, and correct a report, while failed calls and stale responses cannot silently overwrite newer edits. Preparation stays blocked until routing is implemented and resolved.

### Stage 4: Implement verified local routing

1. Research official City, County, and relevant utility reporting sources and authoritative boundary data.
2. Record each destination, supported category, portal URL, required fields, source URL, and verification date.
3. Resolve the confirmed location against boundaries and category specific responsibility rules. A city boundary alone must not imply ownership of every road, light, or hydrant.
4. Return unresolved status when ownership or jurisdiction cannot be established. Let the user correct location/jurisdiction and validate the corrected destination.
5. Check verified City, County, boundary, outside-area, missing-location, and category-specific cases.

**Done when:** every configured rule has an official source and expected routing tests pass. Unresolved or out-of-scope cases remain blocked rather than receiving a guessed destination. No live form submission is needed for testing.

### Stage 5: Complete report preparation and manual handoff

1. Assemble the reviewed photo, confirmed location, supported category, edited description, and resolved destination.
2. Enforce preparation conditions on the server and require explicit review of the current revision.
3. Implement the exact Prepare Report button and Report Prepared wording in Section 1.
4. Add copyable report text, manual submission instructions, and a link to the verified government form.
5. For an unavailable form, explain the issue and retain the report within the retention window. Never display submission success.
6. Demonstrate location/category corrections, unavailable forms, repeated preparation clicks, and missing or unresolved inputs.

**Done when:** the whole workflow works with real analysis and routing, the user understands that nothing was submitted, and all required corrections are possible before preparation.

### Stage 6: Run independent evaluation and walkthroughs

1. Assemble 100 independent classification photos, 20 per supported category. Keep them separate from prompt development. Review labels independently and check duplicates or related scenes against the development collection.
2. Add the planned 20 cases covering unclear images, unsupported issues, missing locations, and uncertain routing. Keep their recovery results separate from five-class accuracy.
3. Select the deployment candidate using development results, then freeze provider, model/revision, quantization, prompt, preprocessing, and routing version before the final run. Keep comparison runs separate from final acceptance results. Score the first prediction before user edits; abstentions on valid five-class test images count as incorrect.
4. Report overall and per-category accuracy, confusion matrix, and description checks. Each passing report contains zero unsupported generated facts.
5. Run 100 timing requests with one active request and another 100 with three concurrent requests. Include retries and failure counts. Keep cold-start and environment details visible.
6. Run 10 clear-image walkthroughs from starting the report to marking it prepared. Add the planned wrong-category, wrong-jurisdiction, and unavailable-form recovery exercises, recording their outcomes separately if outside the 10 timed runs.
7. Record actual observations, fixes, and remaining limits. If test examples influence later tuning, retire them from the independent test or label the next result as development evidence.

**Done when:** the evidence report compares actual results with all original targets and explains misses. Do not invent participants, human validation, or passing results.

### Stage 7: Deploy and verify operations

1. Verify current hosting, database persistence, pricing, quotas, and provider settings; record the chosen setup and cost assumptions. A self-hosted model needs its own measured compute and network profile; a small web host is not assumed to run it.
2. Build and run app containers. Document the actual startup command, dependencies, and environment variable names without secrets.
3. Verify production session access, upload validation, HTTPS, rate limits, and safe logging.
4. Verify deletion on clear/cancel and automatic expiry within 24 hours, including temporary files and application backups. Document any separate provider retention limits accurately.
5. Run a deployed workflow smoke test and check deployed latency. Keep local and deployed measurements distinct.
6. Provide setup, troubleshooting, data rights, evaluation, and known-limit documentation. Update only affected course document entries with evidence references after review.

**Done when:** another person can reproduce the app, the deployed workflow works, and privacy/cleanup claims are backed by observed checks. Deployment approval is a separate later action.

## 6. Acceptance criteria carried from the latest course document

| Requirement | Target or pass condition | Evidence |
| --- | --- | --- |
| Model independence | Configuration-only switch across two real model configurations, including a self-hosted open source model; same validated app contract | Adapter tests and real inference records; mocks excluded |
| Local processing | Local mode makes no hosted inference calls; fallback cannot silently export photos | Network/configuration inspection and failure tests |
| Classification | At least 85 correct first predictions out of the independent 100 photos | Frozen evaluation outputs, confusion matrix, and per-category results |
| AI timing | Usable result within 10 seconds for at least 95 of 100 requests, assessed separately at each planned load | 100 requests at one active request; 100 at three concurrent requests; include retries and errors |
| Workflow timing | Under 60 seconds to mark a clear-image report prepared | Individual times and outcomes for 10 walkthroughs; show every miss |
| Description quality | No unsupported generated facts in a passing report | Statement-by-statement comparison with photo and user inputs |
| Review and correction | Current fields are editable; unresolved required inputs block preparation | API and interface tests, including edits after analysis |
| Routing | Source-backed destination or explicit unresolved state | Expected results for documented routing cases |
| Submission boundary | Exact preparation wording; no authority submission, acceptance claim, or authority tracking ID | End-to-end inspection, including unavailable forms |
| Privacy | Session isolation; safe logs; metadata removal; clear/cancel deletion and 24-hour expiry | Cross-session, metadata, log, and deletion checks |
| Reproduction | Working documented app startup and verified containers | Clean setup and container run evidence |

All numerical performance goals remain provisional until measured. If a target changes, keep the original value, new value, reason, and evidence visible.

## 7. Decisions to review together

1. **Stage order:** start with repository cleanup and a real AI baseline, then build the app around the measured output. This draft recommends that order.
2. **Inference choice:** implement model independence and a real open source backend as requirements. Select a provisional default from development results; the original Gemini choice is optional and must not block the core.
3. **Infrastructure:** keep the latest PostgreSQL/Vercel/Render plan as the starting point, subject to verification. Provisioning and public deployment are later steps.
4. **Data collection:** establish a practical way to obtain independent, appropriately licensed test photos and human label review, especially for hydrants and local conditions.
5. **Handoff depth:** this draft follows the revised semester boundary of report preparation and separate manual submission. External form automation remains a later extension.

The first runnable task is Stage 0. Use the kickoff below to start it. Each later command selects one stage or Stage 1 substage, preserving a reviewable boundary.

## 8. Source record

- [Current main tree](https://github.com/Itz-Viggy/civicfix/tree/main), inspected October 20, 2026; tree SHA `aaacb067e92dd0681e77b2b5c090fb49326d1250`.
- [Current README](https://github.com/Itz-Viggy/civicfix/blob/main/README.md), inspected October 20, 2026.
- [Saved playground output](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/docs/NOTEBOOK_PREVIEW.md), inspected October 20, 2026.
- [Model notes](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/docs/MODEL_NOTES.md) and [proposal updates](https://github.com/Itz-Viggy/civicfix/blob/dataset-playground/docs/PROPOSAL_UPDATES.md), inspected October 20, 2026.
- `Milestone3_Data_Collection_Revised.docx`, current version 7, last modified October 10, 2026; Sections 2.1, 2.2, 3.3, and 4.4 establish the targets, controls, and manual submission boundary used here. Older submission wording remains elsewhere in that document; this PRD follows its explicit prototype clarification.
- [Official Gemini 2.5 Flash-Lite documentation](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite), checked October 20, 2026 for model access restrictions. No account-specific availability was tested while preparing this draft.

## 9. Coding model recommendations for a ChatGPT Plus user

These choices concern the agent writing the code, not the vision model serving CivicFix. Recommendations are task-specific judgments. Current official documentation lists GPT-6.1 Sol and GPT-6 Luna on Plus, subject to availability and client rollout. Use Standard speed and the effort below where selectable.

| Build stage | Recommended coding model | Effort | Work to hand it |
| --- | --- | --- | --- |
| 0 | GPT-6.1 Sol | High | Repository reconciliation and contracts |
| 1A | GPT-6.1 Sol | High | Provider interface and validation |
| 1B–1C | GPT-6.1 Sol | High | Open source serving, adapters, switching |
| 1D | GPT-6.1 Sol | High | Benchmark and error analysis |
| 2 | GPT-6.1 Sol | Medium | Upload, location, sessions |
| 3 | GPT-6.1 Sol | High | Analysis, edits, stale-state handling |
| 4 | GPT-6.1 Sol | High | Source-backed routing |
| 5 | GPT-6.1 Sol | Medium | Review and preparation workflow |
| 6 | GPT-6.1 Sol | High | Independent evaluation and fixes |
| 7 | GPT-6.1 Sol | High | Deployment and retention checks |

Use GPT-6 Luna at High for isolated README edits, formatting, or other small defined follow-ups. Keep the main implementation on Sol. These effort settings are starting suggestions, not availability guarantees. Increase effort only when unresolved complexity warrants it; Max/Ultra are unnecessary defaults here.

Sign in to Codex with the ChatGPT account to use included plan usage. Plus does not provide a general runtime API budget for CivicFix: API charges and self-hosted compute are separate. Actual plan limits and model availability must be checked in the account; this plan promises no number of included coding sessions.

## 10. Execution tracker and handoff

Keep a copy of this PRD at `docs/CIVICFIX_DEVELOPMENT_PRD.md` when beginning repository work. Add a `docs/IMPLEMENTATION_STATUS.md` tracker containing each stage ID, status, evidence/PR link, blocker, and next action. Use `not_started`, `in_progress`, `blocked`, or `complete`. Start every entry as `not_started`; mark completion only after its exit conditions pass.

| Task | Depends on | Starting status | Main deliverables |
| --- | --- | --- | --- |
| 0 | None | not_started | Reconciled baseline, contracts, setup notes, tracker |
| 1A | 0 | not_started | Schemas, registry, test adapter, contract checks |
| 1B | 1A and runnable compute | not_started | Self-hosted model adapter and real inference evidence |
| 1C | 1A; real configurations for switching proof | not_started | Hosted adapter, switching checks, explicit live-check status |
| 1D | At least one real backend; full Stage 1 exit needs switching proof | not_started | Development benchmark and provisional default |
| 2 | 0 and shared draft contract | not_started | Photo/location input and session isolation |
| 3 | 1A, 2, and at least one real backend | not_started | Integrated analysis and editable review |
| 4 | 0 and location contract | not_started | Verified routing rules and tests |
| 5 | 3 and 4 | not_started | Prepared report and manual handoff |
| 6 | 5 and independent test data; all Stage 1 requirements for final release | not_started | Accuracy, timing, quality, walkthrough evidence |
| 7 | 6 and verified deployment resources | not_started | Reproducible deployment and operations checks |

The default order is the table order. If compute or credentials block one task, identify independent runnable work in the tracker. A blocked hosted integration does not prevent local development. A mock-only app may be developed but cannot be presented as a working AI integration.

### Ready-to-paste kickoff prompt

```text
Read the attached CivicFix PRD v0.2 and inspect Itz-Viggy/civicfix, including main and dataset-playground. Read applicable AGENTS.md instructions first. Implement Stage 0 only now.

Save the agreed PRD as docs/CIVICFIX_DEVELOPMENT_PRD.md and create docs/IMPLEMENTATION_STATUS.md with all stages and substages. Reconcile missing supporting documentation and README links while preserving the notebook, immutable dataset, labels, and attribution. Define the provider independent request/result contract, configuration, proposed folder layout, and acceptance checklist. Document available compute and missing credentials without requiring them for this stage. Do not download model weights or make paid calls as part of Stage 0.

CivicFix must support hosted and self-hosted vision models. A real open source integration is required in Stage 1. Keep model SDKs out of UI, report workflow, and routing logic. Never silently switch providers. The semester app prepares reports for separate manual submission and must not submit to an authority.

Work on an isolated branch. Complete Stage 0, run checks appropriate to the changes, update the tracker, and prepare a reviewable commit or draft PR if the environment supports it. Report changed files, checks, blockers, and the exact next task. Do not merge, deploy, or proceed to Stage 1 without the next instruction.
```

### Continue one task at a time

```text
Read docs/CIVICFIX_DEVELOPMENT_PRD.md, docs/IMPLEMENTATION_STATUS.md, and applicable AGENTS.md instructions. Implement task [STAGE_ID] only. Check its dependencies, complete its listed work and exit checks, and record actual evidence and blockers. Keep provider independence, deterministic routing, dataset preservation, and the report preparation boundary intact. Do not invent passing tests or real model results. Finish with a reviewable change and the next recommended task; do not begin the following task automatically.
```

Use `1A`, `1B`, `1C`, and `1D` separately when continuing Stage 1. The model/effort is selected in Codex; asking the coding agent to use a named model inside this prompt does not itself change the selected model.

## 11. Additional sources checked for v0.2

- [Official Work/Codex model guidance](https://learn.chatgpt.com/docs/models), checked October 20, 2026 for coding model roles and availability.
- [Official Work/Codex pricing](https://learn.chatgpt.com/docs/pricing?codex-pricing-plans=individual), checked October 20, 2026 for Plus access and separate API billing.
- [Qwen3-VL-4B-Instruct official model card](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), checked October 20, 2026 for image input, license, and self-hosting options.
- [Qwen3-VL-8B-Instruct official model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct), checked October 20, 2026 for image input, license, and self-hosting options.

No model was installed, benchmarked, or called while revising this PRD. Coding recommendations and runtime candidate selection are separate decisions.
