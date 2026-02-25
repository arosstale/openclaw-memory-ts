/**
 * Memory Indexer - Build FTS5 + semantic search index
 *
 * Indexes Markdown files from the workspace:
 * - MEMORY.md (core durable facts)
 * - memory/YYYY-MM-DD.md (daily logs)
 * - bank/entities/*.md (entity summaries)
 * - bank/opinions.md (confidence-bearing beliefs)
 */
export interface IndexConfig {
    workspace: string;
    dbPath: string;
    embedProvider?: 'openai' | 'local' | 'gemini';
    chunkSize?: number;
    chunkOverlap?: number;
}
export interface IndexedChunk {
    id: string;
    file: string;
    lineStart: number;
    lineEnd: number;
    text: string;
    embedding?: number[];
    score?: number;
}
export declare class MemoryIndexer {
    private db;
    private workspace;
    private chunkSize;
    readonly chunkOverlap: number;
    constructor(config: IndexConfig);
    /**
     * Index all memory files in workspace
     */
    indexWorkspace(): Promise<number>;
    /**
     * Index a single Markdown file
     */
    indexFile(filePath: string): Promise<number>;
    /**
     * Search indexed memory (FTS5 only for now, semantic search coming)
     * @param query Natural language query
     * @param k Number of results to return
     * @param mode 'fts5' | 'semantic' | 'hybrid' (BM25 + vectors)
     */
    search(query: string, k?: number, mode?: 'fts5' | 'semantic' | 'hybrid'): Promise<IndexedChunk[]>;
    /**
     * Rebuild index (useful after memory file changes)
     */
    rebuild(): Promise<void>;
    /**
     * Private: Split text into chunks with overlap
     */
    private chunkText;
    /**
     * Private: Initialize database schema
     */
    private initSchema;
}
//# sourceMappingURL=MemoryIndexer.d.ts.map