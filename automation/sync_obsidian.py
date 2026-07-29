#!/usr/bin/env python3
"""Publish a safe, GitHub-friendly view of the CCNA Obsidian vault."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


EXCLUDED_PARTS = {".obsidian", ".trash", ".git", ".anki-sync", ".packet-tracer-tracker"}
PROGRESS_SOURCES = {
    Path("Anki Progress/Anki Progress Dashboard.md"): Path("progress/anki.md"),
    Path("Packet Tracer Progress/Lab Status.md"): Path("labs/README.md"),
    Path("Packet Tracer Progress/Packet Tracer Dashboard.md"): Path("progress/packet-tracer.md"),
    Path("Udemy Progress/Udemy Progress Dashboard.md"): Path("progress/udemy.md"),
}
NOTE_ROOT = "Notes"
MANIFEST = Path(".obsidian-sync-manifest.json")
README_START = "<!-- OBSIDIAN_SYNC:START -->"
README_END = "<!-- OBSIDIAN_SYNC:END -->"

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True, help="Path to the Obsidian vault")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="Report changes without writing them")
    return parser.parse_args()


def opted_out(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    frontmatter = text[4:end]
    return bool(re.search(r"(?mi)^publish\s*:\s*(?:false|no|off)\s*$", frontmatter))


def strip_frontmatter(text: str) -> str:
    """Remove vault-only YAML metadata from a public GitHub page."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :].lstrip("\n")


def github_friendly(text: str, link_renderer=None) -> str:
    """Replace Obsidian-only links with readable labels without exposing local paths."""

    def replace_embed(match: re.Match[str]) -> str:
        target = match.group(1).replace("\\|", "|")
        label = target.split("|", 1)[-1]
        return f"*{label}*"

    def replace_link(match: re.Match[str]) -> str:
        target = match.group(1).replace("\\|", "|")
        if link_renderer is not None:
            return link_renderer(target)
        return target.split("|", 1)[-1]

    text = re.sub(r"!\[\[([^\]]+)\]\]", replace_embed, text)
    text = re.sub(r"\[\[([^\]]+)\]\]", replace_link, text)
    return text.rstrip() + "\n"


def notes_friendly(relative_source: Path, text: str) -> str:
    """Convert Obsidian note links into relative GitHub Markdown links."""

    def render_link(raw_target: str) -> str:
        target, separator, alias = raw_target.partition("|")
        path_text, heading_separator, heading = target.partition("#")
        default_label = Path(path_text).name
        if default_label.lower().endswith(".md"):
            default_label = default_label[:-3]
        label = alias if separator else (default_label or heading or target)
        label = label.replace("]", "\\]")

        if path_text:
            target_path = Path(path_text)
            if not path_text.lower().endswith(".md"):
                target_path = Path(f"{path_text}.md")
            if target_path.parts and target_path.parts[0].casefold() == NOTE_ROOT.casefold():
                target_path = Path(*target_path.parts[1:])
            if "/" not in path_text:
                target_path = relative_source.parent / target_path
            start = relative_source.parent.as_posix() or "."
            href = posixpath.relpath(target_path.as_posix(), start)
        else:
            href = ""

        if heading_separator:
            anchor = re.sub(r"[^a-z0-9 -]", "", heading.lower()).strip().replace(" ", "-")
            href = f"{href}#{anchor}"
        return f"[{label}](<{href}>)"

    return github_friendly(text, render_link)


