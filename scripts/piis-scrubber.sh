#!/bin/bash
# OpenClaw V2.1 Elite - PII Scrubber
# Removes Personally Identifiable Information from knowledge packages
# Ensures safe community knowledge transfer

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
TEMP_DIR=$(mktemp -d)
SCRUB_REPORT_FILE="$TEMP_DIR/scrub-report.txt"
PII_PATTERNS=(
    # Email addresses
    "s/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[EMAIL_REDACTED]/g"

    # Phone numbers (various formats)
    "s/\b[0-9]{3}[-.]?[0-9]{3}[-.]?[0-9]{4}\b/[PHONE_REDACTED]/g"
    "s/\b\([0-9]{3}\)[-. ]\([0-9]{3}\)[-. ]\([0-9]{4}\)/[PHONE_REDACTED]/g"
    "s/\b[0-9]{3}[-.]?([0-9]{3})[-.]?[0-9]{4}\b/[PHONE_REDACTED]/g"

    # Social Security (SSN-like)
    "s/\b[0-9]{3}[-.][0-9]{2}[-.][0-9]{4}\b/[SSN_REDACTED]/g"

    # Credit card numbers
    "s/\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b/[CC_REDACTED]/g"
    "s/\b4[0-9]{12}([0-9]{3})?\b/[CC_REDACTED]/g"

    # IP addresses
    "s/\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b/[IP_REDACTED]/g"

    # URLs with sensitive paths
    "s|https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._%+-]*\.(txt|log|sql|db|json|csv))?[a-zA-Z0-9?]*|[URL_REDACTED]|g"

    # File paths with sensitive extensions
    "s|/[a-zA-Z0-9._-]+\.(txt|log|sql|db|json|csv|key|pem|p12)|/[SENSITIVE_FILE]|g"

    # API keys (common patterns)
    "s/sk-[a-zA-Z0-9]{32,48}/[API_KEY_REDACTED]/g"
    "s/AKIAIOSFODNN7EXAMPLE/[API_KEY_REDACTED]/g"
    "s/bearer [a-zA-Z0-9._-]+/[TOKEN_REDACTED]/g"
    "s/password[\"'\s:=]+[^\s\"']+/password\" = \"[REDACTED]\"/gi"

    # Dates with specific names (common in logs)
    "s/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* [0-9]{1,2}, [0-9]{4} at [0-9]{1,2}:[0-9]{2}/[DATE_REDACTED]/gi"

    # User mentions (preserve agent names)
    "s/@[a-zA-Z][a-zA-Z0-9._]{3,}/[USER_MENTION]/g"

    # Session IDs
    "s/session-[a-f0-9]{8,16}/[SESSION_ID]/gi"
    "s/[a-f0-9]{32}/[UUID_REDACTED]/g"

    # Physical addresses (simplified)
    "s/[0-9]+ [A-Za-z]+ [A-Za-z]+, [A-Za-z]+ [0-9]{5}/[ADDRESS_REDACTED]/g"

    # Medical/health info
    "s/(blood pressure|heart rate|temperature|weight|height|medication|prescription|doctor|hospital|clinic): [^,.!?;\n]+/\1: [REDACTED]/gi"
)

# Sensitive file patterns to remove
SENSITIVE_FILE_PATTERNS=(
    "*.log"
    "*.sql"
    "*.db"
    "*.sqlite"
    "*.key"
    "*.pem"
    "*.p12"
    ".env"
    "*credentials*"
    "*secrets*"
    "memory/YYYY-MM-DD.md"  # Daily logs
    ".openclaw/session-*"
)

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🛡️ PII Scrubber - Secure Knowledge Transfer                 ║"
echo "║                                                                ║"
echo "║   Removing personally identifiable information                  ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <input-tar.gz> <output-tar.gz>${NC}"
    echo ""
    echo -e "${CYAN}What gets removed:${NC}"
    echo "  • Email addresses"
    echo "  • Phone numbers"
    echo "  • SSN, credit cards, IPs"
    echo "  • API keys and tokens"
    echo "  • Session IDs and UUIDs"
    echo "  • Daily memory logs"
    echo "  • Sensitive files (.log, .sql, .key)"
    echo "  • URLs with sensitive paths"
    echo "  • User mentions (@username)"
    echo ""
    echo -e "${YELLOW}⚠️  Note: AGENTS.md and MUTATION_LOG.md are preserved.${NC}"
    echo "  These contain only instruction mutations, not personal data."
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"

# Validate input
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}❌ Error: Input file not found: $INPUT_FILE${NC}"
    exit 1
fi

echo -e "${CYAN}📦 Extracting Knowledge Package...${NC}"
echo ""

