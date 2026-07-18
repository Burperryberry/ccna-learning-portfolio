#!/bin/zsh
set -euo pipefail

repo_dir="${0:A:h:h}"
label="com.burperryberry.ccna-anki-sync"
source_plist="$repo_dir/automation/$label.plist"
target_plist="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"
run_sync="$repo_dir/automation/run_anki_sync.sh"
collection="${ANKI_COLLECTION:-$HOME/Library/Application Support/Anki2/User 1/collection.anki2}"
log_file="$HOME/Library/Logs/ccna-anki-sync.log"

if ! gh auth status -h github.com >/dev/null 2>&1; then
  print -u2 "GitHub authentication is unavailable. Run: gh auth refresh -h github.com"
  exit 2
fi

if [[ ! -f "$collection" ]]; then
  print -u2 "Anki collection not found: $collection"
  exit 2
fi

plutil -lint "$source_plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
sed \
  -e "s|__RUN_SYNC__|$run_sync|g" \
  -e "s|__COLLECTION__|$collection|g" \
  -e "s|__LOG__|$log_file|g" \
  "$source_plist" > "$target_plist"
plutil -lint "$target_plist"
launchctl bootout "$domain/$label" >/dev/null 2>&1 || true
launchctl bootstrap "$domain" "$target_plist"
print "Installed $label; it will run daily at 8:00 PM local time."