def lab_readme(text: str) -> str:
    """Turn the vault's lab checklist into the public lab index."""
    pattern = re.compile(
        r"(?m)^- \[(?P<done>[ xX])\] "
        r"\[\[Packet Tracer Progress/Labs/(?P<file>[^|\]]+)"
        r"(?:\|(?P<label>[^\]]+))?\]\]$"
    )
    labs = []
    for match in pattern.finditer(text):
        filename = match.group("file")
        label = match.group("label") or Path(filename).stem
        day_match = re.match(r"Day\s+(\d+)\s+Lab\s+-\s+(.+)", label)
        if day_match is None:
            raise RuntimeError(f"Unrecognized Packet Tracer lab label: {label}")
        labs.append(
            {
                "day": int(day_match.group(1)),
                "name": day_match.group(2),
                "filename": filename,
                "complete": match.group("done").lower() == "x",
            }
        )

    if not labs:
        raise RuntimeError("No Packet Tracer labs were found in the lab status note")

    complete = sum(lab["complete"] for lab in labs)
    ready = len(labs) - complete
    rows = [
        f"| {lab['day']} | {lab['name']} | {'Complete' if lab['complete'] else 'Ready'} "
        f"| [Open](<{lab['filename']}>) |"
        for lab in labs
    ]
    return "\n".join(
        [
            "# Packet Tracer Labs",
            "",
            "This is the single public checklist and download index for the Cisco Packet Tracer "
            "labs tracked in the CCNA learning portfolio.",
            "",
            "## Current snapshot",
            "",
            "| Metric | Current |",
            "|---|---:|",
            f"| Tracked labs | **{len(labs)}** |",
            f"| Complete | **{complete}** |",
            f"| Ready to complete | **{ready}** |",
            f"| Lab files available in this folder | **{len(labs)} of {len(labs)}** |",
            "",
            "See the [Packet Tracer progress dashboard](../progress/packet-tracer.md) for study "
            "time and recent activity.",
            "",
            "After completing a lab, use the [lab reflection template](REFLECTION_TEMPLATE.md) "
            "to record what you configured, how you verified it, and what you learned.",
            "",
            "## Lab inventory",
            "",
            "| Day | Lab | Status | File |",
            "|---:|---|---|---|",
            *rows,
            "",
            "Packet Tracer files are binary. Download a file and open it with Cisco Packet Tracer "
            "to inspect or continue the lab. Completion is tracked manually because Packet Tracer "
            "files do not provide a dependable completion score.",
            "",
        ]
    )


def progress_friendly(relative_source: Path, text: str) -> str:
    """Remove local operating instructions that do not belong in the public portfolio."""
    if relative_source == Path("Packet Tracer Progress/Lab Status.md"):
        return lab_readme(text)
    text = strip_frontmatter(text)
    if relative_source == Path("Anki Progress/Anki Progress Dashboard.md"):
        text = text.split("\n## How to use this dashboard", 1)[0].rstrip() + "\n"
    if relative_source == Path("Packet Tracer Progress/Packet Tracer Dashboard.md"):
        text = re.sub(
            r"\[\[Packet Tracer Progress/Lab Status(?:\|([^\]]+))?\]\]",
            lambda match: f"[{match.group(1) or 'lab checklist and downloads'}]"
            "(<../labs/README.md>)",
            text,
        )
    if relative_source == Path("Udemy Progress/Udemy Progress Dashboard.md"):
        text = text.split("\n## How to update this dashboard", 1)[0].rstrip() + "\n"
    return github_friendly(text)


def progress_readme() -> str:
    return """# CCNA Progress Dashboards

This folder contains the public progress snapshots generated from the CCNA study system.

| Dashboard | What it tracks |
|---|---|
| [Anki](anki.md) | Card workload, reviews, study time, and weak-topic signals |
| [Packet Tracer](packet-tracer.md) | Lab completion, tracked practice time, and recent activity |
| [Udemy](udemy.md) | Course position, completed videos, and section progress |

The [Packet Tracer lab index](../labs/README.md) is the single checklist and download page for lab files.

These pages are generated from local dashboards. Their “Last synchronized” timestamps show when each source was most recently published.
"""


def published_note_path(relative_source: Path) -> Path:
    """Remove the vault-only Notes root from public note destinations."""
    if relative_source.parts and relative_source.parts[0].casefold() == NOTE_ROOT.casefold():
        return Path(*relative_source.parts[1:])
    return relative_source


def find_content_notes(vault: Path) -> list[Path]:
    progress_roots = {path.parts[0] for path in PROGRESS_SOURCES}
    notes: list[Path] = []
    for path in vault.rglob("*.md"):
        relative = path.relative_to(vault)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts[0] in progress_roots:
            continue
        notes.append(path)
    return sorted(notes)


def scan_for_secrets(outputs: dict[Path, str]) -> None:
    findings: list[str] = []
    for destination, text in outputs.items():
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{destination}: possible {label}")
    if findings:
        joined = "\n  - ".join(findings)
        raise RuntimeError(f"Refusing to publish possible secrets:\n  - {joined}")


def artifact_label(source: Path, destination: Path) -> str:
    if destination == Path("labs/README.md"):
        return "Packet Tracer Labs"
    return source.stem


