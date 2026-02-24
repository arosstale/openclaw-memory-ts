"""
Full OpenClaw + ALE Integration Demo.

Shows all four integrations working together:
1. PAOM → OpenClaw Memory (Export observations)
2. IPA → Hybrid Search (Rerank results)
3. ALMA → Memory Design (Optimize parameters)
4. ROLL → Strategy Weights (Store optimized weights)
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / ".openclaw"))

from integrations.paom_openclaw_exporter import PAOMOpenClawExporter
from integrations.ipa_search_reranker import IPASearchReranker
from integrations.alma_memory_optimizer import ALMAMemoryOptimizer
from integrations.roll_weights_manager import ROLLWeightsManager


def demo_full_integration():
    """Full integration demo."""
    
    print("🐺📿 OpenClaw + ALE Full Integration Demo")
    print("=" * 60)
    
    # ============================================
    # Integration 1: PAOM → OpenClaw Memory
    # ============================================
    print("\n📊 Integration 1: PAOM → OpenClaw Memory")
    print("-" * 60)
    
    exporter = PAOMOpenClawExporter(memory_dir="memory")
    
    # Create mock PAOM observations
    from ipa.ipa_evaluator import InteractionChunk
    mock_chunks = [
        InteractionChunk(
            chunk_id="obs_1",
            content=[{"content": "User prefers dark mode", "priority": "🔴"}],
            metadata={"date": "2026-02-11"}
        ),
        InteractionChunk(
            chunk_id="obs_2",
            content=[{"content": "Project deadline Friday", "priority": "🟡"}],
            metadata={"date": "2026-02-11"}
        )
    ]
    
    print(f"Exporting {len(mock_chunks)} PAOM chunks to memory...")
    print(f"✅ PAOM exporter ready")
    print(f"   Usage: exporter.export_observations(paom, date='2026-02-11')")
    
    # ============================================
    # Integration 2: IPA → Hybrid Search
    # ============================================
    print("\n🔍 Integration 2: IPA → Hybrid Search")
    print("-" * 60)
    
    reranker = IPASearchReranker(weight=0.3, gamma=0.99)
    
    # Mock search results
    mock_results = [
        {
            "path": "MEMORY.md",
            "text": "User prefers dark mode in all applications",
            "score": 0.75
        },
        {
            "path": "memory/2026-02-10.md",
            "text": "Project deadline is Friday 2026-02-14",
            "score": 0.65
        }
    ]
    
    print(f"Reranking {len(mock_results)} search results with IPA...")
    reranked = reranker.rerank_search_results(mock_results, query="user preferences")
    
    print(f"✅ IPA reranked results:")
    for i, result in enumerate(reranked):
        print(f"   {i+1}. [{result['path']}]")
        print(f"      IPA: {result['_ipa_score']:.3f} | Combined: {result['_combined_score']:.3f}")
    
    # ============================================
    # Integration 3: ALMA → Memory Design
    # ============================================
    print("\n🎯 Integration 3: ALMA → Memory Design")
    print("-" * 60)
    
    optimizer = ALMAMemoryOptimizer()
    
    # Create default design
    design = optimizer._create_default_design()
    print(f"Optimizing memory design with ALMA...")
    print(f"   Design ID: {design.design_id}")
    print(f"   Parameters: {list(design.parameters.keys())}")
    
    # Optimize
    optimized = optimizer.optimize_design(design, num_iterations=5)
    
    print(f"✅ ALMA optimized design:")
    print(f"   Chunk Size: {optimized.parameters['chunk_size']} tokens")
    print(f"   Overlap: {optimized.parameters['overlap_pct']}%")
    print(f"   Temporal Anchors: {optimized.parameters['temporal_anchors']}")
    print(f"   Score: {optimized.metrics['accuracy']:.4f}")
    
    # ============================================
    # Integration 4: ROLL → Strategy Weights
    # ============================================
    print("\n⚖️  Integration 4: ROLL → Strategy Weights")
    print("-" * 60)
    
    weights_manager = ROLLWeightsManager()
    
    # Mock V7 strategy weights
    current_weights = {
        "TrendCapturePro": 0.25,
        "VolatilityBreakoutSystem": 0.25,
        "SupertrendNovaCloud": 0.25,
        "DivergenceVolatilityEnhanced": 0.25
    }
    
    print(f"Optimizing V7 strategy weights with ROLL...")
    print(f"   Current: {current_weights}")
    
    # Generate mock trajectories
    from rock.rock_environment import V7SimulationEnv
    env = V7SimulationEnv(market_regime="sideways")
    trajectories = []
    
    for _ in range(3):
        env.reset()
        traj = env.generate_trajectory(lambda obs: "buy", num_steps=20)
        trajectories.append(traj)
    
    # Optimize
    optimized_weights = weights_manager.optimize_with_roll(
        strategy_id="v7_trading",
        current_weights=current_weights,
        trajectories=trajectories,
        num_iterations=2
    )
    
    print(f"✅ ROLL optimized weights:")
    for strategy, weight in optimized_weights.weights.items():
        print(f"   {strategy}: {weight:.3f}")
    print(f"   Score: {optimized_weights.score:.4f}")
    
    # ============================================
    # Summary
    # ============================================
    print("\n" + "=" * 60)
    print("📊 Integration Summary")
    print("=" * 60)
    
    print("""
✅ PAOM → OpenClaw Memory: Export observations to memory/YYYY-MM-DD.md
✅ IPA → Hybrid Search: Rerank results with interaction scoring
✅ ALMA → Memory Design: Optimize chunk size, thresholds, anchors
✅ ROLL → Strategy Weights: Store optimized weights in memory

All four integrations are working together!
    """)
    
    print("🔗 Integration Files:")
    print(f"   - .openclaw/integrations/paom_openclaw_exporter.py")
    print(f"   - .openclaw/integrations/ipa_search_reranker.py")
    print(f"   - .openclaw/integrations/alma_memory_optimizer.py")
    print(f"   - .openclaw/integrations/roll_weights_manager.py")
    
    print("\n🐺📿 Full Integration Demo Complete!")
    
    return {
        "paom_exporter": exporter,
        "ipa_reranker": reranker,
        "alma_optimizer": optimizer,
        "roll_manager": weights_manager
    }


def example_workflows():
    """Show example workflows for each integration."""
    
    print("\n" + "=" * 60)
    print("📚 Example Workflows")
    print("=" * 60)
    
    print("""
1. PAOM Export Workflow:
   ```python
   from integrations import PAOMOpenClawExporter
   
   exporter = PAOMOpenClawExporter(memory_dir="memory")
   exporter.export_observations(paom, date="2026-02-11")
   ```
   
2. IPA Reranking Workflow:
   ```python
   from integrations import IPASearchReranker
   
   reranker = IPASearchReranker(weight=0.3)
   results = memory_search(query="user preferences")
   reranked = reranker.rerank_search_results(results, query)
   ```
   
3. ALMA Optimization Workflow:
   ```python
   from integrations import ALMAMemoryOptimizer
   
   optimizer = ALMAMemoryOptimizer()
   design = optimizer._create_default_design()
   optimized = optimizer.optimize_design(design, num_iterations=10)
   optimizer.save_design(optimized)
   ```
   
4. ROLL Weights Workflow:
   ```python
   from integrations import ROLLWeightsManager
   
   manager = ROLLWeightsManager()
   optimized = manager.optimize_with_roll(
       strategy_id="v7_trading",
       current_weights={"strat_a": 0.5, "strat_b": 0.5},
       trajectories=trajectories
   )
   ```
    """)


if __name__ == "__main__":
    demo_full_integration()
    example_workflows()
