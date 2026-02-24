#!/bin/bash
# OpenClaw V2.1 Elite - Knowledge Export
# Exports Pi's learnings for transfer to fresh agent instances

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
EXPORT_DIR=".openclaw/knowledge-transfer"
EXPORT_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_FILE="knowledge-pi-${EXPORT_TIMESTAMP}.tar.gz"

# Ensure export directory exists
mkdir -p "$EXPORT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🧬 Cross-Agent Knowledge Transfer - Export                     ║"
echo "║                                                                ║"
echo "║   Exporting Pi's learnings for fresh agent instances              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Create export directory
mkdir -p "$EXPORT_DIR"
rm -rf "${EXPORT_DIR:?}/temp"
mkdir -p "$EXPORT_DIR/temp"

echo -e "${CYAN}📦 Extracting Knowledge Components...${NC}"
echo ""

# 1. Export MUTATION_LOG (IQ history)
if [ -f "MUTATION_LOG.md" ]; then
    cp MUTATION_LOG.md "$EXPORT_DIR/temp/"
    echo -e "${GREEN}✅${NC} IQ Growth History (MUTATION_LOG.md)"
else
    echo -e "${YELLOW}⚠️  No MUTATION_LOG.md found${NC}"
fi

# 2. Export AGENTS.md (learned behaviors)
if [ -f ".openclaw/core/AGENTS.md" ]; then
    cp .openclaw/core/AGENTS.md "$EXPORT_DIR/temp/"
    echo -e "${GREEN}✅${NC} Learned Behaviors (AGENTS.md)"
else
    echo -e "${YELLOW}⚠️  No AGENTS.md found${NC}"
fi

# 3. Export IDENTITY.md (personality)
if [ -f ".openclaw/core/IDENTITY.md" ]; then
    cp .openclaw/core/IDENTITY.md "$EXPORT_DIR/temp/"
    echo -e "${GREEN}✅${NC} Personality Profile (IDENTITY.md)"
else
    echo -e "${YELLOW}⚠️  No IDENTITY.md found${NC}"
fi

# 4. Extract GEPA mutation tags
echo ""
echo -e "${CYAN}🧬 Extracting GEPA Mutation History...${NC}"
if git tag -l "mutation-*" | grep -q .; then
    echo "# GEPA Mutation History - Exported from Pi" > "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
    echo "" >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
    echo "Export Date: $(date -Iseconds)" >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
    echo "" >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"

    git tag -l "mutation-*" --sort=-version:refname | head -20 | while read tag; do
        echo "" >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
        echo "## $tag" >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
        git show "$tag" | head -30 >> "$EXPORT_DIR/temp/MUTATION_HISTORY.md"
    done

    echo -e "${GREEN}✅${NC} GEPA Mutation History (20 most recent)"
else
    echo -e "${YELLOW}⚠️  No mutation tags found${NC}"
fi

# 5. Extract Git Notes (reflections)
echo ""
echo -e "${CYAN}💭 Extracting Git Notes (Reflections)...${NC}"
if command -v git &> /dev/null; then
    git notes list | head -10 | while read note_ref; do
        note_content=$(git notes show "$note_ref" 2>/dev/null || echo "Error reading note")
        echo -e "📝 ${BLUE}$note_ref${NC}"
        echo "$note_content" >> "$EXPORT_DIR/temp/REFLECTIONS.md"
        echo "---" >> "$EXPORT_DIR/temp/REFLECTIONS.md"
    done

    if [ -s "$EXPORT_DIR/temp/REFLECTIONS.md" ]; then
        echo -e "${GREEN}✅${NC} Agent Reflections (10 most recent)"
    else
        echo -e "${YELLOW}⚠️  No Git Notes found${NC}"
        rm -f "$EXPORT_DIR/temp/REFLECTIONS.md"
    fi
else
    echo -e "${YELLOW}⚠️  Git not available${NC}"
fi

