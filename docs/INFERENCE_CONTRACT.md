# Inference contract v1

Design finalized for Stage 1A implementation; no adapter or executable validator exists yet. [PRD](CIVICFIX_DEVELOPMENT_PRD.md) governs scope. [Baseline](STAGE_0_BASELINE.md) records prerequisites; [app contract](APP_CONTRACT.md) owns routing and preparation.

## One application operation

`analyze_issue(request: AnalysisRequest) -> AnalysisExecution`

The application imports only shared schemas and an adapter interface. A server-owned registry maps exactly `deterministic`, `self_hosted`, and `gemini` to adapters. An explicit deployment configuration selects one adapter and exact model. The UI cannot select arbitrary providers, URLs, prompts, or models. No automatic fallback is configured.

`AnalysisExecution` is a tagged union: `{status: "ok", result: AnalysisResult, metadata: ExecutionMetadata}` or `{status: "error", error: ExecutionError, metadata: ExecutionMetadata}`. Unknown fields/enums, invalid types, non-finite numbers, and blank required strings fail validation. No provider response object crosses the adapter boundary. SDK types, native JSON schemas, image encodings, prompt wrappers, response parsing, token budgets and sampling controls remain adapter details. Shared validation applies even when a provider supports schema output.

## Request (internal; never a browser-controlled endpoint contract)

| Field | Type and rule |
| --- | --- |
| `contract_version` | Literal `1`. |
| `request_id` | Opaque random correlation ID, no user information. |
| `draft_id`, `input_revision` | Internal draft UUID and positive integer snapshot revision for stale-result checks; never included in a model prompt. |
| `image` | Validated in-memory bytes, MIME `image/jpeg`, width/height, preprocessing version. API creates an EXIF/GPS-free RGB JPEG derivative, max side 1280 pixels without upscaling. No path, public URL, EXIF, coordinates, or ownership/session token sent to model. |
| `user_observations` | Optional trimmed UTF-8 string, max 2000 characters. Explicitly labeled as user-supplied claims, never treated as image evidence. |

Location is deliberately absent. Provider/model/prompt settings come from trusted configuration, not this request. Browser confirmation of the processing disclosure is checked before calling the operation. Image and observation text are untrusted input; text in a photo must not override the task, prompt, or output schema. No model tool calls are enabled.

## Result

| Field | Type and rule |
| --- | --- |
| `category` | One of `pothole`, `broken_streetlight`, `damaged_sign`, `leaking_hydrant`, `illegal_dumping`, or null. Definitions are in the [baseline](STAGE_0_BASELINE.md). |
| `outcome` | `supported`, `unclear`, or `unsupported`. |
| `visible_observations` | Array of 0–10 nonblank strings, each <=500 characters. Describe only visible evidence; may be empty when unusable. |
| `suggested_description` | String, <=2000 characters; nonblank for supported, may be empty otherwise. Attribute any included user claim explicitly. Never invent causes, legality, identities, measurements, jurisdiction, or unseen details. |
| `clarification_reasons` | Array of 0–10 `{code, message}` entries; message nonblank <=500 characters. Codes: `blurry_image`, `insufficient_visibility`, `ambiguous_category`, `needs_user_observation`, `multiple_issues`, `outside_supported_categories`. |

Invariants:

- `supported` requires a category, a nonblank description and no unresolved clarification reasons. Visible observations may be empty if the suggestion relies on an explicitly attributed user observation.
- `unclear` requires null category and at least one reason. Do not force the closest label or attach a guessed confidence number.
- `unsupported` requires null category and `outside_supported_categories`; it is a successful photo assessment, not an infrastructure error.
- Unsupported labels or malformed provider output produce `invalid_output`, never coercion to a valid category. Semantic factuality still needs human evaluation; syntactic validation alone cannot prove description quality.

Illustrative result only; this is not a model run:

```json
{
  "category": "pothole",
  "outcome": "supported",
  "visible_observations": ["A patch of missing pavement is visible in the road surface."],
  "suggested_description": "A patch of missing pavement is visible in the road surface.",
  "clarification_reasons": []
}
```

## Execution metadata and errors

`ExecutionMetadata` contains `request_id`, `provider`, `model_id`, nullable `model_revision` and `quantization`, `prompt_version`, `adapter_version`, `preprocessing_version`, processed width/height, `duration_ms` (monotonic total including retries), `attempt_count`, and `simulated` boolean. A measured real integration additionally records serving runtime/version and processor revision. Use null for unavailable revisions, never invent them. A configuration that cannot identify required artifacts is not eligible for the frozen final benchmark. For setup errors before configuration resolves, provider/model/prompt identifiers may be null, attempt_count is 0, duration_ms is nonnegative, and simulated is false because no inference ran; an error never counts as real-integration evidence. Successful executions require resolved identifiers, attempt_count >=1, duration_ms >=0, and simulated true exactly for the deterministic provider. Provider usage can be a separate restricted, namespaced accounting record; do not compare incompatible token units.

