#!/usr/bin/env python3
"""
ALMA Integration with Observational Memory

Combines ALMA meta-learning with PAOM for self-improving memory systems.
"""

import sys
from pathlib import Path

# Add .openclaw to path
openclaw_path = Path(__file__).parent / ".openclaw"
sys.path.insert(0, str(openclaw_path))

from observational_memory import ObservationalMemory, ObservationConfig
from alma.alma_agent import ALMAAgent, MemoryDesign
from datetime import datetime
from typing import Dict, List, Optional, Callable


class ALMAPAOSystem:
    """
    Combines ALMA meta-learning with Observational Memory.

    Architecture:
    - ALMA: Discovers optimal memory designs
    - PAOM: Implements memory design
    - Loop: ALMA proposes → PAOM implements → ALMA evaluates
    """

    def __init__(
        self,
        alma_db_path: str = ".openclaw/alma_designs.db",
        paom_config: Optional[ObservationConfig] = None
    ):
        """
        Initialize ALMA+PAOM system.

        Args:
            alma_db_path: Path to ALMA designs database
            paom_config: Configuration for Observational Memory
        """
        # ALMA for meta-learning
        self.alma = ALMAAgent(alma_db_path)

        # PAOM for memory implementation
        self.paom_config = paom_config or ObservationConfig()
        self.paom = ObservationalMemory(self.paom_config)

    def apply_best_design(self) -> MemoryDesign:
        """
        Apply the best-performing memory design to PAOM.

        Returns:
            Best memory design
        """
        # Get best design from ALMA
        best_design = self.alma.get_best_design()

        if not best_design:
            # No designs yet, create initial design
            print("No designs found, creating initial design...")
            best_design = self.alma.propose_design()
            return best_design

        # Apply design parameters to PAOM
        self._apply_design_to_paom(best_design)

        return best_design

    def run_meta_learning_cycle(
        self,
        num_iterations: int = 5,
        num_designs_per_iteration: int = 3,
        evaluator: Optional[Callable] = None
    ) -> List[MemoryDesign]:
        """
        Run complete meta-learning cycle.

        Args:
            num_iterations: Number of iterations to run
            num_designs_per_iteration: Designs per iteration
            evaluator: Optional evaluator function

        Returns:
            List of evaluated designs
        """
        all_designs = []

        for iteration in range(num_iterations):
            print(f"\n🔄 Iteration {iteration + 1}/{num_iterations}")

            # Run ALMA iteration
            best_design, results = self.alma.run_meta_learning_iteration(
                num_designs=num_designs_per_iteration,
                evaluator=evaluator or self._default_evaluator
            )

            all_designs.extend([r for r in results])

            # Apply best design
            if best_design:
                self._apply_design_to_paom(best_design)
                print(f"✅ Applied design: {best_design.design_id} (score: {best_design.performance_score:.2f})")

        return all_designs

    def _apply_design_to_paom(self, design: MemoryDesign):
        """Apply design parameters to PAOM."""
        params = design.parameters

        # Update PAOM configuration
        if "observation_threshold" in params:
            self.paom_config.observation_threshold = params["observation_threshold"]
        if "reflection_threshold" in params:
            self.paom_config.reflection_threshold = params["reflection_threshold"]
        if "observer_temperature" in params:
            self.paom_config.observer_temperature = params["observer_temperature"]
        if "reflector_temperature" in params:
            self.paom_config.reflector_temperature = params["reflector_temperature"]
        if "llm_provider" in params:
            self.paom_config.llm_provider = params["llm_provider"]
        if "use_tiktoken" in params:
            self.paom_config.use_tiktoken = params["use_tiktoken"]

        # Store current design reference
        self._current_design = design

        print(f"🔧 Applied design parameters:")
        for key, value in params.items():
            print(f"   {key}: {value}")

    def _default_evaluator(self, design: MemoryDesign) -> Dict[str, float]:
        """Default evaluator for testing."""
        import random
        return {
            "accuracy": round(random.uniform(85.0, 95.0), 2),
            "efficiency": round(random.uniform(80.0, 90.0), 2),
            "compression": round(random.uniform(70.0, 85.0), 2),
        }

    def get_system_stats(self) -> Dict:
        """Get statistics about the entire system."""
        alma_stats = self.alma.get_stats()

        return {
            "alma": alma_stats,
            "paom_config": {
                "observation_threshold": self.paom_config.observation_threshold,
                "reflection_threshold": self.paom_config.reflection_threshold,
                "llm_provider": self.paom_config.llm_provider,
                "use_tiktoken": self.paom_config.use_tiktoken,
            },
            "current_design": getattr(self, '_current_design', None),
        }


def example_self_improving_system():
    """Example of self-improving memory system."""
    print("🐺📿 Self-Improving Memory System Example")
    print("=" * 60)

    # Initialize system
    system = ALMAPAOSystem()

    # Run initial optimization
    print("\n🚀 Initial optimization...")
    designs = system.run_meta_learning_cycle(
        num_iterations=3,
        num_designs_per_iteration=3,
    )

    # Get best design
    best_design = system.alma.get_best_design()
    if best_design:
        print(f"\n🏆 Best design: {best_design.design_id}")
        print(f"   Score: {best_design.performance_score:.2f}")
        print(f"   Evaluations: {best_design.num_evaluations}")

    # Get system stats
    stats = system.get_system_stats()
    print(f"\n📈 System statistics:")
    print(f"   ALMA designs: {stats['alma']['num_designs']}")
    print(f"   ALMA evaluations: {stats['alma']['num_evaluations']}")
    print(f"   Best score: {stats['alma']['best_score']:.2f}")

    print("\n✅ Self-improving system example complete")


if __name__ == "__main__":
    example_self_improving_system()
