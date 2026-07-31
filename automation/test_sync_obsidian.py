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
            "# Portfolio\n\n## Current snapshot\n\n"
            "- **Current topic:** Old\n"
            "- **Packet Tracer labs:** 0 of 0 marked complete\n"
            "- **Snapshot date:** January 1, 2000\n\n"
            "## Portfolio sections\n",
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
        self.write_note("STP/VLANs 802.1Q.md", "# VLANs\n")
        result = sync_obsidian.sync(self.vault, self.repo, check=False)
        self.assertEqual(result, 0)
        self.assertIn("See [VLAN notes](<VLANs 802.1Q.md>) and", (self.repo / "notes/STP/STP.md").read_text())
        self.assertIn("[VLANs 802.1Q](<VLANs 802.1Q.md>)", (self.repo / "notes/STP/STP.md").read_text())
        readme = (self.repo / "README.md").read_text()
        self.assertIn("- **Current topic:** STP", readme)
        self.assertIn(sync_obsidian.README_START, readme)
        self.assertLess(readme.index(sync_obsidian.README_START), readme.index("## Portfolio sections"))

    def test_notes_root_is_not_repeated_in_public_path(self):
        self.write_note(
            "Notes/STP/STP.md",
            "# STP\n\nSee [[Notes/VLANs/VLANs|VLAN notes]].\n",
        )
        self.write_note("Notes/VLANs/VLANs.md", "# VLANs\n")
        sync_obsidian.sync(self.vault, self.repo, check=False)
        published = self.repo / "notes/STP/STP.md"
        self.assertTrue(published.exists())
        self.assertFalse((self.repo / "notes/Notes/STP/STP.md").exists())
        self.assertIn("[VLAN notes](<../VLANs/VLANs.md>)", published.read_text())

    def test_note_aliases_resolve_across_folders_and_missing_notes_stay_plain(self):
        self.write_note(
            "Notes/Dynamic Routing/Dynamic Routing - Fundamentals.md",
            "---\ntitle: Dynamic Routing - Fundamentals\naliases:\n"
            "  - Dynamic Routing\n---\n# Dynamic Routing\n",
        )
        self.write_note(
            "Notes/OSPF/OSPF.md",
            "# OSPF\n\nSee [[Dynamic Routing]], "
            "[[VLANs Part 2 - Trunks, 802.1Q, and ROAS]], "
            "and [[Static Routing]].\n",
        )
        self.write_note(
            "Notes/VLANs/VLANs Part 2 - Trunks, 802.1Q, and ROAS.md",
            "# VLANs Part 2\n",
        )

        sync_obsidian.sync(self.vault, self.repo, check=False)

        published = (self.repo / "notes/OSPF/OSPF.md").read_text()
        self.assertIn(
            "[Dynamic Routing](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)",
            published,
        )
        self.assertIn(
            "[VLANs Part 2 - Trunks, 802.1Q, and ROAS]"
            "(<../VLANs/VLANs Part 2 - Trunks, 802.1Q, and ROAS.md>)",
            published,
        )
        self.assertIn("and Static Routing.", published)
        self.assertNotIn("[Static Routing]", published)

    def test_udemy_dashboard_publishes_as_progress(self):
        self.write_note(
            "Udemy Progress/Udemy Progress Dashboard.md",
            "---\ntags: [ccna, progress]\ncssclasses: [local-dashboard]\n---\n\n"
            "# Udemy Progress\n\n33% complete.\n\n"
            "Related: [[Packet Tracer Progress/Packet Tracer Dashboard"
            "|Packet Tracer Progress]].\n\n"
            "## How to update this dashboard\n\nLocal steps.\n",
        )
        sync_obsidian.sync(self.vault, self.repo, check=False)
        published = self.repo / "progress/udemy.md"
        self.assertTrue(published.exists())
        self.assertIn("33% complete", published.read_text())
        self.assertNotIn("Local steps", published.read_text())
        self.assertNotIn("cssclasses", published.read_text())
        self.assertNotIn("tags:", published.read_text())
        self.assertIn(
            "[Packet Tracer Progress](<packet-tracer.md>)",
            published.read_text(),
        )

    def test_lab_status_becomes_the_labs_readme(self):
        self.write_note(
            "Packet Tracer Progress/Lab Status.md",
            "# Lab Status\n\n"
            "- [x] [[Packet Tracer Progress/Labs/Day 01 Lab - Introduction.pkt"
            "|Day 01 Lab - Introduction]]\n"
            "- [ ] [[Packet Tracer Progress/Labs/Day 02 Lab - Switching.pkt"
            "|Day 02 Lab - Switching]]\n",
        )
        (self.repo / "progress").mkdir()
        (self.repo / "progress/lab-status.md").write_text("old duplicate\n", encoding="utf-8")
        (self.repo / sync_obsidian.MANIFEST).write_text(
            '{"managed_files": ["progress/lab-status.md"]}\n',
            encoding="utf-8",
        )

        sync_obsidian.sync(self.vault, self.repo, check=False)

        published = self.repo / "labs/README.md"
        self.assertTrue(published.exists())
        self.assertIn("| Tracked labs | **2** |", published.read_text())
        self.assertIn("| Complete | **1** |", published.read_text())
        self.assertIn("| 2 | Switching | Ready |", published.read_text())
        self.assertIn("[lab reflection template](REFLECTION_TEMPLATE.md)", published.read_text())
        self.assertFalse((self.repo / "progress/lab-status.md").exists())
        manifest = (self.repo / sync_obsidian.MANIFEST).read_text()
        self.assertIn('"labs/README.md"', manifest)
        self.assertNotIn('"progress/lab-status.md"', manifest)

    def test_packet_dashboard_links_to_combined_lab_index(self):
        self.write_note(
            "Packet Tracer Progress/Packet Tracer Dashboard.md",
            "---\ntags: [ccna, progress]\ncssclasses: [local-dashboard]\n---\n\n"
            "Use the [[Packet Tracer Progress/Lab Status|completion checklist]].\n\n"
            "| File |\n|---|\n"
            "| [[Packet Tracer Progress/Labs/Day 28 Lab - OSPF (Part 3).pkt"
            "\\|Open lab]] |\n",
        )
        sync_obsidian.sync(self.vault, self.repo, check=False)
        published = (self.repo / "progress/packet-tracer.md").read_text()
        self.assertIn("[completion checklist](<../labs/README.md>)", published)
        self.assertIn(
            "[Open lab](<../labs/Day 28 Lab - OSPF (Part 3).pkt>)",
            published,
        )
        self.assertNotIn("cssclasses", published)

    def test_readme_snapshot_and_progress_index_are_generated(self):
        self.write_note(
            "Packet Tracer Progress/Packet Tracer Dashboard.md",
            "# Packet Tracer\n\n"
            "| Today | Total time | Completed | Started |\n"
            "|---:|---:|---:|---:|\n"
            "| 20 min | 3h | 18/20 | 6/20 |\n",
        )
        self.write_note(
            "Udemy Progress/Udemy Progress Dashboard.md",
            "# Udemy\n\n> **Day 28 — OSPF Part 3**\n",
        )

        sync_obsidian.sync(self.vault, self.repo, check=False)

        readme = (self.repo / "README.md").read_text()
        self.assertIn("- **Current topic:** Day 28 — OSPF Part 3", readme)
        self.assertIn("- **Packet Tracer labs:** 18 of 20 marked complete", readme)
        self.assertNotIn("January 1, 2000", readme)
        self.assertIn("[progress dashboard index](progress/README.md)", readme)

        progress_index = (self.repo / "progress/README.md").read_text()
        self.assertIn("[Anki](anki.md)", progress_index)
        self.assertIn("[Packet Tracer](packet-tracer.md)", progress_index)
        self.assertIn("[Udemy](udemy.md)", progress_index)

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
