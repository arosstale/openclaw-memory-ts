#!/usr/bin/env python3
"""
OpenClaw Memory Template - Health Check Endpoint
Provides HTTP endpoint for monitoring and observability
"""

import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import traceback


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and metrics"""

    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_json(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, message, status_code=500):
        """Send error response"""
        self._send_json({"error": message, "status": "error"}, status_code)

    def _get_workspace_dir(self):
        """Get workspace directory from environment or current path"""
        return Path(os.environ.get("OPENCLAW_HOME", Path(__file__).parent.parent))

    def _check_memory_dir(self):
        """Check if memory directory exists"""
        workspace = self._get_workspace_dir()
        memory_dir = workspace / "memory"
        return {
            "exists": memory_dir.exists(),
            "path": str(memory_dir),
            "git_initialized": (memory_dir / ".git").exists()
        }

    def _check_core_dir(self):
        """Check if .openclaw/core directory exists"""
        workspace = self._get_workspace_dir()
        core_dir = workspace / ".openclaw" / "core"
        return {
            "exists": core_dir.exists(),
            "path": str(core_dir),
            "files": [f.name for f in core_dir.iterdir()] if core_dir.exists() else []
        }

    def _check_msam(self):
        """Check if MSAM is running"""
        import socket
        try:
            host = os.environ.get("MSAM_API_HOST", "127.0.0.1")
            port = int(os.environ.get("MSAM_API_PORT", "3001"))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return {"running": result == 0, "host": host, "port": port}
        except Exception as e:
            return {"running": False, "error": str(e)}

    def _check_git_sync(self):
        """Check if Git is synced with remote"""
        import subprocess
        workspace = self._get_workspace_dir()
        memory_dir = workspace / "memory"

        if not (memory_dir / ".git").exists():
            return {"git_initialized": False, "synced": False}

        try:
            # Check if there's a remote configured
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=memory_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            has_remote = bool(result.stdout.strip())

            if not has_remote:
                return {"git_initialized": True, "has_remote": False, "synced": False}

            # Check if there are uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=memory_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            has_changes = bool(result.stdout.strip())

            return {
                "git_initialized": True,
                "has_remote": True,
                "synced": not has_changes
            }
        except Exception as e:
            return {"git_initialized": True, "synced": False, "error": str(e)}

    def _get_atom_count(self):
        """Get MSAM atom count if available"""
        import subprocess
        try:
            result = subprocess.run(
                ["python", "-m", "msam.remember", "stats"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("total_atoms", 0)
        except Exception:
            pass
        return None

    def do_GET(self):
        """Handle GET requests"""
        path = self.path

        try:
            if path == "/health" or path == "/":
                # Health check endpoint
                response = {
                    "status": "healthy",
                    "version": "2.5.0",
                    "timestamp": __import__("time").time()
                }
                self._send_json(response)

            elif path == "/metrics":
                # Metrics endpoint
                response = {
                    "memory": self._check_memory_dir(),
                    "core": self._check_core_dir(),
                    "msam": self._check_msam(),
                    "git": self._check_git_sync(),
                    "atoms": self._get_atom_count(),
                    "timestamp": __import__("time").time()
                }
                self._send_json(response)

            elif path == "/readiness":
                # Readiness check (Kubernetes-style)
                memory_ok = self._check_memory_dir()["exists"]
                core_ok = self._check_core_dir()["exists"]

                if memory_ok and core_ok:
                    response = {"status": "ready"}
                    self._send_json(response)
                else:
                    response = {
                        "status": "not_ready",
                        "memory_ok": memory_ok,
                        "core_ok": core_ok
                    }
                    self._send_json(response, 503)

            else:
                # 404
                self._send_error("Not found", 404)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
            self._send_error(error_msg, 500)

    def log_message(self, format, *args):
        """Override to reduce logging"""
        return


def main():
    """Start health check server"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenClaw Health Check Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    args = parser.parse_args()

    print(f"🚀 OpenClaw Health Check Server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Endpoints:")
    print(f"     - http://{args.host}:{args.port}/health")
    print(f"     - http://{args.host}:{args.port}/metrics")
    print(f"     - http://{args.host}:{args.port}/readiness")
    print()

    try:
        server = HTTPServer((args.host, args.port), HealthCheckHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        server.shutdown()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
