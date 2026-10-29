# Artifact fixity and version-binding check

Load this reference before using the optional local checker for CPR-02/CPR-11,
or before asserting that recovered or saved bytes are the exact reviewed version.
This is a narrow instrument for the existing identity and lineage rules, not a
new release policy. The approved component profile still controls requiredness.

## Prerequisites and inputs

- Python 3.9 or newer; the checker and its unit tests use only the standard library.
- Authorized local copies of the candidate and separately materialized saved file.
- An intended target identity confirmed from an authoritative record, not selected
  from a filename, timestamp, file size, or an old upload receipt.
- Saved-file and review records naming the same artifact and explicit version.
  Obtain these records through an authorized source; the checker cannot authenticate
  them or query a remote system.
- A JSON manifest in the same private directory tree as the authorized input files.
  File paths are relative to that manifest. Absolute paths, traversal outside its
  directory, missing files, duplicate JSON keys, and unknown fields are blocked.

The contract is described in `schemas/artifact-fixity.schema.json`. A runnable,
fully synthetic example is `fixtures/artifact-fixity/success-with-history.json`.
The fields have distinct jobs:

| Field | Meaning |
| --- | --- |
| target | Intended artifact ID, explicit version, SHA-256 and authority reference |
| candidate.path | Local candidate bytes, read without modification |
| saved | Separately materialized saved bytes plus versioned saved record and receipt reference |
| review | Artifact/version/digest named by retained review evidence |
| historical_receipts | Optional earlier receipts; retain rather than overwrite |

A record can be syntactically correct but false. Verify its authority, source,
currentness, permitted access and relationship to the requested task before using
it. Never invent these fields just to satisfy the checker. A manifest does not
grant permission to read or transfer a file.

## Ordered procedure

1. Resolve the intended artifact and current explicit version from the owner/source.
   Preserve ambiguous candidates; stop for owner clarification if authority conflicts.
2. Obtain the authorized saved bytes and current metadata. Treat any older receipt
   as a separate historical record until its version has been reconciled.
3. Identify the exact bytes named in the review or test evidence. If the candidate
   changed after that review, rerun the affected review; never merely replace its hash.
4. Write the manifest with private configuration and evidence references. Keep it
   outside a publicly distributed skill package unless all fields and files are safe.
5. Run the read-only check. From this skill directory, the safe demonstration is:

```bash
python scripts/check_artifact_fixity.py fixtures/artifact-fixity/success-with-history.json
```

For real work, replace the final argument with the authorized private manifest.
The command reads only; it never downloads, overwrites, uploads, deletes, retries
a denied action, selects a current file, or changes a record.
6. Read the JSON result and exit status. Preserve both sides of each disagreement.
   Route unknown identity/currentness to the owner; refresh stale source records
   only through authorized access. Inspect uncertain write outcomes before retrying.
7. Attach the narrow result to the existing CPR finding/evidence record, preserving
   downstream owner and release gates. Repeat after any material byte or version change.

## Results and recovery

- Exit 0, `pass`: candidate and saved digests match the supplied target; saved and
  review records name that same artifact/version/digest. A different-version
  historical receipt is retained as `different_revision`, not a delivery failure.
- Exit 1, `mismatch`: at least one explicit identity, version or digest comparison
  disagrees. Exact finding codes identify the pair. A stale saved receipt can
  disagree while current saved bytes match; do not label this corrupt delivery.
- Exit 2, `blocked`: required input is invalid, missing, unreadable or outside the
  allowed local input directory; no identity conclusion is established. Stop and
  obtain the missing authorized evidence. Do not bypass access denial.

A pass is not proof of remote currentness, receipt authenticity, review quality,
content or table/figure completeness, recipient access, human acceptance,
publication, or release authorization. Two corrupt copies can match. Two different
serializations can represent equivalent content while their bytes differ. Such
semantic questions require the proper specialist; do not weaken the hash check to
make them pass.

## Tests and limits

```bash
python tests/test_artifact_fixity.py
python tests/compare_fixity_baseline.py
```

The second command needs the optional `jsonschema` package for the pinned baseline
schema comparison; it does not install it. If unavailable, record that comparison
as unrun, not passed. The baseline experiment tests only the schema's enforcement
scope, not the performance of the full existing agent workflow.

Tests include matching current bytes with an older historical receipt, changed
saved bytes, changed candidate bytes, stale review, stale receipt, wrong artifact,
same-version conflicting receipts, missing inputs, boundary/path rejection and no
mutation. Synthetic text inputs deliberately avoid private manuscripts. No DOCX
rendering, document-content extraction, cloud connector or recipient access was
tested by this instrument.