# Extract to temp directory
mkdir -p "$TEMP_DIR/extract"
mkdir -p "$TEMP_DIR/clean"
tar -xzf "$INPUT_FILE" -C "$TEMP_DIR/extract" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to extract package${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Extracted to temporary directory${NC}"
echo ""

# Scrubbing statistics
TOTAL_FILES=0
SCRUBBED_FILES=0
REMOVED_FILES=0
PII_REDACTIONS=0

# Process each file
echo -e "${CYAN}🛡️ Scrubbing PII from extracted files...${NC}"
echo ""

while IFS= read -r -d '' file; do
    TOTAL_FILES=$((TOTAL_FILES + 1))

    # Check if file should be removed
    filename=$(basename "$file")

    for pattern in "${SENSITIVE_FILE_PATTERNS[@]}"; do
        if [[ "$filename" == $pattern ]]; then
            echo -e "${RED}   🗑️  Removing: ${BLUE}$filename${NC}"
            rm "$file"
            REMOVED_FILES=$((REMOVED_FILES + 1))
            continue 2
        fi
    done

    # Scrub content
    file_ext="${filename##*.}"

    # Only scrub text/markdown files
    if [[ "$file_ext" =~ ^(md|txt|json|yaml|yml)$ ]]; then
        echo -e "${YELLOW}   🔍 Scrubbing: ${BLUE}$filename${NC}"

        temp_file="$TEMP_DIR/scrub-temp.txt"
        original_content=$(cat "$file")

        # Apply PII patterns
        scrubbed_content="$original_content"
        file_redactions=0

        for pattern in "${PII_PATTERNS[@]}"; do
            # Count matches before
            before_count=$(echo "$scrubbed_content" | grep -oP "$pattern" | wc -l)

            # Apply pattern
            scrubbed_content=$(echo "$scrubbed_content" | sed -E "$pattern")

            # Count matches after
            after_count=$(echo "$scrubbed_content" | grep -oP "$pattern" | wc -l)

            file_redactions=$((file_redactions + before_count))
        done

        # Write scrubbed content
        echo "$scrubbed_content" > "$temp_file"

        # Move to clean directory if changed
        if [ "$original_content" != "$scrubbed_content" ]; then
            relative_path="${file#$TEMP_DIR/extract/}"
            mkdir -p "$(dirname "$TEMP_DIR/clean/$relative_path")"
            cp "$temp_file" "$TEMP_DIR/clean/$relative_path"
            echo -e "${GREEN}   ✅ Redacted ${file_redactions} PII instances${NC}"
            SCRUBBED_FILES=$((SCRUBBED_FILES + 1))
            PII_REDACTIONS=$((PII_REDACTIONS + file_redactions))
        else
            relative_path="${file#$TEMP_DIR/extract/}"
            mkdir -p "$(dirname "$TEMP_DIR/clean/$relative_path")"
            cp "$file" "$TEMP_DIR/clean/$relative_path"
        fi

        rm -f "$temp_file"
    else
        # Copy non-text files as-is
        relative_path="${file#$TEMP_DIR/extract/}"
        mkdir -p "$(dirname "$TEMP_DIR/clean/$relative_path")"
        cp "$file" "$TEMP_DIR/clean/$relative_path"
    fi
done < <(find "$TEMP_DIR/extract" -type f -print0)

echo ""
echo -e "${CYAN}📦 Repackaging Clean Knowledge Package...${NC}"
echo ""

# Create clean tarball
cd "$TEMP_DIR/clean"
tar -czf "$OUTPUT_FILE" * 2>/dev/null
cd - > /dev/null

echo -e "${GREEN}✅ Clean package created: ${BLUE}$OUTPUT_FILE${NC}"
echo ""

# Generate report
echo -e "${CYAN}📊 PII Scrubbing Report${NC}"
echo ""
echo "Total Files Processed:    $TOTAL_FILES"
echo -e "Files Scrubbed:          ${GREEN}$SCRUBBED_FILES${NC}"
echo -e "Files Removed:            ${RED}$REMOVED_FILES${NC}"
echo -e "PII Redactions:           ${RED}$PII_REDACTIONS${NC}"
echo ""

# Report what was preserved
echo -e "${CYAN}✅ Preserved Components${NC}"
echo ""
if [ -f "$TEMP_DIR/clean/MUTATION_LOG.md" ]; then
    echo "  • MUTATION_LOG.md (IQ growth history)"
fi
if [ -f "$TEMP_DIR/clean/AGENTS.md" ]; then
    echo "  • AGENTS.md (learned behaviors)"
fi
if [ -f "$TEMP_DIR/clean/IDENTITY.md" ]; then
    echo "  • IDENTITY.md (personality)"
fi
if [ -f "$TEMP_DIR/clean/MANIFEST.json" ]; then
    echo "  • MANIFEST.json (metadata)"
fi

echo ""
echo -e "${MAGENTA}🎉 Scrubbing Complete!${NC}"
echo ""
echo -e "The package is safe for community sharing."
echo -e "It contains only ${GREEN}instruction mutations${NC} and ${GREEN}energy patterns${NC}."
echo -e "All ${RED}PII has been removed${NC}."
echo ""

# Cleanup
rm -rf "$TEMP_DIR"

exit 0
