/**
 * Hindsight Memory System for OpenClaw
 *
 * Retain → Recall → Reflect architecture
 * - ALMA: meta-learning agent that optimizes memory design
 * - Observational Memory: extracts structured facts with temporal anchoring
 * - Memory Indexer: full-text + semantic search over workspace
 */
export * from './alma/types';
export * from './alma/ALMAAgent';
export * from './observational-memory/types';
export * from './observational-memory/ObserverAgent';
export * from './knowledge/MemoryIndexer';
/**
 * Initialize the memory system for an OpenClaw workspace
 *
 * @param workspacePath Path to ~/.openclaw/workspace
 * @returns Memory system instance with all three subsystems
 */
export declare function initializeMemorySystem(_workspacePath: string): Promise<{
    alma: null;
    observer: null;
    indexer: null;
}>;
//# sourceMappingURL=index.d.ts.map