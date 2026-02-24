#!/usr/bin/env python3
"""
Fix Research Docs Organization
- Move papers from lowercase folders to proper case
- Remove duplicate papers
- Clean up organization
"""

import os
import shutil
from pathlib import Path

# Base directory
RESEARCH_BASE = Path.home() / "pi-mono-workspace/openclaw-memory-template/research/papers"

# Mapping of lowercase -> proper folder names
FOLDER_MAPPINGS = {
    "cognitive": "Cognitive Science",
    "ai": "Artificial Intelligence",
    "trading": "Trading & Finance",
}

def fix_organization():
    """Fix folder organization"""
    print("=" * 60)
    print("🔧 Fixing Research Docs Organization")
    print("=" * 60)
    print()

    papers_base = RESEARCH_BASE

    for lowercase_name, proper_name in FOLDER_MAPPINGS.items():
        lowercase_path = papers_base / lowercase_name
        proper_path = papers_base / proper_name

        # Check if lowercase folder exists
        if lowercase_path.exists():
            print(f"📁 Found: {lowercase_name}/")

            # Ensure proper folder exists
            proper_path.mkdir(exist_ok=True)

            # Move papers from lowercase to proper
            papers_to_move = list(lowercase_path.glob("*.md"))
            print(f"   Processing {len(papers_to_move)} papers...")

            for paper in papers_to_move:
                dest = proper_path / paper.name
                # Check for duplicates
                if dest.exists():
                    print(f"   ⚠️  Duplicate: {paper.name}")
                    # Compare and remove if identical
                    try:
                        with open(paper, 'r') as f1, open(dest, 'r') as f2:
                            if f1.read() == f2.read():
                                print(f"   🗑️  Removing duplicate: {paper.name}")
                                paper.unlink()
                    except:
                        pass
                    continue

                # Move if not duplicate
                try:
                    shutil.move(str(paper), str(dest))
                    print(f"   ✓ Moved: {paper.name}")
                except Exception as e:
                    print(f"   ❌ Error moving {paper.name}: {e}")

            # Try to remove lowercase folder if empty
            try:
                remaining = list(lowercase_path.glob("*"))
                if len(remaining) == 0 and lowercase_path.exists():
                    lowercase_path.rmdir()
                    print(f"   🗑️  Removed empty folder: {lowercase_name}/")
            except Exception as e:
                print(f"   ℹ️  Could not remove {lowercase_name}: {e}")

            print()

    # Summary
    print("=" * 60)
    print("✅ Organization Fix Complete!")
    print("=" * 60)

    # Show final structure
    print("\n📊 Final Paper Folders:")
    print()

    for folder in sorted(papers_base.iterdir()):
        if folder.is_dir():
            paper_count = len(list(folder.glob("*.md")))
            print(f"   • {folder.name}/ ({paper_count} papers)")

    print()


if __name__ == "__main__":
    fix_organization()
