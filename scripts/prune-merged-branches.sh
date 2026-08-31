#!/usr/bin/env bash
# Delete remote cursor/* branches already merged into main.
# Safe to re-run; skips branches that are not fully merged.
set -euo pipefail

git fetch origin --prune
mapfile -t merged < <(git branch -r --merged origin/main | sed 's/^[* ]*//' | grep '^origin/cursor/' || true)

if [ "${#merged[@]}" -eq 0 ]; then
  echo "No merged cursor/* branches to prune."
  exit 0
fi

echo "Merged cursor branches to delete:"
printf '  %s\n' "${merged[@]}"
read -r -p "Delete these remote branches? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

for ref in "${merged[@]}"; do
  branch="${ref#origin/}"
  git push origin --delete "$branch"
done

echo "Done. Remaining cursor branches:"
git branch -r | grep cursor/ || echo "  (none)"
