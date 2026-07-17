#!/usr/bin/env python3
"""Publish a safe, GitHub-friendly view of the CCNA Obsidian vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


EXCLUDED_PARTS = {".obsidian", ".trash", ".git", ".anki-sync", ".packet-tracer-tracker"}
PROGRESS_SOURCES = {
    Path("Anki Progress/Anki Progress Dashboard.md"): Path("progress/anki.md"),
    Path("Packet Tracer Progress/Lab Status.md"): Path("progress/lab-status.md"),
    Path("Packet Tracer Progress/Packet Tracer Dashboard.md"): Path("progress/packet-tracer.md"),
}
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


def github_friendly(text: str) -> str:
    """Replace Obsidian-only links with readable labels without exposing local paths."""

    def replace_embed(match: re.Match[str]) -> str:
        target = match.group(1).replace("\\|", "|")
        label = target.split("|", 1)[-1]
        return f"*{label}*"

    def replace_link(match: re.Match[str]) -> str:
        target = match.group(1).replace("\\|", "|")
        return target.split("|", 1)[-1]

    text = re.sub(r"!\[\[([^\]]+)\]\]", replace_embed, text)
    text = re.sub(r"\[\[([^\]]+)\]\]", replace_link, text)
    return text.rstrip() + "\n"


def progress_friendly(relative_source: Path, text: str) -> str:
    """Remove local operating instructions that do not belong in the public portfolio."""
    if relative_source == Path("Anki Progress/Anki Progress Dashboard.md"):
        text = text.split("\n## How to use this dashboard", 1)[0].rstrip() + "\n"
    return github_friendly(text)


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


def activity_markdown(items: list[tuple[Path, Path]]) -> str:
    rows = []
    for source, destination in sorted(items, key=lambda item: item[0].stat().st_mtime, reverse=True):
        changed = datetime.fromtimestamp(source.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M %Z")
        area = source.parent.name
        label = source.stem
        href = quote(destination.as_posix(), safe="/")
        rows.append(f"| {changed} | {area} | [{label}]({href}) |")

    return "\n".join(
        [
            "# Recent CCNA Learning Activity",
            "",
            "This page is generated from publishable activity in the CCNA Obsidian vault.",
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
    if content_items:
        current_topic = content_items[0][0].parent.name
        readme = re.sub(r"(?m)^\*\*Current topic:\*\*.*$", f"**Current topic:** {current_topic}", readme)

    recent_lines = []
    for source, destination in ordered[:5]:
        href = quote(destination.as_posix(), safe="/")
        recent_lines.append(f"- [{source.stem}]({href})")

    block = "\n".join(
        [
            README_START,
            "## Recent Activity",
            "",
            *recent_lines,
            "",
            "See [the complete activity log](ACTIVITY.md) and the [progress dashboards](progress/).",
            README_END,
        ]
    )

    if README_START in readme and README_END in readme:
        pattern = re.compile(re.escape(README_START) + r".*?" + re.escape(README_END), re.DOTALL)
        return pattern.sub(block, readme)

    anchor = "\n## Labs and Projects"
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
        destination = Path("notes") / source.relative_to(vault)
        outputs[destination] = github_friendly(text)
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
        if relative.parts[0] not in {"notes", "progress"}:
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
