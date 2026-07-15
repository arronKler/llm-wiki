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
python3 "$CLI" --workspace "$VAULT" --json export-capabilities --format site

printf '%s\n' \
  '---' \
  'title: Release Smoke' \
  'type: concept' \
  'classification: public' \
  'created: 2026-07-15' \
  'updated: 2026-07-15' \
  'sources: []' \
  '---' \
  '' \
  '# Release Smoke' \
  '' \
  'Installed static-site export works.' \
  '' \
  '## Verify' \
  '' \
  '```text' \
  'theme and add-ons' \
  '```' > "$VAULT/wiki/release-smoke.md"
python3 "$CLI" --workspace "$VAULT" export outputs/site --format site --title "Release Smoke Wiki" \
  --theme editorial --addon toc --addon graph --addon code-copy

test -f "$VAULT/skills-lock.json"
test -n "$(find "$VAULT/raw/sources" -path '*/original/release-smoke.txt' -print -quit)"
test ! -e "$VAULT/wiki/Wiki.base"
test -f "$VAULT/outputs/site/index.html"
test -f "$VAULT/outputs/site/pages/release-smoke.html"
test -f "$VAULT/outputs/site/export-report.json"
test -f "$VAULT/outputs/site/assets/graph-data.js"
rg -q 'data-theme="editorial"' "$VAULT/outputs/site/index.html"
rg -q 'code-copy-button' "$VAULT/outputs/site/assets/app.js"
test ! -e "$VAULT/outputs/site/raw"

echo "npx skills smoke test passed"
