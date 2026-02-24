"""
ALMA (Algorithm Learning via Meta-learning Agents)

Based on the paper: "ALMA: Algorithm Learning via Meta-learning Agents"
arXiv: https://arxiv.org/pdf/2602.07755
GitHub: https://github.com/zksha/alma

ALMA enables AI systems to learn HOW to optimize, not just WHAT to execute.
This is a key component of self-improving agentic systems.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class MemoryDesign:
    """A memory design for meta-learning optimization."""
    design_id: str
    created_at: datetime
    parameters: Dict[str, any]
    performance_score: float = 0.0
    num_evaluations: int = 0
    is_best: bool = False


@dataclass
class EvaluationResult:
    """Result of evaluating a memory design."""
    design_id: str
    score: float
    metrics: Dict[str, float]
    timestamp: datetime


class ALMAAgent:
    """
    Algorithm Learning via Meta-learning Agents.

    The ALMA agent discovers optimal memory designs through:
    1. Design proposal (mutation of existing designs)
    2. Evaluation (measure performance)
    3. Archive (store with score)
    4. Repeat (iterate to improve)
    """

    def __init__(self, db_path: str = ".openclaw/alma_designs.db"):
        """
        Initialize ALMA agent.

        Args:
            db_path: Path to designs database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database for memory designs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Memory designs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_designs (
                design_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                parameters TEXT NOT NULL,
                performance_score REAL DEFAULT 0.0,
                num_evaluations INTEGER DEFAULT 0,
                is_best INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                design_id TEXT NOT NULL,
                score REAL NOT NULL,
                metrics TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (design_id) REFERENCES memory_designs(design_id)
            )
        """)

        # Index on performance score
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance
            ON memory_designs(performance_score DESC)
        """)

        conn.commit()
        conn.close()

    def propose_design(self, base_design_id: Optional[str] = None) -> MemoryDesign:
        """
        Propose a new memory design.

        If base_design_id is provided, mutates that design.
        Otherwise, creates a random design.

        Args:
            base_design_id: Optional base design to mutate

        Returns:
            New memory design
        """
        if base_design_id:
            # Mutate existing design
            base_design = self.get_design(base_design_id)
            if not base_design:
                base_design = self._create_random_design()
            parameters = self._mutate_parameters(base_design.parameters)
        else:
            # Create random design
            parameters = self._create_random_parameters()

        # Generate design ID
        design_id = self._generate_design_id()

        # Create design
        design = MemoryDesign(
            design_id=design_id,
            created_at=datetime.now(),
            parameters=parameters,
        )

        # Save to database
        self._save_design(design)

        return design

    def evaluate_design(
        self,
        design_id: str,
        metrics: Dict[str, float]
    ) -> EvaluationResult:
        """
        Evaluate a memory design.

        Args:
            design_id: Design to evaluate
            metrics: Performance metrics (e.g., accuracy, efficiency, compression)

        Returns:
            Evaluation result with composite score
        """
        # Calculate composite score
        score = self._calculate_score(metrics)

        # Create result
        result = EvaluationResult(
            design_id=design_id,
            score=score,
            metrics=metrics,
            timestamp=datetime.now(),
        )

        # Save to database
        self._save_evaluation(result)
        self._update_design_score(design_id, score)

        return result

    def get_best_design(self) -> Optional[MemoryDesign]:
        """
        Get the best-performing design.

        Returns:
            Best design or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT design_id, created_at, parameters, performance_score, num_evaluations, is_best
            FROM memory_designs
            WHERE is_best = 1
            ORDER BY performance_score DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_design(row)

    def get_top_designs(self, limit: int = 10) -> List[MemoryDesign]:
        """
        Get top-performing designs.

        Args:
            limit: Maximum number of designs

        Returns:
            List of top designs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT design_id, created_at, parameters, performance_score, num_evaluations, is_best
            FROM memory_designs
            ORDER BY performance_score DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_design(row) for row in rows]

    def run_meta_learning_iteration(
        self,
        num_designs: int = 5,
        evaluator: Optional[callable] = None
    ) -> Tuple[MemoryDesign, List[EvaluationResult]]:
        """
        Run one meta-learning iteration.

        Args:
            num_designs: Number of designs to propose and evaluate
            evaluator: Optional function to evaluate designs (callable)

        Returns:
            (best_design, evaluation_results)
        """
        results = []

        for i in range(num_designs):
            # Propose design
            if i == 0:
                # First design: random
                design = self.propose_design()
            else:
                # Mutate best design so far
                best = self.get_best_design()
                base_id = best.design_id if best else None
                design = self.propose_design(base_id)

            # Evaluate
            if evaluator:
                metrics = evaluator(design)
            else:
                # Default evaluation (uses mock metrics)
                metrics = self._mock_evaluate(design)

            result = self.evaluate_design(design.design_id, metrics)
            results.append(result)

        # Update best flag
        self._update_best_flag()

        # Get best design
        best_design = self.get_best_design()

        return best_design, results

    def _create_random_parameters(self) -> Dict[str, any]:
        """Create random design parameters."""
        import random
        return {
            # Memory parameters
            "observation_threshold": random.choice([10000, 15000, 20000, 25000, 30000]),
            "reflection_threshold": random.choice([15000, 20000, 30000, 40000, 50000]),
            "observer_temperature": round(random.uniform(0.1, 0.5), 2),
            "reflector_temperature": round(random.uniform(0.0, 0.2), 2),

            # LLM parameters
            "llm_provider": random.choice(["anthropic", "openai", "google"]),
            "llm_model": random.choice([
                "claude-sonnet-4-20250214",
                "gpt-4o",
                "gemini-2.5-pro",
            ]),

            # Token counting
            "use_tiktoken": random.choice([True, False]),

            # Additional parameters
            "compression_ratio": round(random.uniform(0.5, 0.9), 2),
            "context_window": random.choice([4000, 8000, 32000, 100000]),
        }

    def _mutate_parameters(self, base_params: Dict[str, any]) -> Dict[str, any]:
        """Mutate base design parameters."""
        import random

        # Copy base params
        params = base_params.copy()

        # Mutate 1-3 parameters randomly
        num_mutations = random.randint(1, 3)
        param_keys = list(params.keys())
        selected_keys = random.sample(param_keys, num_mutations)

        for key in selected_keys:
            value = params[key]

            if isinstance(value, (int, float)):
                # Numeric: add small random change
                params[key] = value * random.uniform(0.9, 1.1)
                if isinstance(value, int):
                    params[key] = int(params[key])
            elif isinstance(value, bool):
                # Boolean: flip
                params[key] = not value
            elif isinstance(value, str):
                # String: pick from options if it's a known key
                if key == "llm_provider":
                    params[key] = random.choice(["anthropic", "openai", "google"])
                elif key == "llm_model":
                    params[key] = random.choice([
                        "claude-sonnet-4-20250214",
                        "gpt-4o",
                        "gemini-2.5-pro",
                    ])

        return params

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate composite score from metrics.

        Formula: (accuracy * 0.4) + (efficiency * 0.3) + (compression * 0.3)

        Args:
            metrics: Dictionary of metrics

        Returns:
            Composite score (0-100)
        """
        accuracy = metrics.get("accuracy", 0.0)
        efficiency = metrics.get("efficiency", 0.0)
        compression = metrics.get("compression", 0.0)

        score = (accuracy * 0.4) + (efficiency * 0.3) + (compression * 0.3)
        return min(max(score, 0.0), 100.0)

    def _mock_evaluate(self, design: MemoryDesign) -> Dict[str, float]:
        """Mock evaluation for testing."""
        import random
        return {
            "accuracy": round(random.uniform(70.0, 95.0), 2),
            "efficiency": round(random.uniform(60.0, 90.0), 2),
            "compression": round(random.uniform(50.0, 85.0), 2),
        }

    def _generate_design_id(self) -> str:
        """Generate unique design ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def _save_design(self, design: MemoryDesign):
        """Save design to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memory_designs
            (design_id, created_at, parameters, performance_score, num_evaluations, is_best)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            design.design_id,
            design.created_at.isoformat(),
            json.dumps(design.parameters),
            design.performance_score,
            design.num_evaluations,
            1 if design.is_best else 0,
        ))

        conn.commit()
        conn.close()

    def _save_evaluation(self, result: EvaluationResult):
        """Save evaluation to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evaluations
            (design_id, score, metrics, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            result.design_id,
            result.score,
            json.dumps(result.metrics),
            result.timestamp.isoformat(),
        ))

        conn.commit()
        conn.close()

    def _update_design_score(self, design_id: str, score: float):
        """Update design score in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE memory_designs
            SET performance_score = ?,
                num_evaluations = num_evaluations + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE design_id = ?
        """, (score, design_id))

        conn.commit()
        conn.close()

    def _update_best_flag(self):
        """Update best flag based on highest score."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Reset all is_best flags
        cursor.execute("UPDATE memory_designs SET is_best = 0")

        # Set flag on highest-scoring design
        cursor.execute("""
            UPDATE memory_designs
            SET is_best = 1
            WHERE design_id = (
                SELECT design_id FROM memory_designs
                ORDER BY performance_score DESC
                LIMIT 1
            )
        """)

        conn.commit()
        conn.close()

    def get_design(self, design_id: str) -> Optional[MemoryDesign]:
        """Get design by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT design_id, created_at, parameters, performance_score, num_evaluations, is_best
            FROM memory_designs
            WHERE design_id = ?
        """, (design_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_design(row)

    def _row_to_design(self, row) -> MemoryDesign:
        """Convert database row to MemoryDesign."""
        import json
        return MemoryDesign(
            design_id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            parameters=json.loads(row[2]),
            performance_score=row[3],
            num_evaluations=row[4],
            is_best=bool(row[5]),
        )

    def get_stats(self) -> Dict:
        """Get statistics about meta-learning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count designs
        cursor.execute("SELECT COUNT(*) FROM memory_designs")
        num_designs = cursor.fetchone()[0]

        # Count evaluations
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        num_evaluations = cursor.fetchone()[0]

        # Get best score
        cursor.execute("SELECT MAX(performance_score) FROM memory_designs")
        best_score = cursor.fetchone()[0] or 0.0

        conn.close()

        return {
            "num_designs": num_designs,
            "num_evaluations": num_evaluations,
            "best_score": best_score,
        }


__all__ = [
    "ALMAAgent",
    "MemoryDesign",
    "EvaluationResult",
]
