# CivicFix Commons Curated Collection v1

This is an agent-curated convenience sample, not an official benchmark. The exact dataset commit is in `data/dataset_config.json`; the dataset commit precedes the notebook implementation to avoid circular retrieval. The committed photographs, manifest and source records are the versioned source of truth.

## Selection and acquisition

No prior dataset or proposal was supplied: the initial folder contained only the acceptance specification. Wikimedia Commons searches and category listings covered potholes, damaged streetlights, damaged road signs, leaking/broken hydrants, fly tipping and illegal dumping. Additional Czech damaged-light and flowing-hydrant pages were searched for coverage. Metadata and actual file pages were inspected before image inclusion, and selected license links were checked on those pages before upload. Creative Commons license deeds were also read at implementation time. Download errors and rate limiting were corrected with slower retries; a protocol-relative license-link comparison error was fixed. These temporary failures are not missing permissions or final dataset rows.

The agent compared source captions with visible defects and reviewed photographs for people, readable plates and ambiguity. `candidate_review.csv` records the bounded candidate pool, exclusions and review type. Search-result totals are not this candidate pool. Nonphotographs and tests were not relabeled to increase counts. Unknown metadata is empty; location text is source-supported and no Gainesville coordinates are fabricated. No independent human review has occurred.

## Rights and transformations

Three photographs carry explicit author public-domain releases rather than numbered CC licenses; their license URLs point to preserved permission declarations. They are not mislabeled as CC0.

Each photograph retains the individual license or public-domain status shown below and in `data/labels.csv`. Required credits include author, original title, source and license link. For each CC BY-SA photograph, CivicFix's transformed version is distributed under that same license version. Attribution and change notices must accompany copies; no blanket code license applies to third-party images. No selected image uses a noncommercial license. Private repository access does not revoke recipients' source-license rights.

Stored files differ from originals: Commons thumbnails were used where available, EXIF orientation was applied, images were converted to RGB, resized without cropping to at most 1280 pixels on either side, and re-encoded as JPEG at quality 90. All EXIF/GPS/IPTC metadata was stripped. No faces or plates were obscured; candidates with privacy risks were excluded instead. `sha256` refers to stored bytes. `source_records.json` also preserves original URLs, original Commons SHA-1, downloaded-byte SHA-256, file-upload timestamps, page revisions and file-page check timestamps/hashes. Remote reproduction retrieves these stored, reviewed derivatives rather than whatever Commons serves later.

All authors' attribution and copyright interests are retained. The parsed Commons caption/source metadata is third-party source material; unstructured Commons page text is under the [Commons page-text CC BY-SA 4.0 terms](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia). This does not change individual photograph licenses. Raw downloads and unneeded GPS information are not committed.

## Per-image attribution and permission evidence

The linked source page and preserved revision are the image-specific permission evidence. License URLs link to the terms actually selected; the JSON records when the page was checked. Dates in the manifest are actual UTC retrieval timestamps, not capture dates.

### commons-04258228ae — damaged_sign

- Title: Damaged road sign along Seein Road - geograph.org.uk - 4325202.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_sign_along_Seein_Road_-_geograph.org.uk_-_4325202.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=945805704).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/d/d4/Damaged_road_sign_along_Seein_Road_-_geograph.org.uk_-_4325202.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:49:03.198017+00:00; permission page checked: 2026-10-05T00:49:02.988972+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Road-name panel and its frame are detached and tilted against a fence.

### commons-0a68e3b438 — pothole

- Title: A photo of a pothole 2021-07-11.jpg
- Author: Thomas Booker (CoderThomasB)
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:A_photo_of_a_pothole_2021-07-11.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1003535190).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/8/82/A_photo_of_a_pothole_2021-07-11.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:15.887918+00:00; permission page checked: 2026-10-05T00:42:15.733784+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Visible dark road-surface cavity beside an intact drain cover.

### commons-0f02ab33ca — illegal_dumping

- Title: Fly-tipping, Johnstone - geograph.org.uk - 1597453.jpg
- Author: wfmillar
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly-tipping,_Johnstone_-_geograph.org.uk_-_1597453.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1255492093).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/2/2d/Fly-tipping%2C_Johnstone_-_geograph.org.uk_-_1597453.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:56:20.665083+00:00; permission page checked: 2026-10-05T00:56:19.976283+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Discarded bulky items lie beyond a rural hedge; source says waste was thrown over it beside Auchenlodment Road.

