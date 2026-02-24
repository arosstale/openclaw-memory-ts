#!/usr/bin/env python3
"""
Pi-Agent Task Prioritization System

Replaces binary thermal gating (68°C/72°C) with intelligent task queuing.
Prioritizes low-compute tasks when hot, allows full compute when cool.

Classes:
- TaskPriority: LOW, MEDIUM, HIGH, CRITICAL
- Task: Represents a unit of work with priority and compute intensity
- TaskQueue: Manages task execution based on thermal state
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any
import subprocess
import time
import json
from pathlib import Path

# ========================================
# Task Priorities
# ========================================

class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 4    # Always execute (emergency responses, health checks)
    HIGH = 3        # Execute when available (respond to user messages)
    MEDIUM = 2      Execute when cool enough (memory compaction, reflection)
    LOW = 1         # Execute only when idle (optimization, analysis, mutation)

# ========================================
# Task Types
# ========================================

class ComputeIntensity(Enum):
    """Compute intensity levels for thermal estimation."""
    MINIMAL = 1     # < 5% CPU (respond to simple queries)
    LOW = 2         # < 10% CPU (read memory, basic search)
    MEDIUM = 3      # < 25% CPU (reflection, compression)
    HIGH = 4        # < 50% CPU (mutation, optimization)
    INTENSIVE = 5   # > 50% CPU (full meta-learning)

# ========================================
# Task Definition
# ========================================

@dataclass
class Task:
    """A unit of work with priority and compute requirements."""
    
    name: str
    priority: TaskPriority
    intensity: ComputeIntensity
    callback: Callable[[], Any]
    description: str = ""
    timeout: int = 300  # 5 minutes default
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"<Task {self.name} [{self.priority.name}/{self.intensity.name}]>"

# ========================================
# Thermal State
# ========================================

@dataclass
class ThermalState:
    """Current thermal state of the system."""
    
    temperature: float  # Celsius
    throttling: bool
    cpu_usage: float  # Percentage
    memory_usage: float  # Percentage
    timestamp: float = field(default_factory=time.time)
    
    @property
    def severity(self) -> int:
        """Thermal severity: 0=cool, 1=warm, 2=hot, 3=critical"""
        if self.temperature >= 85:
            return 3  # Critical
        elif self.temperature >= 75:
            return 2  # Hot
        elif self.temperature >= 65:
            return 1  # Warm
        else:
            return 0  # Cool
    
    @property
    def allowed_priorities(self) -> List[TaskPriority]:
        """Which priorities are allowed in this thermal state."""
        severity = self.severity
        if severity == 0:  # Cool
            return [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        elif severity == 1:  # Warm
            return [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM]
        elif severity == 2:  # Hot
            return [TaskPriority.CRITICAL, TaskPriority.HIGH]
        else:  # Critical
            return [TaskPriority.CRITICAL]

    @property
    def allowed_intensity(self) -> ComputeIntensity:
        """Maximum allowed compute intensity in this thermal state."""
        severity = self.severity
        if severity == 0:
            return ComputeIntensity.INTENSIVE
        elif severity == 1:
            return ComputeIntensity.MEDIUM
        elif severity == 2:
            return ComputeIntensity.LOW
        else:
            return ComputeIntensity.MINIMAL

# ========================================
# Task Queue
# ========================================

class TaskQueue:
    """Manages task execution based on thermal state."""
    
    def __init__(self, log_file: str = None):
        self.queue: List[Task] = []
        self.running: Optional[Task] = None
        self.completed: List[Task] = []
        self.deferred: List[Task] = []
        self.failed: List[Task] = []
        self.log_file = log_file
        
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def add(self, task: Task):
        """Add a task to the queue."""
        self.queue.append(task)
        self._log(f"Added task: {task.name}")
    
    def get_thermal_state(self) -> ThermalState:
        """Get current thermal state."""
        try:
            # Get temperature (simplified - adjust for your system)
            temp_result = subprocess.run(
                ["sensors", "-j"],
                capture_output=True,
                text=True,
                timeout=5
            )
            temperature = 45.0  # Fallback
            
            if temp_result.returncode == 0:
                import json
                sensors_data = json.loads(temp_result.stdout)
                # Parse temperature (adjust based on your sensors output)
                for chip in sensors_data.values():
                    for sensor in chip.values():
                        if isinstance(sensor, dict) and "temp" in str(sensor):
                            for k, v in sensor.items():
                                if k.endswith("_input"):
                                    temperature = max(temperature, float(v))
            
            # Get CPU usage
            cpu_result = subprocess.run(
                ["top", "-bn1", "-o", "%CPU"],
                capture_output=True,
                text=True,
                timeout=5
            )
            cpu_usage = 10.0  # Fallback
            
            # Get memory usage
            mem_result = subprocess.run(
                ["free", "-m"],
                capture_output=True,
                text=True,
                timeout=5
            )
            mem_usage = 50.0  # Fallback
            if mem_result.returncode == 0:
                lines = mem_result.stdout.split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        total = float(parts[1])
                        used = float(parts[2])
                        mem_usage = (used / total) * 100
            
            return ThermalState(
                temperature=temperature,
                throttling=temperature > 80,
                cpu_usage=cpu_usage,
                memory_usage=mem_usage
            )
        except Exception as e:
            self._log(f"Error getting thermal state: {e}")
            return ThermalState(
                temperature=45.0,
                throttling=False,
                cpu_usage=10.0,
                memory_usage=50.0
            )
    
    def can_execute(self, task: Task, thermal_state: ThermalState) -> bool:
        """Check if a task can be executed given thermal state."""
        # Check priority
        if task.priority not in thermal_state.allowed_priorities:
            return False
        
        # Check intensity
        if task.intensity.value > thermal_state.allowed_intensity.value:
            return False
        
        return True
    
    def execute_next(self) -> bool:
        """Execute the next eligible task. Returns True if a task was executed."""
        thermal_state = self.get_thermal_state()
        self._log(f"Thermal State: {thermal_state.temperature}°C, Severity: {thermal_state.severity}")
        self._log(f"Allowed Priorities: {[p.name for p in thermal_state.allowed_priorities]}")
        
        # Find first executable task
        for i, task in enumerate(self.queue):
            if self.can_execute(task, thermal_state):
                self._log(f"Executing: {task.name}")
                self.running = task
                del self.queue[i]
                
                try:
                    result = task.callback()
                    self.completed.append(task)
                    self._log(f"Completed: {task.name}")
                    return True
                except Exception as e:
                    self._log(f"Failed: {task.name} - {e}")
                    self.failed.append(task)
                    return True
                finally:
                    self.running = None
            else:
                self._log(f"Deferred: {task.name} (thermal state)")
                self.deferred.append(task)
                del self.queue[i]
        
        # No executable tasks
        return False
    
    def run_queue(self, max_tasks: int = None) -> int:
        """Run the queue until empty or max_tasks reached. Returns tasks executed."""
        executed = 0
        while self.queue:
            if max_tasks and executed >= max_tasks:
                break
            if not self.execute_next():
                break  # No more executable tasks
            executed += 1
            time.sleep(0.1)  # Brief pause between tasks
        
        return executed
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return {
            "queued": len(self.queue),
            "running": 1 if self.running else 0,
            "completed": len(self.completed),
            "deferred": len(self.deferred),
            "failed": len(self.failed),
        }
    
    def _log(self, message: str):
        """Log message."""
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"{time.ctime()}: {message}\n")
        else:
            print(message)

# ========================================
# Predefined Tasks
# ========================================

def create_standard_tasks(queue: TaskQueue) -> None:
    """Add standard Pi-Agent tasks to the queue."""
    
    # CRITICAL: Always run
    queue.add(Task(
        name="health_check",
        priority=TaskPriority.CRITICAL,
        intensity=ComputeIntensity.LOW,
        callback=lambda: subprocess.run(
            ["/home/majinbu/pi-mono-workspace/scripts/health-check.sh"],
            capture_output=True
        ),
        description="Run health check",
        timeout=60
    ))
    
    # HIGH: User-facing tasks
    queue.add(Task(
        name="respond_to_user",
        priority=TaskPriority.HIGH,
        intensity=ComputeIntensity.MINIMAL,
        callback=lambda: None,  # Placeholder
        description="Respond to user messages",
        timeout=10
    ))
    
    # MEDIUM: Background processing
    queue.add(Task(
        name="memory_compaction",
        priority=TaskPriority.MEDIUM,
        intensity=ComputeIntensity.MEDIUM,
        callback=lambda: None,  # Placeholder
        description="Compact memory when cool",
        timeout=300
    ))
    
    queue.add(Task(
        name="reflection",
        priority=TaskPriority.MEDIUM,
        intensity=ComputeIntensity.MEDIUM,
        callback=lambda: None,  # Placeholder
        description="Reflect and learn",
        timeout=300
    ))
    
    # LOW: Optimization tasks
    queue.add(Task(
        name="alma_optimization",
        priority=TaskPriority.LOW,
        intensity=ComputeIntensity.HIGH,
        callback=lambda: None,  # Placeholder
        description="ALMA meta-learning",
        timeout=600
    ))
    
    queue.add(Task(
        name="parameter_tuning",
        priority=TaskPriority.LOW,
        intensity=ComputeIntensity.HIGH,
        callback=lambda: None,  # Placeholder
        description="Optimize parameters",
        timeout=600
    ))

# ========================================
# CLI
# ========================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pi-Agent Task Prioritization System")
    parser.add_argument("--log", help="Log file path")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed")
    parser.add_argument("--stats", action="store_true", help="Show queue statistics")
    parser.add_argument("--thermal", action="store_true", help="Show current thermal state")
    
    args = parser.parse_args()
    
    log_file = args.log or "/home/majinbu/pi-mono-workspace/logs/task_queue.log"
    queue = TaskQueue(log_file=log_file)
    
    if args.thermal:
        state = queue.get_thermal_state()
        print(f"Temperature: {state.temperature}°C")
        print(f"Severity: {state.severity}")
        print(f"Allowed Priorities: {[p.name for p in state.allowed_priorities]}")
        print(f"Allowed Intensity: {state.allowed_intensity.name}")
        print(f"CPU Usage: {state.cpu_usage}%")
        print(f"Memory Usage: {state.memory_usage}%")
    elif args.stats:
        create_standard_tasks(queue)
        stats = queue.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        create_standard_tasks(queue)
        if args.dry_run:
            print("Tasks queued (dry run):")
            for task in queue.queue:
                print(f"  - {task}")
        else:
            executed = queue.run_queue()
            print(f"Executed {executed} tasks")
            print(queue.get_stats())
