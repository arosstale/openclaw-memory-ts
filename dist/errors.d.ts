/**
 * Memory System Error Types
 */
export declare class MemoryError extends Error {
    code: string;
    constructor(code: string, message: string);
}
export declare class LLMError extends MemoryError {
    provider?: string | undefined;
    constructor(message: string, provider?: string | undefined);
}
export declare class DatabaseError extends MemoryError {
    constructor(message: string);
}
export declare class IndexError extends MemoryError {
    constructor(message: string);
}
export declare class ConfigError extends MemoryError {
    constructor(message: string);
}
/**
 * Result type for operations that may fail
 */
export type Result<T> = {
    ok: true;
    data: T;
} | {
    ok: false;
    error: MemoryError;
};
export declare function Ok<T>(data: T): Result<T>;
export declare function Err<T>(error: MemoryError): Result<T>;
/**
 * Graceful degradation helpers
 */
export declare class GracefulDegradation {
    /**
     * Try operation, log error and return null on failure
     */
    static tryAsync<T>(name: string, fn: () => Promise<T>, fallback?: T): Promise<T | null>;
    /**
     * Try operation synchronously, log error and return null on failure
     */
    static trySync<T>(name: string, fn: () => T, fallback?: T): T | null;
    /**
     * Retry with exponential backoff
     */
    static retry<T>(name: string, fn: () => Promise<T>, maxRetries?: number, backoffMs?: number): Promise<T | null>;
}
//# sourceMappingURL=errors.d.ts.map