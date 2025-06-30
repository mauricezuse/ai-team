#!/bin/sh
# setup_hooks.sh: Installs the commit-msg hook for git
# Usage: ./setup_hooks.sh (run from repo root)

if [ ! -d .git ]; then
  echo "Error: .git directory not found. Run this script from the root of your git repository."
  exit 1
fi

cp .githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg

echo "commit-msg hook installed successfully." 