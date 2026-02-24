"""
ALMA + ROLL Hybrid Integration.

Combines ALMA's meta-learning (design optimization) with ROLL's post-training 
optimization (weight tuning) for two-level optimization.
"""

from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from roll.roll_framework import ROLLFramework

try:
    from alma.alma_agent import ALMAAgent
    ALMA_AVAILABLE = True
except ImportError:
    ALMA_AVAILABLE = False
    print("ALMA not available, using mock")


class ALMA_ROLL_Hybrid:
    """
    Hybrid optimizer combining ALMA (meta-learning) and ROLL (weight optimization).
    """
    
    def __init__(self, alma_db_path: str = None, roll_learning_rate: float = 0.01):
        if ALMA_AVAILABLE and alma_db_path:
            try:
                self.alma = ALMAAgent(db_path=alma_db_path)
            except Exception as e:
                print(f"ALMA initialization failed: {e}, using mock")
                self.alma = MockALMAAgent()
        else:
            self.alma = MockALMAAgent()
            
        self.roll = ROLLFramework(learning_rate=roll_learning_rate)
        self.history = []
        
    def two_level_optimize(self, 
                          current_weights: Dict[str, float],
                          trajectories: List[List[Dict[str, Any]]],
                          num_alma_iterations: int = 3,
                          num_roll_iterations: int = 5) -> Dict[str, Any]:
        """
        Perform two-level optimization:
        1. Level 1: ALMA optimizes meta-designs (hyperparameters)
        2. Level 2: ROLL optimizes weights given the meta-design
        """
        results = []
        
        # Level 1: ALMA Meta-Learning
        for i in range(num_alma_iterations):
            # Get optimal design from ALMA
            alma_design = self.alma.propose_design()
            
            # Level 2: ROLL Weight Optimization
            optimized_weights = current_weights.copy()
            
            for j in range(num_roll_iterations):
                # Use ALMA design to tune ROLL
                if hasattr(alma_design, "parameters"):
                    params = alma_design.parameters
                    if "learning_rate" in params:
                        self.roll.learning_rate = params["learning_rate"]
                    if "batch_size" in params:
                        # Use batch_size for trajectory sampling
                        pass
                        
                # Optimize weights with current trajectories
                optimized_weights = self.roll.optimize_weights(
                    optimized_weights, 
                    trajectories
                )
                
            # Evaluate final weights
            final_score = self._evaluate_weights(optimized_weights, trajectories)
            
            results.append({
                "iteration": i,
                "alma_design": alma_design,
                "final_weights": optimized_weights,
                "score": final_score
            })
            
            self.history.append(results[-1])
            
        # Return best result
        best_result = max(results, key=lambda r: r["score"])
        
        return {
            "best_iteration": best_result["iteration"],
            "best_design": best_result["alma_design"],
            "best_weights": best_result["final_weights"],
            "best_score": best_result["score"],
            "all_iterations": results
        }
        
    def _evaluate_weights(self, weights: Dict[str, float], trajectories: List) -> float:
        """Evaluate weights on trajectories."""
        total_reward = 0
        for traj in trajectories:
            for step in traj:
                # Simple evaluation: weight-weighted reward
                step_reward = step.get("reward", 0)
                # In real system, would use strategy-specific weights
                total_reward += step_reward
        return total_reward / len(trajectories) if trajectories else 0
        
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get history of optimization iterations."""
        return self.history


class MockALMAAgent:
    """Mock ALMA agent for testing without full ALMA."""
    
    class MockDesign:
        def __init__(self):
            self.parameters = {
                "learning_rate": 0.05,
                "batch_size": 10,
                "mutation_strength": 0.1
            }
            
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.iteration = 0
        
    def propose_design(self):
        """Propose a mock design."""
        design = self.MockDesign()
        # Vary parameters slightly each time
        design.parameters["learning_rate"] = 0.05 + (self.iteration * 0.01)
        self.iteration += 1
        return design


class ALMA_ROLL_CLI:
    """CLI for ALMA + ROLL hybrid optimization."""
    
    @staticmethod
    def optimize(weights_file: str, trajectories_file: str):
        """Run two-level optimization."""
        # Load weights and trajectories (in real system)
        weights = {"strategy_a": 0.5, "strategy_b": 0.5}
        
        # Generate mock trajectories
        from rock.rock_environment import V7SimulationEnv
        env = V7SimulationEnv()
        trajectories = []
        for _ in range(10):
            trajectories.append(env.generate_trajectory(lambda obs: "buy", num_steps=50))
        
        # Run optimization
        hybrid = ALMA_ROLL_Hybrid()
        result = hybrid.two_level_optimize(weights, trajectories)
        
        print(f"🚀 ALMA + ROLL Two-Level Optimization")
        print(f"   Best Score: {result['best_score']:.4f}")
        print(f"   Best Weights: {result['best_weights']}")
        print(f"   Best Design: {result['best_design'].parameters}")
        
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ALMA + ROLL Hybrid CLI")
    parser.add_argument("command", choices=["optimize"])
    parser.add_argument("--weights", help="Initial weights file")
    parser.add_argument("--trajectories", help="Trajectories file")
    
    args = parser.parse_args()
    
    if args.command == "optimize":
        ALMA_ROLL_CLI.optimize(args.weights, args.trajectories)
