# Portfolio automation

This repository includes separate workflows for publishing Anki progress and selected Obsidian content. The Anki workflow is the nightly GitHub sync.

## Nightly Anki progress sync

`automation/export_anki_progress.py` reads a stable temporary snapshot of the local Anki collection and generates both public dashboards:

- `progress/anki.md`
- `flashcard-progress/Anki Progress Dashboard.md`

Only aggregate statistics are exported: workload counts, review totals, study time, answer-button success rates, streaks, and deck-level weak-topic signals. Card questions, answers, note fields, and raw review history are never written to the repository. The live Anki database is opened only through a copied SQLite/WAL snapshot and is never modified.

The installed runtime uses a dedicated checkout under `~/Library/Application Support/CCNA Sync/`. Keeping the runner and checkout outside `Documents` prevents macOS privacy controls from blocking the background LaunchAgent.

Run the complete Anki export, commit, push, and draft-PR workflow manually:

```bash
"$HOME/Library/Application Support/CCNA Sync/repo/automation/run_anki_sync.sh"
```

Install or reload the 8:00 PM local-time schedule:

```bash
"$HOME/Library/Application Support/CCNA Sync/repo/automation/install_anki_launch_agent.sh"
```

Operational output is written to `~/Library/Logs/ccna-anki-sync.log`. The job refuses to publish if GitHub authentication is unavailable, the checkout has uncommitted changes, or its branch has diverged from `origin/main`.

## Obsidian portfolio export

The separate Obsidian generator can publish selected study notes and GitHub-friendly progress pages without changing the vault itself.

It excludes Obsidian internals, trash, local tracker state, and Packet Tracer binaries. Add this frontmatter to any Markdown note that should stay private:

```yaml
---
publish: false
---
```

Preview Obsidian changes:

```bash
python3 automation/sync_obsidian.py --vault "$HOME/Documents/CCNA" --check
```

The previous Obsidian LaunchAgent is not used for the nightly Anki sync because macOS denied its background process access to the checkout under `Documents`.
