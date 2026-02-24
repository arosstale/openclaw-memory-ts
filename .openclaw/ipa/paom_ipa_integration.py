"""
PAOM + IPA Integration.

Combines Observational Memory (PAOM) with Interaction-Perceptive Evaluation (IPA).
Enables semantic chunk evaluation for memory records.
"""

from typing import List, Dict, Any
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from ipa.ipa_evaluator import IPAEvaluator, InteractionChunk

try:
    from observational_memory import ObservationalMemory, PriorityLevel, ObservationConfig
    PAOM_AVAILABLE = True
except ImportError:
    PAOM_AVAILABLE = False
    print("PAOM not available, using mock")


class PAOM_IPA_Integrator:
    """
    Integrates PAOM (Observational Memory) with IPA (Interaction Evaluation).
    """
    
    def __init__(self, db_path: str = None):
        if PAOM_AVAILABLE:
            from observational_memory import ObservationConfig
            config = ObservationConfig()
            if db_path:
                config.db_path = db_path
            self.paom = ObservationalMemory(config=config)
        else:
            self.paom = None
        self.ipa = IPAEvaluator()
        
    def chunk_paom_records(self, thread_id: str) -> List[InteractionChunk]:
        """
        Convert PAOM memory records into IPA chunks.
        """
        if not self.paom:
            return []
            
        record = self.paom.get_observation_record(thread_id)
        if record is None:
            return []
            
        observations = record.observations
        chunks = []
        
        current_chunk_content = []
        chunk_index = 0
        
        for i, record in enumerate(records):
            current_chunk_content.append({
                "timestamp": record.timestamp,
                "content": record.content,
                "priority": record.priority,
                "metadata": record.metadata
            })
            
            # Chunk based on priority changes or size
            is_high_priority = record.priority == PriorityLevel.HIGH
            is_full = len(current_chunk_content) >= 5
            is_last = (i == len(records) - 1)
            
            if is_high_priority or is_full or is_last:
                chunk = InteractionChunk(
                    chunk_id=f"{thread_id}_chunk_{chunk_index}",
                    content=current_chunk_content,
                    metadata={
                        "paom_thread": thread_id,
                        "record_range": f"{i - len(current_chunk_content) + 1}-{i}"
                    }
                )
                chunks.append(chunk)
                current_chunk_content = []
                chunk_index += 1
                
        return chunks
        
    def evaluate_memory_quality(self, thread_id: str) -> Dict[str, Any]:
        """
        Evaluate the quality of PAOM memory using IPA.
        """
        chunks = self.chunk_paom_records(thread_id)
        scored_chunks = self.ipa.assign_credit(chunks)
        
        # Calculate PAOM-specific metrics
        total_chunks = len(scored_chunks)
        high_priority_chunks = sum(1 for c in scored_chunks 
                                   if any(r.get("priority") == "🔴" for r in c.content))
        
        avg_score = sum(c.score for c in scored_chunks) / total_chunks if total_chunks > 0 else 0
        
        return {
            "thread_id": thread_id,
            "total_chunks": total_chunks,
            "high_priority_chunks": high_priority_chunks,
            "avg_chunk_score": avg_score,
            "chunks": scored_chunks
        }
        
    def trigger_reflection_on_chunks(self, chunks: List[InteractionChunk]):
        """
        Trigger PAOM reflection based on chunk scores.
        """
        if not self.paom:
            return
            
        # Sort chunks by score (descending)
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
        
        # Reflection context: top 3 chunks + bottom 3 chunks
        top_chunks = sorted_chunks[:3]
        bottom_chunks = sorted_chunks[-3:]
        
        reflection_context = []
        
        for chunk in top_chunks:
            for item in chunk.content:
                reflection_context.append(item["content"])
                
        reflection_summary = self.paom._compress_context(
            reflection_context[:50],  # Limit to avoid truncation
            target_tokens=1000
        )
        
        # Store reflection
        from observational_memory import Reflection
        reflection = Reflection(
            timestamp="now",
            compressed_context=reflection_summary,
            reflection_type="chunk_based",
            original_size=len(reflection_context),
            compressed_size=1000,
            metadata={"chunk_count": len(chunks)}
        )
        
        self.paom.save_reflection(reflection)
        
        return reflection_summary


class PAOM_IPA_CLI:
    """CLI interface for PAOM + IPA integration."""
    
    @staticmethod
    def evaluate(thread_id: str, db_path: str = None):
        """Evaluate PAOM memory with IPA."""
        integrator = PAOM_IPA_Integrator(db_path=db_path)
        result = integrator.evaluate_memory_quality(thread_id)
        
        print(f"📊 PAOM + IPA Evaluation for '{thread_id}'")
        print(f"   Total Chunks: {result['total_chunks']}")
        print(f"   High Priority: {result['high_priority_chunks']}")
        print(f"   Avg Chunk Score: {result['avg_chunk_score']:.4f}")
        
        return result
        
    @staticmethod
    def reflect(thread_id: str, db_path: str = None):
        """Trigger chunk-based reflection."""
        integrator = PAOM_IPA_Integrator(db_path=db_path)
        chunks = integrator.chunk_paom_records(thread_id)
        reflection = integrator.trigger_reflection_on_chunks(chunks)
        
        print(f"🔄 Chunk-based Reflection Complete")
        print(f"   Reflection: {reflection[:200]}...")
        
        return reflection


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PAOM + IPA Integration CLI")
    parser.add_argument("command", choices=["evaluate", "reflect"])
    parser.add_argument("--thread", required=True, help="Thread ID")
    parser.add_argument("--db", help="Database path")
    
    args = parser.parse_args()
    
    cli = PAOM_IPA_CLI()
    
    if args.command == "evaluate":
        cli.evaluate(args.thread, args.db)
    elif args.command == "reflect":
        cli.reflect(args.thread, args.db)
