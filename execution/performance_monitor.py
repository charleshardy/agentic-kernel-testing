"""Performance metrics capture system for test execution.

This module provides functionality for:
- Resource usage monitoring during test execution
- Performance metric collection and storage
- Metrics reporting through API endpoints
- Performance trend analysis
"""

import os
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import json
import subprocess
from collections import defaultdict, deque

from ai_generator.models import TestResult, Environment


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    process_count: int
    load_average: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceSnapshot':
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        return cls(**data, timestamp=timestamp)


@dataclass
class ProcessMetrics:
    """Metrics for a specific process."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    memory_vms_mb: float
    num_threads: int
    num_fds: int
    io_read_mb: float
    io_write_mb: float
    create_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['create_time'] = self.create_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessMetrics':
        """Create from dictionary."""
        create_time = datetime.fromisoformat(data.pop('create_time'))
        return cls(**data, create_time=create_time)


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a test execution."""
    test_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Resource usage statistics
    peak_cpu_percent: float
    avg_cpu_percent: float
    peak_memory_mb: float
    avg_memory_mb: float
    total_disk_read_mb: float
    total_disk_write_mb: float
    total_network_sent_mb: float
    total_network_recv_mb: float
    
    # Process-specific metrics
    process_metrics: List[ProcessMetrics] = field(default_factory=list)
    
    # Time series data (sampled)
    resource_snapshots: List[ResourceSnapshot] = field(default_factory=list)
    
    # Performance indicators
    performance_score: float = 0.0
    bottlenecks: List[str] = field(default_factory=list)
    
    # Environment info
    environment_id: str = ""
    architecture: str = ""
    memory_total_mb: float = 0.0
    cpu_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        data['process_metrics'] = [pm.to_dict() for pm in self.process_metrics]
        data['resource_snapshots'] = [rs.to_dict() for rs in self.resource_snapshots]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create from dictionary."""
        start_time = datetime.fromisoformat(data.pop('start_time'))
        end_time = datetime.fromisoformat(data.pop('end_time'))
        process_metrics = [ProcessMetrics.from_dict(pm) for pm in data.pop('process_metrics', [])]
        resource_snapshots = [ResourceSnapshot.from_dict(rs) for rs in data.pop('resource_snapshots', [])]
        
        return cls(**data, start_time=start_time, end_time=end_time,
                   process_metrics=process_metrics, resource_snapshots=resource_snapshots)


class PerformanceMonitor:
    """Monitor and collect performance metrics during test execution."""
    
    def __init__(self, sample_interval: float = 1.0, max_samples: int = 1000):
        """Initialize the performance monitor.
        
        Args:
            sample_interval: Interval between samples in seconds
            max_samples: Maximum number of samples to keep in memory
        """
        self.sample_interval = sample_interval
        self.max_samples = max_samples
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.start_time = None
        self.end_time = None
        
        # Data collection
        self.resource_snapshots = deque(maxlen=max_samples)
        self.process_metrics = {}
        self.monitored_processes = set()
        
        # Initial system state
        self.initial_disk_io = None
        self.initial_network_io = None
        
        # Performance metrics storage
        self.metrics_storage = {}
    
    def start_monitoring(self, test_id: str, process_ids: Optional[List[int]] = None):
        """Start monitoring performance metrics.
        
        Args:
            test_id: ID of the test being monitored
            process_ids: Optional list of specific process IDs to monitor
        """
        if self.monitoring:
            self.stop_monitoring()
        
        self.test_id = test_id
        self.monitoring = True
        self.start_time = datetime.now()
        self.resource_snapshots.clear()
        self.process_metrics.clear()
        
        # Set monitored processes
        if process_ids:
            self.monitored_processes = set(process_ids)
        else:
            self.monitored_processes = set()
        
        # Capture initial I/O counters
        try:
            self.initial_disk_io = psutil.disk_io_counters()
            self.initial_network_io = psutil.net_io_counters()
        except:
            self.initial_disk_io = None
            self.initial_network_io = None
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Optional[PerformanceMetrics]:
        """Stop monitoring and return collected metrics.
        
        Returns:
            PerformanceMetrics object with collected data
        """
        if not self.monitoring:
            return None
        
        self.monitoring = False
        self.end_time = datetime.now()
        
        # Wait for monitoring thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        # Generate performance metrics
        metrics = self._generate_metrics()
        
        # Store metrics
        if hasattr(self, 'test_id'):
            self.metrics_storage[self.test_id] = metrics
        
        return metrics
    
    def add_process(self, process_id: int):
        """Add a process to monitor.
        
        Args:
            process_id: Process ID to monitor
        """
        self.monitored_processes.add(process_id)
    
    def remove_process(self, process_id: int):
        """Remove a process from monitoring.
        
        Args:
            process_id: Process ID to stop monitoring
        """
        self.monitored_processes.discard(process_id)
    
    def _monitoring_loop(self):
        """Main monitoring loop running in separate thread."""
        while self.monitoring:
            try:
                # Capture system snapshot
                snapshot = self._capture_system_snapshot()
                self.resource_snapshots.append(snapshot)
                
                # Capture process metrics
                self._capture_process_metrics()
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.sample_interval)
    
    def _capture_system_snapshot(self) -> ResourceSnapshot:
        """Capture a snapshot of system resources.
        
        Returns:
            ResourceSnapshot with current system state
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk I/O
        disk_io_read_mb = 0.0
        disk_io_write_mb = 0.0
        try:
            current_disk_io = psutil.disk_io_counters()
            if self.initial_disk_io and current_disk_io:
                disk_io_read_mb = (current_disk_io.read_bytes - self.initial_disk_io.read_bytes) / (1024 * 1024)
                disk_io_write_mb = (current_disk_io.write_bytes - self.initial_disk_io.write_bytes) / (1024 * 1024)
        except:
            pass
        
        # Network I/O
        network_io_sent_mb = 0.0
        network_io_recv_mb = 0.0
        try:
            current_network_io = psutil.net_io_counters()
            if self.initial_network_io and current_network_io:
                network_io_sent_mb = (current_network_io.bytes_sent - self.initial_network_io.bytes_sent) / (1024 * 1024)
                network_io_recv_mb = (current_network_io.bytes_recv - self.initial_network_io.bytes_recv) / (1024 * 1024)
        except:
            pass
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems only)
        load_average = []
        try:
            load_average = list(os.getloadavg())
        except:
            pass
        
        return ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb,
            process_count=process_count,
            load_average=load_average
        )
    
    def _capture_process_metrics(self):
        """Capture metrics for monitored processes."""
        for pid in list(self.monitored_processes):
            try:
                process = psutil.Process(pid)
                
                # Basic process info
                process_info = process.as_dict([
                    'name', 'cpu_percent', 'memory_percent', 'memory_info',
                    'num_threads', 'num_fds', 'io_counters', 'create_time'
                ])
                
                # Convert to ProcessMetrics
                memory_info = process_info.get('memory_info', psutil.pmem(0, 0))
                io_counters = process_info.get('io_counters', psutil.pio(0, 0, 0, 0))
                
                metrics = ProcessMetrics(
                    pid=pid,
                    name=process_info.get('name', 'unknown'),
                    cpu_percent=process_info.get('cpu_percent', 0.0),
                    memory_percent=process_info.get('memory_percent', 0.0),
                    memory_rss_mb=memory_info.rss / (1024 * 1024) if memory_info else 0.0,
                    memory_vms_mb=memory_info.vms / (1024 * 1024) if memory_info else 0.0,
                    num_threads=process_info.get('num_threads', 0),
                    num_fds=process_info.get('num_fds', 0),
                    io_read_mb=io_counters.read_bytes / (1024 * 1024) if io_counters else 0.0,
                    io_write_mb=io_counters.write_bytes / (1024 * 1024) if io_counters else 0.0,
                    create_time=datetime.fromtimestamp(process_info.get('create_time', time.time()))
                )
                
                self.process_metrics[pid] = metrics
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists or access denied
                self.monitored_processes.discard(pid)
            except Exception as e:
                print(f"Error capturing metrics for process {pid}: {e}")
    
    def _generate_metrics(self) -> PerformanceMetrics:
        """Generate comprehensive performance metrics from collected data.
        
        Returns:
            PerformanceMetrics object
        """
        if not self.start_time or not self.end_time:
            raise ValueError("Monitoring was not properly started/stopped")
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate resource usage statistics
        snapshots = list(self.resource_snapshots)
        
        if snapshots:
            cpu_values = [s.cpu_percent for s in snapshots]
            memory_values = [s.memory_used_mb for s in snapshots]
            
            peak_cpu = max(cpu_values)
            avg_cpu = sum(cpu_values) / len(cpu_values)
            peak_memory = max(memory_values)
            avg_memory = sum(memory_values) / len(memory_values)
            
            # Total I/O (from last snapshot)
            last_snapshot = snapshots[-1]
            total_disk_read = last_snapshot.disk_io_read_mb
            total_disk_write = last_snapshot.disk_io_write_mb
            total_network_sent = last_snapshot.network_io_sent_mb
            total_network_recv = last_snapshot.network_io_recv_mb
        else:
            peak_cpu = avg_cpu = 0.0
            peak_memory = avg_memory = 0.0
            total_disk_read = total_disk_write = 0.0
            total_network_sent = total_network_recv = 0.0
        
        # Calculate performance score (0-100)
        performance_score = self._calculate_performance_score(
            avg_cpu, peak_memory, duration
        )
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(snapshots)
        
        # Get environment info
        environment_info = self._get_environment_info()
        
        # Sample snapshots for storage (keep every Nth snapshot to reduce size)
        sample_rate = max(1, len(snapshots) // 100)  # Keep ~100 samples max
        sampled_snapshots = snapshots[::sample_rate]
        
        return PerformanceMetrics(
            test_id=getattr(self, 'test_id', 'unknown'),
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=duration,
            peak_cpu_percent=peak_cpu,
            avg_cpu_percent=avg_cpu,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            total_disk_read_mb=total_disk_read,
            total_disk_write_mb=total_disk_write,
            total_network_sent_mb=total_network_sent,
            total_network_recv_mb=total_network_recv,
            process_metrics=list(self.process_metrics.values()),
            resource_snapshots=sampled_snapshots,
            performance_score=performance_score,
            bottlenecks=bottlenecks,
            **environment_info
        )
    
    def _calculate_performance_score(self, avg_cpu: float, peak_memory_mb: float, duration: float) -> float:
        """Calculate a performance score (0-100) based on resource usage.
        
        Args:
            avg_cpu: Average CPU usage percentage
            peak_memory_mb: Peak memory usage in MB
            duration: Test duration in seconds
            
        Returns:
            Performance score (higher is better)
        """
        # Base score starts at 100
        score = 100.0
        
        # Penalize high CPU usage
        if avg_cpu > 80:
            score -= (avg_cpu - 80) * 2
        elif avg_cpu > 50:
            score -= (avg_cpu - 50) * 0.5
        
        # Penalize high memory usage (relative to system memory)
        try:
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
            memory_ratio = peak_memory_mb / total_memory_mb
            
            if memory_ratio > 0.8:
                score -= (memory_ratio - 0.8) * 100
            elif memory_ratio > 0.5:
                score -= (memory_ratio - 0.5) * 50
        except:
            pass
        
        # Penalize very long execution times (relative penalty)
        if duration > 300:  # 5 minutes
            score -= min(20, (duration - 300) / 60)  # -1 point per minute over 5
        
        return max(0.0, min(100.0, score))
    
    def _identify_bottlenecks(self, snapshots: List[ResourceSnapshot]) -> List[str]:
        """Identify performance bottlenecks from resource snapshots.
        
        Args:
            snapshots: List of resource snapshots
            
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        if not snapshots:
            return bottlenecks
        
        # Analyze CPU usage
        cpu_values = [s.cpu_percent for s in snapshots]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        
        if avg_cpu > 80:
            bottlenecks.append("high_cpu_usage")
        if max_cpu > 95:
            bottlenecks.append("cpu_saturation")
        
        # Analyze memory usage
        memory_values = [s.memory_percent for s in snapshots]
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        
        if avg_memory > 80:
            bottlenecks.append("high_memory_usage")
        if max_memory > 95:
            bottlenecks.append("memory_pressure")
        
        # Analyze I/O patterns
        if snapshots:
            last_snapshot = snapshots[-1]
            
            # High disk I/O
            total_disk_io = last_snapshot.disk_io_read_mb + last_snapshot.disk_io_write_mb
            if total_disk_io > 1000:  # > 1GB
                bottlenecks.append("high_disk_io")
            
            # High network I/O
            total_network_io = last_snapshot.network_io_sent_mb + last_snapshot.network_io_recv_mb
            if total_network_io > 500:  # > 500MB
                bottlenecks.append("high_network_io")
        
        # Analyze load average (Unix-like systems)
        if snapshots and snapshots[0].load_average:
            try:
                cpu_count = psutil.cpu_count()
                avg_load = sum(s.load_average[0] for s in snapshots if s.load_average) / len(snapshots)
                
                if avg_load > cpu_count * 2:
                    bottlenecks.append("system_overload")
                elif avg_load > cpu_count:
                    bottlenecks.append("high_system_load")
            except:
                pass
        
        return bottlenecks
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for metrics.
        
        Returns:
            Dictionary with environment info
        """
        try:
            return {
                "environment_id": "local",
                "architecture": os.uname().machine,
                "memory_total_mb": psutil.virtual_memory().total / (1024 * 1024),
                "cpu_count": psutil.cpu_count()
            }
        except:
            return {
                "environment_id": "unknown",
                "architecture": "unknown",
                "memory_total_mb": 0.0,
                "cpu_count": 0
            }
    
    def get_metrics(self, test_id: str) -> Optional[PerformanceMetrics]:
        """Get stored metrics for a test.
        
        Args:
            test_id: Test ID to get metrics for
            
        Returns:
            PerformanceMetrics object, or None if not found
        """
        return self.metrics_storage.get(test_id)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all stored metrics.
        
        Returns:
            Dictionary mapping test IDs to PerformanceMetrics
        """
        return self.metrics_storage.copy()
    
    def save_metrics_to_file(self, test_id: str, file_path: str) -> bool:
        """Save metrics to a JSON file.
        
        Args:
            test_id: Test ID to save metrics for
            file_path: Path to save file
            
        Returns:
            True if successful
        """
        metrics = self.get_metrics(test_id)
        if not metrics:
            return False
        
        try:
            with open(file_path, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metrics to {file_path}: {e}")
            return False
    
    def load_metrics_from_file(self, file_path: str) -> Optional[PerformanceMetrics]:
        """Load metrics from a JSON file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            PerformanceMetrics object, or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            metrics = PerformanceMetrics.from_dict(data)
            self.metrics_storage[metrics.test_id] = metrics
            return metrics
            
        except Exception as e:
            print(f"Error loading metrics from {file_path}: {e}")
            return None


# Global performance monitor instance
_monitor_instance: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.
    
    Returns:
        The global PerformanceMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance


def monitor_test_performance(test_id: str, process_ids: Optional[List[int]] = None) -> PerformanceMonitor:
    """Start monitoring performance for a test.
    
    Args:
        test_id: ID of the test to monitor
        process_ids: Optional list of process IDs to monitor
        
    Returns:
        PerformanceMonitor instance (for context manager usage)
    """
    monitor = get_performance_monitor()
    monitor.start_monitoring(test_id, process_ids)
    return monitor


class PerformanceContext:
    """Context manager for performance monitoring."""
    
    def __init__(self, test_id: str, process_ids: Optional[List[int]] = None):
        """Initialize performance monitoring context.
        
        Args:
            test_id: ID of the test to monitor
            process_ids: Optional list of process IDs to monitor
        """
        self.test_id = test_id
        self.process_ids = process_ids
        self.monitor = get_performance_monitor()
        self.metrics = None
    
    def __enter__(self) -> 'PerformanceContext':
        """Start performance monitoring."""
        self.monitor.start_monitoring(self.test_id, self.process_ids)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop performance monitoring and collect metrics."""
        self.metrics = self.monitor.stop_monitoring()
    
    def get_metrics(self) -> Optional[PerformanceMetrics]:
        """Get collected performance metrics.
        
        Returns:
            PerformanceMetrics object, or None if monitoring not completed
        """
        return self.metrics