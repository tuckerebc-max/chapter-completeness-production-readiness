# Staged change: exact artifact/version binding

**Candidate:** `artifact-fixity-v3`. Reviewable local extension, not installed,
published, accepted, or release-ready.

## Purpose and boundary

Add an optional executable instrument for the existing CPR-02/CPR-11 rules:
compare actual candidate and saved bytes with explicit target and review records,
while keeping historical receipts separate. The single SKILL.md change routes this
episode to a concise reference; existing policy, rule registry, schemas, governing
specification and domain ownership remain unchanged.

The instrument is not a cloud client, release gate replacement, content extractor,
acceptance tracker, or proof of remote currentness. It cannot establish the truth
or authority of its input records. All new fixtures are synthetic.

## Source and attribution

Full baseline copied from
[chapter-completeness-production-readiness](https://github.com/tuckerebc-max/chapter-completeness-production-readiness)
at commit `362506cbf98c365920398d25638805b14e434497`.
The original package and its attribution were preserved. Repository ownership is
not a claim of original authorship. The inspected baseline contains no LICENSE
file; this candidate adds no license and does not authorize public redistribution.
Obtain the appropriate source-rights and publication decision before remote submission.

The observation/staging procedure was guided by Task Observer, created by Eoghan
Henn / Rebelytics, CC BY 4.0:
[One Skill to Rule Them All](https://github.com/rebelytics/one-skill-to-rule-them-all).
No Task Observer text or code is embedded here and its license is not assigned to
the CPR baseline. Permission controls override any source's retry advice.

## Changes

- Route the identity-check episode from workflow step 4.
- Add `references/artifact-fixity.md`, input schema and a standard-library checker.
- Add synthetic current, historical, changed and missing-file scenarios.
- Add 24 CLI/adversarial tests and a five-case pinned-schema comparison.
- Normalize symlink-loop resolution failures at input, manifest, and root paths
  into the existing blocked-input contract; retain path-escape and alias rejection.
- Restore six manifest-required regression resource paths by byte-identical copies from verified root files, preserving the originals; REGRESSION_RESOURCE_RESTORE.json records each mapping.

## Results and unchanged limits

All 24 instrument tests passed. All five comparison expectations passed: the
existing file-record schema accepted each structurally valid record; the new
instrument passed the current-version case with historical receipt, reported
three identity/fixity mismatches, and blocked the missing-file case. This shows a
bounded schema-enforcement gap, **not failure of the full baseline agent workflow
or general performance superiority**.

The baseline suite validates 38 synthetic fixture definitions and its scorer
self-test passes 38 gold-versus-gold cases; that self-test is not an execution
benchmark. The original package validator failed six expected paths under
`CHANGELOG_REGRESSION/`. Their exact content exists at the pinned repository root,
including three DOS-style aliases. This candidate restores those required paths
with byte-identical copies and retains the originals. The full package validator
now passes. No missing content was fabricated; the restoration mapping is explicit.

The independent v2 review found one robustness defect among 18 new probes: on
Python 3.12, a symlink loop raised RuntimeError instead of returning blocked JSON.
This v3 repair catches RuntimeError only at path-resolution calls and adds five
regressions (candidate, saved, manifest and root loops, plus retained escape
rejection). The author's rerun of the independent probe now meets all 18
expectations; all supplied input bytes and package bytes remain unchanged during
the probe. That rerun is not a fresh independent approval of v3.

A fresh independent repair check, source-rights decision, owner approval and any
intended repository submission remain separate. A passing fixity result never closes other
CPR, RCI, TE, EQA, proof, accessibility, rights or acceptance gates.