### commons-1b000da556 — leaking_hydrant

- Title: Leaking Fire Hydrant - geograph.org.uk - 1219371.jpg
- Author: PAUL FARMER
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Leaking_Fire_Hydrant_-_geograph.org.uk_-_1219371.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=975319840).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/8/86/Leaking_Fire_Hydrant_-_geograph.org.uk_-_1219371.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:55:28.282488+00:00; permission page checked: 2026-10-05T00:55:21.249597+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Unintended-looking water plume rises from a pavement utility opening; source explicitly identifies a leaking fire hydrant.

### commons-1be7ba9610 — damaged_sign

- Title: A damaged road sign at Tamlaght, Newtownsaville - geograph.org.uk - 4456079.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:A_damaged_road_sign_at_Tamlaght,_Newtownsaville_-_geograph.org.uk_-_4456079.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=945626135).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/d/db/A_damaged_road_sign_at_Tamlaght%2C_Newtownsaville_-_geograph.org.uk_-_4456079.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:33.083640+00:00; permission page checked: 2026-10-05T00:48:32.932186+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Road-name panel is mostly missing/illegible, with damage to its support.

### commons-1ce17d43d9 — illegal_dumping

- Title: Illegal dumping on public lands in the Medford District.jpg
- Author: BLM Oregon & Washington
- License: [CC BY 2.0](https://creativecommons.org/licenses/by/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Illegal_dumping_on_public_lands_in_the_Medford_District.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=917514018).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/f/f3/Illegal_dumping_on_public_lands_in_the_Medford_District.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:55:47.076254+00:00; permission page checked: 2026-10-05T00:55:46.915078+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Discarded broken electronic/appliance housings are dumped on public-land soil; BLM source explicitly describes illegal dumping.

### commons-2409b4bbcb — broken_streetlight

- Title: Lužiny, Archeologická, poškozená lampa.jpg
- Author: ŠJů
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Lu%C5%BEiny,_Archeologick%C3%A1,_po%C5%A1kozen%C3%A1_lampa.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1176168556).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/7/7b/Lu%C5%BEiny%2C_Archeologick%C3%A1%2C_po%C5%A1kozen%C3%A1_lampa.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:51:30.480691+00:00; permission page checked: 2026-10-05T00:51:30.316280+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Globe is displaced to one side of the mounting, exposing the socket hardware.

### commons-289e64dab5 — damaged_sign

- Title: Damaged road sign, Backfarm - geograph.org.uk - 5310260.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_sign,_Backfarm_-_geograph.org.uk_-_5310260.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=957228566).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/e/e9/Damaged_road_sign%2C_Backfarm_-_geograph.org.uk_-_5310260.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:54:36.760108+00:00; permission page checked: 2026-10-05T00:54:35.827508+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Detached road-name panel lies below its remaining post, with broken framing.

### commons-359e62bbe5 — illegal_dumping

- Title: Suburban fly tipping site - geograph.org.uk - 4363398.jpg
- Author: Thomas Nugent
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Suburban_fly_tipping_site_-_geograph.org.uk_-_4363398.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=979515362).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/0/0b/Suburban_fly_tipping_site_-_geograph.org.uk_-_4363398.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:56:15.053420+00:00; permission page checked: 2026-10-05T00:56:13.475380+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Discarded mattress and bulky objects sit beside a road rather than a collection container; source identifies a fly-tipping site.

### commons-3e69e554ed — pothole

- Title: Banbury's Bretch Hill Pothole, 2010.png
- Author: Snow storm in Eastern Asia at en.wikipedia
- License: [Public domain](https://commons.wikimedia.org/w/index.php?oldid=816245806); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Banbury%27s_Bretch_Hill_Pothole,_2010.png); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=816245806).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/b/b1/Banbury%27s_Bretch_Hill_Pothole%2C_2010.png?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:07.661128+00:00; permission page checked: 2026-10-05T00:42:07.124529+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Two visible surface cavities with exposed material on asphalt.

### commons-47aa637b4d — damaged_sign

- Title: Broken Give Way sign on a corner near Shifnal - geograph.org.uk - 4760128.jpg
- Author: Jaggery
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Broken_Give_Way_sign_on_a_corner_near_Shifnal_-_geograph.org.uk_-_4760128.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1217369040).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/f/fb/Broken_Give_Way_sign_on_a_corner_near_Shifnal_-_geograph.org.uk_-_4760128.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:35.626585+00:00; permission page checked: 2026-10-05T00:48:35.453002+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Give Way signpost is broken short near the verge, leaving the sign unusually close to the ground; source identifies a broken Give Way sign.

