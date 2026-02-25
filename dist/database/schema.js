/**
 * SQLite Database Schema for Memory System
 *
 * Three tables:
 * 1. memory_chunks — indexed text (FTS5)
 * 2. memory_embeddings — optional vectors
 * 3. alma_designs — memory design evolution
 * 4. alma_evaluations — performance metrics
 */
export function initializeSchema(db) {
    // Enable FTS5 extension
    db.exec('CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks USING fts5(file, line_start, line_end, content, tokenize = "unicode61 remove_diacritics 0")');
    // Embeddings table (optional, for semantic search)
    db.exec(`
    CREATE TABLE IF NOT EXISTS memory_embeddings (
      id INTEGER PRIMARY KEY,
      chunk_id TEXT UNIQUE NOT NULL,
      embedding BLOB NOT NULL,
      model TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (chunk_id) REFERENCES memory_chunks(id)
    )
  `);
    // Create indices for faster queries
    db.exec('CREATE INDEX IF NOT EXISTS idx_embeddings_model ON memory_embeddings(model)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_chunks_file ON memory_chunks(file)');
    // ALMA design evolution
    db.exec(`
    CREATE TABLE IF NOT EXISTS alma_designs (
      design_id TEXT PRIMARY KEY,
      created_at TEXT NOT NULL,
      parameters TEXT NOT NULL,
      performance_score REAL DEFAULT 0.0,
      num_evaluations INTEGER DEFAULT 0,
      is_best INTEGER DEFAULT 0,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);
    // ALMA evaluations
    db.exec(`
    CREATE TABLE IF NOT EXISTS alma_evaluations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      design_id TEXT NOT NULL,
      score REAL NOT NULL,
      metrics TEXT NOT NULL,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (design_id) REFERENCES alma_designs(design_id)
    )
  `);
    // Index for ALMA queries
    db.exec('CREATE INDEX IF NOT EXISTS idx_alma_performance ON alma_designs(performance_score DESC)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_alma_eval_design ON alma_evaluations(design_id)');
    // Metadata table (schema version, last sync, etc)
    db.exec(`
    CREATE TABLE IF NOT EXISTS metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);
    // Store schema version
    const stmt = db.prepare('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)');
    stmt.run('schema_version', '1.0.0');
}
/**
 * Migrate schema if needed
 */
export function migrateSchema(db) {
    const meta = db.prepare('SELECT value FROM metadata WHERE key = ?').get('schema_version');
    const currentVersion = meta?.value || '0.0.0';
    if (currentVersion === '1.0.0') {
        return; // Up to date
    }
    if (currentVersion === '0.0.0') {
        // Fresh database — schema was just created by initializeSchema, no migration needed.
        // The sql.js fallback may not persist the INSERT from initializeSchema,
        // so we treat 0.0.0 as equivalent to a fresh 1.0.0 install.
        return;
    }
    throw new Error(`Unknown schema version: ${currentVersion}`);
}
//# sourceMappingURL=schema.js.map