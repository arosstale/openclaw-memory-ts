/**
 * Memory Dashboard Server
 * Simple Express app serving React UI at localhost:9091
 */
import { type Express } from 'express';
declare const app: Express;
/**
 * Initialize dashboard with memory services
 */
export declare function initDashboard(config: {
    indexPath: string;
    workspace: string;
    almaPath: string;
}): Express;
/**
 * Start server
 */
export declare function startDashboard(): Promise<void>;
export default app;
//# sourceMappingURL=server.d.ts.map