"""Opening the brief in Obsidian: only a file inside a vault opens, through the `obsidian://` URI."""

import pytest
import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote


pytestmark = pytest.mark.unit

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "open_brief.py"
spec = importlib.util.spec_from_file_location("open_brief", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class OpenBriefTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()
        self.launched = []
        original = app.launch
        app.launch = self.launched.append
        self.addCleanup(setattr, app, "launch", original)

    def brief(self, vault):
        plan = self.dir / "repo" / "docs" / "plans" / "2026-01-01 my plan"
        plan.mkdir(parents=True)
        if vault:
            (self.dir / "repo" / ".obsidian").mkdir()
        path = plan / "brief.md"
        path.write_text("# Brief\n", encoding="utf-8")
        return path

    def run_open(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = app.main([str(arg) for arg in args])
        return code, out.getvalue(), err.getvalue()

    def test_check_names_the_vault_and_opens_nothing(self):
        code, out, _ = self.run_open(self.brief(vault=True), "--check")
        self.assertEqual(code, app.OK)
        self.assertEqual(out.strip(), "VAULT %s" % (self.dir / "repo"))
        self.assertEqual(self.launched, [])

    def test_a_brief_in_a_vault_opens_by_its_encoded_absolute_path(self):
        path = self.brief(vault=True)
        code, out, _ = self.run_open(path)
        self.assertEqual(code, app.OK)
        (uri,) = self.launched
        prefix = "obsidian://open?path="
        self.assertTrue(uri.startswith(prefix))
        self.assertNotIn(" ", uri)
        self.assertNotIn("/", uri[len(prefix):])
        self.assertEqual(unquote(uri[len(prefix):]), str(path))
        self.assertIn("OPENED " + uri, out)

    def test_a_brief_outside_any_vault_is_refused_and_opens_nothing(self):
        for args in (["--check"], []):
            code, _, err = self.run_open(self.brief(vault=False), *args)
            self.assertEqual(code, app.NO_VAULT)
            self.assertIn("NO VAULT", err)
            self.assertEqual(self.launched, [])
            self.tmp.cleanup()
            self.dir.mkdir()

    def test_a_missing_brief_is_refused(self):
        (self.dir / ".obsidian").mkdir()
        code, _, err = self.run_open(self.dir / "brief.md")
        self.assertEqual(code, app.NO_VAULT)
        self.assertIn("NO VAULT", err)


if __name__ == "__main__":
    unittest.main()
