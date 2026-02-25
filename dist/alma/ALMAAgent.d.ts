/**
 * ALMA Agent - Meta-learning memory optimizer
 *
 * Evolves memory system designs through:
 * 1. Design proposal (mutation of existing designs)
 * 2. Evaluation (measure performance)
 * 3. Archive (store with score)
 * 4. Repeat (iterate to improve)
 */
import { MemoryDesign, EvaluationResult, ALMAConfig } from './types';
export declare class ALMAAgent {
    private db;
    private constraints;
    readonly populationSize: number;
    readonly mutationRate: number;
    constructor(config: ALMAConfig);
    /**
     * Propose a new memory design
     * @param baseDesignId Optional base design to mutate
     * @returns New memory design
     */
    proposeDesign(baseDesignId?: string): MemoryDesign;
    /**
     * Evaluate a memory design
     * @param designId Design to evaluate
     * @param metrics Performance metrics (accuracy, efficiency, compression)
     * @returns Evaluation result
     */
    evaluateDesign(designId: string, metrics: Record<string, number>): EvaluationResult;
    /**
     * Get the best-performing design
     */
    getBestDesign(): MemoryDesign | null;
    /**
     * Get top N designs by performance
     */
    getTopDesigns(k?: number): MemoryDesign[];
    /**
     * Private: Mutate parameters of an existing design
     */
    private mutateParameters;
    /**
     * Private: Create random parameters
     */
    private createRandomParameters;
    /**
     * Private: Calculate composite performance score
     */
    private calculateScore;
}
//# sourceMappingURL=ALMAAgent.d.ts.map