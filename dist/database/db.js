/**
 * Database Abstraction Layer
 * Supports both better-sqlite3 (native) and sql.js (pure JS fallback)
 */
let dbImpl = 'better-sqlite3';
/**
 * Create database instance (synchronous)
 * Tries better-sqlite3 first, falls back to sql.js
 */
export function createDatabase(dbPath) {
    try {
        const BetterSqlite3 = require('better-sqlite3');
        dbImpl = 'better-sqlite3';
        return new BetterSqlite3(dbPath);
    }
    catch {
        dbImpl = 'sql.js';
        return createSqlJsDatabase(dbPath);
    }
}
/**
 * sql.js wrapper that matches better-sqlite3 API
 */
function createSqlJsDatabase(_dbPath) {
    let dbReady = null;
    try {
        const SQL = require('sql.js/dist/sql-wasm.js');
        dbReady = new SQL.Database();
    }
    catch {
        dbReady = createInMemoryDb();
    }
    return wrapSqlJsDb(dbReady);
}
function createInMemoryDb() {
    // Minimal in-memory SQL database using Map-based storage
    // This handles the basic operations needed by the memory system
    const tables = new Map();
    return {
        run(sql, params) {
            executeSql(tables, sql, params);
        },
        exec(sql) {
            executeSql(tables, sql);
        },
        prepare(sql) {
            return {
                run: (...params) => executeSql(tables, sql, params),
                get: (...params) => querySql(tables, sql, params, true),
                all: (...params) => querySql(tables, sql, params, false),
                getAsObject: (...params) => querySql(tables, sql, params, true),
            };
        },
        close() { tables.clear(); },
        _isMock: true,
    };
}
function executeSql(tables, sql, params) {
    const upperSql = sql.toUpperCase().trim();
    if (upperSql.startsWith('CREATE')) {
        const tableMatch = sql.match(/CREATE\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)/i);
        if (tableMatch) {
            const name = tableMatch[1];
            if (!tables.has(name)) {
                const colMatch = sql.match(/\(([^)]+)\)/);
                const columns = colMatch
                    ? colMatch[1].split(',').map(c => c.trim().split(/\s+/)[0]).filter(c => c && !c.startsWith('FOREIGN'))
                    : [];
                tables.set(name, { columns, rows: [] });
            }
        }
        // Also handle CREATE INDEX — no-op
        return { changes: 0 };
    }
    if (upperSql.startsWith('INSERT') || upperSql.startsWith('REPLACE')) {
        const match = sql.match(/(?:INSERT|REPLACE)\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)\s*\(([^)]+)\)/i);
        if (match && params) {
            const tableName = match[1];
            const columns = match[2].split(',').map(c => c.trim());
            const table = tables.get(tableName);
            if (table) {
                const row = {};
                columns.forEach((col, i) => {
                    row[col] = params[i];
                });
                // Handle OR REPLACE — remove existing row with same primary key
                if (sql.toUpperCase().includes('OR REPLACE') && columns.length > 0) {
                    const pk = columns[0];
                    table.rows = table.rows.filter((r) => r[pk] !== params[0]);
                }
                table.rows.push(row);
                return { changes: 1, lastInsertRowid: table.rows.length };
            }
        }
        return { changes: 0 };
    }
    if (upperSql.startsWith('UPDATE')) {
        const match = sql.match(/UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE\s+(\w+)\s*=\s*\?/i);
        if (match && params) {
            const tableName = match[1];
            const setParts = match[2];
            const whereCol = match[3];
            const table = tables.get(tableName);
            if (table) {
                const whereVal = params[params.length - 1];
                const setCols = setParts.split(',').map(s => s.trim().split(/\s*=\s*/)[0]);
                let changes = 0;
                for (const row of table.rows) {
                    if (row[whereCol] === whereVal) {
                        setCols.forEach((col, i) => {
                            if (col && params[i] !== undefined) {
                                row[col] = params[i];
                            }
                        });
                        changes++;
                    }
                }
                return { changes };
            }
        }
        return { changes: 0 };
    }
    return { changes: 0 };
}
function querySql(tables, sql, params, single) {
    const match = sql.match(/SELECT\s+.+?\s+FROM\s+(\w+)/i);
    if (!match)
        return single ? null : [];
    const tableName = match[1];
    const table = tables.get(tableName);
    if (!table)
        return single ? null : [];
    let rows = [...table.rows];
    // Handle WHERE clause with positional params
    const whereMatch = sql.match(/WHERE\s+(\w+)\s*=\s*\?/i);
    if (whereMatch && params && params.length > 0) {
        const col = whereMatch[1];
        rows = rows.filter((r) => r[col] === params[0]);
    }
    // Handle ORDER BY
    const orderMatch = sql.match(/ORDER\s+BY\s+(\w+)\s+(ASC|DESC)?/i);
    if (orderMatch) {
        const col = orderMatch[1];
        const desc = orderMatch[2]?.toUpperCase() === 'DESC';
        rows.sort((a, b) => desc ? (b[col] - a[col]) : (a[col] - b[col]));
    }
    // Handle LIMIT
    const limitMatch = sql.match(/LIMIT\s+(\?|\d+)/i);
    if (limitMatch) {
        const limit = limitMatch[1] === '?' ? (params?.[params.length - 1] ?? 10) : parseInt(limitMatch[1]);
        rows = rows.slice(0, limit);
    }
    if (single)
        return rows[0] || null;
    return rows;
}
function wrapSqlJsDb(db) {
    if (db._isMock) {
        return {
            prepare(sql) {
                const stmt = db.prepare(sql);
                return {
                    run: (...params) => stmt.run(...params),
                    get: (...params) => stmt.get(...params),
                    all: (...params) => stmt.all(...params),
                };
            },
            exec(sql) { db.exec(sql); },
            close() { db.close(); },
        };
    }
    // Real sql.js database
    return {
        prepare(sql) {
            return {
                run(...params) {
                    db.run(sql, params);
                    return { changes: db.getRowsModified() };
                },
                get(...params) {
                    const stmt = db.prepare(sql);
                    if (params.length)
                        stmt.bind(params);
                    if (stmt.step()) {
                        const row = stmt.getAsObject();
                        stmt.free();
                        return row;
                    }
                    stmt.free();
                    return null;
                },
                all(...params) {
                    const results = [];
                    const stmt = db.prepare(sql);
                    if (params.length)
                        stmt.bind(params);
                    while (stmt.step()) {
                        results.push(stmt.getAsObject());
                    }
                    stmt.free();
                    return results;
                },
            };
        },
        exec(sql) { db.run(sql); },
        close() { db.close(); },
    };
}
/**
 * Get current database implementation
 */
export function getDbImpl() {
    return dbImpl;
}
//# sourceMappingURL=db.js.map