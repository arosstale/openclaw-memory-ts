#!/bin/bash
# OpenClaw V2.1 Elite - Knowledge Import
# Imports learned knowledge from another Pi instance

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Usage: $0 <knowledge-bundle.tar.gz> [--merge]${NC}"
    echo ""
    echo "Arguments:"
    echo "  <knowledge-bundle.tar.gz>  Path to knowledge export bundle"
    echo "  --merge                     Merge with existing knowledge (default: skip existing)"
    echo ""
    echo "Example:"
    echo "  $0 .openclaw/knowledge-transfer/knowledge-pi-20260209.tar.gz"
    echo "  $0 knowledge-pi.tar.gz --merge"
    exit 1
fi

BUNDLE_PATH="$1"
MERGE_MODE="${2:-}"
TEMP_DIR=".openclaw/knowledge-transfer/temp"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🧬 Cross-Agent Knowledge Transfer - Import                     ║"
echo "║                                                                ║"
echo "║   Learning from another Pi instance                               ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Validate bundle
if [ ! -f "$BUNDLE_PATH" ]; then
    echo -e "${RED}❌ Error: Bundle not found: $BUNDLE_PATH${NC}"
    exit 1
fi

echo -e "${CYAN}📦 Validating Knowledge Bundle...${NC}"
echo ""

# Extract to temp directory
mkdir -p "$TEMP_DIR"
rm -rf "${TEMP_DIR:?}/import"
mkdir -p "$TEMP_DIR/import"

echo -e "  Extracting: ${BLUE}$BUNDLE_PATH${NC}"
tar -xzf "$BUNDLE_PATH" -C "$TEMP_DIR/import" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to extract bundle${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Bundle extracted successfully${NC}"
echo ""

# Read manifest
if [ -f "$TEMP_DIR/import/MANIFEST.json" ]; then
    echo -e "${CYAN}📋 Knowledge Source${NC}"
    echo ""
    cat "$TEMP_DIR/import/MANIFEST.json" | head -10
    echo ""
else
    echo -e "${YELLOW}⚠️  Warning: No MANIFEST.json found${NC}"
    echo ""
fi

# Import counters
IMPORTED=0
SKIPPED=0
MERGED=0

# Function to import file with merge support
import_file() {
    local src_file="$1"
    local dest_file="$2"
    local component_name="$3"

    if [ ! -f "$src_file" ]; then
        return
    fi

    if [ "$MERGE_MODE" = "--merge" ] && [ -f "$dest_file" ]; then
        echo -e "${YELLOW}🔀 Merging${NC} $component_name"
        # Simple merge: append source to dest
        echo "" >> "$dest_file"
        echo "" >> "$dest_file"
        echo "--- MERGED KNOWLEDGE ---" >> "$dest_file"
        echo "" >> "$dest_file"
        cat "$src_file" >> "$dest_file"
        MERGED=$((MERGED + 1))
    elif [ -f "$dest_file" ]; then
        echo -e "${YELLOW}⏭️  Skipping${NC} $component_name (already exists)"
        SKIPPED=$((SKIPPED + 1))
    else
        echo -e "${GREEN}✅ Importing${NC} $component_name"
        cp "$src_file" "$dest_file"
        IMPORTED=$((IMPORTED + 1))
    fi
}

# Import components
echo -e "${CYAN}🧬 Importing Knowledge Components...${NC}"
echo ""

# 1. IQ Growth History
import_file "$TEMP_DIR/import/MUTATION_LOG.md" "MUTATION_LOG.md" "IQ Growth History"

# 2. Learned Behaviors
import_file "$TEMP_DIR/import/AGENTS.md" ".openclaw/core/AGENTS.md" "Learned Behaviors"

# 3. Personality Profile
if [ -f "$TEMP_DIR/import/IDENTITY.md" ]; then
    echo -e "${GREEN}✅ Importing${NC} Personality Profile"
    cp "$TEMP_DIR/import/IDENTITY.md" ".openclaw/core/IDENTITY.md"
    IMPORTED=$((IMPORTED + 1))
    # Force identity import
    echo -e "${MAGENTA}📝 Identity imported: New agent name is now 'Pi'${NC}"
fi

# 4. GEPA Mutation History
if [ -f "$TEMP_DIR/import/MUTATION_HISTORY.md" ]; then
    mkdir -p ".openclaw/knowledge-transfer/imported"
    cp "$TEMP_DIR/import/MUTATION_HISTORY.md" ".openclaw/knowledge-transfer/imported/MUTATION_HISTORY.md"
    echo -e "${GREEN}✅ Importing${NC} GEPA Mutation History (reference only)"
    IMPORTED=$((IMPORTED + 1))
fi

# 5. Agent Reflections
if [ -f "$TEMP_DIR/import/REFLECTIONS.md" ]; then
    mkdir -p ".openclaw/knowledge-transfer/imported"
    cp "$TEMP_DIR/import/REFLECTIONS.md" ".openclaw/knowledge-transfer/imported/REFLECTIONS.md"
    echo -e "${GREEN}✅ Importing${NC} Agent Reflections (reference only)"
    IMPORTED=$((IMPORTED + 1))
fi

# 6. Thermal Patterns
if [ -f "$TEMP_DIR/import/THERMAL_PATTERNS.md" ]; then
    mkdir -p ".openclaw/knowledge-transfer/imported"
    cp "$TEMP_DIR/import/THERMAL_PATTERNS.md" ".openclaw/knowledge-transfer/imported/THERMAL_PATTERNS.md"
    echo -e "${GREEN}✅ Importing${NC} Thermal Energy Patterns (reference only)"
    IMPORTED=$((IMPORTED + 1))
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}📊 Import Summary${NC}"
echo ""
echo -e "Imported: ${GREEN}$IMPORTED${NC}"
echo -e "Merged:   ${YELLOW}$MERGED${NC}"
echo -e "Skipped:  ${YELLOW}$SKIPPED${NC}"
echo ""

