# Change Log — Chapter Completeness & Production Readiness

## 0.1.0 — 2026-08-13

Status: draft for editorial-owner review.

- Bound `01_SPECIFICATION.md` to `MWM-CPR-SPEC` v0.1.0-draft; source hash is recorded in `package_manifest.json`.
- Added 30 machine-readable rules for profile authority, component status, file/version lineage, metadata, structure, assets, rights evidence, cross-file reconciliation, stage gates, dependencies, and human sign-off.
- Added 12 explicit MWM decision hooks; unresolved policy is conservative and never silently converted into a requirement.
- Added schemas for manifests, profiles, components, evidence, files, upstream results, findings, ledger, decisions, outputs, and cross-family contracts.
- Added a 38-fixture synthetic evaluation set with clean, single-error, adversarial, negative-control, and integration cases plus rule crosswalk and scorer.
- Added regression intake and production-failure capture templates for false readiness, silent repair, status conflation, version ambiguity, conditionality errors, and boundary violations.

## Change policy

Any behavior change must identify the specification/rule/profile IDs, authority, rationale, effective date, fixture mutation or addition, regression result, owner approval, and migration treatment. Publisher profiles are versioned separately from MWM policy.

## 2026-08-14 packaging update

- Added `01_SPECIFICATION.docx` as a source-preserving Word version of the governing specification. The Markdown specification remains the design authority; no editorial rule or open MWM decision was changed.
