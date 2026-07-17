#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("sync_obsidian.py")
SPEC = importlib.util.spec_from_file_location("sync_obsidian", MODULE_PATH)
sync_obsidian = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_obsidian)


class SyncObsidianTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.vault = root / "vault"
        self.repo = root / "repo"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.repo / ".git").mkdir(parents=True)
        (self.repo / "README.md").write_text(
            "# Portfolio\n\n## Current snapshot\n\n- **Current topic:** Old\n\n## Portfolio sections\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def write_note(self, relative: str, content: str) -> None:
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_sync_publishes_notes_and_updates_readme(self):
        self.write_note(
            "STP/STP.md",
            "# STP\n\nSee [[VLANs 802.1Q|VLAN notes]] and [[VLANs 802.1Q]].\n",
        )
        result = sync_obsidian.sync(self.vault, self.repo, check=False)
        self.assertEqual(result, 0)
        self.assertIn("See [VLAN notes](<VLANs 802.1Q.md>) and", (self.repo / "notes/STP/STP.md").read_text())
        self.assertIn("[VLANs 802.1Q](<VLANs 802.1Q.md>)", (self.repo / "notes/STP/STP.md").read_text())
        readme = (self.repo / "README.md").read_text()
        self.assertIn("- **Current topic:** STP", readme)
        self.assertIn(sync_obsidian.README_START, readme)
        self.assertLess(readme.index(sync_obsidian.README_START), readme.index("## Portfolio sections"))

    def test_publish_false_is_private(self):
        self.write_note("Private.md", "---\npublish: false\n---\n# Private\n")
        self.write_note("Public.md", "# Public\n")
        sync_obsidian.sync(self.vault, self.repo, check=False)
        self.assertFalse((self.repo / "notes/Private.md").exists())
        self.assertTrue((self.repo / "notes/Public.md").exists())

    def test_secret_pattern_stops_sync(self):
        self.write_note("Token.md", "# Token\n\nghp_abcdefghijklmnopqrstuvwxyz123456\n")
        with self.assertRaises(RuntimeError):
            sync_obsidian.build_outputs(self.vault, self.repo)


if __name__ == "__main__":
    unittest.main()
