/**
 * LLM Client - Unified interface for extracting observations
 *
 * Supports: OpenAI, Anthropic, Gemini
 */

import { Observation, ObservationConfig, ObservationKind, PriorityLevel } from './types';

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export class LLMClient {
  private config: ObservationConfig;

  constructor(config: ObservationConfig) {
    this.config = config;
  }

  /**
   * Call LLM to extract observations from messages
   */
  async extractObservations(
    messages: Array<{ role: string; content: string; timestamp: Date }>,
    sourceFile: string
  ): Promise<Observation[]> {
    const systemPrompt = this.getSystemPrompt();
    const userPrompt = this.buildUserPrompt(messages);

    const llmMessages: LLMMessage[] = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ];

    let response: string;

    switch (this.config.llmProvider) {
      case 'openai':
        response = await this.callOpenAI(llmMessages);
        break;
      case 'anthropic':
        response = await this.callAnthropic(llmMessages);
        break;
      case 'gemini':
        response = await this.callGemini(llmMessages);
        break;
      default:
        throw new Error(`Unknown LLM provider: ${this.config.llmProvider}`);
    }

    // Parse response into observations
    return this.parseObservations(response, sourceFile);
  }

  /**
   * Parse LLM response into structured observations
   * Expected format:
   * 14:30 [High] W @Alice: Prefers async communication. (meaning Feb 24, 2026)
   */
  private parseObservations(response: string, sourceFile: string): Observation[] {
    const observations: Observation[] = [];
    const lines = response.split('\n');

    let lineNumber = 0;
    for (const line of lines) {
      lineNumber++;
      if (!line.trim()) continue;

      try {
        const obs = this.parseLine(line, sourceFile, lineNumber);
        if (obs) observations.push(obs);
      } catch (e) {
        // Skip malformed lines
        console.error(`Failed to parse observation line ${lineNumber}: ${line}`, e);
      }
    }

    return observations;
  }

  /**
   * Parse a single observation line
   */
  private parseLine(line: string, sourceFile: string, lineNumber: number): Observation | null {
    // Pattern: (time) [priority] type @entity: content. (optional date)
    // Example: 14:30 [High] W @Alice: Prefers async. (meaning Feb 24, 2026)

    const match = line.match(
      /\((\d{1,2}):(\d{2})\)\s+\[(\w+)\]\s+(\w+)\s+(.*?)\.(?:\s+\(meaning\s+(.*?)\))?$/
    );

    if (!match) return null;

    const [, hours, minutes, priorityStr, kindChar, contentWithEntities, dateRef] = match;

    // Parse time
    const time = new Date();
    time.setHours(parseInt(hours), parseInt(minutes), 0, 0);

    // Parse priority
    const priority = this.parsePriority(priorityStr);

    // Parse kind (W/B/O/S)
    const kind = this.parseKind(kindChar);

    // Extract entities (@Name)
    const entities = this.extractEntities(contentWithEntities);

    // Extract confidence if opinion
    const confidence = kind === 'opinion' ? this.extractConfidence(contentWithEntities) : undefined;

    // Build observation
    const obs: Observation = {
      kind,
      timestamp: time,
      entities,
      content: contentWithEntities.replace(/@[\w-]+/g, '').trim(),
      source: `${sourceFile}#L${lineNumber}`,
      priority,
      confidence,
    };

    return obs;
  }

  /**
   * Parse priority level
   */
  private parsePriority(priorityStr: string): PriorityLevel {
    const normalized = priorityStr.toLowerCase();
    if (normalized === 'high') return 'high';
    if (normalized === 'medium') return 'medium';
    if (normalized === 'low') return 'low';
    return 'medium'; // default
  }

  /**
   * Parse observation kind
   */
  private parseKind(kindChar: string): ObservationKind {
    const char = kindChar.toLowerCase();
    if (char === 'w') return 'world';
    if (char === 'b') return 'biographical';
    if (char === 'o') return 'opinion';
    if (char === 's') return 'observation';
    return 'observation'; // default
  }

  /**
   * Extract entity mentions (@Name)
   */
  private extractEntities(text: string): string[] {
    const matches = text.match(/@[\w-]+/g) || [];
    return matches.map((m) => m.slice(1)); // Remove @ prefix
  }

  /**
   * Extract confidence from opinion observations
   * Example: O(c=0.92)
   */
  private extractConfidence(text: string): number | undefined {
    const match = text.match(/\(c=([\d.]+)\)/);
    if (match) return parseFloat(match[1]);
    return undefined;
  }

  /**
   * Call OpenAI API
   */
  private async callOpenAI(messages: LLMMessage[]): Promise<string> {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config.llmModel,
        messages,
        temperature: 0.3,
        max_tokens: 2000,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.statusText}`);
    }

    const data = (await response.json()) as any;
    return data.choices[0].message.content;
  }

  /**
   * Call Anthropic API
   */
  private async callAnthropic(messages: LLMMessage[]): Promise<string> {
    // Convert system message
    const systemMsg = messages.find((m) => m.role === 'system')?.content || '';
    const userMessages = messages.filter((m) => m.role !== 'system');

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.config.apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: this.config.llmModel,
        max_tokens: 2000,
        system: systemMsg,
        messages: userMessages,
      }),
    });

    if (!response.ok) {
      throw new Error(`Anthropic API error: ${response.statusText}`);
    }

    const data = (await response.json()) as any;
    return data.content[0].text;
  }

  /**
   * Call Gemini API
   */
  private async callGemini(messages: LLMMessage[]): Promise<string> {
    const userContent = messages.find((m) => m.role === 'user')?.content || '';

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${this.config.llmModel}:generateContent?key=${this.config.apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [{ text: userContent }],
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.statusText}`);
    }

    const data = (await response.json()) as any;
    return data.candidates[0].content.parts[0].text;
  }

  /**
   * Get system prompt for observation extraction
   */
  private getSystemPrompt(): string {
    return `You are the memory consciousness of an AI assistant. Extract observations from conversation history.

FORMAT: (HH:MM) [Priority] Type @Entity: observation text. (optional date reference)

Types: W (world), B (biographical), O (opinion), S (summary)
Priorities: High, Medium, Low

Examples:
(14:30) [High] W @Alice: Lives in New York City.
(14:45) [Medium] O(c=0.92) @Alice: Prefers async communication over sync.
(15:00) [Low] B: Fixed a critical bug in the authentication flow.

Rules:
1. SPECIFIC: Capture distinguishing details
2. TEMPORAL: Include time statement was made
3. STATE CHANGES: Mark when info updates
4. COMMON SENSE: If it helps recall later, observe it

Output one observation per line. Be concise.`;
  }

  /**
   * Build user prompt from message history
   */
  private buildUserPrompt(messages: Array<{ role: string; content: string }>): string {
    const history = messages
      .map((m) => {
        const role = m.role === 'user' ? 'User' : 'Assistant';
        return `${role}: ${m.content}`;
      })
      .join('\n\n');

    return `Extract observations from this conversation:\n\n${history}\n\nOutput observations one per line.`;
  }
}
