# Research, citations and public-domain information

Modern scholarship is welcome when it improves accuracy or explains a design
choice. A work need not be public domain to be read and cited. Facts and ideas
can inform original wording; copying protected prose, examples, tables, data or
images needs a suitable licence or another documented basis. Public access and
public-domain status are separate questions. See the [US Copyright Office's
explanation](https://www.copyright.gov/help/faq/faq-protect.html) and the
[Creative Commons FAQ](https://creativecommons.org/faq/). These are practical
guidelines; rights can differ by jurisdiction and by the kind of material.

## Record each source

Give each source a stable bibliography ID. Record author/editor/translator,
title, date, edition, publisher or repository, DOI/URL, access date, and a precise
page, section, entry or line locator for the claim. For a dataset, also record
version, file hash, licence and the copied/adapted fields. Keep evidence of the
rights statement with the package. Changes of edition or translation are new
source records when their rights or wording differ.

Use these roles explicitly: **direct input**, **method reference**, **background
reading**, or **candidate not used**. Link future corrections to entry/sense IDs
in a sidecar record; do not imply that a general bibliography supports every
definition. Existing per-entry gloss/model/prompt provenance is preserved. This
packaging round adds no new definitions and no retrospective scholarly review.

## Include what can be reused

Public-domain ancient texts can be useful for historical senses and citations.
Verify the particular transcription, edition, notes, images and translation;
modern additions can have their own rights. Preserve author and edition credit
even when copyright has expired. Never label an entire website public domain
because it hosts an old work.

Openly licensed modern research and datasets can be included under their exact
terms, retaining author credit, licence links and modification notices. CC BY
material can be incorporated into a CC BY-SA adaptation while preserving its
attribution. A NonCommercial or NoDerivatives grant is unsuitable as the basis
for unrestricted adaptation in this dataset; obtain another grant or keep it as
reference reading. Unknown rights mean the copied material is not included by
assumption. A citation can still identify a work without reproducing it.

For contested claims, record who advances the interpretation and what evidence
they use. Do not turn a disputed historical explanation into an unqualified
dictionary fact. Keep traditional and simplified forms, regional readings and
distinct cultural terms where supported by the source evidence.

## Citation sidecar for future content work

Keep a UTF-8 JSON record with `entry_id`, optional `sense_uid`, `bibliography_id`,
`locator`, `claim`, `use` (fact/paraphrase/quotation/data), `rights_basis`, and
`review_kind`. A record must describe the actual use. The current database schema
is unchanged; no invented per-sense citations are assigned to existing outputs.

The bibliography includes direct sources and the technical works cited in the
project's existing handwriting research. Additional vocabulary research is
labelled background reading and has no effect on the shipped lexicon.