### commons-4be599b76a — broken_streetlight

- Title: Broken lantern - panoramio.jpg
- Author: Laima Gūtmane (simka…
- License: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Broken_lantern_-_panoramio.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=834837947).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/e/ea/Broken_lantern_-_panoramio.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:01.283970+00:00; permission page checked: 2026-10-05T00:48:00.451783+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Wall-mounted street lantern has visibly broken/missing glazing and damaged enclosure.

### commons-4c4c4bc5e0 — damaged_sign

- Title: Broken road sign - geograph.org.uk - 975071.jpg
- Author: Keith Evans
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Broken_road_sign_-_geograph.org.uk_-_975071.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=952364723).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/d/d3/Broken_road_sign_-_geograph.org.uk_-_975071.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:41.496239+00:00; permission page checked: 2026-10-05T00:48:37.973055+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Circular road sign has a fractured edge and missing portion.

### commons-5000667ac9 — damaged_sign

- Title: Damaged road sign along Glenhordial Road - geograph.org.uk - 4298106.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_sign_along_Glenhordial_Road_-_geograph.org.uk_-_4298106.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=937768384).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/a/aa/Damaged_road_sign_along_Glenhordial_Road_-_geograph.org.uk_-_4298106.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:52.948066+00:00; permission page checked: 2026-10-05T00:48:52.800216+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Road-name panel has a large broken-out section through its lettering.

### commons-53a0d4c79e — pothole

- Title: Pothole in an asphalt pavement.jpg
- Author: Frankie Fouganthin
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_in_an_asphalt_pavement.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1123611728).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/b/b3/Pothole_in_an_asphalt_pavement.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:51:23.828405+00:00; permission page checked: 2026-10-05T00:51:23.196205+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Distinct missing asphalt and exposed aggregate in road pavement.

### commons-7b78ffad33 — illegal_dumping

- Title: Fly tipping, Straiton - geograph.org.uk - 6379984.jpg
- Author: Jim Barton
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_tipping,_Straiton_-_geograph.org.uk_-_6379984.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1243874177).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/2/24/Fly_tipping%2C_Straiton_-_geograph.org.uk_-_6379984.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:55:49.639990+00:00; permission page checked: 2026-10-05T00:55:49.443385+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Large piles of branches and waste occupy an abandoned paved area; source identifies fly tipping.

### commons-81da3dfe1b — broken_streetlight

- Title: Chalupkova, rozbitá lampa 425096.jpg
- Author: ŠJů
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Chalupkova,_rozbit%C3%A1_lampa_425096.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1018157833).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/1/12/Chalupkova%2C_rozbit%C3%A1_lampa_425096.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:51:27.684853+00:00; permission page checked: 2026-10-05T00:51:26.361462+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Lamp lens/enclosure is fractured and open, with inner hardware exposed.

### commons-84bcb35daa — broken_streetlight

- Title: Decapitated lamppost in Central Park 01.jpg
- Author: Jay Dobkin
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Decapitated_lamppost_in_Central_Park_01.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1188764542).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/f/fe/Decapitated_lamppost_in_Central_Park_01.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:43:12.088832+00:00; permission page checked: 2026-10-05T00:43:11.858613+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Lamp head is detached and hanging down below the top of the park lamppost.

### commons-8ecf201b0b — pothole

