# Agent review of near-duplicate screening

Reviewed against stored derivatives, source titles and captions on 2026-10-04 (America/New_York). Reviewer: Codex agent; no independent human validation. The executed notebook's 64-bit average-hash screen uses Hamming distance <= 6. Its three candidates were compared visually:

| Left ID | Right ID | Distance | Visual decision |
|---|---|---:|---|
| commons-5000667ac9 | commons-bb9ea4bd37 | 5 | Damaged Glenhordial Road name panel versus bulky waste on a rural path near Chickenley. Different objects and scenes; screening false positive. |
| commons-bb9ea4bd37 | commons-ddf392a527 | 6 | Rural path waste versus a water-filled asphalt pothole in Potomac. Different objects, places and composition details; screening false positive. |
| commons-bb9ea4bd37 | commons-f5eb1a435d | 6 | Rural path waste versus a fallen road-name panel at Roscavey Road. Different objects and scenes; screening false positive. |

No screened pair warranted removal or relabeling. Average hash loses detail and can match unrelated scenes with similar large-scale brightness. An empty exact-hash duplicate result or dismissal of these three pairs does not establish exhaustive absence of near duplicates.

Separately, the Vero Beach hydrant wide view and close view clearly show the same event despite differing bytes. The wide view was excluded during curation; `candidate_review.csv` records that decision. Reserve images of similar sign/light hardware were excluded for coverage/clarity after targets were reached, without asserting that they were event duplicates. Formal event independence and an evaluation train/test split remain unverified.
