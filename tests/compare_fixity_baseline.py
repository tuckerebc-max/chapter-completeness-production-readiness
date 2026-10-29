"""Bounded pinned-schema vs byte/version instrument comparison; not an agent benchmark."""
import importlib.util
import json
from pathlib import Path
import sys

try:
    import jsonschema
except ImportError:
    print("UNRUN: optional jsonschema dependency unavailable", file=sys.stderr)
    raise SystemExit(2)
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures/artifact-fixity"
spec = importlib.util.spec_from_file_location("fixity", ROOT / "scripts/check_artifact_fixity.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
schema = json.loads((FIX / "baseline-file-record.schema.json").read_text())
cases = {"success-with-history": "pass", "mismatched-saved-bytes": "mismatch",
         "stale-review": "mismatch", "stale-saved-receipt": "mismatch",
         "missing-saved": "blocked"}
results = []
for name, expected in cases.items():
    data = json.loads((FIX / (name + ".json")).read_text())
    # Same supplied target file record. The existing schema does not read paths,
    # saved copies, versioned receipts or review evidence.
    record = {"file_id": "CPR-F-SYNTHETIC", "path_or_uri": data["candidate"]["path"],
              "filename": "candidate.txt", "extension": ".txt",
              "version_id": data["target"]["version_id"], "declared_purpose": "synthetic packet",
              "status": "current", "clean_state": "clean",
              "hash_or_stable_id": data["target"]["sha256"], "supersedes": None,
              "evidence_id": "CPR-E-SYNTHETIC", "owner": "synthetic-owner"}
    baseline_errors = list(jsonschema.Draft202012Validator(schema).iter_errors(record))
    try:
        output = guard.check(data, FIX)
    except (guard.InvalidInput, OSError, ValueError, TypeError, KeyError):
        output = {"status": "blocked"}
    passed = not baseline_errors and output["status"] == expected
    results.append({"case": name, "baseline_schema": "valid" if not baseline_errors else "invalid",
                    "candidate": output["status"], "expected_candidate": expected, "pass": passed})
out = {"baseline": "file-record.schema.json @ 362506cbf98c365920398d25638805b14e434497",
       "scope": "Schema-enforcement comparison only, not a full-agent failure or superiority claim.",
       "cases": results, "pass": all(x["pass"] for x in results)}
print(json.dumps(out, indent=2))
raise SystemExit(0 if out["pass"] else 1)

