# Obsidian portfolio automation

This repository can publish a GitHub-friendly view of the CCNA Obsidian vault without changing the vault itself.

## What is published

- Study notes are copied to `notes/` while preserving topic folders.
- The Anki and Packet Tracer Markdown dashboards are copied to `progress/`.
- Obsidian-only wiki links are converted to readable text.
- `ACTIVITY.md` and the README recent-activity section are regenerated from vault modification times.

The sync excludes Obsidian internals, trash, local tracker state, and Packet Tracer binaries. Add this frontmatter to any Markdown note that should stay private:

```yaml
---
publish: false
---
```

The script also stops before writing when it recognizes a high-confidence private-key or service-token pattern. This is a backstop, not a substitute for reviewing the draft pull request.

## Manual use

Preview changes:

```bash
python3 automation/sync_obsidian.py --vault "$HOME/Documents/CCNA" --check
```

Run the full sync, commit, push, and draft-PR workflow from the dedicated `agent/obsidian-sync` worktree:

```bash
automation/run_sync.sh
```

The full workflow requires an authenticated GitHub CLI session. Repair an expired session with:

```bash
gh auth refresh -h github.com
```

## Schedule

`automation/install_launch_agent.sh` installs a macOS LaunchAgent that runs daily at 8:00 PM local time. It writes operational output to `~/Library/Logs/ccna-obsidian-sync.log` and will not publish when the GitHub login is unavailable or the automation worktree has uncommitted changes.
