# Planned hosted model (separate from image licensing)

Documentation checked on 2026-10-04 (America/New_York). Planned exact model ID: `gemini-2.5-flash-lite` in the Gemini API. It is a hosted multimodal API model, not downloaded open weights. No model license is assigned to this image collection. Google's documentation-page CC BY license does not license model weights or grant API use rights.

Primary sources inspected:

- [Official model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite)
- [Official deprecation schedule](https://ai.google.dev/gemini-api/docs/deprecations)
- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms), effective March 23, 2026
- [Google APIs Terms](https://developers.google.com/terms), referenced by the additional terms

The model page and deprecation schedule currently say Gemini 2.5 access is limited to prior active users. The stable Flash-Lite model has no announced shutdown date; its September 2025 preview is shut down. CivicFix's ability to use the exact planned ID therefore needs an account-level availability check before inference development. This assignment did not perform one and did not silently substitute another model. Reconsider the model in a separate project decision if access is unavailable.

API use is governed by both Google APIs Terms and Gemini Additional Terms, not an open-weight license. The additional terms distinguish paid and unpaid processing: unpaid content can be used for product improvement and reviewed by people; sensitive or personal content must not be submitted there. Paid-service prompts and responses are handled under the referenced processing terms and are not used for product improvement. Recheck applicable terms, user-photo permissions and privacy before any future inference experiment. Image reuse rights for this repository do not by themselves resolve rights to grant a third-party API's submission license.

The required notebook has no API key, Gemini SDK, model calls, classification metrics or availability claim.
