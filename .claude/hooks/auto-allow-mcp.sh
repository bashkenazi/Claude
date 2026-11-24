#!/usr/bin/env bash
# PermissionRequest hook: auto-approve research connector tools that
# .claude/settings.json already allows, unless they're on its "ask" list.
input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
dir="$(cd "$(dirname "$0")/.." && pwd)"
case "$tool" in
  mcp__SRS_MCP__*|mcp__Notion__*|mcp__Supabase__*|mcp__FactSet__*|mcp__Insider_Score__*|mcp__Claude_Docs__*) ;;
  *) exit 0 ;;
esac
if jq -e --arg t "$tool" '.permissions.ask // [] | index($t)' "$dir/settings.json" >/dev/null 2>&1; then
  exit 0
fi
printf '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"allow"}}}\n'
