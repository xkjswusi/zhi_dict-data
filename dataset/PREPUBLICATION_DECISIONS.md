# Release status and remaining content choices

**Owner direction, 2026-10-10:** Adam Woeltz authorised a complete app-code and
data package, with Apache-2.0 for project software. Dictionary data retains
CC-BY-SA-4.0; separate graphics retain Arphic-1999. Closed app testing is underway,
with at most one final content revision campaign if the owner chooses it.

**Owner direction, 2026-10-31:** publish the current dataset. This lexical export and
the Arphic assets, with their inputs and builders, are public at
https://github.com/xkjswusi/zhi_dict-data. The complete source package stays
unpublished.

## Rights decisions completed

- **Software:** Q85 is resolved by the owner's Apache-2.0 selection. Root `LICENSE`,
  `NOTICE`, `LICENSES.md`, contribution terms and per-file licence inventory state
  its scope; lexical exports carry their own code/data licence files.
- **SUBTLEX-CH:** PLOS's institutional Figshare record explicitly states CC BY 4.0.
  Its `Files_S1.zip` is byte-identical to the pinned input. Evidence, file identity
  and author attribution are archived in `evidence/subtlex-license.json`.
- **Arphic:** original graphics, modified assets, adjacent modification notices,
  unaltered licence, editable inputs and rebuilders are included as a separate
  component. The lexical-only export excludes them.
- **Project attribution:** use Adam Woeltz; preserve upstream names and AI provenance.
  Grants cover rights held and subsisting. Historical provider contracts are not
  archived, and no exclusive AI authorship is represented.
- **Research:** modern scholarship can inform cited facts/original wording. Copied
  protected material requires appropriate rights. Source roles and claim locators
  follow `RESEARCH_POLICY.md`; the bibliography does not fabricate sense citations.

## Final version pairing

This package pins dictionary content hash `2eadcac5…`, compiled 2026-10-30, and the
app source at that content; **2026.10.30-v3.3** is the package version, paired with app
0.1.2 (versionCode 3). The earlier 0.1.1 carries `10c435ec…`, and 2026.10.22-v3.2 stays
its source and data. 2026.10.10-v3.1 paired content `97384fb7…` with app 0.1.0.
If a final content campaign changes the dictionary, recompile and regenerate
JSON, TSV, deck, assets, bibliography/source evidence and checksum inventories
together. Keep the distributed app and its data version paired. Verify the
actual notices and availability of source/data when sharing an app build; this
local archive does not establish what an existing public URL currently hosts.

**Pairing made (2026-10-22, R101, Q135):** R96 moved the content to `10c435ec…`, and the
flashcard and help campaign (R97–R101) changed the app source. R101 set app `versionName`
0.1.1 and `versionCode` 2, regenerated this package and the export at this version, and built
upload-signed files outside the package. The Play upload remains the owner's.

**Re-emitted (2026-10-30, R104, D264):** the print-edition enrichment campaign (R102–R104)
moved the content to `2eadcac5…`: 456 new entries, 576 new senses, and every 参见 now names
an entry. The app source is re-pinned, and this package and the export regenerated. No
version was raised and no release built.

**Pairing made (2026-10-30):** app `versionName` 0.1.2 and `versionCode` 3 carry this content
and night mode (D271). This package and the export were re-emitted at that pairing, with
upload-signed files built outside the package. The Play upload remains the owner's.

## Current limitations preserved

- All definitions are personally unreviewed. There are 71 redirects, 17 stubs,
  52 label-only senses and references beyond the selected vocabulary.
- Existing correction candidates include 華盛頓's missing capital sense, 唐 Tang2's
  missing surname sense and 開's missing/collapsed meaning. No content was changed
  during packaging. The owner can select a finite final fix list or accept them.
- Android backup is disabled, and list export does not include study marks.
  The application ID change to `org.coldscholar.dictionary` creates a separate app
  from the prior ID, without automatic migration of earlier tester data.
- Structural, hash and rebuild checks establish representation and reproducibility;
  they do not establish every definition's accuracy or a mobile/desktop Anki
  visual playtest. App release timing remains the owner's choice.

No permission request to a third party, new tester programme or AI regeneration
was performed in this packaging round.
