#!/bin/zsh
set -euo pipefail

repo_dir="${0:A:h:h}"
label="com.burperryberry.ccna-obsidian-sync"
source_plist="$repo_dir/automation/$label.plist"
target_plist="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"
run_sync="$repo_dir/automation/run_sync.sh"
vault_dir="${OBSIDIAN_VAULT:-$HOME/Documents/CCNA}"
log_file="$HOME/Library/Logs/ccna-obsidian-sync.log"

if ! gh auth status >/dev/null 2>&1; then
  print -u2 "GitHub authentication is unavailable. Run: gh auth refresh -h github.com"
  exit 2
fi

plutil -lint "$source_plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
sed \
  -e "s|__RUN_SYNC__|$run_sync|g" \
  -e "s|__VAULT__|$vault_dir|g" \
  -e "s|__LOG__|$log_file|g" \
  "$source_plist" > "$target_plist"
plutil -lint "$target_plist"
launchctl bootout "$domain/$label" >/dev/null 2>&1 || true
launchctl bootstrap "$domain" "$target_plist"
print "Installed $label; it will run daily at 8:00 PM local time."
