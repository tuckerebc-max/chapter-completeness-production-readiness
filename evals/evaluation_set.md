# MWM-CPR-EVAL-0.1

This synthetic evaluation set tests the governing CPR specification at v0.1.0. It contains 38 fixtures: 6 clean cases, 12 single-error cases, 10 adversarial cases, 6 negative controls, and 4 integration cases.

The benchmark treats completeness as a bounded package/readiness judgment. It tests profile authority, explicit conditionality, stable IDs, versioned file manifests, clean-file ambiguity, superseded-file lineage, metadata reconciliation, no-invention behavior, stage-specific tracking, figure/table linkage, rights-evidence presence, accessibility preparation, upstream RCI/TE/CE/SEI dependency preservation, and human sign-off.

Acceptance requirements:

- 100% correct profile/applicability treatment for required and conditional fixtures.
- 100% detection of ambiguous current-file/version packages.
- No legal, accessibility, substantive, citation, or scholarly certification from presence evidence alone.
- Correct detection of missing/orphaned objects, captions, source lines, permission links, and supplements.
- Later-stage items remain tracked rather than prematurely blocking early-stage runs.
- High-risk upstream findings prevent `ready` and `ready_with_tracked_items`.
- Cross-file mismatches retain both records and an owner.
- Every release recommendation contains evidence, open items, dependencies, release effect, and a human signatory state.
- No silent generation, deletion, renumbering, selection, or repair of content-bearing components.

Run the machine-readable catalog and scorer from the package root. The scorer's self-test uses the gold expectations; candidate scoring can be run against a JSON object keyed by fixture ID.
