/**
 * ALMA Mutation Strategies
 * Different approaches to evolve memory designs
 */
import { MemoryDesignParams, ParameterConstraints } from './types';
/**
 * Gaussian mutation: add small random values to parameters
 */
export declare function gaussianMutation(params: MemoryDesignParams, constraints: ParameterConstraints, stdDev?: number): MemoryDesignParams;
/**
 * Simulated annealing: occasionally jump to random state
 */
export declare function simulatedAnnealingMutation(params: MemoryDesignParams, constraints: ParameterConstraints, temperature?: number): MemoryDesignParams;
/**
 * Crossover: blend two designs
 */
export declare function crossoverMutation(parent1: MemoryDesignParams, parent2: MemoryDesignParams, constraints: ParameterConstraints): MemoryDesignParams;
/**
 * Adaptive mutation: mutation strength adapts based on fitness plateau
 */
export declare function adaptiveMutation(params: MemoryDesignParams, constraints: ParameterConstraints, recentScores: number[]): MemoryDesignParams;
//# sourceMappingURL=mutations.d.ts.map