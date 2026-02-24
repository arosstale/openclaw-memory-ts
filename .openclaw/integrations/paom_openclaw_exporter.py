"""
OpenClaw Memory Integration for PAOM.

Exports PAOM observations to OpenClaw memory files (memory/YYYY-MM-DD.md).
"""

from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    from observational_memory import ObservationalMemory, ObservationConfig
    PAOM_AVAILABLE = True
except ImportError:
    PAOM_AVAILABLE = False


class PAOMOpenClawExporter:
    """
    Exports PAOM observations to OpenClaw memory format.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
    def export_observations(
        self, 
        paom, 
        date_str: Optional[str] = None,
        append: bool = True
    ) -> str:
        """
        Export PAOM observations to OpenClaw memory file.
        
        Args:
            paom: ObservationalMemory instance
            date_str: Date string in YYYY-MM-DD format (default: today)
            append: Append to existing file
            
        Returns:
            Path to exported file
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        memory_path = self.memory_dir / f"{date_str}.md"
        
        # Get observations
        record = paom.get_observation_record("openclaw_export")
        
        if not record or not record.observations:
            return str(memory_path)
            
        # Format observations
        lines = []
        for obs in record.observations:
            emoji = obs.priority  # 🔴, 🟡, 🟢
            time_str = obs.timestamp.strftime("%H:%M")
            
            # Format: * 🔴 (14:30) User prefers dark mode
            lines.append(f"* {emoji} ({time_str}) {obs.content}")
            
            # Add referenced date if available
            if obs.referenced_date:
                ref_date = obs.referenced_date.strftime("%Y-%m-%d")
                lines[-1] += f" (referenced {ref_date})"
                
        # Write to file
        mode = "a" if append and memory_path.exists() else "w"
        
        with open(memory_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n\n")
                
            # Add header if new file
            if mode == "w":
                f.write(f"# Memory Log - {date_str}\n\n")
                
            # Add section header
            f.write(f"## PAOM Observations ({datetime.now().strftime('%H:%M')})\n\n")
            
            # Write observations
            for line in lines:
                f.write(f"{line}\n")
                
        return str(memory_path)
        
    def export_reflections(
        self, 
        paom, 
        date_str: Optional[str] = None,
        append: bool = True
    ) -> str:
        """
        Export PAOM reflections to OpenClaw memory file.
        
        Args:
            paom: ObservationalMemory instance
            date_str: Date string in YYYY-MM-DD format (default: today)
            append: Append to existing file
            
        Returns:
            Path to exported file
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        memory_path = self.memory_dir / f"{date_str}.md"
        
        # Get record
        record = paom.get_observation_record("openclaw_export")
        
        if not record:
            return str(memory_path)
            
        mode = "a" if append and memory_path.exists() else "w"
        
        with open(memory_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n\n")
                
            # Add section header
            f.write(f"## PAOM Reflections ({datetime.now().strftime('%H:%M')})\n\n")
            
            # Add suggested response
            if record.suggested_response:
                f.write(f"**Suggested Response**:\n{record.suggested_response}\n\n")
                
            # Add current task
            if record.current_task:
                f.write(f"**Current Task**:\n{record.current_task}\n\n")
                
        return str(memory_path)
        
    def export_all(
        self, 
        paom, 
        date_str: Optional[str] = None
    ) -> dict:
        """
        Export both observations and reflections.
        
        Returns:
            Dict with paths to exported files
        """
        obs_path = self.export_observations(paom, date_str, append=True)
        ref_path = self.export_reflections(paom, date_str, append=True)
        
        return {
            "observations": obs_path,
            "reflections": ref_path
        }


def auto_export_on_threshold(
    paom, 
    memory_dir: str = "memory",
    export_threshold: int = 50
) -> bool:
    """
    Auto-export when PAOM observation count exceeds threshold.
    
    Args:
        paom: ObservationalMemory instance
        memory_dir: Directory for memory files
        export_threshold: Observation count threshold
        
    Returns:
        True if export was triggered
    """
    record = paom.get_observation_record("openclaw_export")
    
    if not record or len(record.observations) < export_threshold:
        return False
        
    # Export
    exporter = PAOMOpenClawExporter(memory_dir)
    exporter.export_all(paom)
    
    return True
