#!/bin/bash

# OpenClaw Memory Template - One-Command Setup
# Creates a new agent workspace from this template

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE="${1:-$HOME/openclaw-agent}"

echo "🚀 OpenClaw Agent Setup"
echo "======================"
echo ""
echo "Creating agent workspace: $WORKSPACE"
echo ""

# Check if workspace already exists
if [ -d "$WORKSPACE" ]; then
    echo "⚠️  Workspace already exists: $WORKSPACE"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Create workspace
echo "📁 Creating workspace..."
mkdir -p "$WORKSPACE"

# Copy template files
echo "📋 Copying template files..."
cp -r "$TEMPLATE_DIR/.openclaw" "$WORKSPACE/"
cp -r "$TEMPLATE_DIR/memory" "$WORKSPACE/" 2>/dev/null || mkdir -p "$WORKSPACE/memory"/{daily,projects}
cp -r "$TEMPLATE_DIR/research" "$WORKSPACE/" 2>/dev/null || mkdir -p "$WORKSPACE/research"/{papers,summaries,daily}
cp -r "$TEMPLATE_DIR/scripts" "$WORKSPACE/" 2>/dev/null || mkdir -p "$WORKSPACE/scripts"
cp "$TEMPLATE_DIR"/{README.md,QUICK_START.md,requirements.txt,.gitignore} "$WORKSPACE/" 2>/dev/null || true

# Run initialization
echo "🔧 Running initialization..."
cd "$WORKSPACE" || exit 1

if [ -f ".openclaw/scripts/init.sh" ]; then
    bash .openclaw/scripts/init.sh
else
    echo "⚠️  init.sh not found, creating basic structure..."
    mkdir -p .openclaw/core .openclaw/context .openclaw/scripts .openclaw/logs
    mkdir -p memory/daily memory/projects memory/core
fi

# Create today's daily log
TODAY=$(date +%Y-%m-%d)
if [ ! -f "memory/daily/$TODAY.md" ]; then
    echo "# $TODAY" > "memory/daily/$TODAY.md"
    echo "" >> "memory/daily/$TODAY.md"
    echo "## Session" >> "memory/daily/$TODAY.md"
    echo "" >> "memory/daily/$TODAY.md"
    echo "### Active Projects" >> "memory/daily/$TODAY.md"
    echo "- " >> "memory/daily/$TODAY.md"
    echo "" >> "memory/daily/$TODAY.md"
    echo "✅ Created daily log: memory/daily/$TODAY.md"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. cd $WORKSPACE"
echo "2. Edit .openclaw/core/IDENTITY.md  (your agent persona)"
echo "3. Edit .openclaw/core/SOUL.md      (behavior rules)"
echo "4. Edit .openclaw/core/USER.md      (your human's info)"
echo "5. Initialize Git: cd memory && git init && git remote add origin <your-repo>"
echo ""
echo "Quick start: .openclaw/scripts/log.sh"
echo "           .openclaw/scripts/sync.sh"
