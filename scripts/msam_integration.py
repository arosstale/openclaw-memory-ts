#!/usr/bin/env python3
"""
MSAM Integration for OpenClaw Memory Template

Exports MEMORY.md, USER.md, LEARNINGS.md to MSAM atoms
Imports MSAM context for agent startup

Usage:
    python msam_integration.py init     # Initialize MSAM
    python msam_integration.py export    # Export memories to MSAM
    python msam_integration.py import    # Import context from MSAM
    python msam_integration.py status    # Show MSAM stats
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# Configuration
WORKSPACE = Path.home() / "pi-mono-workspace"
MSAM_REPO = Path.home() / "msam"  # MSAM is installed at ~/msam
MEMORY_DIR = WORKSPACE / "openclaw-memory-template" / ".openclaw" / "core"
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
USER_FILE = MEMORY_DIR / "USER.md"
LEARNINGS_FILE = MEMORY_DIR / "LEARNINGS.md"

# Stream mappings
STREAM_MAPPINGS = {
    "system_info": "semantic",
    "user_profile": "semantic",
    "agent_identity": "semantic",
    "preferences": "semantic",
    "projects": "semantic",
    "key_contacts": "semantic",
    "services": "semantic",
    "api_keys": "semantic",
    "aliases": "semantic",
    "file_locations": "semantic",
    "critical_config": "semantic",
    "git_repos": "semantic",
    "resources": "semantic",
    "important_dates": "semantic",
    "emotional_resonance": "episodic",
    "evolutionary_history": "semantic",
}


def run_msam_cmd(cmd_parts):
    """Run MSAM CLI command and return JSON result."""
    try:
        result = subprocess.run(
            ["python", "-m", "msam.remember"] + cmd_parts,
            cwd=MSAM_REPO,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"MSAM error: {result.stderr}", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"MSAM command failed: {e}", file=sys.stderr)
        return None


def init_msam():
    """Initialize MSAM database."""
    print("🔧 Initializing MSAM...")

    if not MSAM_REPO.exists():
        print(f"❌ MSAM repo not found at {MSAM_REPO}")
        print("   Clone from: https://github.com/jadenschwab/msam")
        return False

    # Check if already initialized
    msam_dir = Path.home() / ".msam"
    if msam_dir.exists():
        print("✅ MSAM already initialized")
        return True

    # Initialize
    result = subprocess.run(
        ["python", "-m", "msam.init_db"],
        cwd=MSAM_REPO,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ MSAM database initialized")
        print(f"   Config: {msam_dir / 'msam.toml'}")
        return True
    else:
        print(f"❌ MSAM init failed: {result.stderr}")
        return False


def parse_xml_memory(content: str) -> dict:
    """Parse MEMORY.md XML structure into structured data."""
    atoms = []

    try:
        # Parse XML
        root = ET.fromstring(f"<root>{content}</root>")

        # Extract sections
        for section in root:
            section_name = section.tag

            # Map to stream
            stream = STREAM_MAPPINGS.get(section_name, "semantic")

            # Extract text content
            text_content = ET.tostring(section, encoding="unicode", method="text")

            # Clean up whitespace
            text_content = " ".join(text_content.split())

            if text_content and len(text_content) > 10:
                atoms.append({
                    "content": f"[{section_name}] {text_content[:500]}...",
                    "stream": stream,
                    "arousal": 0.5,
                    "valence": 0.0,
                    "encoding_confidence": 0.8
                })

    except ET.ParseError as e:
        print(f"⚠️  XML parse error: {e}")
        print("   Using fallback text extraction")

        # Fallback: split by sections
        lines = content.split("\n")
        current_section = "general"
        current_content = []

        for line in lines:
            if line.startswith("## <"):
                # Save previous section
                if current_content:
                    atoms.append({
                        "content": f"[{current_section}] {' '.join(current_content[:100])}",
                        "stream": STREAM_MAPPINGS.get(current_section, "semantic"),
                        "arousal": 0.5,
                        "valence": 0.0,
                        "encoding_confidence": 0.8
                    })
                    current_content = []

                current_section = line.replace("## <", "").replace(">", "")
            else:
                current_content.append(line)

    return atoms


def export_to_msam():
    """Export memories to MSAM atoms."""
    print("📤 Exporting memories to MSAM...")

    exported = 0

    # Export MEMORY.md
    if MEMORY_FILE.exists():
        print(f"   Processing {MEMORY_FILE}...")
        content = MEMORY_FILE.read_text()
        atoms = parse_xml_memory(content)

        for atom in atoms:
            result = run_msam_cmd(["store", atom["content"]])
            if result and result.get("stored"):
                exported += 1
                print(f"     ✓ Stored: {atom['content'][:50]}...")

    # Export USER.md
    if USER_FILE.exists():
        print(f"   Processing {USER_FILE}...")
        content = USER_FILE.read_text()
        lines = [l.strip() for l in content.split("\n") if l.strip() and len(l) > 20]

        for line in lines[:100]:  # Limit to first 100 meaningful lines
            result = run_msam_cmd(["store", line])
            if result and result.get("stored"):
                exported += 1

    # Export LEARNINGS.md
    if LEARNINGS_FILE.exists():
        print(f"   Processing {LEARNINGS_FILE}...")
        content = LEARNINGS_FILE.read_text()
        lines = [l.strip() for l in content.split("\n") if l.strip() and len(l) > 20]

        for line in lines[:50]:  # Limit to first 50 learning points
            result = run_msam_cmd(["store", line])
            if result and result.get("stored"):
                exported += 1

    print(f"\n✅ Exported {exported} atoms to MSAM")


def import_from_msam(query: str = "user preferences"):
    """Import context from MSAM."""
    print("📥 Importing context from MSAM...")

    result = run_msam_cmd(["query", query])

    if result:
        print(f"\n✅ Confidence Tier: {result.get('confidence_tier', 'unknown')}")
        print(f"   Tokens: {result.get('total_tokens', 0)}")
        print(f"   Items: {result.get('items_returned', 0)}")

        if result.get("atoms"):
            print("\n   Retrieved:")
            for atom in result["atoms"][:5]:
                print(f"     - {atom['content'][:80]}...")

        return result
    else:
        print("❌ Failed to import from MSAM")
        return None


def show_status():
    """Show MSAM statistics."""
    print("📊 MSAM Status")
    print("=" * 50)

    result = run_msam_cmd(["stats"])

    if result:
        print(f"Total Atoms: {result.get('total_atoms', 0)}")
        print(f"Active Atoms: {result.get('active_atoms', 0)}")
        print(f"Total Accesses: {result.get('total_accesses', 0)}")
        print(f"Avg Activation: {result.get('avg_activation', 0):.2f}")
        print(f"Est Tokens: {result.get('est_active_tokens', 0)}")
        print(f"DB Size: {result.get('db_size_kb', 0):.1f} KB")

        # Show by stream
        by_stream = result.get('by_stream', {})
        if by_stream:
            print("\nBy Stream:")
            for stream, count in by_stream.items():
                print(f"  {stream}: {count}")

        # Show by profile
        by_profile = result.get('by_profile', {})
        if by_profile:
            print("\nBy Profile:")
            for profile, count in by_profile.items():
                print(f"  {profile}: {count}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python msam_integration.py <command>")
        print("\nCommands:")
        print("  init    - Initialize MSAM database")
        print("  export  - Export memories to MSAM")
        print("  import  - Import context from MSAM")
        print("  status  - Show MSAM statistics")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_msam()
    elif command == "export":
        export_to_msam()
    elif command == "import":
        query = sys.argv[2] if len(sys.argv) > 2 else "user preferences"
        import_from_msam(query)
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
