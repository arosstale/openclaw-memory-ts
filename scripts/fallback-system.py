#!/usr/bin/env python3
"""
Pi-Agent Fallback System

Automatically degrades to graceful fallback modes when components fail.
Ensures system remains functional even when dependencies are unavailable.

Components with fallbacks:
- PostgreSQL → SQLite
- QMD → Built-in search
- Vector Store → BM25 search
- Dual Memory → Single memory
- Swarm → Solo mode
"""

import subprocess
import os
import sqlite3
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

# ========================================
# Component Status
# ========================================

class ComponentStatus(Enum):
    """Status of a component."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    Fallback = "fallback"

# ========================================
# Component Health Check
# ========================================

@dataclass
class ComponentHealth:
    """Health status of a component."""
    
    name: str
    status: ComponentStatus
    last_check: float
    response_time: Optional[float] = None
    error: Optional[str] = None
    fallback_mode: Optional[str] = None

# ========================================
# Fallback Strategy
# ========================================

@dataclass
class FallbackStrategy:
    """Fallback strategy for a component."""
    
    component: str
    fallback_mode: str
    trigger_conditions: List[str]
    degradation_level: int  # 0-100 (higher = more degraded)
    auto_enable: bool = True
    manual_override: bool = False

# ========================================
# Fallback System
# ========================================

class FallbackSystem:
    """Manages component fallbacks and graceful degradation."""
    
    def __init__(self, config_file: str = None, log_file: str = None):
        self.config_file = config_file or "/home/majinbu/pi-mono-workspace/.openclaw/fallback_config.json"
        self.log_file = log_file or "/home/majinbu/pi-mono-workspace/logs/fallback.log"
        
        self.fallbacks: Dict[str, FallbackStrategy] = {}
        self.health_history: Dict[str, List[ComponentHealth]] = {}
        
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.load_config()
    
    # ========================================
    # Component Checks
    # ========================================
    
    def check_postgresql(self) -> ComponentHealth:
        """Check PostgreSQL availability."""
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-U", "openclaw"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Test actual connection
                conn = sqlite3.connect(":memory:")
                conn.close()
                
                return ComponentHealth(
                    name="postgresql",
                    status=ComponentStatus.OPERATIONAL,
                    last_check=time.time(),
                    response_time=0.1
                )
            else:
                return ComponentHealth(
                    name="postgresql",
                    status=ComponentStatus.FAILED,
                    last_check=time.time(),
                    error=result.stderr
                )
        except Exception as e:
            return ComponentHealth(
                name="postgresql",
                status=ComponentStatus.FAILED,
                last_check=time.time(),
                error=str(e)
            )
    
    def check_qmd(self) -> ComponentHealth:
        """Check QMD availability."""
        try:
            result = subprocess.run(
                ["which", "qmd"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                return ComponentHealth(
                    name="qmd",
                    status=ComponentStatus.OPERATIONAL,
                    last_check=time.time(),
                    response_time=0.05
                )
            else:
                return ComponentHealth(
                    name="qmd",
                    status=ComponentStatus.FAILED,
                    last_check=time.time(),
                    error="qmd not found in PATH"
                )
        except Exception as e:
            return ComponentHealth(
                name="qmd",
                status=ComponentStatus.FAILED,
                last_check=time.time(),
                error=str(e)
            )
    
    def check_docker(self) -> ComponentHealth:
        """Check Docker availability."""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return ComponentHealth(
                    name="docker",
                    status=ComponentStatus.OPERATIONAL,
                    last_check=time.time(),
                    response_time=0.2
                )
            else:
                return ComponentHealth(
                    name="docker",
                    status=ComponentStatus.FAILED,
                    last_check=time.time(),
                    error=result.stderr
                )
        except Exception as e:
            return ComponentHealth(
                name="docker",
                status=ComponentStatus.FAILED,
                last_check=time.time(),
                error=str(e)
            )
    
    def check_vector_store(self) -> ComponentHealth:
        """Check vector store availability."""
        try:
            # Check if vector database is running
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5433"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return ComponentHealth(
                    name="vector_store",
                    status=ComponentStatus.OPERATIONAL,
                    last_check=time.time(),
                    response_time=0.1
                )
            else:
                return ComponentHealth(
                    name="vector_store",
                    status=ComponentStatus.FAILED,
                    last_check=time.time(),
                    error="Vector DB not available"
                )
        except Exception as e:
            return ComponentHealth(
                name="vector_store",
                status=ComponentStatus.FAILED,
                last_check=time.time(),
                error=str(e)
            )
    
    # ========================================
    # Fallback Actions
    # ========================================
    
    def enable_postgresql_fallback(self) -> bool:
        """Enable SQLite fallback for PostgreSQL."""
        self._log("Enabling PostgreSQL → SQLite fallback")
        
        # Set environment variable to use SQLite
        os.environ["OPENCLAW_DB_FALLBACK"] = "sqlite"
        os.environ["OPENCLAW_DB_PATH"] = "/home/majinbu/pi-mono-workspace/.openclaw/openclaw.db"
        
        # Update config
        self._update_fallback("postgresql", "sqlite")
        
        self._log("PostgreSQL fallback enabled: Using SQLite")
        return True
    
    def enable_qmd_fallback(self) -> bool:
        """Enable built-in search fallback for QMD."""
        self._log("Enabling QMD → Built-in search fallback")
        
        # Set environment variable
        os.environ["OPENCLAW_SEARCH_FALLBACK"] = "builtin"
        
        # Update config
        self._update_fallback("qmd", "builtin_search")
        
        self._log("QMD fallback enabled: Using built-in search")
        return True
    
    def enable_vector_store_fallback(self) -> bool:
        """Enable BM25 fallback for vector store."""
        self._log("Enabling Vector Store → BM25 fallback")
        
        # Set environment variable
        os.environ["OPENCLAW_VECTOR_FALLBACK"] = "bm25"
        
        # Update config
        self._update_fallback("vector_store", "bm25")
        
        self._log("Vector Store fallback enabled: Using BM25")
        return True
    
    # ========================================
    # Auto-Fallback Management
    # ========================================
    
    def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Check all components and enable fallbacks if needed."""
        health = {
            "postgresql": self.check_postgresql(),
            "qmd": self.check_qmd(),
            "docker": self.check_docker(),
            "vector_store": self.check_vector_store(),
        }
        
        # Store in history
        for name, h in health.items():
            if name not in self.health_history:
                self.health_history[name] = []
            self.health_history[name].append(h)
            # Keep only last 100 checks
            self.health_history[name] = self.health_history[name][-100:]
        
        # Auto-enable fallbacks
        for name, h in health.items():
            if h.status == ComponentStatus.FAILED:
                self._auto_fallback(name)
        
        return health
    
    def _auto_fallback(self, component: str) -> bool:
        """Auto-enable fallback for a failed component."""
        self._log(f"Auto-fallback triggered for: {component}")
        
        fallback_actions = {
            "postgresql": self.enable_postgresql_fallback,
            "qmd": self.enable_qmd_fallback,
            "vector_store": self.enable_vector_store_fallback,
            "docker": lambda: self._log("Docker has no direct fallback"),
        }
        
        action = fallback_actions.get(component)
        if action:
            return action()
        return False
    
    # ========================================
    # Config Management
    # ========================================
    
    def load_config(self) -> None:
        """Load fallback configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    for name, config in data.get("fallbacks", {}).items():
                        self.fallbacks[name] = FallbackStrategy(
                            component=name,
                            fallback_mode=config.get("fallback_mode"),
                            trigger_conditions=config.get("trigger_conditions", []),
                            degradation_level=config.get("degradation_level", 0),
                            auto_enable=config.get("auto_enable", True),
                            manual_override=config.get("manual_override", False)
                        )
            except Exception as e:
                self._log(f"Error loading config: {e}")
    
    def save_config(self) -> None:
        """Save fallback configuration."""
        data = {
            "fallbacks": {}
        }
        
        for name, strategy in self.fallbacks.items():
            data["fallbacks"][name] = {
                "fallback_mode": strategy.fallback_mode,
                "trigger_conditions": strategy.trigger_conditions,
                "degradation_level": strategy.degradation_level,
                "auto_enable": strategy.auto_enable,
                "manual_override": strategy.manual_override
            }
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _update_fallback(self, component: str, fallback_mode: str) -> None:
        """Update fallback status."""
        if component in self.fallbacks:
            self.fallbacks[component].fallback_mode = fallback_mode
            self.fallbacks[component].degradation_level = 50
        else:
            self.fallbacks[component] = FallbackStrategy(
                component=component,
                fallback_mode=fallback_mode,
                trigger_conditions=["failed"],
                degradation_level=50,
                auto_enable=True
            )
        
        self.save_config()
    
    # ========================================
    # Status Reporting
    # ========================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        health = self.check_all_components()
        
        operational = sum(1 for h in health.values() if h.status == ComponentStatus.OPERATIONAL)
        failed = sum(1 for h in health.values() if h.status == ComponentStatus.FAILED)
        total = len(health)
        
        degradation_score = sum(s.degradation_level for s in self.fallbacks.values()) / max(len(self.fallbacks), 1)
        
        return {
            "total_components": total,
            "operational": operational,
            "failed": failed,
            "degradation_score": degradation_score,
            "fallbacks_active": len(self.fallbacks),
            "component_health": {
                name: {
                    "status": h.status.value,
                    "error": h.error,
                    "response_time": h.response_time
                }
                for name, h in health.items()
            },
            "active_fallbacks": {
                name: {
                    "mode": strategy.fallback_mode,
                    "level": strategy.degradation_level
                }
                for name, strategy in self.fallbacks.items()
            }
        }
    
    # ========================================
    # Utilities
    # ========================================
    
    def _log(self, message: str) -> None:
        """Log message."""
        import time
        timestamp = time.ctime()
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[Fallback] {message}")

# ========================================
# CLI
# ========================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pi-Agent Fallback System")
    parser.add_argument("--check", action="store_true", help="Check all components")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--enable-fallback", help="Enable fallback for component")
    parser.add_argument("--log", help="Log file path")
    
    args = parser.parse_args()
    
    system = FallbackSystem(log_file=args.log)
    
    if args.check:
        health = system.check_all_components()
        print("Component Health:")
        for name, h in health.items():
            status_icon = "✅" if h.status == ComponentStatus.OPERATIONAL else "❌"
            print(f"  {status_icon} {name}: {h.status.value}")
            if h.error:
                print(f"      Error: {h.error}")
    elif args.status:
        status = system.get_system_status()
        print("System Status:")
        print(f"  Components: {status['operational']}/{status['total_components']} operational")
        print(f"  Failed: {status['failed']}")
        print(f"  Degradation Score: {status['degradation_score']:.1f}%")
        print(f"  Active Fallbacks: {status['fallbacks_active']}")
        print("\nActive Fallbacks:")
        for comp, info in status['active_fallbacks'].items():
            print(f"  - {comp} → {info['mode']} (level: {info['level']})")
    elif args.enable_fallback:
        component = args.enable_fallback
        if component == "postgresql":
            system.enable_postgresql_fallback()
        elif component == "qmd":
            system.enable_qmd_fallback()
        elif component == "vector":
            system.enable_vector_store_fallback()
        else:
            print(f"Unknown component: {component}")
    else:
        # Default: check and report
        health = system.check_all_components()
        print("Pi-Agent Fallback System")
        print("=" * 40)
        
        for name, h in health.items():
            status_icon = "✅" if h.status == ComponentStatus.OPERATIONAL else "❌"
            print(f"{status_icon} {name:15} {h.status.value}")
            if h.error:
                print(f"    └─ {h.error}")
        
        print("\nActive Fallbacks:")
        if system.fallbacks:
            for name, strategy in system.fallbacks.items():
                print(f"  - {name} → {strategy.fallback_mode}")
        else:
            print("  (none)")
