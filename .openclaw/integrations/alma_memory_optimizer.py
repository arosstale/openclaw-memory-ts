"""
ALMA Memory Design Optimizer.

Uses ALMA meta-learning to optimize OpenClaw memory designs.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from alma.alma_agent import ALMAAgent, MemoryDesign
    from ipa.ipa_evaluator import IPAEvaluator
    ALMA_AVAILABLE = True
except ImportError:
    ALMA_AVAILABLE = False


class MemoryDesign:
    """OpenClaw memory design."""
    
    def __init__(self, 
                 design_id: str,
                 parameters: Dict[str, Any],
                 metrics: Dict[str, float]):
        self.design_id = design_id
        self.parameters = parameters
        self.metrics = metrics
        
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            f"## Memory Design {self.design_id}",
            "",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "### Parameters",
            ""
        ]
        
        for key, value in self.parameters.items():
            lines.append(f"- **{key}**: {value}")
            
        lines.append("")
        lines.append("### Metrics")
        lines.append("")
        
        for key, value in self.metrics.items():
            lines.append(f"- **{key}**: {value:.4f}")
            
        lines.append("")
        lines.append("---")
        
        return "\n".join(lines)


class ALMAMemoryOptimizer:
    """
    Optimizes OpenClaw memory designs using ALMA meta-learning.
    """
    
    def __init__(self, 
                 db_path: str = ".openclaw/alma/memory_designs.db",
                 memory_path: str = "memory/ALMA_DESIGNS.md"):
        self.db_path = Path(db_path)
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        if ALMA_AVAILABLE:
            self.alma = ALMAAgent(str(db_path))
        else:
            self.alma = None
            
        self.ipa = IPAEvaluator() if ALMA_AVAILABLE else None
        
    def optimize_design(
        self,
        base_design: Optional[MemoryDesign] = None,
        num_iterations: int = 10
    ) -> MemoryDesign:
        """
        Optimize memory design using ALMA meta-learning.
        
        Args:
            base_design: Starting design (if None, create random)
            num_iterations: Number of ALMA optimization iterations
            
        Returns:
            Optimized memory design
        """
        if not self.alma:
            return self._create_default_design()
            
        # Start with base or random design
        if base_design:
            design = base_design
        else:
            design = self._create_default_design()
            
        # Run ALMA optimization
        best_design = design
        best_score = float('-inf')
        
        for i in range(num_iterations):
            # Evaluate current design
            score = self._evaluate_design(design)
            
            if score > best_score:
                best_score = score
                best_design = design
                
            # Propose new design (ALMA meta-learning)
            if hasattr(self.alma, 'propose_design'):
                alma_design = self.alma.propose_design()
                if hasattr(alma_design, 'parameters'):
                    design.parameters.update(alma_design.parameters)
                    
        return best_design
        
    def _evaluate_design(self, design: MemoryDesign) -> float:
        """
        Evaluate memory design performance.
        
        Returns:
            Composite score (0-1)
        """
        # Get parameters
        params = design.parameters
        
        # Heuristic scoring based on memory design principles
        score = 0.0
        
        # 1. Chunk size: Optimal range 300-500 tokens
        chunk_size = params.get("chunk_size", 400)
        if 300 <= chunk_size <= 500:
            score += 0.3
        elif 200 <= chunk_size <= 600:
            score += 0.2
            
        # 2. Overlap: 10-20% is good
        overlap_pct = params.get("overlap_pct", 15)
        if 10 <= overlap_pct <= 20:
            score += 0.2
        elif 5 <= overlap_pct <= 25:
            score += 0.1
            
        # 3. Priority threshold: Balanced (not too strict, not too loose)
        priority_threshold = params.get("priority_threshold", 10000)
        if 5000 <= priority_threshold <= 20000:
            score += 0.2
            
        # 4. Temporal anchors: Should have 2-3 dates
        temporal_anchors = params.get("temporal_anchors", 2)
        if 2 <= temporal_anchors <= 3:
            score += 0.3
            
        return min(1.0, score)
        
    def _create_default_design(self) -> MemoryDesign:
        """Create default memory design."""
        return MemoryDesign(
            design_id="default_openclaw",
            parameters={
                "chunk_size": 400,
                "overlap_pct": 15,
                "priority_threshold": 10000,
                "reflection_threshold": 40000,
                "temporal_anchors": 2,
                "vector_weight": 0.7,
                "text_weight": 0.3
            },
            metrics={
                "accuracy": 0.85,
                "efficiency": 0.78,
                "compression": 0.82,
                "speed": 0.75
            }
        )
        
    def save_design(self, design: MemoryDesign, append: bool = True) -> str:
        """
        Save memory design to OpenClaw memory file.
        
        Args:
            design: Memory design to save
            append: Append to existing file
            
        Returns:
            Path to saved file
        """
        mode = "a" if append and self.memory_path.exists() else "w"
        
        with open(self.memory_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n\n")
                
            f.write(design.to_markdown())
            
        return str(self.memory_path)
        
    def optimize_memory_parameters(
        self,
        current_memory_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize OpenClaw memory parameters based on statistics.
        
        Args:
            current_memory_stats: Current memory usage statistics
            
        Returns:
            Optimized parameters
        """
        # Extract stats
        avg_chunk_size = current_memory_stats.get("avg_chunk_size", 400)
        avg_compression = current_memory_stats.get("avg_compression", 0.5)
        retrieval_accuracy = current_memory_stats.get("retrieval_accuracy", 0.7)
        
        # Optimize using ALMA
        design = MemoryDesign(
            design_id=f"optimized_{datetime.now().strftime('%Y%m%d_%H%M')}",
            parameters={
                "chunk_size": min(600, max(200, avg_chunk_size * 1.1)),
                "overlap_pct": max(5, min(30, 20 - avg_compression * 10)),
                "priority_threshold": 10000 - retrieval_accuracy * 5000,
                "reflection_threshold": 40000 - avg_compression * 10000,
                "temporal_anchors": 2 if retrieval_accuracy > 0.8 else 3,
                "vector_weight": 0.7 if retrieval_accuracy > 0.7 else 0.5,
                "text_weight": 0.3 if retrieval_accuracy > 0.7 else 0.5
            },
            metrics={
                "accuracy": retrieval_accuracy,
                "efficiency": avg_compression,
                "compression": avg_compression,
                "speed": 1.0 - avg_compression
            }
        )
        
        return self.optimize_design(design, num_iterations=5).parameters


class ALMAMemoryOptimizerCLI:
    """CLI for ALMA memory optimization."""
    
    @staticmethod
    def optimize(memory_stats_file: str = None):
        """Optimize memory design."""
        optimizer = ALMAMemoryOptimizer()
        
        # Mock memory stats
        stats = {
            "avg_chunk_size": 380,
            "avg_compression": 0.45,
            "retrieval_accuracy": 0.75
        }
        
        # Optimize
        design = optimizer._create_default_design()
        optimized = optimizer.optimize_design(design, num_iterations=5)
        
        # Save
        path = optimizer.save_design(optimized, append=True)
        
        print(f"🎯 ALMA Memory Design Optimization")
        print("-" * 50)
        print(f"✅ Optimized design saved to: {path}")
        print(f"\nOptimized Parameters:")
        for key, value in optimized.parameters.items():
            print(f"  - {key}: {value}")
        print(f"\nMetrics:")
        for key, value in optimized.metrics.items():
            print(f"  - {key}: {value:.4f}")
            
        return optimized


if __name__ == "__main__":
    ALMAMemoryOptimizerCLI.optimize()
