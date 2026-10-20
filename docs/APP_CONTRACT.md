# Application contract v1

Stage 0 design for later implementation. No endpoints, runtime database, or frontend exist yet. See [inference contract](INFERENCE_CONTRACT.md) and [PRD](CIVICFIX_DEVELOPMENT_PRD.md).

## Folder boundaries

Preserve root `data/`, `playground.ipynb`, `requirements.txt`, `Dockerfile`, `.python-version`, and dataset `scripts/`. Add future code only in the appropriate stage:

```text
apps/web/                   Next.js/React/TypeScript, package.json + npm lock (Stage 2)
services/api/               own pyproject + lock, Python 3.12 (1A foundations; API in 2)
  civicfix/contracts/      shared typed inference/draft schemas
  civicfix/inference/      interface, registry, validated config, adapters/
  civicfix/prompts/        versioned common prompt and adapter wrappers
  civicfix/drafts/         revisions, review, prepare, deletion; no SDK imports
  civicfix/routing/        deterministic boundary and category rules; no SDK imports
  civicfix/storage/        private photos, session ownership and expiry
  tests/                  contract, adapter, workflow and access tests
contracts/                 generated JSON Schema/OpenAPI snapshots; no second handwritten model
config/                    nonsecret examples only
routing/                   versioned official evidence/rules/boundaries (Stage 4)
evaluation/                manifests/protocols/allowed non-sensitive result records
infra/                     app containers and ops documentation (Stage 7)
docs/                      PRD, tracker, contracts, evidence and data rights
.runtime/                  ignored local private drafts/config, never public assets
.venv-api/                 ignored app environment
.venv-inference/           ignored separate inference environment; weights outside Git
```

Pydantic schemas in 1A become the inference contract's executable source; generate JSON Schema and frontend types rather than duplicating enum/validation logic. OpenAPI generation begins when the API exists. This stage intentionally defines the contract in prose without implementing 1A or scaffolding the UI.

## Stored draft and view

All times UTC RFC3339; IDs random UUIDs; revisions positive integers. Trim and bound text; reject unknown write fields, NaN/infinity, invalid enums and client-controlled server fields. Internal/private fields below never appear in browser JSON.

| Field | Type/rule |
| --- | --- |
| `id`, `revision` | Server-generated internal draft ID and monotonically increasing content/derived-data revision. |
| `owner_session_hash` | Private hash/reference to an opaque session secret, never a browser field. |
| `state` | `draft`, `analyzing`, `needs_correction`, `ready_for_review`, `prepared`. Deleted/expired is terminal absence, optionally a content-free tombstone. |
| `created_at`, `updated_at`, `expires_at` | Server clocks; expiry fixed at creation +24 hours, never extended by analysis/preparation. |
| `photo` | Nullable `{id, mime_type, width, height, bytes, preprocessing_version}` for sanitized derivative. Private storage key and original filename never returned. Original input discarded after validation/derivation; temporary files cleaned on all paths. |
| `location` | Nullable `{latitude, longitude, label, source, confirmed}`. WGS84 finite lat [-90,90], lon [-180,180]; label <=500 chars. Source `manual` or `browser`. Confirmed boolean must come from an explicit user action. |
| `user_observations` | Optional string <=2000 characters; source claims distinguished from visible facts. |
| `processing_acknowledgement` | Nullable server record `{disclosure_version, provider, model_id, input_revision, acknowledged_at}` for the provider/data disclosure accepted before analysis. New photo/observations or provider/disclosure changes require acknowledgement again. |
| `analysis` | Nullable last validated shared result, execution summary and input snapshot revision; outcome errors stored separately. Show suggestions separately from user edits. Raw provider payloads are not stored with the draft. |
| `category`, `description` | Effective reviewed fields: nullable supported category; string <=2000 characters. Initially from a successful result, then editable. Track each field's source (`model` or `user`). |
| `manual_correction` | Nullable `{reason, corrected_at}` (reason <=1000 chars) when a user resolves unclear/unsupported classification through explicit category/description correction. Keep the original outcome visible; never rewrite model evaluation results. |
| `route` | Nullable route result below, bound to effective category and confirmed location. |
| `review_revision`, `reviewed_at` | Null until explicit review of the current snapshot; cannot be set by general PATCH. |
| `prepared_revision`, `prepared_at` | Null until server preparation succeeds for reviewed current revision. Preparing does not create external actions. |

