#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_CLI_VERSION="${SKILLS_CLI_VERSION:-1.5.17}"
VAULT="$(mktemp -d "${TMPDIR:-/tmp}/llm-wiki-smoke.XXXXXX")"

cleanup() {
  rm -rf -- "$VAULT"
}
trap cleanup EXIT

mkdir -p "$VAULT/.obsidian"

cd "$VAULT"
npx --yes "skills@${SKILLS_CLI_VERSION}" add "$REPO_ROOT" \
  --skill '*' \
  -a universal \
  -a claude-code \
  -y

for skill in wiki-configure wiki-ingest wiki-maintain wiki-query; do
  test -f ".agents/skills/${skill}/SKILL.md"
  test -L ".claude/skills/${skill}"
done

CLI="$VAULT/.agents/skills/wiki-configure/scripts/wiki.py"
python3 "$CLI" --vault "$VAULT" init
python3 "$CLI" --vault "$VAULT" doctor
python3 "$CLI" --vault "$VAULT" lint --strict

printf 'release smoke evidence\n' > "$VAULT/inbox/release-smoke.txt"
python3 "$CLI" --vault "$VAULT" capture "$VAULT/inbox/release-smoke.txt" --classification public
python3 "$CLI" --vault "$VAULT" status
python3 "$CLI" --vault "$VAULT" lint --strict

test -f "$VAULT/skills-lock.json"
test -n "$(find "$VAULT/raw/sources" -path '*/original/release-smoke.txt' -print -quit)"

echo "npx skills smoke test passed"
