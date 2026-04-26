# Claude Code Hooks — Quran Integrity

This document describes the recommended Claude Code hook configuration to enforce
content integrity automatically when editing Quranic data or content-serving code.

---

## What Hooks Do

Claude Code hooks are shell commands that run automatically in response to tool
events (e.g., after editing a file). They run in the user's shell and can block
or warn on violations. They are configured in `.claude/settings.json`.

Reference: https://docs.anthropic.com/en/docs/claude-code/hooks

---

## Recommended Hook: Post-Edit Quran Integrity Check

Run `validate-quran-integrity.ts` after any edit to content-related paths.

### Hook Configuration

Add the following to `.claude/settings.json` under the `hooks` key:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "node -e \"const p=process.env.CLAUDE_TOOL_INPUT_FILE_PATH||''; const trigger=['src/data/','src/content/','src/features/ask/','src/features/search/','src/features/sources/','data/raw/','data/manifests/','data/concepts/','backend/app/data/']; if(trigger.some(t=>p.includes(t))){ require('child_process').execSync('npx tsx scripts/validate-quran-integrity.ts 2>&1',{stdio:'inherit'}); }\""
          }
        ]
      }
    ]
  }
}
```

### Simpler Alternative (bash)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'p=\"${CLAUDE_TOOL_INPUT_FILE_PATH:-}\"; case \"$p\" in *src/data/*|*src/content/*|*src/features/ask/*|*src/features/search/*|*src/features/sources/*|*data/raw/*|*data/manifests/*|*data/concepts/*|*backend/app/data/*) npx tsx scripts/validate-quran-integrity.ts ;; esac'"
          }
        ]
      }
    ]
  }
}
```

---

## Paths That Trigger the Hook

The hook fires when any of these path segments appear in the edited file:

| Path Pattern | What It Covers |
|---|---|
| `src/data/` | Source registry, frontend data files |
| `src/content/` | Static content files |
| `src/features/ask/` | Ask / RAG interface |
| `src/features/search/` | Search interface |
| `src/features/sources/` | Sources display |
| `data/raw/` | Raw Quran text and translations |
| `data/manifests/` | Quran, tafsir, stories manifests |
| `data/concepts/` | Concept dictionary |
| `backend/app/data/` | Themes taxonomy and backend data |

---

## What the Validator Checks

`scripts/validate-quran-integrity.ts` verifies:

1. Total surah count = 114
2. Total ayah count = 6,236
3. Every ayah has a valid surah number (1–114) and ayah number (≥1)
4. No duplicate ayah keys (sura:aya)
5. No missing ayah keys (every key in the expected sequence exists)
6. No empty Arabic text fields
7. Source registry has all required fields per source
8. Every tafsir source entry has a `sourceId`
9. No source has `reliabilityLevel = experimental` without a warning note
10. License status is not unknown for canonical sources

---

## Additional Recommended Hooks

### Pre-commit: Prevent Direct Quran Text Edits

Add this to block commits that touch the Quran raw data without a review flag:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'p=\"${CLAUDE_TOOL_INPUT_FILE_PATH:-}\"; case \"$p\" in *data/raw/quran*|*quran_uthmani*|*hafs_smart*) echo \"WARNING: Editing Quran text files requires explicit authorization. Ensure changes are intentional and validated.\"; ;; esac'"
          }
        ]
      }
    ]
  }
}
```

### Stop Notification: Show Validation Status

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '--- Tadabbur Content Integrity Status ---' && npx tsx scripts/validate-quran-integrity.ts --summary 2>/dev/null || echo 'Integrity validator not run or failed.'"
          }
        ]
      }
    ]
  }
}
```

---

## Manual Validation

Run the validator at any time:

```bash
# From project root
npx tsx scripts/validate-quran-integrity.ts

# Verbose output
npx tsx scripts/validate-quran-integrity.ts --verbose

# Summary only (for hooks)
npx tsx scripts/validate-quran-integrity.ts --summary
```

---

## CI Integration

Add to your CI pipeline (e.g., GitHub Actions):

```yaml
- name: Quran Integrity Check
  run: npx tsx scripts/validate-quran-integrity.ts
  working-directory: ${{ github.workspace }}
```

This ensures no content-breaking change can be merged without passing validation.
