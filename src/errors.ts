/**
 * Memory System Error Types
 */

export class MemoryError extends Error {
  constructor(public code: string, message: string) {
    super(message);
    this.name = 'MemoryError';
  }
}

export class LLMError extends MemoryError {
  constructor(message: string, public provider?: string) {
    super('LLM_ERROR', `LLM error (${provider}): ${message}`);
  }
}

export class DatabaseError extends MemoryError {
  constructor(message: string) {
    super('DATABASE_ERROR', `Database error: ${message}`);
  }
}

export class IndexError extends MemoryError {
  constructor(message: string) {
    super('INDEX_ERROR', `Index error: ${message}`);
  }
}

export class ConfigError extends MemoryError {
  constructor(message: string) {
    super('CONFIG_ERROR', `Configuration error: ${message}`);
  }
}

/**
 * Result type for operations that may fail
 */
export type Result<T> = { ok: true; data: T } | { ok: false; error: MemoryError };

export function Ok<T>(data: T): Result<T> {
  return { ok: true, data };
}

export function Err<T>(error: MemoryError): Result<T> {
  return { ok: false, error };
}

/**
 * Graceful degradation helpers
 */
export class GracefulDegradation {
  /**
   * Try operation, log error and return null on failure
   */
  static async tryAsync<T>(
    name: string,
    fn: () => Promise<T>,
    fallback?: T
  ): Promise<T | null> {
    try {
      return await fn();
    } catch (e) {
      console.warn(`[Memory] ${name} failed (degraded):`, e instanceof Error ? e.message : e);
      return fallback ?? null;
    }
  }

  /**
   * Try operation synchronously, log error and return null on failure
   */
  static trySync<T>(name: string, fn: () => T, fallback?: T): T | null {
    try {
      return fn();
    } catch (e) {
      console.warn(`[Memory] ${name} failed (degraded):`, e instanceof Error ? e.message : e);
      return fallback ?? null;
    }
  }

  /**
   * Retry with exponential backoff
   */
  static async retry<T>(
    name: string,
    fn: () => Promise<T>,
    maxRetries: number = 3,
    backoffMs: number = 100
  ): Promise<T | null> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (e) {
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
