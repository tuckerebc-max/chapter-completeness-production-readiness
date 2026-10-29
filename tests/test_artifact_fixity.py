"""Synthetic CLI and adversarial tests; no remote writes or external source data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_artifact_fixity.py"
spec = importlib.util.spec_from_file_location("fixity", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class FixityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.current = b"synthetic packet revision two\n"
        self.old = b"synthetic packet revision one\n"
        for name, body in [("candidate", self.current), ("saved", self.current), ("old", self.old)]:
            (self.root / name).write_bytes(body)
        self.sha = hashlib.sha256(self.current).hexdigest()
        self.oldsha = hashlib.sha256(self.old).hexdigest()
        ident = {"artifact_id": "packet", "version_id": "v2", "sha256": self.sha}
        self.data = {"contract_version": guard.CONTRACT,
                     "target": dict(ident, authority_ref="synthetic-owner"),
                     "candidate": {"path": "candidate"},
                     "saved": dict(ident, path="saved", receipt_ref="synthetic-save"),
                     "review": dict(ident, review_ref="synthetic-review")}

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, data=None, text=None):
        p = self.root / "input.json"
        p.write_text(text if text is not None else json.dumps(data or self.data))
        out = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
        return out.returncode, json.loads(out.stdout)

    def codes(self, result):
        return {item["code"] for item in result["findings"]}

    def test_success(self):
        code, out = self.cli()
        self.assertEqual((code, out["status"]), (0, "pass"))
        self.assertIn("acceptance", out["not_established"])

    def test_old_receipt_is_history_not_delivery_failure(self):
        self.data["historical_receipts"] = [dict(self.data["target"], version_id="v1", sha256=self.oldsha)]
        item = self.data["historical_receipts"][0]
        item["receipt_ref"] = item.pop("authority_ref")
        code, out = self.cli()
        self.assertEqual(code, 0)
        self.assertEqual(out["historical_receipts"][0]["classification"], "different_revision")

    def test_changed_saved_bytes(self):
        (self.root / "saved").write_bytes(self.old)
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("saved_bytes_mismatch", self.codes(out))
        self.assertIn("saved_receipt_bytes_mismatch", self.codes(out))

    def test_stale_review(self):
        self.data["review"].update(version_id="v1", sha256=self.oldsha)
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("review_version_mismatch", self.codes(out))
        self.assertIn("review_digest_mismatch", self.codes(out))

    def test_stale_saved_receipt_not_blind_retry(self):
        self.data["saved"].update(version_id="v1", sha256=self.oldsha)
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("saved_version_mismatch", self.codes(out))
        self.assertNotIn("saved_bytes_mismatch", self.codes(out))

    def test_unreviewed_candidate_change(self):
        (self.root / "candidate").write_bytes(self.old)
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("candidate_bytes_mismatch", self.codes(out))

    def test_missing_saved(self):
        self.data["saved"]["path"] = "unavailable"
        self.assertEqual(self.cli()[0], 2)

    def test_missing_required_review(self):
        self.data.pop("review")
        self.assertEqual(self.cli()[0], 2)

    def test_unknown_fields(self):
        self.data["release_approved"] = True
        self.assertEqual(self.cli()[0], 2)

    def test_blank_identity(self):
        self.data["target"]["version_id"] = " "
        self.assertEqual(self.cli()[0], 2)

    def test_bad_digest(self):
        self.data["target"]["sha256"] = "unverified"
        self.assertEqual(self.cli()[0], 2)

    def test_wrong_artifact(self):
        self.data["saved"]["artifact_id"] = "unrelated"
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("saved_artifact_mismatch", self.codes(out))

    def test_same_copy_not_round_trip(self):
        self.data["saved"]["path"] = "candidate"
        self.assertEqual(self.cli()[0], 2)

    def test_absolute_path_rejected(self):
        self.data["saved"]["path"] = str(self.root / "saved")
        self.assertEqual(self.cli()[0], 2)

    def test_path_escape_rejected(self):
        self.data["saved"]["path"] = "../"
        self.assertEqual(self.cli()[0], 2)

    def assert_blocked_process(self, path):
        out = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(out.returncode, 2)
        self.assertEqual(out.stderr, "")
        result = json.loads(out.stdout)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("invalid_or_unavailable_input", self.codes(result))

    def test_candidate_symlink_loop_is_json_blocked(self):
        (self.root / "loop").symlink_to("loop")
        self.data["candidate"]["path"] = "loop"
        path = self.root / "input.json"
        path.write_text(json.dumps(self.data))
        self.assert_blocked_process(path)

    def test_saved_symlink_loop_is_json_blocked(self):
        (self.root / "loop").symlink_to("loop")
        self.data["saved"]["path"] = "loop"
        path = self.root / "input.json"
        path.write_text(json.dumps(self.data))
        self.assert_blocked_process(path)

    def test_manifest_symlink_loop_is_json_blocked(self):
        path = self.root / "manifest-loop.json"
        path.symlink_to(path.name)
        self.assert_blocked_process(path)

    def test_root_symlink_loop_is_rejected(self):
        path = self.root / "root-loop"
        path.symlink_to(path.name)
        # Python 3.13+ raises OSError; earlier pathlib uses RuntimeError,
        # which the helper normalizes to InvalidInput rather than leaking.
        with self.assertRaises((guard.InvalidInput, OSError)):
            guard.check(self.data, path)

    def test_symlink_escape_remains_blocked(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "outside"
            target.write_bytes(self.current)
            (self.root / "escape").symlink_to(target)
            self.data["saved"]["path"] = "escape"
            code, out = self.cli()
            self.assertEqual((code, out["status"]), (2, "blocked"))
            self.assertIn("escapes the manifest directory", out["findings"][0]["reason"])
            self.assertEqual(target.read_bytes(), self.current)

    def test_same_version_conflicting_history(self):
        item = dict(self.data["saved"], sha256=self.oldsha)
        item.pop("path")
        self.data["historical_receipts"] = [item]
        code, out = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("same_version_receipt_conflict", self.codes(out))

    def test_duplicate_json_keys(self):
        self.assertEqual(self.cli(text='{"contract_version":"a","contract_version":"b"}')[0], 2)

    def test_no_mutation(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.cli()
        for name, body in before.items():
            self.assertEqual((self.root / name).read_bytes(), body)

    def test_supplied_authority_does_not_become_verified(self):
        out = guard.check(self.data, self.root)
        self.assertIn("source authority", out["not_established"])
        self.assertIn("remote currentness", out["not_established"])

if __name__ == "__main__":
    unittest.main(verbosity=2)

