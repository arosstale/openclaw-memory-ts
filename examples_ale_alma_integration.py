"""
ALE + ALMA Integration Example.

Demonstrates the full pipeline:
1. ROCK: Generate trajectories in sandbox
2. ROLL: Optimize weights with two-level optimization
3. ALMA: Meta-learn optimal designs
4. IPA: Evaluate with interaction-perceptive chunks
5. PAOM: Store and reflect on observations
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / ".openclaw"))

try:
    from rock.rock_environment import V7SimulationEnv
    from roll.alma_roll_integration import ALMA_ROLL_Hybrid
    from ipa.ipa_evaluator import IPAEvaluator
    from ipa.paom_ipa_integration import PAOM_IPA_Integrator
except ImportError as e:
    print(f"Import error: {e}")
    print("Attempting to import with absolute paths...")
    # Fallback to direct imports
    import os
    os.chdir(str(Path(__file__).parent))
    from .openclaw.rock.rock_environment import V7SimulationEnv
    from .openclaw.roll.alma_roll_integration import ALMA_ROLL_Hybrid
    from .openclaw.ipa.ipa_evaluator import IPAEvaluator
    from .openclaw.ipa.paom_ipa_integration import PAOM_IPA_Integrator


def demo_full_pipeline():
    """Run the full ALE + ALMA pipeline demo."""
    
    print("🐺📿 ALE + ALMA Full Pipeline Demo\n")
    
    # ============================================
    # Phase 1: ROCK - Trajectory Generation
    # ============================================
    print("📊 Phase 1: ROCK - Trajectory Generation")
    print("-" * 50)
    
    env = V7SimulationEnv(market_regime="sideways", initial_balance=10000.0)
    
    # Simple strategy: buy on odd steps, sell on even
    def simple_strategy(obs):
        return "buy" if obs["step"] % 2 == 0 else "sell"
    
    # Generate trajectory
    trajectory = env.generate_trajectory(simple_strategy, num_steps=50)
    
    # Calculate basic metrics
    total_reward = sum(step["reward"] for step in trajectory)
    final_balance = env.balance
    return_pct = (final_balance - env.initial_balance) / env.initial_balance * 100
    
    print(f"   Generated {len(trajectory)} steps")
    print(f"   Total Reward: {total_reward:.2f}")
    print(f"   Return: {return_pct:+.2f}%")
    print(f"   Final Balance: ${final_balance:.2f}")
    
    # ============================================
    # Phase 2: ROLL + ALMA - Two-Level Optimization
    # ============================================
    print("\n🔄 Phase 2: ROLL + ALMA - Two-Level Optimization")
    print("-" * 50)
    
    # Generate multiple trajectories for optimization
    trajectories = []
    for _ in range(5):
        env.reset()
        traj = env.generate_trajectory(simple_strategy, num_steps=30)
        trajectories.append(traj)
    
    # Initial weights
    initial_weights = {
        "trend_strategy": 0.6,
        "momentum_strategy": 0.4
    }
    
    print(f"   Initial Weights: {initial_weights}")
    print(f"   Optimizing with {len(trajectories)} trajectories...")
    
    # Run two-level optimization
    hybrid = ALMA_ROLL_Hybrid()
    result = hybrid.two_level_optimize(
        initial_weights,
        trajectories,
        num_alma_iterations=2,
        num_roll_iterations=3
    )
    
    print(f"\n   ✅ Optimization Complete!")
    print(f"   Best Score: {result['best_score']:.4f}")
    print(f"   Best Weights: {result['best_weights']}")
    print(f"   Best Learning Rate: {result['best_design'].parameters['learning_rate']:.3f}")
    
    # ============================================
    # Phase 3: IPA - Interaction Evaluation
    # ============================================
    print("\n🔍 Phase 3: IPA - Interaction Evaluation")
    print("-" * 50)
    
    ipa = IPAEvaluator(gamma=0.99)
    ipa_result = ipa.evaluate(trajectory)
    
    print(f"   Total Score: {ipa_result['total_score']:.4f}")
    print(f"   Num Chunks: {ipa_result['num_chunks']}")
    print(f"   Avg Chunk Score: {ipa_result['avg_chunk_score']:.4f}")
    
    print(f"\n   Top Chunks:")
    for i, chunk in enumerate(ipa_result['chunks'][:3]):
        print(f"     Chunk {i}: Score {chunk.score:.2f} ({len(chunk.content)} steps)")
    
    # ============================================
    # Phase 4: PAOM - Memory & Reflection
    # ============================================
    print("\n🧠 Phase 4: PAOM - Memory & Reflection")
    print("-" * 50)
    
    integrator = PAOM_IPA_Integrator(db_path="demo_paom.db")
    
    # In real system: would process actual messages through PAOM
    # For demo: show integration is ready
    print("   PAOM + IPA Integration Ready")
    print("   To use:")
    print("     1. Pass messages to PAOM: integrator.paom.process_messages(thread_id, messages)")
    print("     2. Chunk records: chunks = integrator.chunk_paom_records(thread_id)")
    print("     3. Evaluate: result = integrator.evaluate_memory_quality(thread_id)")
    
    # ============================================
    # Summary
    # ============================================
    print("\n📊 Pipeline Summary")
    print("-" * 50)
    print(f"   ROCK Trajectories: {len(trajectories)}")
    print(f"   ROLL+ALMA Score: {result['best_score']:.4f}")
    print(f"   IPA Chunks: {ipa_result['num_chunks']}")
    print(f"   PAOM Integration: Ready")
    
    print("\n✅ Full Pipeline Demo Complete!")
    print("\n🔗 To use in production:")
    print("   1. Replace simple_strategy with V7 strategies")
    print("   2. Connect to real ALMA database")
    print("   3. Use real PAOM for live trading observations")
    print("   4. Run Terminal Bench Pro for validation")
    
    return {
        "trajectory": trajectory,
        "optimization": result,
        "ipa": ipa_result,
        "chunks": []  # Would be populated with real PAOM data
    }


if __name__ == "__main__":
    demo_full_pipeline()
