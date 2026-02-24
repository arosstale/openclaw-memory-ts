# Cross-Agent Knowledge Transfer

OpenClaw V2.1 Elite allows Pi instances to "teach" fresh agent instances what they've learned about:
- Energy patterns and thermal profiles
- Successful GEPA mutations
- IQ growth over time
- Agent behaviors and personality
- Reflections on failures and successes

## Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│   Source Pi     │                    │  Target Pi      │
│   (Teacher)     │                    │  (Student)      │
└────────┬────────┘                    └────────┬────────┘
         │                                       │
         │ 1. Export Knowledge                   │ 2. Import Knowledge
         │    knowledge-export.sh                 │    knowledge-import.sh
         │                                       │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│          Knowledge Transfer Bundle (.tar.gz)               │
│                                                          │
│  Components:                                             │
│  • MUTATION_LOG.md - IQ growth history                    │
│  • AGENTS.md - Learned behaviors                         │
│  • IDENTITY.md - Personality profile                      │
│  • MUTATION_HISTORY.md - GEPA mutations                   │
│  • REFLECTIONS.md - Agent reflections                     │
│  • THERMAL_PATTERNS.md - Energy patterns                  │
│  • MANIFEST.json - Bundle metadata                         │
└─────────────────────────────────────────────────────────────────┘
```

## Exporting Knowledge

On the source Pi (the teacher):

```bash
# Export all learnings
bash scripts/knowledge-export.sh

# Output:
# 📦 knowledge-pi-20260209_142530.tar.gz
# Location: .openclaw/knowledge-transfer/
```

**Exported Components**:
1. **IQ Growth History** - Track how agent's intelligence evolved
2. **Learned Behaviors** - AGENTS.md with accumulated wisdom
3. **Personality Profile** - IDENTITY.md with core traits
4. **GEPA Mutation History** - Last 20 mutation tags with details
5. **Agent Reflections** - Last 10 Git Notes with learnings
6. **Thermal Patterns** - Energy patterns from memory logs
7. **Knowledge Manifest** - JSON metadata for verification

## Importing Knowledge

On the target Pi (the student):

```bash
# 1. Copy bundle to target instance
scp source-pi:.openclaw/knowledge-transfer/knowledge-pi-*.tar.gz \
    target-pi:~/openclaw-memory-template/

# 2. Import knowledge (overwrite mode)
bash scripts/knowledge-import.sh knowledge-pi-20260209_142530.tar.gz

# OR, merge with existing knowledge
bash scripts/knowledge-import.sh knowledge-pi-20260209_142530.tar.gz --merge
```

**Import Modes**:
- **Default (overwrite)**: Replaces existing files with imported knowledge
- **`--merge`**: Appends imported knowledge to existing files

**Imported Components**:
1. **IQ Growth History** - Merges into MUTATION_LOG.md
2. **Learned Behaviors** - Merges into AGENTS.md
3. **Personality Profile** - Updates agent name to "Pi"
4. **GEPA History** - Saved as reference in `.openclaw/knowledge-transfer/imported/`
5. **Reflections** - Saved as reference in `.openclaw/knowledge-transfer/imported/`
6. **Thermal Patterns** - Saved as reference in `.openclaw/knowledge-transfer/imported/`

## Use Cases

### 1. New Team Member Onboarding
When a new team member sets up their Pi:

```bash
# Senior Pi teaches the newbie
bash scripts/knowledge-export.sh
# Share knowledge-pi-*.tar.gz via Google Drive, S3, etc.

# Newbie imports
bash scripts/knowledge-import.sh knowledge-pi-senior.tar.gz
```

### 2. Disaster Recovery
If Pi's workspace is corrupted:

```bash
# Restore from backup knowledge
bash scripts/knowledge-import.sh backup-knowledge-20260201.tar.gz
```

### 3. A/B Testing
Test different strategies:

```bash
# Clone to test branch
git checkout -b test-thermal-strategy

# Import thermal-optimized knowledge
bash scripts/knowledge-import.sh thermal-optimized.tar.gz

# Run stability test
bash scripts/stability-test.sh 100

# Compare results, keep best
```

### 4. Swarm Knowledge Sharing
Multiple Pis sharing specialized knowledge:

```bash
# Research Pi shares findings
bash scripts/knowledge-export.sh

# Ops Pi imports research knowledge
bash scripts/knowledge-import.sh knowledge-pi-research.tar.gz --merge

# Developer Pi imports both
bash scripts/knowledge-import.sh knowledge-pi-research.tar.gz --merge
bash scripts/knowledge-import.sh knowledge-pi-ops.tar.gz --merge
```

## Knowledge Integrity

### Export Verification
```bash
# After export, verify bundle contents
tar -tzf .openclaw/knowledge-transfer/knowledge-pi-*.tar.gz

# View manifest
cat .openclaw/knowledge-transfer/MANIFEST.json
```

### Import Verification
```bash
# After import, run GEPA test
bash scripts/gepa-test.sh

# Review import log
cat .openclaw/knowledge-transfer/IMPORT_LOG.md

# Compare IQ growth
git log --oneline --all
```

## Best Practices

1. **Export Regularly**: Before major changes, export knowledge
2. **Version Control**: Commit knowledge bundles to Git
3. **Review Before Merge**: Always review merged knowledge
4. **Test After Import**: Run `gepa-test.sh` after importing
5. **Document Changes**: Update MANIFEST.json with custom metadata

## Security Considerations

- Knowledge bundles may contain sensitive information
- Encrypt sensitive bundles before sharing:
  ```bash
  gpg --encrypt --recipient user@domain.com knowledge-pi.tar.gz
  ```
- Decrypt before import:
  ```bash
  gpg --decrypt knowledge-pi.tar.gz.gpg > knowledge-pi.tar.gz
  ```

## Troubleshooting

### Import Fails
```bash
# Verify bundle integrity
tar -tzf knowledge-pi.tar.gz > /dev/null

# Check manifest
cat knowledge-pi/EXPORT_DIR/temp/MANIFEST.json
```

### Merge Conflicts
```bash
# Use overwrite mode for clean import
bash scripts/knowledge-import.sh knowledge-pi.tar.gz

# Then manually merge AGENTS.md
git diff .openclaw/core/AGENTS.md
```

### Identity Mismatch
```bash
# After import, verify identity
cat .openclaw/core/IDENTITY.md

# If wrong, correct it
vim .openclaw/core/IDENTITY.md
```

---

**The Knowledge Transfer system enables Pi instances to evolve together, sharing wisdom and accelerating collective intelligence.** 🧬
