#!/usr/bin/env python3
"""Deterministic scorer for the synthetic MWM CPR evaluation set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
RULES = ROOT / "02_RULES" / "ruleset.json"
CATALOG = EVALS / "fixture_catalog.json"
CROSSWALK = EVALS / "rule_fixture_crosswalk.json"
CONTROLS = EVALS / "adversarial_negative_controls.json"
INTEGRATIONS = EVALS / "integration_cases.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_map() -> dict[str, dict[str, Any]]:
    return {item["fixture_id"]: item for item in load(CATALOG)["fixtures"]}


def validate_suite() -> dict[str, Any]:
    catalog = load(CATALOG)
    ruleset = load(RULES)
    crosswalk = load(CROSSWALK)
    controls = load(CONTROLS)
    integrations = load(INTEGRATIONS)
    fixtures = catalog["fixtures"]
    ids = [item["fixture_id"] for item in fixtures]
    errors: list[str] = []
    if catalog.get("fixture_count") != len(fixtures):
        errors.append("fixture_count does not match fixtures length")
    if len(ids) != len(set(ids)):
        errors.append("fixture IDs are not unique")
    if not all(item.get("synthetic") is True for item in fixtures):
        errors.append("all fixtures must be synthetic")
    observed_counts: dict[str, int] = {}
    for item in fixtures:
        observed_counts[item["kind"]] = observed_counts.get(item["kind"], 0) + 1
        for key in ("fixture_id", "kind", "title", "synthetic", "input", "gold"):
            if key not in item:
                errors.append(f"{item.get('fixture_id', '<unknown>')} missing {key}")
        for key in ("expected_release_status", "expected_rule_ids", "expected_interventions", "must_not_emit_rule_ids"):
            if key not in item.get("gold", {}):
                errors.append(f"{item.get('fixture_id', '<unknown>')} missing gold.{key}")
    if observed_counts != catalog.get("fixture_kind_counts"):
        errors.append(f"fixture kind counts differ: {observed_counts}")
    rule_ids = {rule["rule_id"] for rule in ruleset["rules"]}
    if len(crosswalk.get("rows", [])) != len(rule_ids):
        errors.append("crosswalk must contain exactly one row per rule")
    crosswalk_ids = [row.get("rule_id") for row in crosswalk.get("rows", [])]
    if set(crosswalk_ids) != rule_ids:
        errors.append("crosswalk rule IDs do not match ruleset")
    fixture_ids = set(ids)
    for row in crosswalk.get("rows", []):
        for key in ("positive", "negative", "adversarial", "integration"):
            if row.get(key) not in fixture_ids:
                errors.append(f"crosswalk {row.get('rule_id')} references unknown {key} fixture")
    adversarial = {item["fixture_id"] for item in fixtures if item["kind"] == "adversarial"}
    negative = {item["fixture_id"] for item in fixtures if item["kind"] == "negative_control"}
    if set(controls.get("adversarial_ids", [])) != adversarial:
        errors.append("adversarial controls do not cover exactly the adversarial fixtures")
    if set(controls.get("negative_ids", [])) != negative:
        errors.append("negative controls do not cover exactly the negative fixtures")
    integration_ids = {item["fixture_id"] for item in fixtures if item["kind"] == "integration"}
    if {case["case_id"] for case in integrations.get("cases", [])} != integration_ids:
        errors.append("integration cases do not cover exactly the integration fixtures")
    return {
        "evaluation_set_id": catalog.get("evaluation_set_id"),
        "fixture_count": len(fixtures),
        "fixture_counts": observed_counts,
        "rule_count": len(rule_ids),
        "crosswalk_rows": len(crosswalk.get("rows", [])),
        "errors": errors,
        "pass": not errors,
    }


def _list(value: Any) -> list[str]:
    return list(value or [])


def score_fixture(fixture: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    gold = fixture["gold"]
    mismatches: list[str] = []
    if candidate.get("release_status") != gold["expected_release_status"]:
        mismatches.append("release_status")
    for field, gold_key in (
        ("rule_ids", "expected_rule_ids"),
        ("interventions", "expected_interventions"),
        ("statuses", "expected_statuses"),
        ("hooks", "expected_hooks"),
        ("routes", "expected_routes"),
    ):
        if gold_key in gold and set(_list(candidate.get(field))) != set(_list(gold[gold_key])):
            mismatches.append(field)
    forbidden = set(_list(gold.get("must_not_emit_rule_ids")))
    emitted = set(_list(candidate.get("rule_ids")))
    if forbidden.intersection(emitted):
        mismatches.append("forbidden_rule_ids")
    return {"fixture_id": fixture["fixture_id"], "pass": not mismatches, "mismatches": mismatches}


def gold_candidate(fixture: dict[str, Any]) -> dict[str, Any]:
    gold = fixture["gold"]
    return {
        "release_status": gold["expected_release_status"],
        "rule_ids": gold["expected_rule_ids"],
        "interventions": gold["expected_interventions"],
        "statuses": gold.get("expected_statuses", []),
        "hooks": gold.get("expected_hooks", []),
        "routes": gold.get("expected_routes", []),
    }


def self_test() -> dict[str, Any]:
    fixtures = fixture_map()
    details = [score_fixture(item, gold_candidate(item)) for item in fixtures.values()]
    zero_tolerance_ids = [
        item["fixture_id"]
        for item in fixtures.values()
        if item["kind"] in {"adversarial", "negative_control"}
    ]
    zero_tolerance_passed = sum(next(result for result in details if result["fixture_id"] == fid)["pass"] for fid in zero_tolerance_ids)
    passed = sum(result["pass"] for result in details)
    return {
        "fixture_count": len(details),
        "passed_count": passed,
        "scored_count": len(details),
        "accuracy": passed / len(details) if details else 0.0,
        "pass": passed == len(details),
        "zero_tolerance": {"passed": zero_tolerance_passed, "total": len(zero_tolerance_ids)},
        "details": details,
    }


def score_file(path: Path) -> dict[str, Any]:
    candidate_data = load(path)
    candidates = candidate_data.get("candidates", candidate_data)
    fixtures = fixture_map()
    details = []
    for fixture_id, candidate in candidates.items():
        if fixture_id not in fixtures:
            details.append({"fixture_id": fixture_id, "pass": False, "mismatches": ["unknown_fixture"]})
            continue
        details.append(score_fixture(fixtures[fixture_id], candidate))
    passed = sum(result["pass"] for result in details)
    return {"fixture_count": len(details), "passed_count": passed, "accuracy": passed / len(details) if details else 0.0, "pass": passed == len(details), "details": details}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-suite", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--score", type=Path)
    args = parser.parse_args()
    output: dict[str, Any] = {}
    if args.validate_suite:
        output["suite_validation"] = validate_suite()
    if args.self_test:
        output["self_test"] = self_test()
    if args.score:
        output["candidate_score"] = score_file(args.score)
    if not output:
        output = {"suite_validation": validate_suite(), "self_test": self_test()}
    print(json.dumps(output, indent=2, sort_keys=True))
    if any(not section.get("pass", False) for section in output.values() if isinstance(section, dict) and "pass" in section):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
