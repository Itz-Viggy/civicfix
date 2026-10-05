# Data quality findings

Measured from a fresh-kernel **github** retrieval of immutable dataset commit `8394bf6d0d84c9dbf33e69258f0cd15ee4795ca4` under Python 3.12.15. Saved results are visible in the root notebook.

## Included data and candidate pool

71 candidates entered the bounded acquisition/review ledger; 69 photographic candidates were downloaded and processed for agent visual review, 26 downloaded candidates were excluded, and 2 were not acquired as usable photographs. The final subset contains **43 photographs**, **43 manifest rows**, **21 metadata fields**, and **13,020,816 image bytes (12.418 MiB)**. No excluded images are tracked or embedded in the notebook. Search listings contained additional items outside this candidate pool.

| Category | Images |
|---|---:|
| `pothole` | 10 |
| `broken_streetlight` | 10 |
| `damaged_sign` | 10 |
| `leaking_hydrant` | 3 |
| `illegal_dumping` | 10 |

The approximately 50-total / ten-per-category project target is not fully met. The licensed, clearly labeled subset was preferred to padding categories with normal infrastructure, a hydrant test, authorized fixture disposal or isolated litter. This is partial coverage, not a completed evaluation benchmark.

## Executed checks

| Check | Measured result |
|---|---:|
| required missing | 0 |
| duplicate ids | 0 |
| duplicate filenames | 0 |
| unsupported labels | 0 |
| missing files | 0 |
| decode successes | 43 |
| hash mismatches | 0 |
| exact duplicate images | 0 |
| inconsistent hash labels | 0 |
| images with exif | 0 |
| images with gps | 0 |
| images without agent review | 0 |

All required manifest values are present. Validated IDs and filenames are unique, labels belong to the five allowed categories, image paths stay inside the retrieval directory, all files decode and all stored-byte hashes match. Every included row is marked `agent_reviewed`, not human-reviewed. No byte-identical duplicates or hash groups with inconsistent labels were found. These checks do not establish label accuracy.

Derived resolution ranges: width **330–1280 pixels**, height **160–1280 pixels**. All stored images are RGB JPEG, with no EXIF fields or GPS. Conversion standardized format and metadata; resolution remains mixed, including small cached thumbnails. The notebook reports resolution/size distributions rather than hiding them.

## Corrections, exclusions and source limitations

See the individual decisions in `candidate_review.csv`. The agent inspected each included photograph alongside its caption. Privacy exclusions include readable vehicle plates and people in some streetlight/storm scenes. An apparently damaged public telephone was excluded despite its Commons category. A disused light, ambiguous nighttime photo, removed fixtures in organized storage, subsidence boundary example and a hydrant leak-detection test were excluded. The Vero Beach wide view was excluded as an alternate view of the same hydrant event; the close view is retained. Small discarded chargers and a small wetland waste bag were excluded in favor of stronger dumping evidence.

Actual file-page licenses and authors were checked before upload. Acquisition parser/link-normalization errors were corrected. Rate-limited original files were replaced by the provider's recommended cached thumbnails, then visually reviewed. Original image metadata was stripped by re-encoding before any commit; hashes were calculated afterward. Stored bytes are transformed derivatives, not original photographs.

Dumping labels rely on explicit source context as well as visible waste: a photograph alone cannot prove illegality. Hydrant pictures require source-confirmed unintended flow, not flushing, testing, recreational use or an intact hydrant. In the two UK examples, the hydrant body is not visible: the road-water/pavement-plume photos depend on explicit source captions and cannot establish photo-only hydrant recognition. The Vero Beach image visibly shows the hydrant and outflow. Streetlight examples mostly demonstrate structural damage; they cannot establish electrical functionality. High-flow hydrant failures may demand urgent utility handling outside a nonemergency application. The collection is for issue-recognition inspection only.

## Near-duplicate review

Average-hash screening produces 3 candidate pairs:

- `commons-5000667ac9` / `commons-bb9ea4bd37`: distance 5; see visual comparison below.
- `commons-bb9ea4bd37` / `commons-ddf392a527`: distance 6; see visual comparison below.
- `commons-bb9ea4bd37` / `commons-f5eb1a435d`: distance 6; see visual comparison below.

The contact-sheet review also considered scene similarity and source titles. The documented Vero Beach alternate view was excluded independently of byte hashing. Similar subject composition or lamp hardware is not by itself the same event. The collection has not undergone exhaustive geometric matching or independent event-level validation. Visual comparison findings for any screened pairs are recorded in `NEAR_DUPLICATE_REVIEW.md`.

## Unknowns and remaining coverage

Optional missing counts: `{'location': 6, 'capture_date': 21, 'lighting': 0, 'weather': 43, 'scene_id': 0}`. Empty values mean source conditions were unavailable or were not uniformly normalized; no capture dates, weather or coordinates were guessed. Location strings are source-supported where recorded, not precise routing coordinates. Lighting was recorded by agent visual assessment where evident; one low-light pothole is included. No confidently reviewed nighttime streetlight example was retained. Rain, fog, snowfall and camera/viewpoint coverage are not representative or systematically measured.

Gainesville-specific images and verified municipal routing locations remain missing. UK signs dominate that class; hardware and geographic distributions differ from Gainesville. Small class sizes and selected Commons material create selection bias. Independent human label validation, broader conditions, local collection permissions and an appropriately separated evaluation protocol remain future work. No accuracy, latency, scaling or 85% target result was measured.
