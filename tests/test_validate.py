"""Test the CLI against disposable copies of the manifests, without Kubernetes."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('apps', 'exemples', 'argocd', 'scripts'):
            shutil.copytree(ROOT / folder, self.root / folder)

    def run_check(self, optimized=False):
        return subprocess.run(
            [sys.executable, *(['-O'] if optimized else []),
             str(self.root / 'scripts/validate.py')],
            capture_output=True, text=True, timeout=10)

    def change(self, before, after):
        path = self.root / 'apps/taskflow/rollout.yaml'
        original = path.read_text()
        self.assertIn(before, original)
        path.write_text(original.replace(before, after))

    def test_valid_manifests(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.run_check(optimized)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_replicas_fail_even_with_optimization(self):
        self.change('replicas: 4', 'replicas: 1')
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.run_check(optimized)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('4 replicas requis', result.stderr)

    def test_lookalike_registry_is_rejected(self):
        self.change('ghcr.io/', 'ghcrXio/')
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_missing_workload_is_rejected(self):
        (self.root / 'apps/taskflow/rollout.yaml').unlink()
        self.assertNotEqual(self.run_check().returncode, 0)


if __name__ == '__main__':
    unittest.main()