Location starts unconfirmed even when device GPS succeeds. Provide manual coordinate entry and a human-readable location label without a geocoder dependency. Any later address lookup is a separate service choice; an unresolved address cannot count as confirmed coordinates. Request denied GPS, missing precision, or corrected location must have a manual recovery path.

Route result: `status` is `resolved` or `unresolved`; `route_id`, `jurisdiction`, `portal_url`, `rules_version`, `source_urls`, `verified_at`, plus `reason_codes` and `input_revision`. Resolved requires a source-backed route ID, jurisdiction, HTTPS portal from the versioned allowlist, rule version, verification timestamp and official evidence URLs. Unresolved has null destination fields and at least one reason (`missing_location`, `unconfirmed_location`, `outside_service_area`, `unknown_ownership`, `missing_category`, `no_verified_rule`). Never open a model-generated link. A city boundary alone does not establish road/light/hydrant ownership.

## HTTP interface (future `/api/v1`)

Session: `POST /session` creates an opaque server-side session and CSRF token. Cookie is HttpOnly, Secure in production, bounded to the draft window, with appropriate SameSite policy. All draft/photo reads and writes require ownership. Reads and updates for missing, expired, deleted and other-session draft IDs return indistinguishable 404s. DELETE uses the uniform content-free 204 behavior documented below. Apply Origin/CSRF checks to mutations and exact credentialed CORS origins where cross-origin access is needed. Never use a draft ID as authentication. Browser responses use `Cache-Control: no-store`; no public photo URLs.

For revision-sensitive operations, require `If-Match: "<revision>"` and compare atomically. Missing header -> 428; stale -> 409 `revision_conflict` without mutation. Return current draft plus quoted revision ETag after success. A user's acknowledgement of analysis disclosure can accompany the analyze command using the current revision and configured disclosure version; the server records it only for that exact input/provider.

| Method/path | Body / success | Behavior |
| --- | --- | --- |
| `POST /drafts` | Optional initial location/observations; 201 draft at revision 1 | Create an empty draft owned by session, no image required yet. |
| `GET /drafts/{id}` | 200 current draft | Never expose storage keys, secrets or raw model payloads. |
| `PUT /drafts/{id}/photo` | Multipart `photo` + If-Match; 200 updated draft | Validate/decode, sanitize, replace old photo and remove obsolete copies; atomically invalidate analysis/route/review. Failure retains prior draft. |
| `GET /drafts/{id}/photo` | 200 sanitized image | Authenticated session-scoped read; no public sharing/caching. |
| `PATCH /drafts/{id}` | Partial location, observations, category, description, manual correction; 200 draft | Validate allowed fields and apply invalidations below; require If-Match. |
| `POST /drafts/{id}/analysis` | `{disclosure_version, acknowledged: true}` + If-Match; 200 updated draft, or typed error | Synchronous bounded call using the configured provider; establish analyzing snapshot first, commit only if still current. Repeated concurrent call -> 409 `analysis_in_progress`. |
| `POST /drafts/{id}/destination` | Empty body + If-Match; 200 draft with route | Deterministic resolution; unresolved is a valid result that blocks preparation. |
| `POST /drafts/{id}/review` | `{confirmed: true}` + If-Match; 200 draft | Server checks all preparation predicates and records review of this exact revision. No content editing in this operation. |
| `POST /drafts/{id}/prepare` | Empty body + If-Match; 200 preparation view | Require current review and all predicates; repeated request for the same prepared revision returns the same result. |
| `DELETE /drafts/{id}` | No revision precondition; 204 | Clear/cancel: cancel pending work, revoke reads, delete all retained app copies; own deleted/missing IDs return 204. Another owner's ID is also a content-free 204 without touching it. |

Preparation view includes current report fields, copyable text, verified form link, `prepared_at`, `expires_at`, and the exact product wording from the [baseline](STAGE_0_BASELINE.md). Opening the form is a user browser action. No prefill automation or submission request is made. If the external form is unavailable, retain within expiry and allow copying; do not claim the form accepted anything. Route validity changes clear review and require re-resolution before preparing again.

