/**
 * Memory Indexer - Build FTS5 + semantic search index
 *
 * Indexes Markdown files from the workspace:
 * - MEMORY.md (core durable facts)
 * - memory/YYYY-MM-DD.md (daily logs)
 * - bank/entities/*.md (entity summaries)
 * - bank/opinions.md (confidence-bearing beliefs)
 */
import { readFileSync, existsSync } from 'fs';
import { readdirSync } from 'fs';
import { join } from 'path';
import { createDatabase } from '../database/db';
export class MemoryIndexer {
    constructor(config) {
        this.workspace = config.workspace;
        this.chunkSize = config.chunkSize || 400;
        this.chunkOverlap = config.chunkOverlap || 80;
        this.db = createDatabase(config.dbPath);
        this.initSchema();
    }
    /**
     * Index all memory files in workspace
     */
    async indexWorkspace() {
        let chunksIndexed = 0;
        // Index MEMORY.md
        const memoryMd = join(this.workspace, 'MEMORY.md');
        if (existsSync(memoryMd)) {
            chunksIndexed += await this.indexFile(memoryMd);
        }
        // Index daily logs (memory/YYYY-MM-DD.md)
        const memoryDir = join(this.workspace, 'memory');
        if (existsSync(memoryDir)) {
            const files = readdirSync(memoryDir).filter((f) => f.match(/^\d{4}-\d{2}-\d{2}\.md$/));
            for (const file of files) {
                chunksIndexed += await this.indexFile(join(memoryDir, file));
            }
        }
        // Index bank/entities/*.md
        const entitiesDir = join(this.workspace, 'bank', 'entities');
        if (existsSync(entitiesDir)) {
            const files = readdirSync(entitiesDir).filter((f) => f.endsWith('.md'));
            for (const file of files) {
                chunksIndexed += await this.indexFile(join(entitiesDir, file));
            }
        }
        // Index bank/opinions.md
        const opinionsFile = join(this.workspace, 'bank', 'opinions.md');
        if (existsSync(opinionsFile)) {
            chunksIndexed += await this.indexFile(opinionsFile);
        }
        return chunksIndexed;
    }
    /**
     * Index a single Markdown file
     */
    async indexFile(filePath) {
        const content = readFileSync(filePath, 'utf-8');
        const chunks = this.chunkText(content, 1);
        const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO memory_chunks (file, line_start, line_end, content)
      VALUES (?, ?, ?, ?)
    `);
        let count = 0;
        for (const chunk of chunks) {
            stmt.run(filePath, chunk.lineStart, chunk.lineEnd, chunk.text);
            count++;
        }
        return count;
    }
    /**
     * Search indexed memory (FTS5 only for now, semantic search coming)
     * @param query Natural language query
     * @param k Number of results to return
     * @param mode 'fts5' | 'semantic' | 'hybrid' (BM25 + vectors)
     */
    async search(query, k = 5, mode = 'fts5') {
        if (mode === 'fts5' || mode === 'hybrid') {
            // FTS5 search (BM25 ranking)
            const stmt = this.db.prepare(`
        SELECT rowid, file, line_start, line_end, content, rank
        FROM memory_chunks
        WHERE content MATCH ?
        ORDER BY rank
        LIMIT ?
      `);
            const rows = stmt.all(query, k);
            return rows.map((row) => ({
                id: `${row.rowid}`,
                file: row.file,
                lineStart: row.line_start,
                lineEnd: row.line_end,
                text: row.content,
                score: Math.abs(row.rank), // Rank is negative; convert to positive
            }));
        }
        // Semantic search stub (TODO: implement after embeddings)
        return [];
    }
    /**
     * Rebuild index (useful after memory file changes)
     */
    async rebuild() {
        // Drop and recreate FTS table
        this.db.exec('DROP TABLE IF EXISTS memory_chunks');
        this.initSchema();
        // Reindex all files
        await this.indexWorkspace();
    }
    /**
     * Private: Split text into chunks with overlap
     */
    chunkText(text, lineStart) {
        // TODO: Split by tokens (or lines as proxy), maintaining overlap
        const lines = text.split('\n');
        const chunks = [];
        for (let i = 0; i < lines.length; i += Math.max(1, Math.floor(this.chunkSize * 0.8))) {
            const end = Math.min(i + this.chunkSize, lines.length);
            chunks.push({
                text: lines.slice(i, end).join('\n'),
                lineStart: lineStart + i,
                lineEnd: lineStart + end,
            });
        }
        return chunks;
    }
    /**
     * Private: Initialize database schema
     */
    initSchema() {
        // Create FTS5 virtual table (BM25 ranking built-in)
        this.db.exec(`
      CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks USING fts5(
        file UNINDEXED,
        line_start UNINDEXED,
        line_end UNINDEXED,
        content,
        tokenize = 'unicode61 remove_diacritics 0'
      )
    `);
    }
}
//# sourceMappingURL=MemoryIndexer.js.map