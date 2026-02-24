#!/bin/bash
# OpenClaw V2.1 Elite - Genetic Versioning Script
# Git tags each GEPA mutation for easy rollback

set -e

MUTATION_ID="${1:-M$(date +%Y%m%d%H%M%S)}"
MUTATION_TYPE="${2:-prompt}"
MUTATION_SEVERITY="${3:-moderate}"
DESCRIPTION="${4:-GEPA auto-mutation}"
TAG_NAME="mutation-${MUTATION_ID}"

echo "🧬 Genetic Versioning - GEPA Mutation $MUTATION_ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Type:     $MUTATION_TYPE"
echo "Severity: $MUTATION_SEVERITY"
echo "Tag:      $TAG_NAME"
echo "Desc:     $DESCRIPTION"
echo ""

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a Git repository"
    exit 1
fi

# Create annotated tag with mutation metadata
git tag -a "$TAG_NAME" -m "GEPA Mutation: $MUTATION_ID

Type: $MUTATION_TYPE
Severity: $MUTATION_SEVERITY
Description: $DESCRIPTION

Date: $(date -Iseconds)
Agent: $(whoami)@$(hostname)"

echo "✅ Git tag created: $TAG_NAME"

# Add to MUTATION_LOG.md
if [ -f "MUTATION_LOG.md" ]; then
    echo ""
    echo "📝 Adding to MUTATION_LOG.md..."
    
    # Append mutation entry to log
    TEMP_LOG=$(mktemp)
    cat > "$TEMP_LOG" << EOF
| $MUTATION_ID | $(date +%Y-%m-%d) | $MUTATION_TYPE | $MUTATION_SEVERITY | $TAG_NAME | TBD | Active |
EOF
    
    # Insert before the "Total Mutations" line
    awk -i inplace -v tmpfile="$TEMP_LOG" '
        /^## Mutation History$/ { found=1 }
        found && !/^|/ && !/^$/ { print; print tmpfile; next }
        { print }
    ' MUTATION_LOG.md
    
    rm "$TEMP_LOG"
    echo "✅ Updated MUTATION_LOG.md"
else
    echo "⚠️  MUTATION_LOG.md not found, skipping log update"
fi

# Push tags to remote (optional)
if [ "${5}" = "--push" ]; then
    echo ""
    echo "📤 Pushing tags to remote..."
    git push origin "$TAG_NAME"
    echo "✅ Tag pushed to remote"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Mutation $MUTATION_ID versioned and ready for rollback"
echo ""
echo "Rollback commands:"
echo "  git checkout $TAG_NAME"
echo "  git checkout -b rollback-from-$MUTATION_ID $TAG_NAME"
