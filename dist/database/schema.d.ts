/**
 * SQLite Database Schema for Memory System
 *
 * Three tables:
 * 1. memory_chunks — indexed text (FTS5)
 * 2. memory_embeddings — optional vectors
 * 3. alma_designs — memory design evolution
 * 4. alma_evaluations — performance metrics
 */
import { Database } from './db';
export declare function initializeSchema(db: Database): void;
/**
 * Migrate schema if needed
 */
export declare function migrateSchema(db: Database): void;
//# sourceMappingURL=schema.d.ts.map