# Create import log
IMPORT_LOG=".openclaw/knowledge-transfer/IMPORT_LOG.md"
mkdir -p ".openclaw/knowledge-transfer"
cat > "$IMPORT_LOG" << EOF
# Knowledge Import Log

**Import Date**: $(date -Iseconds)
**Source Bundle**: $BUNDLE_PATH
**Import Mode**: ${MERGE_MODE:-overwrite}

## Components
- Imported: $IMPORTED
- Merged: $MERGED
- Skipped: $SKIPPED

## Source Information
EOF

if [ -f "$TEMP_DIR/import/MANIFEST.json" ]; then
    echo "" >> "$IMPORT_LOG"
    echo '```json' >> "$IMPORT_LOG"
    cat "$TEMP_DIR/import/MANIFEST.json" >> "$IMPORT_LOG"
    echo '```' >> "$IMPORT_LOG"
fi

echo -e "${GREEN}✅ Import log created: $IMPORT_LOG${NC}"
echo ""

# Clean up
rm -rf "$TEMP_DIR/import"

# Verdict
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}🎯 Import Verdict${NC}"
echo ""

if [ $IMPORTED -gt 0 ]; then
    echo -e "${GREEN}✅ Knowledge Transfer Complete!${NC}"
    echo ""
    echo "This agent has learned from another Pi instance:"
    echo "  • IQ growth history transferred"
    echo "  • Learned behaviors incorporated"
    echo "  • Personality profile updated"
    echo "  • GEPA mutations available for reference"
    echo "  • Thermal patterns analyzed"
    echo ""
    echo -e "${MAGENTA}🧬 The agent is now 'evolved' from birth.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review AGENTS.md for imported behaviors"
    echo "  2. Run bash scripts/gepa-test.sh to validate"
    echo "  3. Review imported mutation history for patterns"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  No knowledge imported${NC}"
    echo ""
    echo "All components were skipped or already exist."
    echo ""
    echo "To merge with existing knowledge, use:"
    echo -e "  ${BLUE}bash $0 $BUNDLE_PATH --merge${NC}"
    echo ""
    exit 1
fi
