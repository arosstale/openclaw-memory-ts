/**
 * Database Abstraction Layer
 * Supports both better-sqlite3 (native) and sql.js (pure JS fallback)
 */
export interface Database {
    prepare(sql: string): Statement;
    exec(sql: string): void;
    close(): void;
}
export interface Statement {
    run(...params: any[]): any;
    get(...params: any[]): any;
    all(...params: any[]): any[];
}
/**
 * Create database instance (synchronous)
 * Tries better-sqlite3 first, falls back to sql.js
 */
export declare function createDatabase(dbPath: string): Database;
/**
 * Get current database implementation
 */
export declare function getDbImpl(): string;
//# sourceMappingURL=db.d.ts.map