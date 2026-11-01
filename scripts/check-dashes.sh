#!/usr/bin/env bash
# check-dashes — centralized PROSE dash gate (Tier PROSE bloquant)
# Scans git-tracked prose files (*.tex, *.md, *.txt, *.rst, *.adoc), with a
# local glob fallback when not a git repo or when the index has no prose yet.
# Blocked patterns (via libs/humanize/humanize_lib.sh):
#   --- (LaTeX em-dash), — U+2014, " -- " (space--space), any – U+2013,
#   LaTeX A--C ranges, LaTeX ~ non-breaking space (Parts~A, scheme~).
# Human ranges: "A - C" / "2024-2025". No interval en-dash exemption.
# Exemptions: full-line TeX comments (^[[:space:]]*%), standalone "---" HR/frontmatter.
# Usage: sh scripts/check-dashes.sh  |  bash scripts/check-dashes.sh  |  ./scripts/check-dashes.sh
# Central source of truth: $HOME/.agents/scripts/check-dashes.sh
# Project copies: k-tex / k-presentation templates copy this file into scripts/check-dashes.sh
# Old canonical: skills/k-tex/scripts/check-dashes.sh (kept for backward compat, do not delete yet)
set -euo pipefail

# --- re-exec under bash if invoked via sh/dash (keeps `sh scripts/check-dashes.sh` working) ---
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

# --- source shared humanize lib (prefer $HOME/.agents, fallback to script dir / git root) ---
_HUMANIZE_LIB="$HOME/.agents/libs/humanize/humanize_lib.sh"
if [ -f "$_HUMANIZE_LIB" ]; then
  # shellcheck disable=SC1090,SC1091
  source "$_HUMANIZE_LIB"
else
  _SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  if [ -f "$_SCRIPT_DIR/../libs/humanize/humanize_lib.sh" ]; then
    # shellcheck disable=SC1090,SC1091
    source "$_SCRIPT_DIR/../libs/humanize/humanize_lib.sh"
  elif [ -f "$_SCRIPT_DIR/../.agents/libs/humanize/humanize_lib.sh" ]; then
    # shellcheck disable=SC1090,SC1091
    source "$_SCRIPT_DIR/../.agents/libs/humanize/humanize_lib.sh"
  else
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
      _GIT_ROOT="$(git rev-parse --show-toplevel)" || _GIT_ROOT=""
      if [ -n "${_GIT_ROOT:-}" ] && [ -f "$_GIT_ROOT/../.agents/libs/humanize/humanize_lib.sh" ]; then
        # shellcheck disable=SC1090,SC1091
        source "$_GIT_ROOT/../.agents/libs/humanize/humanize_lib.sh"
      fi
    fi
  fi
fi

# --- fallback inline definitions if lib not available (project copy without .agents nearby) ---
if ! type contains_blocked_dash >/dev/null 2>&1; then
  HUMANIZE_EM_DASH_TRIPLE="---"
  HUMANIZE_EM_DASH_UNICODE="—"
  HUMANIZE_EN_DASH_UNICODE="–"
  HUMANIZE_EN_DASH_SPACED=" – "
  HUMANIZE_DOUBLE_DASH_SPACED=" -- "
  HUMANIZE_LATEX_NBSP="~"
  _mask_allowed_triple_dashes() {
    local text="$1"
    printf '%s' "$text" | perl -pe 's/\|\s*:?-{2,}:?\s*(?=\|)/$&=~s|-|=|gr/ge; s/^[ \t]*---[ \t]*$/===/mg'
  }
  contains_blocked_dash() {
    local text="$1"
    local text_for_triple
    text_for_triple="$(_mask_allowed_triple_dashes "$text")"
    if [[ "$text_for_triple" == *"$HUMANIZE_EM_DASH_TRIPLE"* ]]; then printf 'EM_DASH_TRIPLE|---\n'; return 0; fi
    if printf '%s' "$text_for_triple" | grep -qE '[A-Za-z0-9]--[A-Za-z0-9]'; then printf 'LATEX_EN_DASH_RANGE|A--C\n'; return 0; fi
    if [[ "$text" == *"$HUMANIZE_EM_DASH_UNICODE"* ]]; then printf 'EM_DASH_UNICODE|—\n'; return 0; fi
    if [[ "$text" == *"$HUMANIZE_DOUBLE_DASH_SPACED"* ]]; then printf 'DOUBLE_DASH_SPACED| -- \n'; return 0; fi
    if [[ "$text" == *"$HUMANIZE_EN_DASH_UNICODE"* ]]; then printf 'EN_DASH_UNICODE|–\n'; return 0; fi
    if [[ "$text" == *"$HUMANIZE_LATEX_NBSP"* ]]; then printf 'LATEX_NBSP|~\n'; return 0; fi
    return 1
  }
fi

fail=0
files=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # `git ls-files` exits non-zero only on a real failure; an empty result (no
  # tracked prose) falls through to the local glob fallback below.
  files="$(git ls-files '*.tex' '*.md' '*.txt' '*.rst' '*.adoc' 2>&1)" || \
    { echo "check-dashes FAILED: git ls-files errored" >&2; exit 1; }
fi

# Fallback: no git, or git with empty prose index → scan local prose (never fake OK)
if [ -z "${files:-}" ]; then
  files="$(
    find . -type f \( -name '*.tex' -o -name '*.md' -o -name '*.txt' -o -name '*.rst' -o -name '*.adoc' \) \
      ! -path './.git/*' ! -path './build/*' ! -path './refs/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' \
      2>/dev/null | sed 's|^\./||' || true
  )"
fi

if [ -z "${files:-}" ]; then
  echo "check-dashes OK: no prose files to scan"
  exit 0
fi

# Use while-read over the file list (handles most prose filenames; spaces are rare for these types)
# shellcheck disable=SC2094  # false positive: we read $f line-by-line and print to stdout, never write back to $f
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue
  lineno=0
  # shellcheck disable=SC2162
  while IFS= read -r line || [ -n "${line:-}" ]; do
    lineno=$((lineno + 1))
    # .tex: skip full-line TeX comments (as before)
    case "$f" in
      *.tex)
        if printf '%s' "$line" | grep -q '^[[:space:]]*%'; then
          continue
        fi
        ;;
    esac
    # Exemption: standalone "---" (Markdown HR / YAML frontmatter delimiter)
    trimmed="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [ "$trimmed" = "---" ]; then
      continue
    fi
    # Tier PROSE bloquant — delegate to lib (dashes + LaTeX A--C + LaTeX ~)
    if contains_blocked_dash "$line" >/dev/null 2>&1; then
      printf '%s:%d:%s\n' "$f" "$lineno" "$line"
      fail=1
    fi
  done < "$f"
done <<EOF
$files
EOF

if [ "$fail" = 1 ]; then
  echo "check-dashes FAILED: blocked non-human dash/nbsp found above — use ASCII '-' or 'A - C', spaces not '~', connectors (, ; : . or / and / to)" >&2
  exit 1
else
  echo "check-dashes OK: no blocked dash in tracked prose files"
fi
