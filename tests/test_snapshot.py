"""Exercise the evidence script with a fake kubectl; no cluster is contacted."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/snapshot.py'


class SnapshotTests(unittest.TestCase):
    def test_wrong_context_stops_before_reading_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / 'kubectl'
            log = root / 'calls'
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\necho other-project\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=f'{root}:{os.environ["PATH"]}', CALL_LOG=str(log))
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    log.unlink(missing_ok=True)
                    result = subprocess.run(
                        [sys.executable, *(['-O'] if optimized else []), str(SCRIPT)],
                        env=env, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, '')
                    self.assertIn('kind-cicd', result.stderr)
                    self.assertEqual(log.read_text(), 'config current-context\n')

    def test_unresponsive_kubectl_has_a_timeout_and_clear_error(self):
        with patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired('kubectl', 30)) as call:
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(SCRIPT), run_name='__main__')
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(call.call_args.kwargs['timeout'], 30)
            self.assertIn('ERREUR kubectl', errors.getvalue())

    def test_valid_context_produces_json(self):
        app = {'spec': {'source': {'repoURL': 'https://example.org/lab.git'}}}
        responses = ['kind-cicd\n', json.dumps(app)] + [json.dumps({'items': []})] * 5
        with patch('subprocess.check_output', side_effect=responses) as calls:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                runpy.run_path(str(SCRIPT), run_name='__main__')
        result = json.loads(output.getvalue())
        self.assertEqual(result['application']['source'], app['spec']['source'])
        self.assertEqual(result['pod'], [])
        self.assertEqual(calls.call_count, 7)


if __name__ == '__main__':
    unittest.main()
