#!/usr/bin/env python3
"""Read-only artifact identity/fixity check; never certifies release or acceptance."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

CONTRACT = "cpr-artifact-fixity/1"
HEX = re.compile(r"^[0-9a-f]{64}$")
IDENTITY = {"artifact_id", "version_id", "sha256"}

class InvalidInput(ValueError):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def obj(value, required, optional, label):
    if not isinstance(value, dict):
        raise InvalidInput(f"{label}: expected object")
    if set(value) - required - optional or required - set(value):
        raise InvalidInput(f"{label}: missing or unknown fields")
    return value

def text_fields(value, keys, label):
    for key in keys:
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise InvalidInput(f"{label}.{key}: nonempty string required")

def identity(value, extra, label):
    obj(value, IDENTITY | extra, set(), label)
    text_fields(value, IDENTITY | extra, label)
    if not HEX.fullmatch(value["sha256"]):
        raise InvalidInput(f"{label}.sha256: lowercase SHA-256 required")

def validate(data):
    obj(data, {"contract_version", "target", "candidate", "saved", "review"},
        {"historical_receipts"}, "manifest")
    if data["contract_version"] != CONTRACT:
        raise InvalidInput("unsupported contract_version")
    identity(data["target"], {"authority_ref"}, "target")
    obj(data["candidate"], {"path"}, set(), "candidate")
    text_fields(data["candidate"], {"path"}, "candidate")
    identity(data["saved"], {"path", "receipt_ref"}, "saved")
    identity(data["review"], {"review_ref"}, "review")
    history = data.get("historical_receipts", [])
    if not isinstance(history, list):
        raise InvalidInput("historical_receipts: expected array")
    for i, item in enumerate(history):
        identity(item, {"receipt_ref"}, f"historical_receipts[{i}]")

def resolve_input(path):
    """Normalize pathlib's pre-3.13 symlink-loop error as invalid input."""
    try:
        return path.resolve(strict=True)
    except RuntimeError as exc:
        raise InvalidInput(f"file path cannot be resolved: {exc}") from exc

def path_in(root, relative):
    p = Path(relative)
    if p.is_absolute():
        raise InvalidInput("file paths must be relative to the manifest directory")
    resolved = resolve_input(root / p)
    if not resolved.is_relative_to(root):
        raise InvalidInput("file path escapes the manifest directory")
    if not resolved.is_file():
        raise InvalidInput("file path is not a regular file")
    return resolved

def digest(path):
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size

def check(data, root):
    """Return evidence only. A matching input record is not verified authority."""
    validate(data)
    root = resolve_input(root)
    candidate_path = path_in(root, data["candidate"]["path"])
    saved_path = path_in(root, data["saved"]["path"])
    if candidate_path.samefile(saved_path):
        raise InvalidInput("saved bytes must be a distinct materialized copy")
    candidate_hash, candidate_size = digest(candidate_path)
    saved_hash, saved_size = digest(saved_path)
    target = data["target"]
    findings = []
    history = []
    def issue(code, reason):
        findings.append({"code": code, "reason": reason})
    # Check logical identity before interpreting byte differences.
    for role in ("saved", "review"):
        record = data[role]
        if record["artifact_id"] != target["artifact_id"]:
            issue(role + "_artifact_mismatch", "Record names a different artifact.")
        elif record["version_id"] != target["version_id"]:
            issue(role + "_version_mismatch",
                  "Refresh or reconcile the versioned record; do not infer corrupt delivery.")
        if record["sha256"] != target["sha256"]:
            issue(role + "_digest_mismatch",
                  "Recorded digest is not bound to the intended target revision.")
    if candidate_hash != target["sha256"]:
        issue("candidate_bytes_mismatch", "Candidate bytes differ from the intended target digest.")
    if saved_hash != target["sha256"]:
        issue("saved_bytes_mismatch",
              "Materialized saved bytes differ from target; this does not identify the cause.")
    if saved_hash != data["saved"]["sha256"]:
        issue("saved_receipt_bytes_mismatch",
              "Saved record and materialized bytes disagree; inspect identity/version before retrying.")
    for item in data.get("historical_receipts", []):
        if item["artifact_id"] != target["artifact_id"]:
            issue("historical_artifact_mismatch", "An unrelated artifact was supplied as version history.")
        elif item["version_id"] == target["version_id"]:
            if item["sha256"] != target["sha256"]:
                issue("same_version_receipt_conflict", "Conflicting digests claim the same artifact version.")
            else:
                history.append({"receipt_ref": item["receipt_ref"], "classification": "same_revision"})
        else:
            history.append({"receipt_ref": item["receipt_ref"], "classification": "different_revision",
                            "version_id": item["version_id"]})
    return {
        "contract_version": CONTRACT, "status": "pass" if not findings else "mismatch",
        "artifact_id": target["artifact_id"], "target_version": target["version_id"],
        "target_sha256": target["sha256"],
        "observed": {"candidate": {"sha256": candidate_hash, "size_bytes": candidate_size},
                     "saved": {"sha256": saved_hash, "size_bytes": saved_size}},
        "findings": findings, "historical_receipts": history,
        "scope": "Byte identity and supplied record binding only.",
        "not_established": ["source authority", "remote currentness", "review quality",
                            "content completeness", "recipient access", "delivery receipt authenticity",
                            "acceptance", "publication", "release authorization"],
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = resolve_input(args.manifest)
        data = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        result = check(data, manifest.parent)
    except (InvalidInput, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"contract_version": CONTRACT, "status": "blocked",
                  "findings": [{"code": "invalid_or_unavailable_input", "reason": str(exc)}],
                  "scope": "No identity decision; no files modified."}
    print(json.dumps(result, indent=2, sort_keys=True))
    return {"pass": 0, "mismatch": 1, "blocked": 2}[result["status"]]

if __name__ == "__main__":
    raise SystemExit(main())

