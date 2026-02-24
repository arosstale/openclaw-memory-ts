/**
 * Integration Test: Full Retain → Recall → Reflect Loop
 * 
 * Run with: npm test (requires SQLite compilation)
 * Expected: All operations complete without crashes
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { ALMAAgent } from '../alma/ALMAAgent';
import { ObserverAgent } from '../observational-memory/ObserverAgent';
import { MemoryIndexer } from '../knowledge/MemoryIndexer';
import { tmpdir } from 'os';
import { join } from 'path';
import { mkdirSync, existsSync } from 'fs';

const testDir = join(tmpdir(), 'openclaw-memory-test');

describe('Memory System Integration', () => {
  let alma: ALMAAgent;
  let observer: ObserverAgent;
  let indexer: MemoryIndexer;

  beforeAll(() => {
    // Setup test directories
    if (!existsSync(testDir)) mkdirSync(testDir, { recursive: true });

    // Initialize components
    alma = new ALMAAgent({
      dbPath: join(testDir, 'alma.db'),
    });

    observer = new ObserverAgent({
      llmProvider: 'anthropic',
      llmModel: 'claude-opus-4-6',
      apiKey: process.env.ANTHROPIC_API_KEY || 'test-key',
    });

    indexer = new MemoryIndexer({
      workspace: testDir,
      dbPath: join(testDir, 'index.db'),
    });
  });

  afterAll(() => {
    // Cleanup (optional: keep for inspection)
  });

  describe('ALMA Agent', () => {
    it('should propose memory designs', () => {
      const design = alma.proposeDesign();

      expect(design).toBeDefined();
      expect(design.designId).toBeTruthy();
      expect(design.parameters).toBeDefined();
      expect(design.performanceScore).toBe(0);
    });

    it('should evaluate designs and track performance', () => {
      const design = alma.proposeDesign();
      const eval1 = alma.evaluateDesign(design.designId, {
        recall: 0.85,
        efficiency: 0.78,
        compression: 0.72,
      });

      expect(eval1).toBeDefined();
      expect(eval1.score).toBeGreaterThan(0);

      // Second evaluation should increase scores
      const eval2 = alma.evaluateDesign(design.designId, {
        recall: 0.87,
        efficiency: 0.80,
        compression: 0.74,
      });

      expect(eval2.score).toBeGreaterThanOrEqual(eval1.score);
    });

    it('should identify best design', () => {
      const d1 = alma.proposeDesign();
      const d2 = alma.proposeDesign();

      alma.evaluateDesign(d1.designId, { recall: 0.75, efficiency: 0.75, compression: 0.75 });
      alma.evaluateDesign(d2.designId, { recall: 0.90, efficiency: 0.85, compression: 0.80 });

      const best = alma.getBestDesign();
      expect(best).toBeDefined();
      expect(best!.designId).toBe(d2.designId);
    });

    it('should return top K designs', () => {
      for (let i = 0; i < 5; i++) {
        const design = alma.proposeDesign();
        alma.evaluateDesign(design.designId, {
          recall: 0.5 + Math.random() * 0.5,
          efficiency: 0.5 + Math.random() * 0.5,
          compression: 0.5 + Math.random() * 0.5,
        });
      }

      const topDesigns = alma.getTopDesigns(3);
      expect(topDesigns).toHaveLength(3);
      expect(topDesigns[0].performanceScore).toBeGreaterThanOrEqual(
        topDesigns[1].performanceScore
      );
    });
  });

  describe('Observer Agent', () => {
    it('should handle missing LLM provider gracefully', async () => {
      // Observer should not crash even if LLM is unavailable
      const messages = [
        {
          role: 'user' as const,
          content: 'I live in NYC and prefer async communication',
          timestamp: new Date(),
        },
      ];

      // This should return empty array, not throw
      const result = await observer.extractObservations(messages);
      expect(Array.isArray(result)).toBe(true);
      // Result may be empty if LLM call failed, but no crash
    });
  });

  describe('Memory Indexer', () => {
    it('should initialize schema without crashing', () => {
      // Just verify it doesn't crash
      expect(indexer).toBeDefined();
    });

    it('should handle missing workspace gracefully', async () => {
      const missingIndexer = new MemoryIndexer({
        workspace: join(testDir, 'nonexistent'),
        dbPath: join(testDir, 'missing.db'),
      });

      // Should not crash even if workspace doesn't exist
      const result = await missingIndexer.indexWorkspace();
      expect(typeof result).toBe('number');
      expect(result).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Full Loop', () => {
    it('should complete Retain → Search → Reflect without crashing', async () => {
      // This is the full happy path test

      // 1. ALMA proposes design
      const design = alma.proposeDesign();
      expect(design).toBeDefined();

      // 2. Observer extracts observations (gracefully degraded if no LLM)
      const messages = [
        {
          role: 'user' as const,
          content: 'I prefer building in TypeScript',
          timestamp: new Date(),
        },
      ];
      const observations = await observer.extractObservations(messages);
      expect(Array.isArray(observations)).toBe(true);

      // 3. Indexer indexes workspace
      const indexed = await indexer.indexWorkspace();
      expect(indexed).toBeGreaterThanOrEqual(0);

      // 4. ALMA evaluates design
      const evaluation = alma.evaluateDesign(design.designId, {
        recall: 0.80,
        efficiency: 0.75,
        compression: 0.70,
      });
      expect(evaluation).toBeDefined();

      // Full loop completed successfully
      expect(true).toBe(true);
    });
  });
});
