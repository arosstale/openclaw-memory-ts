/**
 * Observer Agent - Extracts observations from message history
 *
 * Uses LLM to intelligently extract structured facts with:
 * - Type tags (W/B/O/S)
 * - Entity mentions (@Alice, @The-Castle)
 * - Temporal anchoring (when + what-if-different)
 * - Priority levels (High/Medium/Low)
 * - Confidence scores for opinions
 */
import type { Observation, ObservationConfig } from './types';
export declare class ObserverAgent {
    readonly config: ObservationConfig;
    private llm;
    constructor(config: ObservationConfig);
    /**
     * Extract observations from a message history
     * @param messages Message history from a conversation
     * @param sourceFile File where observations are stored
     * @returns Array of structured observations
     */
    extractObservations(messages: Array<{
        role: string;
        content: string;
        timestamp: Date;
    }>, sourceFile?: string): Promise<Observation[]>;
}
//# sourceMappingURL=ObserverAgent.d.ts.map