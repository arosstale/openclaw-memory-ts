/**
 * LLM Client - Unified interface for extracting observations
 *
 * Supports: OpenAI, Anthropic, Gemini
 * Includes: Retry logic, rate limit handling, graceful degradation
 */
import { Observation, ObservationConfig } from './types';
export interface LLMMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}
export declare class LLMClient {
    private config;
    constructor(config: ObservationConfig);
    /**
     * Call LLM to extract observations from messages
     * Includes retry logic and graceful degradation
     */
    extractObservations(messages: Array<{
        role: string;
        content: string;
        timestamp: Date;
    }>, sourceFile: string): Promise<Observation[]>;
    /**
     * Parse LLM response into structured observations
     * Expected format:
     * 14:30 [High] W @Alice: Prefers async communication. (meaning Feb 24, 2026)
     */
    private parseObservations;
    /**
     * Parse a single observation line
     */
    private parseLine;
    /**
     * Parse priority level
     */
    private parsePriority;
    /**
     * Parse observation kind
     */
    private parseKind;
    /**
     * Extract entity mentions (@Name)
     */
    private extractEntities;
    /**
     * Extract confidence from opinion observations
     * Example: O(c=0.92)
     */
    private extractConfidence;
    /**
     * Call OpenAI API with error handling
     */
    private callOpenAI;
    /**
     * Call Anthropic API with error handling
     */
    private callAnthropic;
    /**
     * Call Gemini API with error handling
     */
    private callGemini;
    /**
     * Get system prompt for observation extraction
     */
    private getSystemPrompt;
    /**
     * Build user prompt from message history
     */
    private buildUserPrompt;
}
//# sourceMappingURL=llm-client.d.ts.map