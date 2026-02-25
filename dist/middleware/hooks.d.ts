/**
 * Auto-Hook Middleware
 * Intercepts agent requests/responses and auto-extracts/injects memories
 */
import { MemoryIndexer } from '../knowledge/MemoryIndexer';
import { ObservationConfig } from '../observational-memory/types';
export interface HookConfig {
    llmConfig: ObservationConfig;
    indexPath: string;
    workspace: string;
    enabled: boolean;
    autoExtract: boolean;
    autoInject: boolean;
}
export interface AgentRequest {
    messages: Array<{
        role: string;
        content: string;
    }>;
    systemPrompt?: string;
    metadata?: Record<string, any>;
}
export interface AgentResponse {
    messages: Array<{
        role: string;
        content: string;
    }>;
    metadata?: Record<string, any>;
}
export declare class MemoryHook {
    private observer;
    readonly indexer: MemoryIndexer;
    private config;
    constructor(config: HookConfig);
    /**
     * Hook: Before agent request
     * Injects relevant memories into system prompt
     */
    beforeRequest(request: AgentRequest): Promise<AgentRequest>;
    /**
     * Hook: After agent response
     * Auto-extracts observations from conversation
     */
    afterResponse(request: AgentRequest, response: AgentResponse): Promise<AgentResponse>;
    /**
     * Rebuild index (after memory updates)
     */
    rebuild(): Promise<void>;
    /**
     * Get memory stats
     */
    getStats(): Promise<{
        indexed: number;
        autoExtractions: number;
        autoInjections: number;
    }>;
}
/**
 * OpenClaw Plugin Interface
 * Registers hooks with openclaw agent system
 */
export declare function createMemoryPlugin(config: HookConfig): {
    name: string;
    version: string;
    hooks: {
        'agent:beforeRequest': (request: AgentRequest) => Promise<AgentRequest>;
        'agent:afterResponse': (request: AgentRequest, response: AgentResponse) => Promise<AgentResponse>;
    };
    commands: {
        'memory:search': (query: string) => Promise<import("../knowledge/MemoryIndexer").IndexedChunk[]>;
        'memory:rebuild': () => Promise<void>;
        'memory:stats': () => Promise<{
            indexed: number;
            autoExtractions: number;
            autoInjections: number;
        }>;
    };
};
//# sourceMappingURL=hooks.d.ts.map