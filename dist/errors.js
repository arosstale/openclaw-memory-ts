/**
 * Memory System Error Types
 */
export class MemoryError extends Error {
    constructor(code, message) {
        super(message);
        this.code = code;
        this.name = 'MemoryError';
    }
}
export class LLMError extends MemoryError {
    constructor(message, provider) {
        super('LLM_ERROR', `LLM error (${provider}): ${message}`);
        this.provider = provider;
    }
}
export class DatabaseError extends MemoryError {
    constructor(message) {
        super('DATABASE_ERROR', `Database error: ${message}`);
    }
}
export class IndexError extends MemoryError {
    constructor(message) {
        super('INDEX_ERROR', `Index error: ${message}`);
    }
}
export class ConfigError extends MemoryError {
    constructor(message) {
        super('CONFIG_ERROR', `Configuration error: ${message}`);
    }
}
export function Ok(data) {
    return { ok: true, data };
}
export function Err(error) {
    return { ok: false, error };
}
/**
 * Graceful degradation helpers
 */
export class GracefulDegradation {
    /**
     * Try operation, log error and return null on failure
     */
    static async tryAsync(name, fn, fallback) {
        try {
            return await fn();
        }
        catch (e) {
            console.warn(`[Memory] ${name} failed (degraded):`, e instanceof Error ? e.message : e);
            return fallback ?? null;
        }
    }
    /**
     * Try operation synchronously, log error and return null on failure
     */
    static trySync(name, fn, fallback) {
        try {
            return fn();
        }
        catch (e) {
            console.warn(`[Memory] ${name} failed (degraded):`, e instanceof Error ? e.message : e);
            return fallback ?? null;
        }
    }
    /**
     * Retry with exponential backoff
     */
    static async retry(name, fn, maxRetries = 3, backoffMs = 100) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await fn();
            }
            catch (e) {
                if (i === maxRetries - 1) {
                    console.warn(`[Memory] ${name} failed after ${maxRetries} retries`);
                    return null;
                }
                console.warn(`[Memory] ${name} retry ${i + 1}/${maxRetries}`);
                await new Promise((resolve) => setTimeout(resolve, backoffMs * Math.pow(2, i)));
            }
        }
        return null;
    }
}
//# sourceMappingURL=errors.js.map