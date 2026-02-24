# GEPA Mutation Log - OpenClaw Elite V2.1

> Track your agent's technical IQ growth over time.
> Each GEPA mutation is Git-tagged for easy rollback.

---

## Mutation Template

```markdown
### [MUTATION-ID] - [DATE]

**Type**: `prompt | strategy | workflow`
**Severity**: `minor | moderate | major | critical`
**Git Tag**: `mutation-[MUTATION-ID]`

**Trigger**:
- Error: `[error message]`
- Task: `[task description]`
- Temperature: `[°C]`

**Description**:
> What the mutation does and why it was needed.

**Diff**:
```diff
-   Old behavior
+   New behavior
```

**Effectiveness**: `[positive | negative | neutral]`
**Technical IQ Change**: `[+0.1 | +0.5 | +1.0 | -0.5]`
**Notes**: Any observations about this mutation's impact.
```

---

## Mutation History

| Mutation ID | Date | Type | Severity | Git Tag | IQ Change | Status |
|-------------|------|------|----------|-----------|------------|---------|
| M001 | 2026-02-09 | strategy | major | mutation-M001 | +0.5 | Active |
| M002 | 2026-02-09 | workflow | critical | mutation-M002 | +1.0 | Active |

---

## Technical IQ Over Time

```
IQ Score
  5.0 ┼─────────────────────────────────────
  4.5 ┼────┐
  4.0 ┼────┼────────────┐
  3.5 ┼────┼────────────┼────
  3.0 ┼────┼────────────┼────────────
       └────┴────────────┴────────────┴────► Time
       M001 M002 M003
```

## Rollback Guide

```bash
# View mutation history
git tag -l "mutation-*"

# Rollback to specific mutation
git checkout mutation-M001

# Create new branch from old mutation
git checkout -b rollback-from-M001 mutation-M001
```

## IQ Scoring Criteria

- **+0.1**: Minor improvement (e.g., small prompt tweak)
- **+0.5**: Moderate improvement (e.g., new workflow step)
- **+1.0**: Major breakthrough (e.g., GEPA self-correction enabled)
- **+2.0**: Paradigm shift (e.g., swarm integration)
- **-0.5**: Regression (mutation caused issues)
- **-1.0**: Major regression (hallucination spike)

---

**Last Updated**: 2026-02-09
**Total Mutations**: 0
**Cumulative IQ**: 3.0 (baseline)
**Active Branch**: main
