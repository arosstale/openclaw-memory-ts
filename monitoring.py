#!/usr/bin/env python3
"""
OpenClaw Memory Template - Monitoring and Alerting
Prometheus metrics exporter and alerting rules
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import parse_qs


class Alert:
    """Alert data structure"""

    def __init__(self, name: str, severity: str, message: str, metadata: Optional[Dict] = None):
        """Initialize alert

        Args:
            name: Alert name
            severity: Alert severity (INFO, WARN, ERROR, CRITICAL)
            message: Alert message
            metadata: Optional additional metadata
        """
        self.name = name
        self.severity = severity
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.resolved = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "severity": self.severity,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "resolved": self.resolved
        }


class AlertManager:
    """Alert management system"""

    def __init__(self, max_alerts: int = 100):
        """Initialize alert manager

        Args:
            max_alerts: Maximum number of alerts to keep
        """
        self.max_alerts = max_alerts
        self.alerts: List[Alert] = []
        self.alert_file = os.environ.get("OPENCLAW_ALERT_FILE", ".openclaw/alerts.json")

        # Load existing alerts
        self._load_alerts()

    def _load_alerts(self) -> None:
        """Load alerts from file"""
        try:
            if os.path.exists(self.alert_file):
                with open(self.alert_file) as f:
                    data = json.load(f)
                    self.alerts = [Alert(**a) for a in data.get("alerts", [])]
        except Exception:
            pass

    def _save_alerts(self) -> None:
        """Save alerts to file"""
        try:
            os.makedirs(os.path.dirname(self.alert_file), exist_ok=True)
            with open(self.alert_file, "w") as f:
                json.dump({
                    "alerts": [a.to_dict() for a in self.alerts],
                    "updated": datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save alerts: {e}", file=sys.stderr)

    def trigger(self, name: str, severity: str, message: str, **metadata) -> None:
        """Trigger an alert

        Args:
            name: Alert name
            severity: Alert severity (INFO, WARN, ERROR, CRITICAL)
            message: Alert message
            **metadata: Additional metadata
        """
        alert = Alert(name, severity, message, metadata)

        # Check for duplicate (same name and severity in last 5 minutes)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_alerts = [
            a for a in self.alerts
            if a.name == name and a.severity == severity
            and not a.resolved
            and datetime.fromisoformat(a.timestamp) > five_minutes_ago
        ]

        if recent_alerts:
            # Update existing alert
            recent_alerts[0].metadata.update(metadata)
            print(f"⚠️  Alert '{name}' already active (updated)")
        else:
            # Add new alert
            self.alerts.append(alert)
            print(f"🚨 ALERT [{severity}] {name}: {message}")

        # Trim old alerts
        self._trim_alerts()
        self._save_alerts()

    def resolve(self, name: str) -> None:
        """Resolve an alert

        Args:
            name: Alert name to resolve
        """
        for alert in self.alerts:
            if alert.name == name and not alert.resolved:
                alert.resolved = True
                print(f"✅ Alert '{name}' resolved")
                break

        self._save_alerts()

    def _trim_alerts(self) -> None:
        """Trim old alerts to max_alerts"""
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]

    def get_active(self) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts

        Returns:
            List of active alert dictionaries
        """
        return [
            a.to_dict()
            for a in self.alerts
            if not a.resolved
        ]

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all alerts

        Returns:
            List of all alert dictionaries
        """
        return [a.to_dict() for a in self.alerts]


class PrometheusMetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alert_manager = AlertManager()
        self.metrics: Dict[str, Dict[str, float]] = {
            "memory_sync_duration_ms": {"value": 0, "help": "Time to sync memory"},
            "memory_sync_success": {"value": 0, "type": "counter", "help": "Successful syncs"},
            "memory_sync_errors": {"value": 0, "type": "counter", "help": "Failed syncs"},
            "msam_query_duration_ms": {"value": 0, "help": "Time to query MSAM"},
            "msam_query_success": {"value": 0, "type": "counter", "help": "Successful MSAM queries"},
            "git_sync_duration_ms": {"value": 0, "help": "Time to sync Git"},
            "git_sync_success": {"value": 0, "type": "counter", "help": "Successful Git syncs"},
            "health_check_duration_ms": {"value": 0, "help": "Time to run health check"},
            "active_alerts": {"value": 0, "type": "gauge", "help": "Number of active alerts"},
        }

    def _set_headers(self, status_code: int = 200, content_type: str = "text/plain"):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def _format_metric(self, name: str, metric: Dict[str, float]) -> str:
        """Format metric in Prometheus format

        Args:
            name: Metric name
            metric: Metric dict with value, type, help

        Returns:
            Formatted Prometheus metric string
        """
        metric_type = metric.get("type", "gauge")
        help_text = metric.get("help", "")

        lines = [f"# HELP openclaw_{name} {help_text}"]
        lines.append(f"# TYPE openclaw_{name} {metric_type}")

        if metric_type == "counter":
            lines.append(f"openclaw_{name} {metric['value']}")
        else:  # gauge
            lines.append(f"openclaw_{name} {metric['value']}")

        return "\n".join(lines)

    def _format_all_metrics(self) -> str:
        """Format all metrics for Prometheus

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        for name, metric in self.metrics.items():
            lines.append(self._format_metric(name, metric))

        # Add active alerts gauge
        active_alerts = len(self.alert_manager.get_active())
        lines.append("# HELP openclaw_active_alerts Number of active alerts")
        lines.append("# TYPE openclaw_active_alerts gauge")
        lines.append(f"openclaw_active_alerts {active_alerts}")

        return "\n".join(lines)

    def do_GET(self):
        """Handle GET requests"""
        path = self.path

        try:
            if path == "/metrics" or path == "/prometheus":
                # Prometheus metrics endpoint
                self._set_headers()
                self.wfile.write(self._format_all_metrics().encode())

            elif path == "/alerts":
                # Alerts endpoint (JSON)
                self._set_headers(200, "application/json")
                alerts_data = {
                    "active": self.alert_manager.get_active(),
                    "all": self.alert_manager.get_all()
                }
                self.wfile.write(json.dumps(alerts_data).encode())

            elif path == "/alert":
                # Trigger alert (GET for simplicity)
                query = parse_qs(self.path.split("?")[1] if "?" in self.path else "")
                name = query.get(b"name", [b"test_alert"])[0].decode()
                severity = query.get(b"severity", [b"INFO"])[0].decode()
                message = query.get(b"message", [b"Test alert"])[0].decode()

                self.alert_manager.trigger(name, severity, message)

                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"status": "triggered"}).encode())

            else:
                # 404
                self._set_headers(404)
                self.wfile.write(b"Not found")

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(f"Error: {str(e)}".encode())