- Title: Pothole Big.jpg
- Author: Uncl3dad
- License: [Public domain](https://commons.wikimedia.org/w/index.php?oldid=1211866573); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_Big.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1211866573).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/c/c7/Pothole_Big.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:41:52.582384+00:00; permission page checked: 2026-10-05T00:41:52.007603+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Large crater with broken asphalt edges and exposed road base.

### commons-9019e613c0 — pothole

- Title: Pothole in Villeray, Montréal.jpg
- Author: Miguel Tremblay
- License: [Public domain](https://commons.wikimedia.org/w/index.php?oldid=1205771119); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_in_Villeray,_Montr%C3%A9al.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1205771119).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/8/86/Pothole_in_Villeray%2C_Montr%C3%A9al.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:41:49.568926+00:00; permission page checked: 2026-10-05T00:41:49.342978+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Water-filled cavity with visibly missing asphalt and broken edges.

### commons-91f5ab98d5 — pothole

- Title: Nasty pothole in the middle of Virginia Avenue.jpg
- Author: Ser Amantio di Nicolao
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Nasty_pothole_in_the_middle_of_Virginia_Avenue.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=903939590).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/e/e0/Nasty_pothole_in_the_middle_of_Virginia_Avenue.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:18.588344+00:00; permission page checked: 2026-10-05T00:42:18.399718+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Broken, sunken asphalt at the edge of a road utility cover; visible loss of road surface.

### commons-9271f8fbbf — pothole

- Title: Pothole in limerock road gilchrist county florida.jpg
- Author: Cosmicray
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_in_limerock_road_gilchrist_county_florida.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1215502264).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/c/c7/Pothole_in_limerock_road_gilchrist_county_florida.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:02.527888+00:00; permission page checked: 2026-10-05T00:42:02.316990+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Visible eroded depression in an unpaved road; source explicitly attributes the pothole to traffic and precipitation.

### commons-951c65e3fc — illegal_dumping

- Title: Fly tipping - geograph.org.uk - 337058.jpg
- Author: Roger Cornfoot
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_tipping_-_geograph.org.uk_-_337058.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1054738270).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/9/96/Fly_tipping_-_geograph.org.uk_-_337058.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:56:29.399237+00:00; permission page checked: 2026-10-05T00:56:23.016454+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Large heap of manufacturing off-cuts obstructs a rural track; source explicitly says the material was dumped.

### commons-95929b7145 — broken_streetlight

- Title: Damaged lamp post, Fira, Santorini, Greece (approx. GPS location) julesvernex2.jpg
- Author: Jules Verne Times Two
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_lamp_post,_Fira,_Santorini,_Greece_(approx._GPS_location)_julesvernex2.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1164332246).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/c/c3/Damaged_lamp_post%2C_Fira%2C_Santorini%2C_Greece_%28approx._GPS_location%29_julesvernex2.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:43:06.392198+00:00; permission page checked: 2026-10-05T00:43:06.243606+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Decorative lamp has missing outer lamp enclosures, leaving inner bulbs exposed; damaged-lamp source caption supports this interpretation.

### commons-9763aaca53 — broken_streetlight

- Title: Umgestürzte Laterne vor dem Rathaus Düsseldorf, 13 März 2024 (1).JPG
- Author: Kürschner ( talk ) 17:03, 13 March 2024 (UTC)
- License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Umgest%C3%BCrzte_Laterne_vor_dem_Rathaus_D%C3%BCsseldorf,_13_M%C3%A4rz_2024_(1).JPG); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=946957554).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/6/67/Umgest%C3%BCrzte_Laterne_vor_dem_Rathaus_D%C3%BCsseldorf%2C_13_M%C3%A4rz_2024_%281%29.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:44:07.186897+00:00; permission page checked: 2026-10-05T00:44:05.434586+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Streetlight post lies broken on the pavement, with its base detached.

### commons-a39e024474 — broken_streetlight

- Title: Tilting street light - 17 August 2026.jpg
- Author: Aethonatic
- License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Tilting_street_light_-_17_August_2026.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1263810330).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/e/eb/Tilting_street_light_-_17_August_2026.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:44:02.916777+00:00; permission page checked: 2026-10-05T00:44:00.821844+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Streetlight pole leans strongly from vertical; source explicitly identifies tilting.

### commons-a3ff7b5c1d — pothole

- Title: Potholes in Bengaluru road.jpg
- Author: Mallikarjunasj
- License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Potholes_in_Bengaluru_road.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1272903966).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/3/36/Potholes_in_Bengaluru_road.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:41:57.669011+00:00; permission page checked: 2026-10-05T00:41:57.441438+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Visible circular missing asphalt and exposed aggregate near the curb.

### commons-b1418840a5 — broken_streetlight

- Title: Beschädigte Straßenlampe in Westerland.webp
- Author: Sebastian Martin Dicke
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Besch%C3%A4digte_Stra%C3%9Fenlampe_in_Westerland.webp); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=822304073).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/8/86/Besch%C3%A4digte_Stra%C3%9Fenlampe_in_Westerland.webp?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:25.735068+00:00; permission page checked: 2026-10-05T00:42:24.050524+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Lamp's outer enclosure is missing and lies beside the pole; source caption states damage.

