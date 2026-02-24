#!/bin/bash
# OpenClaw V2.1 Elite - Swarm Encryption
# Encrypt/decrypt knowledge packages for secure community transfer

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
ENCRYPTION_DIR=".openclaw/knowledge-transfer/encrypted"
KEY_FILE="${ENCRYPTION_DIR}/.swarm-key.pub"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🔐 Swarm Encryption - Secure Knowledge Transfer              ║"
echo "║                                                                ║"
echo "║   Encrypt knowledge packages for community sharing                 ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ensure encryption directory
mkdir -p "$ENCRYPTION_DIR"

# Function: Generate public key (for community sharing)
generate_public_key() {
    echo -e "${CYAN}🔑 Generating Public Encryption Key...${NC}"
    echo ""

    # Generate random 256-bit key (hex)
    openssl rand -hex 32 > "${KEY_FILE}.tmp"

    # Create public key (simplified: same key for demo)
    # In production, use GPG or age
    mv "${KEY_FILE}.tmp" "$KEY_FILE"

    echo -e "${GREEN}✅ Public key generated: ${BLUE}$KEY_FILE${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Keep this file secure!${NC}"
    echo "Share only encrypted .enc files with the community."
    echo ""
}

# Function: Encrypt file
encrypt_file() {
    local input_file="$1"
    local output_file="${input_file}.enc"

    if [ ! -f "$input_file" ]; then
        echo -e "${RED}❌ Error: File not found: $input_file${NC}"
        return 1
    fi

    echo -e "${CYAN}🔐 Encrypting: ${BLUE}$(basename $input_file)${NC}"

    # Generate random IV
    local iv=$(openssl rand -hex 16)

    # Encrypt with AES-256-CBC
    openssl enc -aes-256-cbc -salt -in "$input_file" \
        -out "$output_file" \
        -kfile "$KEY_FILE" \
        -iv "$iv"

    # Embed IV in filename (simple approach)
    mv "$output_file" "${output_file%.enc}.${iv}.enc"

    local file_size=$(du -h "${output_file%.enc}.${iv}.enc" | cut -f1)
    echo -e "${GREEN}✅ Encrypted: ${BLUE}$(basename ${output_file%.enc}.${iv}.enc)${NC} ($file_size)"
    echo ""
}

# Function: Decrypt file
decrypt_file() {
    local input_file="$1"
    local output_file="${input_file%.enc}"

    # Extract IV from filename (format: file.<iv>.enc)
    local iv=$(echo "$input_file" | grep -oP '\.\K[0-9a-f]{32}\.enc$' | sed 's/.enc//')

    if [ -z "$iv" ]; then
        echo -e "${RED}❌ Error: Cannot extract IV from filename${NC}"
        return 1
    fi

    echo -e "${CYAN}🔓 Decrypting: ${BLUE}$(basename $input_file)${NC}"

    # Decrypt with AES-256-CBC
    openssl enc -aes-256-cbc -d -salt \
        -in "$input_file" \
        -out "$output_file" \
        -kfile "$KEY_FILE" \
        -iv "$iv"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Decrypted: ${BLUE}$(basename $output_file)${NC}"
        echo ""
    else
        echo -e "${RED}❌ Decryption failed${NC}"
        return 1
    fi
}

# Function: Encrypt entire knowledge package
encrypt_package() {
    local package_path="$1"

    if [ ! -f "$package_path" ]; then
        echo -e "${RED}❌ Error: Package not found: $package_path${NC}"
        exit 1
    fi

    echo -e "${CYAN}📦 Encrypting Knowledge Package...${NC}"
    echo ""

    # First, run PII scrubber
    echo -e "${YELLOW}⚠️  Running PII scrubber before encryption...${NC}"
    bash "$(dirname "$0")/piis-scrubber.sh" "$package_path" "$package_path.scrubbed"

    if [ ! -f "$package_path.scrubbed" ]; then
        echo -e "${RED}❌ PII scrubbing failed${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✅ PII scrubbing complete${NC}"
    echo ""

    # Encrypt scrubbed package
    encrypt_file "$package_path.scrubbed"

    # Remove scrubbed file after encryption
    rm "$package_path.scrubbed"

    # Get encrypted file path
    local encrypted_file="${package_path.scrubbed}.*.enc"

    echo -e "${MAGENTA}🎉 Secure Knowledge Package Ready!${NC}"
    echo ""
    echo -e "Original:  ${YELLOW}${package_path}${NC} (contains PII)"
    echo -e "Encrypted: ${GREEN}${encrypted_file}${NC} (PII-free)"
    echo ""
    echo -e "${BLUE}Share this file:${NC}"
    ls -lh "$encrypted_file" | awk '{print "  " $9 " (" $5 ")"}'
}

# Function: Decrypt package
decrypt_package() {
    local encrypted_file="$1"

    if [ ! -f "$encrypted_file" ]; then
        echo -e "${RED}❌ Error: Encrypted file not found: $encrypted_file${NC}"
        exit 1
    fi

    echo -e "${CYAN}📦 Decrypting Knowledge Package...${NC}"
    echo ""

    decrypt_file "$encrypted_file"

    echo -e "${MAGENTA}🎉 Knowledge Package Decrypted!${NC}"
    echo ""
    echo -e "You can now import with:"
    echo -e "${BLUE}  bash scripts/knowledge-import.sh ${encrypted_file%.enc} ${NC}"
}

# Main menu
case "${1:-}" in
    "genkey"|"generate-key")
        generate_public_key
        ;;
    "encrypt")
        if [ $# -lt 2 ]; then
            echo -e "${RED}Usage: $0 encrypt <knowledge-package.tar.gz>${NC}"
            exit 1
        fi
        encrypt_package "$2"
        ;;
    "decrypt")
        if [ $# -lt 2 ]; then
            echo -e "${RED}Usage: $0 decrypt <encrypted-package.tar.gz.enc>${NC}"
            exit 1
        fi
        decrypt_package "$2"
        ;;
    "help"|*)
        echo -e "${CYAN}Swarm Encryption Usage:${NC}"
        echo ""
        echo "  Generate public key (first time only):"
        echo -e "    ${GREEN}$0 genkey${NC}"
        echo ""
        echo "  Encrypt knowledge package:"
        echo -e "    ${GREEN}$0 encrypt <knowledge-package.tar.gz>${NC}"
        echo ""
        echo "  Decrypt knowledge package:"
        echo -e "    ${GREEN}$0 decrypt <encrypted-package.tar.gz.enc>${NC}"
        echo ""
        echo -e "${YELLOW}Note: The PII scrubber runs automatically before encryption.${NC}"
        exit 0
        ;;
esac