# 6. Extract thermal patterns (if logs exist)
echo ""
echo -e "${CYAN}🌡️  Extracting Thermal Patterns...${NC}"
if [ -d "memory" ]; then
    grep -r "thermal" memory/ 2>/dev/null | head -5 > "$EXPORT_DIR/temp/THERMAL_PATTERNS.md" || true
    if [ -s "$EXPORT_DIR/temp/THERMAL_PATTERNS.md" ]; then
        echo -e "${GREEN}✅${NC} Thermal Energy Patterns"
    else
        echo -e "${YELLOW}⚠️  No thermal patterns found${NC}"
        rm -f "$EXPORT_DIR/temp/THERMAL_PATTERNS.md"
    fi
else
    echo -e "${YELLOW}⚠️  No memory directory found${NC}"
fi

# 7. Create knowledge manifest
echo ""
echo -e "${CYAN}📋 Creating Knowledge Manifest...${NC}"
cat > "$EXPORT_DIR/temp/MANIFEST.json" << EOF
{
  "exported_at": "$(date -Iseconds)",
  "agent_name": "Pi",
  "agent_identity": "Self-evolving, hardware-aware, swarm-ready",
  "knowledge_version": "1.0",
  "components": {
    "iq_growth_history": "$(test -f "$EXPORT_DIR/temp/MUTATION_LOG.md" && echo "included" || echo "skipped")",
    "learned_behaviors": "$(test -f "$EXPORT_DIR/temp/AGENTS.md" && echo "included" || echo "skipped")",
    "personality_profile": "$(test -f "$EXPORT_DIR/temp/IDENTITY.md" && echo "included" || echo "skipped")",
    "gepa_mutation_history": "$(test -f "$EXPORT_DIR/temp/MUTATION_HISTORY.md" && echo "included" || echo "skipped")",
    "agent_reflections": "$(test -f "$EXPORT_DIR/temp/REFLECTIONS.md" && echo "included" || echo "skipped")",
    "thermal_patterns": "$(test -f "$EXPORT_DIR/temp/THERMAL_PATTERNS.md" && echo "included" || echo "skipped")"
  },
  "source_commit": "$(git rev-parse HEAD 2>/dev/null || echo "unknown")",
  "source_branch": "$(git branch --show-current 2>/dev/null || echo "unknown")"
}
EOF
echo -e "${GREEN}✅${NC} Knowledge Manifest (MANIFEST.json)"

# 8. Package everything
echo ""
echo -e "${CYAN}📦 Packaging Knowledge Transfer Bundle...${NC}"
cd "$EXPORT_DIR/temp" || exit 1
tar -czf "../${EXPORT_FILE}" * 2>/dev/null
cd "$EXPORT_DIR" || exit 1

rm -rf temp

# Calculate file size
FILE_SIZE=$(du -h "$EXPORT_DIR/$EXPORT_FILE" | cut -f1)

echo -e "${GREEN}✅${NC} Knowledge Bundle Created"
echo ""

# 9. Display summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}📊 Knowledge Export Summary${NC}"
echo ""
echo "Bundle:  ${BLUE}$EXPORT_DIR/$EXPORT_FILE${NC}"
echo "Size:    $FILE_SIZE"
echo "Date:    $(date -Iseconds)"
echo ""

# Display contents
echo "Contents:"
ls -lh "$EXPORT_DIR/$EXPORT_FILE" 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}🚀 Transfer to Fresh Instance${NC}"
echo ""
echo "On the new agent instance:"
echo ""
echo "  1. Clone the repository:"
echo -e "     ${BLUE}git clone https://github.com/arosstale/openclaw-memory-template.git${NC}"
echo ""
echo "  2. Copy knowledge bundle:"
echo -e "     ${BLUE}scp $EXPORT_DIR/$EXPORT_FILE user@target:~/openclaw-memory-template/${NC}"
echo ""
echo "  3. Import knowledge:"
echo -e "     ${BLUE}bash scripts/knowledge-import.sh $EXPORT_DIR/$EXPORT_FILE${NC}"
echo ""
echo -e "${GREEN}🎉 Pi's knowledge is ready to teach another agent!${NC}"
echo ""