### commons-bb9ea4bd37 — illegal_dumping

- Title: Fly tipping near Chickenley - geograph.org.uk - 5247658.jpg
- Author: Bill Boaden
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_tipping_near_Chickenley_-_geograph.org.uk_-_5247658.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1255508868).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/9/94/Fly_tipping_near_Chickenley_-_geograph.org.uk_-_5247658.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:56:17.614851+00:00; permission page checked: 2026-10-05T00:56:17.412101+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Bulky rubble and waste are strewn along a rural path verge; source identifies fly tipping.

### commons-be90c97f20 — damaged_sign

- Title: Damaged road name sign, Rathmore Road, Torquay - geograph.org.uk - 5212636.jpg
- Author: Derek Harper
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_name_sign,_Rathmore_Road,_Torquay_-_geograph.org.uk_-_5212636.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=957230679).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/f/fc/Damaged_road_name_sign%2C_Rathmore_Road%2C_Torquay_-_geograph.org.uk_-_5212636.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:48:50.484152+00:00; permission page checked: 2026-10-05T00:48:43.869979+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Road-name lettering is chipped/worn and incomplete; source identifies damaged road-name sign.

### commons-c9de6a8517 — broken_streetlight

- Title: Damaged light donostia.JPG
- Author: Joxemai
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_light_donostia.JPG); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=957239867).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/d/df/Damaged_light_donostia.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:43:09.289481+00:00; permission page checked: 2026-10-05T00:43:09.040201+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Lamp enclosure is detached from its mounting and hangs down beside the post.

### commons-c9f45e0429 — damaged_sign

- Title: At Manchester 2016 068.jpg
- Author: Photograph by Mike Peel ( www.mikepeel.net ).
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:At_Manchester_2016_068.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1246824759).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/b/b7/At_Manchester_2016_068.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:44:16.361318+00:00; permission page checked: 2026-10-05T00:44:12.851129+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Road warning sign has extensive peeling and illegibility; lower distance plate is partly obscured.

### commons-d374fa7f87 — illegal_dumping

- Title: Fly tipping white goods in Parco Alto Milanese - Legnano (MI), Lombardy, Italy - 2021-09-18.jpg
- Author: Mænsard vokser
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_tipping_white_goods_in_Parco_Alto_Milanese_-_Legnano_(MI),_Lombardy,_Italy_-_2021-09-18.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=965196148).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/1/16/Fly_tipping_white_goods_in_Parco_Alto_Milanese_-_Legnano_%28MI%29%2C_Lombardy%2C_Italy_-_2021-09-18.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:46:15.058590+00:00; permission page checked: 2026-10-05T00:46:14.843299+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Discarded large appliance in vegetation; source explicitly describes illegally dumped white goods in an agricultural park.

### commons-d5575814f4 — leaking_hydrant

- Title: Leaking hydrant on Washer Lane - geograph.org.uk - 2054711.jpg
- Author: Stephen Craven
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Leaking_hydrant_on_Washer_Lane_-_geograph.org.uk_-_2054711.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1017819689).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/f/fb/Leaking_hydrant_on_Washer_Lane_-_geograph.org.uk_-_2054711.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:55:18.895085+00:00; permission page checked: 2026-10-05T00:55:17.813247+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Water flows across the road; the original source caption specifically identifies a leaking hydrant on Washer Lane.

### commons-d6849d80e8 — illegal_dumping

- Title: Fly Tipping - geograph.org.uk - 1025840.jpg
- Author: wfmillar
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_Tipping_-_geograph.org.uk_-_1025840.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1128055156).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/7/7c/Fly_Tipping_-_geograph.org.uk_-_1025840.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:55:44.598280+00:00; permission page checked: 2026-10-05T00:55:43.819341+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Discarded appliance and other bulky objects lie in flooded ground; source identifies fly tipping at an abandoned gravel pit.

### commons-d86039e488 — leaking_hydrant

- Title: Broken fire hydrant leak high-pressure water spout (2023, Vero Beach, Florida) 01.jpg
- Author: Kiran891
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Broken_fire_hydrant_leak_high-pressure_water_spout_(2023,_Vero_Beach,_Florida)_01.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=996923402).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/d/d8/Broken_fire_hydrant_leak_high-pressure_water_spout_%282023%2C_Vero_Beach%2C_Florida%29_01.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:46:03.122260+00:00; permission page checked: 2026-10-05T00:46:02.941205+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Hydrant emits a high water plume; source explicitly describes a broken-hydrant leak.

