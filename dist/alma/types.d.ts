/**
 * ALMA (Algorithm Learning via Meta-learning Agents)
 * TypeScript port from Python reference implementation
 * Based on: arXiv 2602.07755
 */
export interface MemoryDesignParams {
    [key: string]: number | string | boolean;
}
export interface MemoryDesign {
    designId: string;
    createdAt: Date;
    parameters: MemoryDesignParams;
    performanceScore: number;
    numEvaluations: number;
    isBest: boolean;
}
export interface EvaluationResult {
    designId: string;
    score: number;
    metrics: Record<string, number>;
    timestamp: Date;
}
export interface ParameterConstraints {
    [key: string]: {
        min?: number;
        max?: number;
        type: 'number' | 'string' | 'boolean';
    };
}
export interface ALMAConfig {
    dbPath: string;
    constraints?: ParameterConstraints;
    populationSize?: number;
    mutationRate?: number;
    elitismRate?: number;
}
//# sourceMappingURL=types.d.ts.map