def activity_markdown(items: list[tuple[Path, Path]]) -> str:
    ordered = sorted(items, key=lambda item: item[0].stat().st_mtime, reverse=True)
    note_items = [item for item in ordered if item[1].parts[0] == "notes"]
    progress_sources = {destination.as_posix(): source for source, destination in ordered}

    def read_progress(destination: str) -> str:
        source = progress_sources.get(destination)
        if source is None:
            return ""
        return source.read_text(encoding="utf-8")

    packet_text = read_progress("progress/packet-tracer.md")
    udemy_text = read_progress("progress/udemy.md")
    anki_text = read_progress("progress/anki.md")

    packet_match = re.search(
        r"\|\s*[^|\n]+\|\s*[^|\n]+\|\s*(\d+\s*/\s*\d+)\s*\|\s*[^|\n]+\|",
        packet_text,
    )
    udemy_match = re.search(
        r"\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*([\d.]+%)\*\*",
        udemy_text,
    )
    anki_match = re.search(
        r"\|(?:\s*\*\*\d+\*\*\s*\|){5}\s*\*\*(\d+)\*\*\s*\|",
        anki_text,
    )
    topic_match = re.search(r">\s*\*\*(Day [^*]+)\*\*", udemy_text)

    summary = [f"- **Published notes:** {len(note_items)}"]
    if topic_match:
        summary.append(f"- **Current topic:** {topic_match.group(1)}")
    if packet_match:
        summary.append(f"- **Packet Tracer:** {packet_match.group(1).replace(' ', '')} labs complete")
    if udemy_match:
        summary.append(
            f"- **Udemy:** {udemy_match.group(1)} of {udemy_match.group(2)} videos complete "
            f"({udemy_match.group(3)})"
        )
    if anki_match:
        summary.append(f"- **Anki:** {anki_match.group(1)} cards tracked")

    recent_lines = []
    for source, destination in note_items[:3]:
        href = quote(destination.as_posix(), safe="/")
        recent_lines.append(f"- [{source.stem}]({href})")

    rows = []
    for source, destination in ordered:
        changed = datetime.fromtimestamp(source.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M %Z")
        area = "Packet Tracer Labs" if destination == Path("labs/README.md") else source.parent.name
        label = artifact_label(source, destination)
        href = quote(destination.as_posix(), safe="/")
        rows.append(f"| {changed} | {area} | [{label}]({href}) |")

    return "\n".join(
        [
            "# Recent CCNA Learning Activity",
            "",
            "This page summarizes publishable study artifacts and progress from the CCNA Obsidian vault.",
            "",
            "## Current portfolio snapshot",
            "",
            *summary,
            "",
            "## Quick links",
            "",
            "- [Browse all study notes](notes/README.md)",
            "- [Download Packet Tracer labs](labs/README.md)",
            "- [Packet Tracer progress](progress/packet-tracer.md)",
            "- [Anki progress](progress/anki.md)",
            "- [Udemy progress](progress/udemy.md)",
            "",
            "## Latest learning",
            "",
            *recent_lines,
            "",
            "## Published activity",
            "",
            "| Last updated | Area | Artifact |",
            "|---|---|---|",
            *rows,
            "",
        ]
    )


def update_readme(readme: str, items: list[tuple[Path, Path]]) -> str:
    ordered = sorted(items, key=lambda item: item[0].stat().st_mtime, reverse=True)
    content_items = [item for item in ordered if item[1].parts[0] == "notes"]
    sources = {destination: source for source, destination in ordered}

    udemy_source = sources.get(Path("progress/udemy.md"))
    udemy_text = udemy_source.read_text(encoding="utf-8") if udemy_source else ""
    topic_match = re.search(r">\s*\*\*(Day [^*]+)\*\*", udemy_text)
    current_topic = topic_match.group(1) if topic_match else (
        content_items[0][0].parent.name if content_items else None
    )
    if current_topic:
        topic_pattern = re.compile(r"(?m)^(?P<prefix>\s*(?:-\s*)?\*\*Current topic:\*\*)[^\n]*$")
        readme = topic_pattern.sub(lambda match: f"{match.group('prefix')} {current_topic}", readme)

    packet_source = sources.get(Path("progress/packet-tracer.md"))
    packet_text = packet_source.read_text(encoding="utf-8") if packet_source else ""
    packet_match = re.search(
        r"\|\s*[^|\n]+\|\s*[^|\n]+\|\s*(\d+)\s*/\s*(\d+)\s*\|\s*[^|\n]+\|",
        packet_text,
    )
    if packet_match:
        lab_pattern = re.compile(
            r"(?m)^(?P<prefix>\s*(?:-\s*)?\*\*Packet Tracer labs:\*\*)[^\n]*$"
        )
        readme = lab_pattern.sub(
            lambda match: (
                f"{match.group('prefix')} {packet_match.group(1)} of "
                f"{packet_match.group(2)} marked complete"
            ),
            readme,
        )

    if ordered:
        newest = datetime.fromtimestamp(ordered[0][0].stat().st_mtime).astimezone()
        snapshot_date = f"{newest.strftime('%B')} {newest.day}, {newest.year}"
        date_pattern = re.compile(
            r"(?m)^(?P<prefix>\s*(?:-\s*)?\*\*Snapshot date:\*\*)[^\n]*$"
        )
        readme = date_pattern.sub(
            lambda match: f"{match.group('prefix')} {snapshot_date}",
            readme,
        )

    recent_lines = []
    for source, destination in ordered[:5]:
        href = quote(destination.as_posix(), safe="/")
        recent_lines.append(f"- [{artifact_label(source, destination)}]({href})")

    block = "\n".join(
        [
            README_START,
            "## Recent Activity",
            "",
            *recent_lines,
            "",
            "See [the complete activity log](ACTIVITY.md) and the "
            "[progress dashboard index](progress/README.md).",
            README_END,
        ]
    )

    if README_START in readme and README_END in readme:
        pattern = re.compile(re.escape(README_START) + r".*?" + re.escape(README_END), re.DOTALL)
        return pattern.sub(block, readme)

    for anchor in ("\n## Portfolio sections", "\n## Labs and Projects"):
        if anchor in readme:
            return readme.replace(anchor, f"\n{block}\n{anchor}", 1)
    return readme.rstrip() + f"\n\n{block}\n"


def build_outputs(vault: Path, repo: Path) -> tuple[dict[Path, str], list[tuple[Path, Path]]]:
    outputs: dict[Path, str] = {}
    activity_items: list[tuple[Path, Path]] = []

    for source in find_content_notes(vault):
        text = source.read_text(encoding="utf-8")
        if opted_out(text):
            continue
        relative_source = source.relative_to(vault)
        relative_destination = published_note_path(relative_source)
        destination = Path("notes") / relative_destination
        outputs[destination] = notes_friendly(relative_destination, text)
        activity_items.append((source, destination))

    for relative_source, destination in PROGRESS_SOURCES.items():
        source = vault / relative_source
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        if opted_out(text):
            continue
        outputs[destination] = progress_friendly(relative_source, text)
        activity_items.append((source, destination))

    if not activity_items:
        raise RuntimeError("No publishable Markdown files were found in the vault")

    outputs[Path("progress/README.md")] = progress_readme()
    outputs[Path("ACTIVITY.md")] = activity_markdown(activity_items)
    readme_path = repo / "README.md"
    if not readme_path.exists():
        raise RuntimeError(f"README not found: {readme_path}")
    outputs[Path("README.md")] = update_readme(readme_path.read_text(encoding="utf-8"), activity_items)
    scan_for_secrets(outputs)
    return outputs, activity_items


def previous_manifest(repo: Path) -> set[Path]:
    path = repo / MANIFEST
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {Path(item) for item in data.get("managed_files", [])}


def sync(vault: Path, repo: Path, check: bool) -> int:
    vault = vault.expanduser().resolve()
    repo = repo.expanduser().resolve()
    if not (vault / ".obsidian").is_dir():
        raise RuntimeError(f"Not an Obsidian vault: {vault}")
    if not (repo / ".git").exists():
        raise RuntimeError(f"Not a Git working tree: {repo}")

    outputs, _ = build_outputs(vault, repo)
    managed = set(outputs) - {Path("README.md")}
    stale = previous_manifest(repo) - managed
    changed: list[Path] = []

    for relative, content in outputs.items():
        destination = repo / relative
        old = destination.read_text(encoding="utf-8") if destination.exists() else None
        if old == content:
            continue
        changed.append(relative)
        if not check:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    for relative in sorted(stale):
        if relative.parts[0] not in {"labs", "notes", "progress"}:
            raise RuntimeError(f"Refusing to delete unexpected managed path: {relative}")
        destination = repo / relative
        if destination.exists():
            changed.append(relative)
            if not check:
                destination.unlink()

    manifest_text = json.dumps({"managed_files": sorted(path.as_posix() for path in managed)}, indent=2) + "\n"
    manifest_path = repo / MANIFEST
    old_manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None
    if old_manifest != manifest_text:
        changed.append(MANIFEST)
        if not check:
            manifest_path.write_text(manifest_text, encoding="utf-8")

    if changed:
        verb = "Would update" if check else "Updated"
        print(f"{verb} {len(changed)} file(s):")
        for path in sorted(changed):
            print(f"  {path}")
        return 1 if check else 0

    print("Obsidian sync is already up to date.")
    return 0


def main() -> int:
    args = parse_args()
    try:
        return sync(args.vault, args.repo, args.check)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
