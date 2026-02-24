#!/usr/bin/env python3
"""
Quick export of MEMORY.md to MSAM atoms

Extracts key facts and stores them as MSAM atoms.
"""

import subprocess
from pathlib import Path

# Paths
MEMORY_FILE = Path.home() / "pi-mono-workspace" / "MEMORY.md"
MSAM_REPO = Path.home() / "msam"

# Key facts to extract (each as a separate atom)
FACTS = [
    "User Alessandro (Majinbu) is the founder and owner of OpenClaw",
    "User email: ciao@openclaw.ai",
    "User phone: +39 329 348 4956",
    "User location: Bergamo, Italia",
    "User timezone: UTC",
    "User GitHub: https://github.com/arosstale",
    "Rayan is CEO and Founder of N-Art (AI Trading platform)",
    "Rayan email: rayan@n-art.io",
    "Rayan Telegram ID: 5264265623",
    "OpenClaw Sales Site: https://openclaw-sales.netlify.app",
    "N-Art Sales Site: https://n-art-sales.netlify.app",
    "OpenClaw Wrappers Site: https://openclaw-wrappers.vercel.app",
    "VibeClaw Site: https://vibeclaw-openclaw.netlify.app",
    "OpenClaw workspace: ~/pi-mono-workspace",
    "OpenClaw memory template: https://github.com/arosstale/openclaw-memory-template",
    "MSAM (Multi-Stream Adaptive Memory): https://github.com/jadenschwab/msam",
    "MSAM provides 99.3% token savings (51 vs 7,327 tokens)",
    "MSAM has 4 memory streams: semantic, episodic, procedural, working",
    "MSAM uses ACT-R activation scoring and confidence-gated retrieval",
    "T013: Graceful Degradation > Brittle Perfection (Trading wisdom)",
    "T014: The RSI Veto Protocol - RSI > 70 veto for longs",
    "T015: The Falling Knife Paradox - Low RSI in downtrend is a trap",
    "Netlify auth token in ~/.bashrc",
    "Netlify team: Fdsa, email: adedararosstale@gmail.com",
    "PostgreSQL passwords changed (swarm_pg, pgvector)",
    "Git repo: https://github.com/arosstale/pi-mono-workspace",
    "Node version: v24.13.1",
    "Shell: bash 5.1.16",
    "OpenSSH, fail2ban, UFW security hardened",
    "Trading systems: Quant, nano-agent, SuperQuant, Dalio, Nash",
    "Skill location: ~/pi-mono-workspace/skills/",
    "Sales sites auto-deploy to Netlify on git push",
]


def store_atom(content: str) -> bool:
    """Store a single atom in MSAM."""
    try:
        result = subprocess.run(
            ["python", "-m", "msam.remember", "store", content],
            cwd=MSAM_REPO,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return data.get("stored", False)
        return False
    except Exception as e:
        print(f"Error storing atom: {e}", file=sys.stderr)
        return False


def main():
    """Export key facts to MSAM."""
    print(f"📤 Exporting {len(FACTS)} facts to MSAM...")

    stored = 0
    for fact in FACTS:
        if store_atom(fact):
            stored += 1
            print(f"  ✓ [{stored}/{len(FACTS)}] {fact[:60]}...")
        else:
            print(f"  ✗ Failed: {fact[:60]}...")

    print(f"\n✅ Exported {stored}/{len(FACTS)} atoms to MSAM")

    # Show stats
    print("\n📊 MSAM Stats:")
    result = subprocess.run(
        ["python", "-m", "msam.remember", "stats"],
        cwd=MSAM_REPO,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(result.stdout)


if __name__ == "__main__":
    import sys
    main()
