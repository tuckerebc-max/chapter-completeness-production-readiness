---
name: chapter-completeness-production-readiness
description: Determine whether an edited-volume chapter package contains the right components, metadata, evidence, links, files, owners, and approvals for its current editorial stage. Use for MWM chapter intake, resubmission deltas, handoff gates, production readiness, conditional applicability, cross-file reconciliation, upstream dependency import, and human-signable release recommendations. Do not use for developmental editing, substantive copyediting, citation construction, deep claim adjudication, legal permission determinations, accessibility conformance, or post-typesetting proof review.
---

# Chapter Completeness & Production Readiness

Use this family to answer one bounded question: is the right thing present, in the right version, with the right companion records, owner, and evidence for this stage? Keep `present`, `complete`, `verified`, `approved`, `accessible`, `cleared`, and `ready` distinct. Presence is never a silent quality, legal, accessibility, or scholarly certification.

## Required inputs

Load the versioned MWM component profile, chapter/volume/version/stage identifiers, current package manifest, manuscript and companion records, and upstream status records from RCI, SGI, TE, Copyediting, and Scholarly/Editorial Integrity. Protect sensitive records by storing identifiers, access status, and locators rather than reproducing their contents. If the profile, current version, authority, protected-record path, upstream status, open-item owner, or signatory role is missing, stop with the appropriate blocked precondition.

## Executable workflow

1. Initialize a run with `MWM-CPR-SPEC`, rule version, profile version, chapter/volume/version/stage, trigger, tool policy, reviewer, and signatory role.
2. Validate the profile before using any checklist. Each item needs requiredness, applicability or activation condition, authority, owner, stage due, and release effect. A publisher or generic exemplar may raise a question but cannot create an MWM requirement.
3. Build a stable component graph for title, authors, affiliations, sections, abstracts, keywords, figures, tables, captions, notes, source lines, permissions, declarations, supplementary objects, files, metadata, and cross-references.
4. Inventory all files with path, name, extension, version, hash or stable identifier, declared purpose, current/superseded/duplicate/unknown status, and evidence. Never choose a final file from timestamp, size, or filename plausibility alone.
5. Evaluate required and conditional components. Use `not_applicable` only when the profile supplies the condition, rationale, and authority. Record narrow evidence and keep `present_unverified` separate from downstream verification or approval.
6. Reconcile manuscript, metadata sheet, volume TOC, file manifest, assets, captions, source lines, permissions, alt text, supplements, and links. Report both sides of every mismatch; do not silently repair, renumber, delete, select, or generate content-bearing values.
7. Import upstream statuses without taking ownership of their substantive judgments. Preserve source Skill, finding ID, owner, severity, response, dependency, and release effect. Completeness cannot close an RCI, TE, CE, or SEI finding.
8. Apply stage-specific gates. Items due later may be `TRACK` with an owner and due stage. Current required gaps are `QUERY`, `ROUTE`, `HOLD`, or `BLOCK` according to the rules. An accepted exception needs an authoritative decision record.
9. Produce the component matrix, file/package manifest, dependency map, exception and risk ledger, tracked-later list, evidence summary, and recommendation: `ready`, `ready_with_tracked_items`, `conditional_hold`, `hold`, `blocked`, or `not_ready`.
10. Require a named human signatory for handoff or release. Freeze the result to the current version; on resubmission compare deltas, preserve superseded records, and rerun affected gates.

## Skill routing

- `CPR-01`: profile and rule applicability; block incomplete or conflicting profiles.
- `CPR-02`: chapter identity, clean-file and version package; block ambiguous current files.
- `CPR-03`: title, author, affiliation, contact, identifier, and volume metadata presence/linkage; route authorship concerns to SEI.
- `CPR-04`: abstract, keyword, biography, and discoverability field presence, scope, count, and due stage; never draft or judge argument fidelity.
- `CPR-05`: required body sections, appendices, boxes, notes, references, and orphan components; TE owns structural correctness.
- `CPR-06`: figure/table/asset/caption/note/source-line/alt-text records and links; TE, accessibility, and rights owners retain substantive authority.
- `CPR-07`: permission and rights-evidence presence/linkage; never decide fair use, ownership, license meaning, or legal sufficiency.
- `CPR-08`: expected citation/reference/cross-reference components and targets; consume RCI/TE and do not duplicate their correctness checks.
- `CPR-09`: conditional declarations, ethics, consent, AI, data, software, funding, and supplementary records; route adequacy to SEI.
- `CPR-10`: declared accessibility target and structured-metadata preparation; never claim WCAG or structured-content conformance without specialized evidence.
- `CPR-11`: cross-file reconciliation and owner routing; preserve conflicting records.
- `CPR-12`: stage gate and human-signable decision; unresolved material upstream findings prevent readiness.

## Evidence and finding discipline

Use evidence levels Q0-Q4 from the ruleset. A `PASS` means only that the configured presence/completeness gate passed. Findings must include exact object/file references, observed fact, authority, status, owner, next action, confidence, dependency, release effect, and closure condition. Use `AUTO_RECORD`, `TRACK`, `QUERY`, `ROUTE`, `HOLD`, `BLOCK`, or `PASS`; do not use a generic "complete" label to hide an unresolved dependency.

## Cross-family contracts

Inbound records are RCI citation/reference status, SGI active style-rule status, TE object and cross-reference status, CE handoff status, SEI disclosure/integrity status, and EQA orchestration metadata. Outbound records are CPR component and package readiness results for EQA, plus explicit handoffs to RCI, TE, CE, SEI, rights, accessibility, and production owners. CPR owns presence, applicability, linkage, version lineage, and stage readiness only; it does not own source truth, stylistic edits, technical-object correctness, rights clearance, accessibility conformance, or integrity adjudication.

## Safety boundaries

Do not invent metadata, abstracts, keywords, bios, source lines, licenses, asset numbers, final-file choices, profile requirements, or signatory approvals. Do not certify legal clearance, accessibility, factual accuracy, citation correctness, or substantive approval from presence evidence. Do not release autonomously. Preserve protected-record access status, disagreement, superseded versions, and unresolved owner decisions.
Invocation: $chapter-completeness-production-readiness