class MetricsCollector:
    """Collects and updates Prometheus metrics"""

    @staticmethod
    def record_memory_sync(duration_ms: float, success: bool) -> None:
        """Record memory sync metric

        Args:
            duration_ms: Duration in milliseconds
            success: Whether sync succeeded
        """
        print(f"# TYPE openclaw_memory_sync_duration_ms gauge")
        print(f"openclaw_memory_sync_duration_ms {duration_ms}")

        print(f"# TYPE openclaw_memory_sync_success counter")
        print(f"openclaw_memory_sync_success {1 if success else 0}")

    @staticmethod
    def record_msam_query(duration_ms: float, success: bool) -> None:
        """Record MSAM query metric

        Args:
            duration_ms: Duration in milliseconds
            success: Whether query succeeded
        """
        print(f"# TYPE openclaw_msam_query_duration_ms gauge")
        print(f"openclaw_msam_query_duration_ms {duration_ms}")

        print(f"# TYPE openclaw_msam_query_success counter")
        print(f"openclaw_msam_query_success {1 if success else 0}")

    @staticmethod
    def record_git_sync(duration_ms: float, success: bool) -> None:
        """Record Git sync metric

        Args:
            duration_ms: Duration in milliseconds
            success: Whether sync succeeded
        """
        print(f"# TYPE openclaw_git_sync_duration_ms gauge")
        print(f"openclaw_git_sync_duration_ms {duration_ms}")

        print(f"# TYPE openclaw_git_sync_success counter")
        print(f"openclaw_git_sync_success {1 if success else 0}")


def main():
    """Start monitoring server"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenClaw Monitoring Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9090, help="Port for Prometheus metrics")
    args = parser.parse_args()

    print(f"📊 OpenClaw Monitoring Server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Endpoints:")
    print(f"     - http://{args.host}:{args.port}/metrics (Prometheus)")
    print(f"     - http://{args.host}:{args.port}/alerts (JSON)")
    print(f"     - http://{args.host}:{args.port}/alert?name=X&severity=Y&message=Z (Trigger)")
    print()

    try:
        server = HTTPServer((args.host, args.port), PrometheusMetricsHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        server.shutdown()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
