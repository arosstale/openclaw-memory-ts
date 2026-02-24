#!/usr/bin/env node
/**
 * OpenClaw V2.3 - ZKP Verify Orchestrator
 * Verifies agent proofs and orchestrates swarm coordination
 */

import { groth16 } from 'snarkjs';
import * as path from 'path';
import * as fs from 'fs';
import { createHash } from 'crypto';

interface ProofVerification {
  valid: boolean;
  agentIdHash: string;
  taskId: string;
  proofHash: string;
  timestamp: number;
  gasCost?: number;
  verificationTime: number;
}

interface SwarmState {
  verifiedProofs: Map<string, ProofVerification>;
  pendingProofs: Map<string, ProofVerification>;
  reputationScores: Map<string, number>;
}

class ZKOrchestrator {
  private vkeyPath: string;
  private state: SwarmState;
  private reputationPath: string;

  constructor() {
    this.vkeyPath = path.join(__dirname, 'circuits/task-proof.vkey');
    this.reputationPath = path.join(__dirname, '../../..', 'SWARM_REPUTATION.md');
    this.state = {
      verifiedProofs: new Map(),
      pendingProofs: new Map(),
      reputationScores: new Map()
    };
  }

  /**
   * Initialize orchestrator with verification key
   */
  async init() {
    console.log('🎮 ZKP Orchestrator initializing...');
    await this.loadReputation();
    console.log('✅ Orchestrator ready');
  }

  /**
   * Verify a single proof
   */
  async verifyProof(proofData: any): Promise<ProofVerification> {
    const startTime = Date.now();

    console.log('🔍 Verifying proof...');

    try {
      // Extract proof and public signals
      const { proof, publicSignals, proofHash, taskId, agentIdHash, timestamp } = proofData;

      // Load verification key
      const vkey = JSON.parse(fs.readFileSync(this.vkeyPath, 'utf-8'));

      // Verify using snarkjs (constant-time)
      const isValid = await groth16.verify(vkey, publicSignals, proof);

      const verificationTime = Date.now() - startTime;

      const result: ProofVerification = {
        valid: isValid,
        agentIdHash,
        taskId,
        proofHash,
        timestamp,
        gasCost: 0, // For L2 integration
        verificationTime
      };

      if (isValid) {
        console.log(`✅ Proof VALID (${verificationTime}ms)`);
        this.state.verifiedProofs.set(taskId, result);
        this.updateReputation(agentIdHash, 1);
      } else {
        console.log('❌ Proof INVALID');
        this.state.pendingProofs.set(taskId, result);
      }

      return result;

    } catch (error) {
      console.error('❌ Verification error:', error);
      return {
        valid: false,
        agentIdHash: 'unknown',
        taskId: 'unknown',
        proofHash: 'unknown',
        timestamp: 0,
        verificationTime: Date.now() - startTime
      };
    }
  }

  /**
   * Batch verify multiple proofs (constant-time)
   */
  async batchVerify(proofs: any[]): Promise<ProofVerification[]> {
    console.log(`📦 Batch verifying ${proofs.length} proofs...`);

    const startTime = Date.now();
    const results = await Promise.all(
      proofs.map(proof => this.verifyProof(proof))
    );
    const totalTime = Date.now() - startTime;

    const validCount = results.filter(r => r.valid).length;
    console.log(`✅ Batch complete: ${validCount}/${proofs.length} valid (${totalTime}ms)`);

    return results;
  }

  /**
   * Verify knowledge package proof
   */
  async verifyKnowledgePackage(packagePath: string): Promise<boolean> {
    console.log('📦 Verifying knowledge package...');

    // Read package manifest
    const manifestPath = path.join(packagePath, 'MANIFEST.json');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

    // Verify proof if present
    if (manifest.proofFile) {
      const proofData = JSON.parse(
        fs.readFileSync(path.join(packagePath, manifest.proofFile), 'utf-8')
      );

      const result = await this.verifyProof(proofData);
      return result.valid;
    }

    return false;
  }

  /**
   * Update reputation based on verified proofs
   */
  private updateReputation(agentIdHash: string, delta: number) {
    const currentScore = this.state.reputationScores.get(agentIdHash) || 0;
    this.state.reputationScores.set(agentIdHash, currentScore + delta);
    this.saveReputation();
  }

  /**
   * Load reputation from file
   */
  private async loadReputation() {
    if (fs.existsSync(this.reputationPath)) {
      const content = fs.readFileSync(this.reputationPath, 'utf-8');
      // Parse reputation file
    }
  }

  /**
   * Save reputation to file
   */
  private saveReputation() {
    // Save to SWARM_REPUTATION.md
  }

  /**
   * Get swarm metrics
   */
  getSwarmMetrics() {
    return {
      totalProofs: this.state.verifiedProofs.size + this.state.pendingProofs.size,
      verifiedProofs: this.state.verifiedProofs.size,
      pendingProofs: this.state.pendingProofs.size,
      uniqueAgents: this.state.reputationScores.size,
      totalReputation: Array.from(this.state.reputationScores.values())
        .reduce((a, b) => a + b, 0)
    };
  }

  /**
   * Generate Merkle root of all verified proofs
   */
  async generateMerkleRoot(): Promise<string> {
    const proofs = Array.from(this.state.verifiedProofs.values());
    const hashes = proofs.map(p => p.proofHash);

    // Simple Merkle tree implementation
    while (hashes.length > 1) {
      const newHashes: string[] = [];
      for (let i = 0; i < hashes.length; i += 2) {
        const left = hashes[i];
        const right = hashes[i + 1] || hashes[i];
        const combined = createHash('sha256')
          .update(left + right)
          .digest('hex');
        newHashes.push(combined);
      }
      hashes.splice(0, hashes.length, ...newHashes);
    }

    return hashes[0] || '0';
  }

  /**
   * Generate swarm report
   */
  async generateReport(): Promise<string> {
    const metrics = this.getSwarmMetrics();
    const merkleRoot = await this.generateMerkleRoot();

    return `
📊 ZKP Swarm Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Proofs:       ${metrics.totalProofs}
Verified Proofs:    ${metrics.verifiedProofs}
Pending Proofs:     ${metrics.pendingProofs}
Unique Agents:      ${metrics.uniqueAgents}
Total Reputation:   ${metrics.totalReputation}

Merkle Root:        ${merkleRoot.substring(0, 32)}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    `.trim();
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  const orchestrator = new ZKOrchestrator();
  await orchestrator.init();

  if (command === 'verify') {
    const proofPath = args[1];
    const proofData = JSON.parse(fs.readFileSync(proofPath, 'utf-8'));
    await orchestrator.verifyProof(proofData);

  } else if (command === 'batch') {
    const proofsDir = args[1] || '.openclaw/zkp/proofs';
    const proofFiles = fs.readdirSync(proofsDir)
      .filter(f => f.endsWith('.zproof'))
      .map(f => JSON.parse(fs.readFileSync(path.join(proofsDir, f), 'utf-8')));

    await orchestrator.batchVerify(proofFiles);

  } else if (command === 'metrics') {
    const report = await orchestrator.generateReport();
    console.log(report);

  } else {
    console.log(`
OpenClaw V2.3 - ZKP Verify Orchestrator

Usage:
  npm run verify verify <proofPath>
  npm run verify batch <proofsDir>
  npm run verify metrics

Example:
  npm run verify verify proofs/task-123.zproof
  npm run verify batch proofs/
  npm run verify metrics
    `);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { ZKOrchestrator, ProofVerification, SwarmState };
