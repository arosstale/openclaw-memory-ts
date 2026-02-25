/**
 * Memory Dashboard Server
 * Simple Express app serving React UI at localhost:9091
 */
import express from 'express';
import cors from 'cors';
import { MemoryIndexer } from '../knowledge/MemoryIndexer';
import { ALMAAgent } from '../alma/ALMAAgent';
const app = express();
const PORT = 9091;
app.use(cors());
app.use(express.json());
// Services
let indexer = null;
let alma = null;
/**
 * Initialize dashboard with memory services
 */
export function initDashboard(config) {
    indexer = new MemoryIndexer({
        workspace: config.workspace,
        dbPath: config.indexPath,
    });
    alma = new ALMAAgent({
        dbPath: config.almaPath,
    });
    return app;
}
/**
 * API Routes
 */
// GET /api/memories - List all memories with pagination
app.get('/api/memories', async (req, res) => {
    try {
        if (!indexer)
            throw new Error('Indexer not initialized');
        const limit = parseInt(req.query.limit) || 20;
        const offset = parseInt(req.query.offset) || 0;
        // TODO: Implement pagination in MemoryIndexer
        // For now, return empty (scaffold)
        res.json({
            memories: [],
            total: 0,
            limit,
            offset,
        });
    }
    catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
});
// GET /api/search - Search memories
app.get('/api/search', async (req, res) => {
    try {
        if (!indexer)
            throw new Error('Indexer not initialized');
        const query = req.query.q;
        if (!query) {
            res.status(400).json({ error: 'Query required' });
            return;
        }
        const results = await indexer.search(query, 10, 'hybrid');
        res.json({
            query,
            results: results.map((r) => ({
                id: r.id,
                file: r.file,
                score: r.score,
                preview: r.text.substring(0, 200),
            })),
        });
    }
    catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
});
// GET /api/stats - Get memory stats
app.get('/api/stats', async (_req, res) => {
    try {
        if (!alma)
            throw new Error('ALMA not initialized');
        const best = alma.getBestDesign();
        const top = alma.getTopDesigns(5);
        res.json({
            memory: {
                indexed: 0, // TODO: Get from indexer
                lastIndexed: new Date(),
            },
            alma: {
                bestDesign: best ? { id: best.designId, score: best.performanceScore } : null,
                topDesigns: top.length,
            },
        });
    }
    catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
});
// GET /api/timeline - Memory timeline
app.get('/api/timeline', async (_req, res) => {
    try {
        // TODO: Query memories by date
        // For now, return empty timeline (scaffold)
        res.json({
            timeline: [
                {
                    date: new Date().toISOString().split('T')[0],
                    count: 0,
                    memories: [],
                },
            ],
        });
    }
    catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
});
// Serve static React UI
app.use(express.static('public'));
app.get('/', (_req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>OpenClaw Memory Dashboard</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #0f172a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { border-bottom: 1px solid #1e293b; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { margin: 0; font-size: 28px; }
        .subtitle { color: #94a3b8; margin-top: 5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; }
        .card h3 { margin: 0 0 10px 0; font-size: 14px; color: #94a3b8; text-transform: uppercase; }
        .card .stat { font-size: 32px; font-weight: bold; margin: 10px 0; }
        .search { margin-bottom: 30px; }
        .search input { width: 100%; padding: 12px 16px; background: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 14px; }
        .search input:focus { outline: none; border-color: #3b82f6; }
        .results { display: grid; gap: 10px; }
        .result { background: #1e293b; border-left: 3px solid #3b82f6; padding: 12px 16px; border-radius: 4px; }
        .result-title { font-weight: 500; margin: 0; }
        .result-file { color: #94a3b8; font-size: 12px; margin-top: 4px; }
        .empty { color: #64748b; text-align: center; padding: 40px 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>🧠 OpenClaw Memory Dashboard</h1>
          <p class="subtitle">Persistent agent memory with ALMA meta-learning</p>
        </header>

        <div class="grid">
          <div class="card">
            <h3>Indexed Memories</h3>
            <div class="stat">0</div>
            <p style="margin: 0; color: #64748b; font-size: 12px;">Searchable facts</p>
          </div>
          <div class="card">
            <h3>Best ALMA Design</h3>
            <div class="stat">-</div>
            <p style="margin: 0; color: #64748b; font-size: 12px;">Optimizing...</p>
          </div>
          <div class="card">
            <h3>Auto-Extractions</h3>
            <div class="stat">0</div>
            <p style="margin: 0; color: #64748b; font-size: 12px;">This session</p>
          </div>
        </div>

        <div class="search">
          <input type="text" id="searchInput" placeholder="Search memories...">
          <div class="results" id="results"></div>
        </div>

        <h2>Timeline</h2>
        <div class="empty">No memories yet. Extract facts from conversations.</div>
      </div>

      <script>
        document.getElementById('searchInput').addEventListener('input', async (e) => {
          const query = e.target.value;
          if (!query) {
            document.getElementById('results').innerHTML = '';
            return;
          }

          try {
            const res = await fetch(\`/api/search?q=\${encodeURIComponent(query)}\`);
            const data = await res.json();
            const html = data.results.length > 0
              ? data.results.map(r => \`
                  <div class="result">
                    <p class="result-title">\${r.preview}...</p>
                    <p class="result-file">\${r.file} (score: \${r.score.toFixed(2)})</p>
                  </div>
                \`).join('')
              : '<div class="empty">No results</div>';
            document.getElementById('results').innerHTML = html;
          } catch (err) {
            console.error('Search failed:', err);
          }
        });

        // Load stats on startup
        fetch('/api/stats').then(r => r.json()).then(data => {
          console.log('Stats:', data);
        });
      </script>
    </body>
    </html>
  `);
});
/**
 * Start server
 */
export function startDashboard() {
    return new Promise((resolve) => {
        app.listen(PORT, () => {
            console.log(`\n🧠 Memory Dashboard: http://localhost:${PORT}`);
            console.log(`   Search, browse, and manage memories\n`);
            resolve();
        });
    });
}
export default app;
//# sourceMappingURL=server.js.map