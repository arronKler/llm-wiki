#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_CLI_VERSION="${SKILLS_CLI_VERSION:-1.5.17}"
VAULT="$(mktemp -d "${TMPDIR:-/tmp}/llm-wiki-smoke.XXXXXX")"

cleanup() {
  rm -rf -- "$VAULT"
}
trap cleanup EXIT

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
python3 "$CLI" --workspace "$VAULT" init
python3 "$CLI" --workspace "$VAULT" doctor
python3 "$CLI" --workspace "$VAULT" lint --strict

printf 'release smoke evidence\n' > "$VAULT/inbox/release-smoke.txt"
python3 "$CLI" --workspace "$VAULT" capture "$VAULT/inbox/release-smoke.txt" --classification public
python3 "$CLI" --workspace "$VAULT" status
python3 "$CLI" --workspace "$VAULT" lint --strict

test -f "$VAULT/skills-lock.json"
test -n "$(find "$VAULT/raw/sources" -path '*/original/release-smoke.txt' -print -quit)"
test ! -e "$VAULT/wiki/Wiki.base"

echo "npx skills smoke test passed"
