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

import { LLMClient } from './llm-client';
import {
  Observation,
  ObservationConfig,
  ObservationKind,
  PriorityLevel,
  TemporalAnchor,
} from './types';

export class ObserverAgent {
  private config: ObservationConfig;
  private llm: LLMClient;

  constructor(config: ObservationConfig) {
    this.config = config;
    this.llm = new LLMClient(config);
  }

  /**
   * Extract observations from a message history
   * @param messages Message history from a conversation
   * @param sourceFile File where observations are stored
   * @returns Array of structured observations
   */
  async extractObservations(
    messages: Array<{ role: string; content: string; timestamp: Date }>,
    sourceFile: string = 'memory/observations.md'
  ): Promise<Observation[]> {
    // Call LLM to extract observations in structured format
    return await this.llm.extractObservations(messages, sourceFile);
  }


}