General error envelope: `{error: {code, message, retryable}, request_id}`; no provider bodies or sensitive content. HTTP: 400 invalid command, 401 missing session, 403 CSRF/origin rejection, 404 unavailable draft/photo, 409 stale/busy/not-ready state, 413 bytes exceeded, 415 unsupported type, 422 invalid fields/decode/dimensions, 428 missing revision, 429 app/provider rate limit, 502 invalid upstream output/refusal, 503 setup/auth/upstream unavailable, 504 analysis deadline. Safe execution codes from the inference contract identify provider failures without classifying the photo. Each failure preserves previous inputs until expiry, except deletion.

## Upload and text limits

Stage 2 must implement and test: one JPEG, PNG, or static WebP; max input 10 MiB (10,485,760 bytes), max request 11 MiB including multipart, max 20,000,000 decoded pixels, and each side <=10,000 pixels and >=1. Reject animated/multi-frame files, decompression bombs, mismatched MIME/content, truncated or undecodable files, HEIC, SVG and arbitrary binary input. Derive RGB JPEG at max side 1280 without upscaling, strip EXIF/GPS and other metadata, and discard the original. Byte/stream and decoder limits must apply before unbounded allocation. Use the orientation, transparency, resize and JPEG settings defined by `rgb-jpeg-1280-v1` in the inference contract; pin the Pillow/encoder versions in 1A/2. Dataset bytes are never rewritten to match runtime rules.

Whitespace-only description is missing; observations are optional. Multi-issue images ask the user to choose one issue for the draft. Server rate limits and analysis concurrency caps must be set before deployment; the benchmark's concurrency of three is a measurement condition, not a production quota.

## Revision, invalidation and lifecycle

Every accepted material content or derived-result change increments `revision` atomically and clears review/prepared markers. No-op PATCH is unchanged. Setting review or preparing the same content does not increment the content revision. `updated_at` may change. Track analysis and route input snapshots privately so revision increments for downstream actions do not incorrectly stale their dependencies.

| Change | Invalidate/recompute |
| --- | --- |
| Photo or user observations | Cancel/invalidate in-flight and previous analysis; clear model-derived effective fields (preserve explicit user edits but require recheck), processing acknowledgement, route, review and preparation. |
| Location or confirmation | Invalidate route/review/preparation; analysis remains usable because it never receives location. |
| Effective category | Invalidate route/review/preparation; preserve original model result. |
| Effective description/manual correction | Invalidate review/preparation; route remains valid if location/category unchanged. |
| Analysis retry | Clear review/preparation, preserve entered fields while pending; result cannot overwrite later user edits. Recompute suggested fields only on the matching snapshot. |
| New route/rule version | Invalidate review/preparation even if the displayed destination happens to match. |
| Delete/expiry | Revoke session reads, cancel/discard all pending results, remove content/derivatives and never resurrect draft. |

`draft` permits partial inputs. `analyzing` is transient. `needs_correction` covers missing required data, unresolved classification or route, and failures needing action. `ready_for_review` means all predicates except explicit review are satisfied. `prepared` means review and preparation succeeded on the current revision. An edit after preparation returns to draft/correction/review eligibility and requires fresh review. Stale model completion returns 409 `stale_analysis` and never overwrites new fields. Provider failures retain previous data with an explicit error; a pending reanalysis cannot silently certify the prior result. Transactions/compare-and-swap apply to concurrent review, prepare, replace and delete.

Server preparation predicates: unexpired owned draft; valid sanitized photo; explicitly confirmed finite coordinates and nonblank location label; effective supported category and nonblank factual description; a completed validated analysis for the current photo/observations (real in production); no active analysis; supported outcome or explicit manual correction resolving original unclear/unsupported reasons; current source-backed resolved route for effective location/category and active rules; and explicit review of the current revision. Missing/unresolved conditions block the operation with actionable reason codes. No client `state`, `review_revision`, destination URL or model metadata can bypass these checks.

## Persistence and cleanup

PostgreSQL stores draft metadata, session ownership, revisions, derived-result references and expiry. Photo bytes go in private app storage, not the repository, public bucket or frontend assets. Choose a persistent storage/cleanup topology before Stage 2 deployment; an initial local store must be explicitly development-only. All app-controlled originals, temp files, derivatives, logs/caches containing content and backups must meet clear/cancel deletion and creation +24-hour expiry. Reject reads at expiry even if the cleanup job is late; monitor physical deletion so the deadline is actually met. In-flight calls cannot restore deleted data, and provider retention is disclosed separately. No application content in ordinary logs. Retained evaluation evidence uses separately permitted dataset examples and contains no runtime user photos or precise locations.
