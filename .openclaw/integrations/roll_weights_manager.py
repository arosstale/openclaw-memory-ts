"""
ROLL Strategy Weights Manager for OpenClaw Memory.

Stores and retrieves ROLL-optimized strategy weights in OpenClaw memory.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

try:
    from roll.roll_framework import ROLLFramework
    ROLL_AVAILABLE = True
except ImportError:
    ROLL_AVAILABLE = False


class StrategyWeights:
    """Strategy weights with metadata."""
    
    def __init__(self, 
                 strategy_id: str,
                 weights: Dict[str, float],
                 timestamp: Optional[str] = None,
                 score: float = 0.0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.strategy_id = strategy_id
        self.weights = weights
        self.timestamp = timestamp or datetime.now().isoformat()
        self.score = score
        self.metadata = metadata or {}
        
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            f"## Strategy Weights: {self.strategy_id}",
            "",
            f"**Updated**: {self.timestamp}",
            f"**Score**: {self.score:.4f}",
            "",
            "### Weights",
            ""
        ]
        
        # Format weights as table
        lines.append("| Strategy | Weight |")
        lines.append("|----------|--------|")
        for strategy, weight in sorted(self.weights.items(), 
                                     key=lambda x: -x[1]):
            pct = weight * 100
            lines.append(f"| {strategy} | {pct:.2f}% |")
            
        lines.append("")
        
        # Add metadata if available
        if self.metadata:
            lines.append("### Metadata")
            lines.append("")
            for key, value in self.metadata.items():
                lines.append(f"- **{key}**: {value}")
                
        lines.append("")
        lines.append("---")
        
        return "\n".join(lines)
        
    def to_json(self) -> str:
        """Convert to JSON format."""
        return json.dumps({
            "strategy_id": self.strategy_id,
            "weights": self.weights,
            "timestamp": self.timestamp,
            "score": self.score,
            "metadata": self.metadata
        }, indent=2)


class ROLLWeightsManager:
    """
    Manages ROLL-optimized strategy weights in OpenClaw memory.
    """
    
    def __init__(self, 
                 memory_path: str = "memory/STRATEGY_WEIGHTS.md",
                 history_path: str = "memory/STRATEGY_HISTORY.json"):
        self.memory_path = Path(memory_path)
        self.history_path = Path(history_path)
        
        # Ensure directories exist
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load history
        self.history = self._load_history()
        
    def save_weights(
        self,
        strategy_id: str,
        weights: Dict[str, float],
        score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        append: bool = True
    ) -> str:
        """
        Save optimized weights to OpenClaw memory.
        
        Args:
            strategy_id: Strategy identifier (e.g., "v7_trading")
            weights: Strategy weight dictionary
            score: Optimization score
            metadata: Additional metadata
            append: Append to existing file
            
        Returns:
            Path to saved file
        """
        # Create strategy weights object
        strategy_weights = StrategyWeights(
            strategy_id=strategy_id,
            weights=weights,
            score=score,
            metadata=metadata
        )
        
        # Save to markdown
        mode = "a" if append and self.memory_path.exists() else "w"
        
        with open(self.memory_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n\n")
                
            f.write(strategy_weights.to_markdown())
            
        # Update history
        self._update_history(strategy_weights)
        
        return str(self.memory_path)
        
    def load_latest_weights(self, strategy_id: str) -> Optional[Dict[str, float]]:
        """
        Load latest weights for a strategy.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Weight dictionary or None
        """
        # Search history for strategy
        for entry in reversed(self.history):
            if entry.get("strategy_id") == strategy_id:
                return entry.get("weights")
                
        return None
        
    def get_weight_history(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        Get weight evolution history for a strategy.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            List of historical weight entries
        """
        return [
            entry for entry in self.history
            if entry.get("strategy_id") == strategy_id
        ]
        
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize weights to sum to 1.0.
        
        Args:
            weights: Raw weight dictionary
            
        Returns:
            Normalized weight dictionary
        """
        total = sum(weights.values())
        
        if total == 0:
            # Equal distribution if all zeros
            count = len(weights)
            return {k: 1.0/count for k in weights}
            
        return {k: v/total for k, v in weights.items()}
        
    def optimize_with_roll(
        self,
        strategy_id: str,
        current_weights: Dict[str, float],
        trajectories: List[Any],
        num_iterations: int = 3
    ) -> StrategyWeights:
        """
        Optimize weights using ROLL framework.
        
        Args:
            strategy_id: Strategy identifier
            current_weights: Current weight distribution
            trajectories: Training trajectories
            num_iterations: Number of ROLL iterations
            
        Returns:
            Optimized strategy weights
        """
        if not ROLL_AVAILABLE:
            # Simple fallback
            weights = self.normalize_weights(current_weights)
            return StrategyWeights(
                strategy_id=strategy_id,
                weights=weights,
                score=0.5,
                metadata={"method": "normalization"}
            )
            
        # Use ROLL to optimize
        roll = ROLLFramework(learning_rate=0.01)
        optimized_weights = roll.optimize_weights(
            current_weights,
            trajectories
        )
        
        # Normalize
        final_weights = self.normalize_weights(optimized_weights)
        
        # Calculate score (simple metric)
        score = max(w for w in final_weights.values())
        
        strategy_weights = StrategyWeights(
            strategy_id=strategy_id,
            weights=final_weights,
            score=score,
            metadata={
                "method": "roll",
                "iterations": num_iterations,
                "learning_rate": 0.01
            }
        )
        
        # Save
        self.save_weights(
            strategy_id=strategy_id,
            weights=final_weights,
            score=score,
            metadata=strategy_weights.metadata
        )
        
        return strategy_weights
        
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load weight history from JSON file."""
        if not self.history_path.exists():
            return []
            
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
            
    def _update_history(self, strategy_weights: StrategyWeights):
        """Update weight history."""
        entry = {
            "strategy_id": strategy_weights.strategy_id,
            "weights": strategy_weights.weights,
            "timestamp": strategy_weights.timestamp,
            "score": strategy_weights.score,
            "metadata": strategy_weights.metadata
        }
        
        self.history.append(entry)
        
        # Save to file
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)
            
    def compare_weights(
        self, 
        old_weights: Dict[str, float], 
        new_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compare old and new weights.
        
        Returns:
            Dictionary of weight differences
        """
        differences = {}
        
        all_strategies = set(old_weights.keys()) | set(new_weights.keys())
        
        for strategy in all_strategies:
            old_val = old_weights.get(strategy, 0.0)
            new_val = new_weights.get(strategy, 0.0)
            differences[strategy] = new_val - old_val
            
        return differences


class ROLLWeightsManagerCLI:
    """CLI for ROLL weights management."""
    
    @staticmethod
    def demo_optimization():
        """Demo weight optimization."""
        manager = ROLLWeightsManager()
        
        # Mock V7 trading strategies
        current_weights = {
            "TrendCapturePro": 0.25,
            "VolatilityBreakoutSystem": 0.25,
            "SupertrendNovaCloud": 0.25,
            "DivergenceVolatilityEnhanced": 0.25
        }
        
        # Generate mock trajectories
        from rock.rock_environment import V7SimulationEnv
        env = V7SimulationEnv()
        trajectories = []
        
        for _ in range(5):
            env.reset()
            traj = env.generate_trajectory(lambda obs: "buy", num_steps=30)
            trajectories.append(traj)
        
        # Optimize
        print("🎯 ROLL Weight Optimization Demo")
        print("-" * 50)
        print(f"Original Weights: {current_weights}\n")
        
        optimized = manager.optimize_with_roll(
            strategy_id="v7_trading",
            current_weights=current_weights,
            trajectories=trajectories,
            num_iterations=3
        )
        
        print(f"Optimized Weights:")
        for strategy, weight in optimized.weights.items():
            print(f"  {strategy}: {weight:.3f}")
        print(f"\nScore: {optimized.score:.4f}")
        print(f"\n✅ Weights saved to: {manager.memory_path}")
        
        # Show history
        print(f"\nHistory entries: {len(manager.history)}")
        
        return optimized


if __name__ == "__main__":
    ROLLWeightsManagerCLI.demo_optimization()