### commons-dbe1344c9f — illegal_dumping

- Title: Fly tipping near High Beech, Essex.jpg
- Author: The wub
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly_tipping_near_High_Beech,_Essex.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1255508889).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/3/3b/Fly_tipping_near_High_Beech%2C_Essex.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:46:17.759688+00:00; permission page checked: 2026-10-05T00:46:17.568548+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Large pile of furniture and appliances dumped along a woodland path; source identifies fly tipping.

### commons-dca2e40d63 — illegal_dumping

- Title: Fly-tipping construction waste in Parco Alto Milanese - Busto Arsizio, Lombardy, Italy.jpg
- Author: Mænsard vokser
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Fly-tipping_construction_waste_in_Parco_Alto_Milanese_-_Busto_Arsizio,_Lombardy,_Italy.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1255492364).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/3/31/Fly-tipping_construction_waste_in_Parco_Alto_Milanese_-_Busto_Arsizio%2C_Lombardy%2C_Italy.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:46:11.879501+00:00; permission page checked: 2026-10-05T00:46:10.803030+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Large mound of rubble blocks a rural path; source explicitly identifies illegally dumped construction waste.

### commons-ddf392a527 — pothole

- Title: Pothole in Potomac after rain.jpg
- Author: Ser Amantio di Nicolao
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_in_Potomac_after_rain.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=1132539314).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/2/29/Pothole_in_Potomac_after_rain.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:13.173440+00:00; permission page checked: 2026-10-05T00:42:12.968901+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Water-filled missing asphalt with broken surface edges.

### commons-dfd2cf17b6 — pothole

- Title: Pothole on local Road in County Monaghan.jpg
- Author: Computerfan0
- License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Pothole_on_local_Road_in_County_Monaghan.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=848072287).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/3/35/Pothole_on_local_Road_in_County_Monaghan.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:41:47.056961+00:00; permission page checked: 2026-10-05T00:41:46.553408+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Long eroded road-surface cavity exposes aggregate; source explicitly identifies a pothole.

### commons-e6dea1ae8d — damaged_sign

- Title: Damaged road sign, Ballinamullan - geograph.org.uk - 4396145.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_sign,_Ballinamullan_-_geograph.org.uk_-_4396145.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=944877273).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/1/14/Damaged_road_sign%2C_Ballinamullan_-_geograph.org.uk_-_4396145.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:54:46.197952+00:00; permission page checked: 2026-10-05T00:54:39.045688+00:00.
- Change notice: Commons cached thumbnail (330 px for small originals) where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Broken road-name panel and framing lie in pieces against vegetation.

### commons-eddb29d0cf — broken_streetlight

- Title: A fallen street light pole.jpg
- Author: Niera
- License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:A_fallen_street_light_pole.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=778166183).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/5/5f/A_fallen_street_light_pole.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:42:21.437225+00:00; permission page checked: 2026-10-05T00:42:21.250165+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Whole streetlight pole lies fallen on a public paved surface; its lamp head is visible at the far end.

### commons-f5eb1a435d — damaged_sign

- Title: Damaged road sign along Roscavey Road - geograph.org.uk - 4485587.jpg
- Author: Kenneth  Allen
- License: [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0); stored derivative retains this license.
- Original file page: [source](https://commons.wikimedia.org/wiki/File:Damaged_road_sign_along_Roscavey_Road_-_geograph.org.uk_-_4485587.jpg); [preserved page revision](https://commons.wikimedia.org/w/index.php?oldid=944318054).
- Original media: [download](https://upload.wikimedia.org/wikipedia/commons/8/8c/Damaged_road_sign_along_Roscavey_Road_-_geograph.org.uk_-_4485587.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original); selected download is recorded in the manifest.
- Retrieved: 2026-10-05T00:49:00.639356+00:00; permission page checked: 2026-10-05T00:49:00.486381+00:00.
- Change notice: Commons thumbnail where available; EXIF orientation applied; RGB; aspect-preserving maximum 1280 px; JPEG quality 90; all EXIF/GPS/IPTC removed; no crop.
- Review: Detached road-name panel lies tilted at the base of its post.
