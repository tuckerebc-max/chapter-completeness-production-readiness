#!/usr/bin/env python3
"""Structural and policy validator for the MWM CPR package."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC_SHA256 = "F8223A92CBBF8F6047321E63633F5202FEC14478CE26282DAF3801094D992CE1"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def required(value: dict[str, Any], keys: list[str], label: str, errors: list[str]) -> None:
    for key in keys:
        if key not in value:
            errors.append(f"{label} missing {key}")


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    spec = ROOT / "01_SPECIFICATION.md"
    if not spec.exists():
        errors.append("missing 01_SPECIFICATION.md")
    else:
        digest = hashlib.sha256(spec.read_bytes()).hexdigest().upper()
        if digest != SPEC_SHA256:
            errors.append(f"specification hash mismatch: {digest}")
    skill = ROOT / "SKILL.md"
    if not skill.exists():
        errors.append("missing SKILL.md")
    else:
        skill_text = skill.read_text(encoding="utf-8")
        if len(skill_text.splitlines()) > 500:
            errors.append("SKILL.md exceeds 500 lines")
        if not re.search(r"^name:\s*chapter-completeness-production-readiness\s*$", skill_text, re.MULTILINE):
            errors.append("SKILL.md frontmatter name is missing")
        if not re.search(r"^description:\s*\S+", skill_text, re.MULTILINE):
            errors.append("SKILL.md frontmatter description is missing")
        if any(token in skill_text for token in ("TODO", "TBD", "FIXME")):
            errors.append("SKILL.md contains unfinished marker")
        if "$chapter-completeness-production-readiness" not in skill_text:
            warnings.append("SKILL.md does not explicitly mention its invocation token")
    agent = ROOT / "agents" / "openai.yaml"
    if not agent.exists():
        errors.append("missing agents/openai.yaml")
    else:
        agent_text = agent.read_text(encoding="utf-8")
        for marker in ("display_name:", "short_description:", "default_prompt:"):
            if marker not in agent_text:
                errors.append(f"agents/openai.yaml missing {marker}")

    required_paths = [
        "01_SPECIFICATION.md", "SKILL.md", "agents/openai.yaml", "package_manifest.json",
        "02_RULES/ruleset.json", "02_RULES/decision_hooks.json", "02_RULES/authority_registry.json", "02_RULES/status_vocabulary.json", "02_RULES/protected_inputs.json",
        "evals/fixture_contract.schema.json", "evals/fixture_catalog.json", "evals/rule_fixture_crosswalk.json", "evals/adversarial_negative_controls.json", "evals/integration_cases.json", "evals/evaluation_set.md", "evals/scorer.py",
        "scripts/validate_package.py",
        "CHANGELOG_REGRESSION/CHANGELOG.md", "CHANGELOG_REGRESSION/regression-intake.schema.json", "CHANGELOG_REGRESSION/regression-intake.template.json", "CHANGELOG_REGRESSION/production-failure.schema.json", "CHANGELOG_REGRESSION/production-failure.template.json", "CHANGELOG_REGRESSION/regression_policy.json",
    ]
    schema_names = ["run-manifest.schema.json", "profile.schema.json", "component.schema.json", "evidence.schema.json", "file-record.schema.json", "upstream-result.schema.json", "finding.schema.json", "ledger.schema.json", "decision.schema.json", "output.schema.json", "cross-family-contracts.json"]
    for name in schema_names:
        required_paths.append(f"schemas/{name}")
    example_names = ["run-manifest.json", "profile.json", "component.json", "evidence.json", "file-record.json", "upstream-result.json", "finding.json", "ledger.json", "decision.json", "output.json"]
    for name in example_names:
        required_paths.append(f"schemas/examples/{name}")
    for relative in required_paths:
        if not (ROOT / relative).exists():
            errors.append(f"missing {relative}")

    json_files = list(ROOT.rglob("*.json"))
    loaded: dict[str, Any] = {}
    for path in json_files:
        try:
            loaded[str(path.relative_to(ROOT)).replace("\\", "/")] = read_json(path)
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    ruleset = loaded.get("02_RULES/ruleset.json", {})
    hooks = loaded.get("02_RULES/decision_hooks.json", {})
    catalog = loaded.get("evals/fixture_catalog.json", {})
    crosswalk = loaded.get("evals/rule_fixture_crosswalk.json", {})
    controls = loaded.get("evals/adversarial_negative_controls.json", {})
    integrations = loaded.get("evals/integration_cases.json", {})
    rules = ruleset.get("rules", [])
    rule_ids = {rule.get("rule_id") for rule in rules}
    if ruleset.get("ruleset_id") != "MWM-CPR-RULES" or ruleset.get("version") != "0.1.0":
        errors.append("ruleset identity/version mismatch")
    if len(rules) != 30 or len(rule_ids) != 30:
        errors.append(f"expected 30 unique rules, found {len(rules)} / {len(rule_ids)}")
    if len(hooks.get("hooks", [])) != 12:
        errors.append("expected 12 decision hooks")
    fixtures = catalog.get("fixtures", [])
    fixture_ids = {item.get("fixture_id") for item in fixtures}
    if catalog.get("fixture_count") != 38 or len(fixtures) != 38 or len(fixture_ids) != 38:
        errors.append("expected 38 unique fixtures")
    expected_counts = {"clean": 6, "single_error": 12, "adversarial": 10, "negative_control": 6, "integration": 4}
    actual_counts: dict[str, int] = {}
    for fixture in fixtures:
        actual_counts[fixture.get("kind")] = actual_counts.get(fixture.get("kind"), 0) + 1
        if fixture.get("synthetic") is not True:
            errors.append(f"fixture {fixture.get('fixture_id')} is not synthetic")
        required(fixture, ["fixture_id", "kind", "title", "synthetic", "input", "gold"], fixture.get("fixture_id", "fixture"), errors)
        gold = fixture.get("gold", {})
        required(gold, ["expected_release_status", "expected_rule_ids", "expected_interventions", "must_not_emit_rule_ids"], f"{fixture.get('fixture_id')}.gold", errors)
        for rule_id in list(gold.get("expected_rule_ids", [])) + list(gold.get("must_not_emit_rule_ids", [])):
            if rule_id not in rule_ids:
                errors.append(f"{fixture.get('fixture_id')} references unknown rule {rule_id}")
    if actual_counts != expected_counts:
        errors.append(f"fixture counts differ: {actual_counts}")
    rows = crosswalk.get("rows", [])
    if len(rows) != 30 or {row.get("rule_id") for row in rows} != rule_ids:
        errors.append("crosswalk must have one row for every rule")
    for row in rows:
        for key in ("positive", "negative", "adversarial", "integration"):
            if row.get(key) not in fixture_ids:
                errors.append(f"crosswalk {row.get('rule_id')} has unknown {key} fixture")
    if set(controls.get("adversarial_ids", [])) != {item["fixture_id"] for item in fixtures if item["kind"] == "adversarial"}:
        errors.append("adversarial control coverage mismatch")
    if set(controls.get("negative_ids", [])) != {item["fixture_id"] for item in fixtures if item["kind"] == "negative_control"}:
        errors.append("negative control coverage mismatch")
    if {case.get("case_id") for case in integrations.get("cases", [])} != {item["fixture_id"] for item in fixtures if item["kind"] == "integration"}:
        errors.append("integration coverage mismatch")
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            warnings.append(f"generated cache present: {path.relative_to(ROOT)}")

    print(json.dumps({"package":"chapter-completeness-production-readiness","specification_sha256":SPEC_SHA256,"rule_count":len(rules),"decision_hook_count":len(hooks.get("hooks", [])),"fixture_count":len(fixtures),"crosswalk_rows":len(rows),"json_file_count":len(json_files),"errors":errors,"warnings":warnings,"pass":not errors}, indent=2, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
