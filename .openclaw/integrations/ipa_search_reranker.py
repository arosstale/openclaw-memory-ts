"""
IPA Reranker for OpenClaw Memory Search.

Uses IPA interaction-perceptive scoring to rerank search results.
"""

from typing import List, Dict, Any, Optional

try:
    from ipa.ipa_evaluator import IPAEvaluator
    IPA_AVAILABLE = True
except ImportError:
    IPA_AVAILABLE = False


class IPASearchReranker:
    """
    Reranks OpenClaw memory search results using IPA scores.
    """
    
    def __init__(self, gamma: float = 0.99, weight: float = 0.3):
        """
        Initialize IPA reranker.
        
        Args:
            gamma: Discount factor for credit assignment
            weight: Weight for IPA score in final ranking (0-1)
        """
        self.ipa = IPAEvaluator(gamma=gamma) if IPA_AVAILABLE else None
        self.weight = weight  # How much to weight IPA vs. original score
        
    def rerank_search_results(
        self, 
        search_results: List[Dict[str, Any]],
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using IPA interaction scoring.
        
        Args:
            search_results: List of search results from OpenClaw memory_search
            query: Original search query (optional context)
            
        Returns:
            Reranked list of results
        """
        if not search_results:
            return []
            
        if not self.ipa:
            return search_results
            
        # Enhance each result with IPA score
        enhanced_results = []
        
        for result in search_results:
            # Extract content for IPA evaluation
            content = result.get("text", "")
            path = result.get("path", "")
            
            # Create a mock interaction for IPA evaluation
            # In production, this would come from actual interaction history
            interaction = {
                "content": content,
                "context": query,
                "path": path
            }
            
            # Evaluate interaction quality with IPA
            ipa_score = self._evaluate_interaction(interaction)
            
            # Combine original score with IPA score
            original_score = result.get("score", 0.5)
            combined_score = (
                (1 - self.weight) * original_score +
                self.weight * ipa_score
            )
            
            # Add IPA metadata
            enhanced_result = result.copy()
            enhanced_result["_ipa_score"] = ipa_score
            enhanced_result["_combined_score"] = combined_score
            enhanced_result["score"] = combined_score
            
            enhanced_results.append(enhanced_result)
            
        # Sort by combined score
        reranked = sorted(
            enhanced_results,
            key=lambda r: r["_combined_score"],
            reverse=True
        )
        
        return reranked
        
    def _evaluate_interaction(self, interaction: Dict[str, Any]) -> float:
        """
        Evaluate interaction quality.
        
        This is a simplified version - in production, would use
        full IPA chunking and credit assignment.
        """
        content = interaction.get("content", "")
        context = interaction.get("context", "")
        
        # Heuristics for interaction quality
        score = 0.0
        
        # Length: Prefer concise, relevant snippets
        length = len(content)
        if 100 <= length <= 500:
            score += 0.3
        elif 500 <= length <= 1000:
            score += 0.5
        elif length > 1000:
            score += 0.3  # Too long
        else:
            score += 0.1  # Too short
            
        # Keywords: Match with query context
        if context:
            context_words = set(context.lower().split())
            content_words = set(content.lower().split())
            overlap = len(context_words & content_words)
            
            if overlap > 0:
                score += min(0.3, overlap * 0.1)
                
        # Structure: Look for markdown formatting (better structured notes)
        if "**" in content or "##" in content or "- " in content:
            score += 0.2
            
        return min(1.0, score)
        
    def chunk_and_evaluate(
        self, 
        search_results: List[Dict[str, Any]],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chunk results and evaluate with full IPA pipeline.
        
        Args:
            search_results: List of search results
            query: Original search query
            
        Returns:
            Evaluation metrics and chunked results
        """
        if not self.ipa:
            return {"error": "IPA not available"}
            
        # Create mock trajectory from search results
        trajectory = []
        for result in search_results:
            trajectory.append({
                "observation": result,
                "action": "retrieve",
                "reward": result.get("score", 0.5),
                "next_observation": result
            })
            
        # Evaluate with IPA
        ipa_result = self.ipa.evaluate(trajectory)
        
        return {
            "ipa_result": ipa_result,
            "chunked_results": [
                {
                    "chunk_id": chunk.id,
                    "score": chunk.score,
                    "size": len(chunk.content)
                }
                for chunk in ipa_result["chunks"]
            ],
            "total_score": ipa_result["total_score"],
            "num_chunks": ipa_result["num_chunks"]
        }


def memory_search_with_ipa(
    query: str,
    ipa_weight: float = 0.3,
    gamma: float = 0.99
) -> List[Dict[str, Any]]:
    """
    Memory search with IPA reranking.
    
    This function would be called from OpenClaw's memory_search.
    """
    # Get original search results (mock)
    original_results = []
    # In production: results = memory_search(query)
    
    # Rerank with IPA
    reranker = IPASearchReranker(gamma=gamma, weight=ipa_weight)
    reranked = reranker.rerank_search_results(original_results, query)
    
    return reranked


class IPARerankerCLI:
    """CLI for IPA reranking."""
    
    @staticmethod
    def rerank(query: str, results_file: str = None):
        """Rerank search results with IPA."""
        # Mock results for demo
        mock_results = [
            {
                "path": "MEMORY.md",
                "text": "User prefers dark mode in all applications.",
                "score": 0.8,
                "line_start": 10,
                "line_end": 10
            },
            {
                "path": "memory/2026-02-10.md",
                "text": "Project deadline is Friday 2026-02-14.",
                "score": 0.7,
                "line_start": 25,
                "line_end": 25
            }
        ]
        
        # Rerank
        reranker = IPASearchReranker()
        reranked = reranker.rerank_search_results(mock_results, query)
        
        print(f"🔍 IPA Reranked Results for: '{query}'")
        print("-" * 50)
        for i, result in enumerate(reranked):
            print(f"{i+1}. [{result['path']}] (Score: {result['score']:.3f})")
            print(f"   IPA: {result['_ipa_score']:.3f} | Combined: {result['_combined_score']:.3f}")
            print(f"   {result['text'][:100]}...")
            print()


if __name__ == "__main__":
    IPARerankerCLI.rerank(
        query="user preferences",
        results_file=None
    )