`ExecutionError` has `code`, a safe fixed `message`, and `retryable` boolean. Codes:

| Code | Meaning | Retry policy |
| --- | --- | --- |
| `setup_error` | Missing key/model/base URL/prompt; unknown provider; unsupported image capability or incompatible parameters | Fail explicitly before outbound inference; no automatic retry. |
| `timeout` | Overall configured deadline elapsed | Preserve draft, user may retry. |
| `provider_unavailable` | Connection failure or upstream 5xx | At most one bounded retry within overall deadline. |
| `rate_limited` | Provider 429 | Retry only if retry-after fits remaining deadline and attempt budget. |
| `authentication_failed` | Provider access denied/invalid credentials | No automatic retry; setup action needed. |
| `invalid_output` | Malformed content or shared validation failure | No hidden corrective generation in v1; explicit retry available. |
| `content_rejected` | Provider safety/content refusal | Preserve draft; do not label photo unsupported. |

No raw headers, API key, full provider URL, image, prompt, user text, exact location, or raw response goes into logs/errors. Record only restricted operational metadata and safe codes. Coordinates/draft content have their own retention rule; operational retention and access must be set before deployment.

## Configuration

[inference.example.toml](../config/inference.example.toml) is a design example explicitly selecting simulated fixtures. It is not loaded by any app yet. Copy to ignored `.runtime/inference.toml` when 1A implements loading; set server-only `CIVICFIX_INFERENCE_CONFIG` to that path. No provider default when configuration is absent. Environment secret references resolve on the server only. Never use `NEXT_PUBLIC_` for inference settings or credentials.

| Setting | Contract |
| --- | --- |
| `contract_version` | Integer 1. |
| `provider` | Required registry identifier. |
| `model_id` | Required exact ID; deterministic uses `fixtures-v1`; self-hosted starts `Qwen/Qwen3-VL-4B-Instruct`; optional Gemini uses `gemini-2.5-flash-lite`. No silent substitution. |
| `base_url` | Required for self-hosted; forbidden for Gemini/deterministic. Only operator-configured loopback or approved private endpoint, never user input. HTTP permitted only on loopback; authenticated TLS for remote serving. Validate against deployment-owned allowlist; refuse redirects and prevent public endpoint substitution. |
| `api_key_env` | Required name for Gemini (`GEMINI_API_KEY`); optional self-hosted secret name; forbidden for deterministic. Nonempty secret must exist if referenced. Never serialize the secret. |
| `timeout_seconds` | Required integer 1–120; initial 30 seconds is a failure ceiling, not the <10-second performance goal. |
| `max_attempts` | Integer 1–2; initial 2. All attempts/backoff share the same deadline. |
| `max_output_tokens` | Positive integer 1–4096, initial 512. Adapter maps to the native output control and rejects unsupported controls rather than guessing equivalence. |
| `prompt_version` | Required immutable prompt ID (`issue-v1` planned); missing prompt is setup error. Prompt content and provider-specific wrappers versioned in 1A/1B/1C. |
| `model_revision`, `quantization` | Optional artifact identifiers; required to be recorded before real acceptance evidence when applicable. Deterministic omits them. |
| `preprocessing_version` | Required `rgb-jpeg-1280-v1`: apply EXIF orientation before removing metadata; composite transparency onto white, convert to RGB, resize with Lanczos to max side 1280 without upscaling; JPEG quality 85, subsampling 2 (4:2:0), optimize false, progressive false, no EXIF/ICC metadata. Pin the Pillow/encoder versions with implementation. All benchmark configurations receive the same derivative. |
| `fallback_policy` | Literal `none` in v1. |

Unknown settings fail startup. Registry capability checks must confirm image support. Adapter configuration changes invalidate existing review/analysis when reanalysis is requested; old results retain their original metadata, never relabeled with the new provider. Display `Simulated analysis` for fixtures in responses and UI. Production preparation rejects simulated evidence; offline development can demonstrate the flow with a persistent simulation label and never count it as acceptance evidence.

## Required implementation checks

1A tests supported/unclear/unsupported shapes, unknown categories, malformed types/extra fields, empty descriptions, invalid combinations, timeouts, missing configuration/keys and explicit simulation labels. Ensure routing/report modules import no provider SDK. Test no implicit provider fallback and no endpoint selection from user input.

1B/1C use permitted non-sensitive examples, verify no hosted inference egress in local mode (including failure paths), and run the same example through two real configurations by changing configuration only. Record versions, timing, validation and actual outputs. If compute or credentials are missing, keep the specific real-integration exit unmet. [Acceptance checklist](ACCEPTANCE_CHECKLIST.md) preserves the full evaluation targets.
