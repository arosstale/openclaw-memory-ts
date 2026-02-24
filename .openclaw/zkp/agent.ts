#!/usr/bin/env node
/**
 * OpenClaw V2.3 - ZKP Prove Agent
 * Generates Zero-Knowledge Proofs for agent task execution
 */

import { buildPoseidon } from 'circomlibjs';
import { groth16 } from 'snarkjs';
import * as path from 'path';
import * as fs from 'fs';
import { createHash } from 'crypto';

interface TaskInput {
  agentId: string;
  taskId: string;
  executionData: any;
  resultData: any;
  timestamp: number;
}

interface ProofOutput {
  proof: any;
  publicSignals: string[];
  proofHash: string;
  taskId: string;
  agentIdHash: string;
}

class ZKProver {
  private poseidon: any;
  private wasmPath: string;
  private zkeyPath: string;

  constructor() {
    this.wasmPath = path.join(__dirname, 'circuits/task-proof_js/task-proof.wasm');
    this.zkeyPath = path.join(__dirname, 'circuits/task-proof.zkey');
  }

  async init() {
    this.poseidon = await buildPoseidon();
  }

  /**
   * Hash agent ID for identity verification
   */
  hashAgentId(agentId: string): string {
    const inputs = this.stringToInputs(agentId, 32);
    const hash = this.poseidon(inputs);
    return this.poseidon.F.toString(hash);
  }

  /**
   * Hash task data for execution proof
   */
  hashExecution(executionData: any): string {
    const json = JSON.stringify(executionData);
    return createHash('sha256').update(json).digest('hex');
  }

  /**
   * Hash result data for output proof
   */
  hashResult(resultData: any): string {
    const json = JSON.stringify(resultData);
    return createHash('sha256').update(json).digest('hex');
  }

  /**
   * Generate ZK proof for completed task
   */
  async generateProof(taskInput: TaskInput): Promise<ProofOutput> {
    console.log('🧬 Generating ZK Proof...');

    // Compute hashes
    const agentIdHash = this.hashAgentId(taskInput.agentId);
    const executionHash = this.hashExecution(taskInput.executionData);
    const resultHash = this.hashResult(taskInput.resultData);

    // Prepare circuit inputs
    const inputs = {
      agent_id: this.stringToInputs(taskInput.agentId, 32),
      task_id: this.stringToInputs(taskInput.taskId, 32),
      execution_hash: this.hexToInputs(executionHash, 32),
      result_hash: this.hexToInputs(resultHash, 32),
      timestamp: this.numberToInputs(taskInput.timestamp, 64),
    };

    console.log('📊 Generating witness...');

    // Generate proof using snarkjs
    const { proof, publicSignals } = await groth16.fullProve(
      inputs,
      this.wasmPath,
      this.zkeyPath
    );

    // Compute proof hash for verification
    const proofData = JSON.stringify({ proof, publicSignals });
    const proofHash = createHash('sha256').update(proofData).digest('hex');

    console.log('✅ ZK Proof generated');
    console.log(`   Task ID: ${taskInput.taskId}`);
    console.log(`   Agent Hash: ${agentIdHash.substring(0, 16)}...`);
    console.log(`   Proof Hash: ${proofHash.substring(0, 16)}...`);

    return {
      proof,
      publicSignals,
      proofHash,
      taskId: taskInput.taskId,
      agentIdHash
    };
  }

  /**
   * Export proof to file
   */
  exportProof(output: ProofOutput, filepath: string) {
    const data = {
      version: '2.3',
      proof: output.proof,
      publicSignals: output.publicSignals,
      proofHash: output.proofHash,
      taskId: output.taskId,
      agentIdHash: output.agentIdHash,
      timestamp: Date.now()
    };

    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
    console.log(`📦 Proof exported to: ${filepath}`);
  }

  /**
   * Import proof from file
   */
  importProof(filepath: string): ProofOutput {
    const data = JSON.parse(fs.readFileSync(filepath, 'utf-8'));
    return data;
  }

  /**
   * Convert string to field inputs
   */
  private stringToInputs(str: string, length: number): string[] {
    const inputs: string[] = [];
    for (let i = 0; i < length; i++) {
      inputs.push(i < str.length ? str.charCodeAt(i).toString() : '0');
    }
    return inputs;
  }

  /**
   * Convert hex string to field inputs
   */
  private hexToInputs(hex: string, length: number): string[] {
    const inputs: string[] = [];
    for (let i = 0; i < length; i++) {
      inputs.push(i < hex.length ? parseInt(hex.substr(i * 2, 2), 16).toString() : '0');
    }
    return inputs;
  }

  /**
   * Convert number to field inputs
   */
  private numberToInputs(num: number, length: number): string[] {
    const binary = num.toString(2).padStart(length, '0');
    const inputs: string[] = [];
    for (let i = 0; i < length; i++) {
      inputs.push(binary[i]);
    }
    return inputs;
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  const prover = new ZKProver();
  await prover.init();

  if (command === 'generate') {
    const taskInput: TaskInput = {
      agentId: args[1] || 'pi-agent-v2.3',
      taskId: args[2] || `task-${Date.now()}`,
      executionData: JSON.parse(args[3] || '{}'),
      resultData: JSON.parse(args[4] || '{}'),
      timestamp: Date.now()
    };

    const output = await prover.generateProof(taskInput);
    const filepath = args[5] || `.openclaw/zkp/proofs/${taskInput.taskId}.zproof`;
    prover.exportProof(output, filepath);

  } else if (command === 'verify') {
    const filepath = args[1];
    const verifier = new ZKVerifier();
    await verifier.init();

    const proof = prover.importProof(filepath);
    const isValid = await verifier.verifyProof(proof);

    console.log(isValid ? '✅ Proof is VALID' : '❌ Proof is INVALID');
    process.exit(isValid ? 0 : 1);

  } else {
    console.log(`
OpenClaw V2.3 - ZKP Prove Agent

Usage:
  npm run prove generate <agentId> <taskId> <executionData> <resultData> <outputPath>
  npm run prove verify <proofPath>

Example:
  npm run prove generate "pi-agent" "task-123" '{"papers":20}' '{"valid":true}' proofs/task-123.zproof
  npm run prove verify proofs/task-123.zproof
    `);
  }
}

class ZKVerifier {
  private vkeyPath: string;

  constructor() {
    this.vkeyPath = path.join(__dirname, 'circuits/task-proof.vkey');
  }

  async init() {
    // Load verification key
  }

  async verifyProof(proof: ProofOutput): Promise<boolean> {
    const { proof, publicSignals } = proof;
    const vkey = JSON.parse(fs.readFileSync(this.vkeyPath, 'utf-8'));

    const isValid = await groth16.verify(vkey, publicSignals, proof);
    return isValid;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { ZKProver, ZKVerifier, TaskInput, ProofOutput };
