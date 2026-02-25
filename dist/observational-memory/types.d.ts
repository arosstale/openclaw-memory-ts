/**
 * Observational Memory - Temporal fact extraction
 * Based on cognitive science (ACT-R, temporal anchoring)
 */
export type ObservationKind = 'world' | 'biographical' | 'opinion' | 'observation';
export type PriorityLevel = 'high' | 'medium' | 'low';
export interface Observation {
    kind: ObservationKind;
    timestamp: Date;
    entities: string[];
    content: string;
    source: string;
    priority: PriorityLevel;
    confidence?: number;
}
export interface ObservationConfig {
    workspace: string;
    memoryDir: string;
    llmProvider: 'openai' | 'anthropic' | 'gemini';
    llmModel: string;
    apiKey: string;
}
export interface TemporalAnchor {
    beginTime: Date;
    endTime?: Date;
}
//# sourceMappingURL=types.d.ts.map