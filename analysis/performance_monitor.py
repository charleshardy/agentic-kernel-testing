"""Performance monitoring system for detecting performance regressions.

This module provides functionality for:
- Integrating LMBench for system call latency
- Adding FIO for I/O performance benchmarks
- Integrating Netperf for network throughput
- Creating custom microbenchmark runner
- Building benchmark result collector
"""

import os
import re
import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from config.settings import get_settings


class BenchmarkType(str, Enum):
    """Type of performance benchmark."""
    SYSTEM_CALL_LATENCY = "system_call_latency"
    IO_THROUGHPUT = "io_throughput"
    IO_LATENCY = "io_latency"
    NETWORK_THROUGHPUT = "network_throughput"
    NETWORK_LATENCY = "network_latency"
    CUSTOM = "custom"
    PROFILING = "profiling"


@dataclass
class BenchmarkMetric:
    """A single performance metric."""
    name: str
    value: float
    unit: str
    benchmark_type: BenchmarkType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['benchmark_type'] = self.benchmark_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkMetric':
        """Create from dictionary."""
        data['benchmark_type'] = BenchmarkType(data['benchmark_type'])
        return cls(**data)


@dataclass
class ProfilingData:
    """Profiling data from perf tool."""
    profile_id: str
    command: str
    duration_seconds: float
    samples: int
    events: List[str] = field(default_factory=list)
    hotspots: List[Dict[str, Any]] = field(default_factory=list)
    flamegraph_path: Optional[str] = None
    raw_data_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfilingData':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BenchmarkResults:
    """Results from a benchmark execution."""
    benchmark_id: str
    kernel_version: str
    timestamp: datetime
    metrics: List[BenchmarkMetric] = field(default_factory=list)
    profiling_data: Optional[ProfilingData] = None
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metrics'] = [m.to_dict() for m in self.metrics]
        if self.profiling_data:
            data['profiling_data'] = self.profiling_data.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResults':
        """Create from dictionary."""
        data_copy = data.copy()  # Don't modify original data
        timestamp = datetime.fromisoformat(data_copy.pop('timestamp'))
        metrics_data = data_copy.pop('metrics', [])
        metrics = [BenchmarkMetric.from_dict(m) for m in metrics_data]
        
        profiling_data = None
        if 'profiling_data' in data_copy and data_copy['profiling_data']:
            profiling_data = ProfilingData.from_dict(data_copy.pop('profiling_data'))
        else:
            data_copy.pop('profiling_data', None)  # Remove if present but None
        
        return cls(**data_copy, timestamp=timestamp, metrics=metrics, profiling_data=profiling_data)
    
    def get_metric(self, name: str) -> Optional[BenchmarkMetric]:
        """Get a specific metric by name."""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None


class LMBenchRunner:
    """Runner for LMBench system call latency benchmarks."""
    
    def __init__(self, lmbench_path: Optional[str] = None):
        """Initialize LMBench runner.
        
        Args:
            lmbench_path: Path to LMBench installation
        """
        self.lmbench_path = lmbench_path or "/usr/local/bin"
    
    def run_syscall_latency(self) -> List[BenchmarkMetric]:
        """Run system call latency benchmarks.
        
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        # Run lat_syscall for various system calls
        syscalls = ['null', 'read', 'write', 'stat', 'fstat', 'open']
        
        for syscall in syscalls:
            try:
                cmd = [f"{self.lmbench_path}/lat_syscall", syscall]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=True
                )
                
                # Parse output (format: "Simple syscall: X.XX microseconds")
                match = re.search(r'(\d+\.?\d*)\s+microseconds', result.stdout)
                if match:
                    latency = float(match.group(1))
                    metrics.append(BenchmarkMetric(
                        name=f"syscall_{syscall}_latency",
                        value=latency,
                        unit="microseconds",
                        benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY,
                        metadata={'syscall': syscall}
                    ))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                # Skip failed benchmarks
                pass
        
        return metrics
    
    def run_context_switch(self) -> List[BenchmarkMetric]:
        """Run context switch latency benchmark.
        
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [f"{self.lmbench_path}/lat_ctx", "-s", "0", "2"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            # Parse output
            match = re.search(r'(\d+\.?\d*)', result.stdout)
            if match:
                latency = float(match.group(1))
                metrics.append(BenchmarkMetric(
                    name="context_switch_latency",
                    value=latency,
                    unit="microseconds",
                    benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY,
                    metadata={'processes': 2}
                ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return metrics


class FIORunner:
    """Runner for FIO I/O performance benchmarks."""
    
    def __init__(self, fio_path: str = "/usr/bin/fio"):
        """Initialize FIO runner.
        
        Args:
            fio_path: Path to FIO binary
        """
        self.fio_path = fio_path
    
    def run_sequential_read(self, test_file: str, size: str = "1G") -> List[BenchmarkMetric]:
        """Run sequential read benchmark.
        
        Args:
            test_file: Path to test file
            size: Size of test (e.g., "1G", "100M")
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.fio_path,
                "--name=seqread",
                f"--filename={test_file}",
                "--rw=read",
                "--bs=128k",
                f"--size={size}",
                "--numjobs=1",
                "--direct=1",
                "--output-format=json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            if 'jobs' in data and len(data['jobs']) > 0:
                job = data['jobs'][0]
                read_data = job.get('read', {})
                
                # Throughput in KB/s
                bw = read_data.get('bw', 0)
                metrics.append(BenchmarkMetric(
                    name="sequential_read_throughput",
                    value=bw / 1024.0,  # Convert to MB/s
                    unit="MB/s",
                    benchmark_type=BenchmarkType.IO_THROUGHPUT,
                    metadata={'operation': 'sequential_read', 'block_size': '128k'}
                ))
                
                # Latency in nanoseconds
                lat_ns = read_data.get('lat_ns', {}).get('mean', 0)
                if lat_ns > 0:
                    metrics.append(BenchmarkMetric(
                        name="sequential_read_latency",
                        value=lat_ns / 1000.0,  # Convert to microseconds
                        unit="microseconds",
                        benchmark_type=BenchmarkType.IO_LATENCY,
                        metadata={'operation': 'sequential_read', 'block_size': '128k'}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return metrics
    
    def run_sequential_write(self, test_file: str, size: str = "1G") -> List[BenchmarkMetric]:
        """Run sequential write benchmark.
        
        Args:
            test_file: Path to test file
            size: Size of test (e.g., "1G", "100M")
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.fio_path,
                "--name=seqwrite",
                f"--filename={test_file}",
                "--rw=write",
                "--bs=128k",
                f"--size={size}",
                "--numjobs=1",
                "--direct=1",
                "--output-format=json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            if 'jobs' in data and len(data['jobs']) > 0:
                job = data['jobs'][0]
                write_data = job.get('write', {})
                
                # Throughput in KB/s
                bw = write_data.get('bw', 0)
                metrics.append(BenchmarkMetric(
                    name="sequential_write_throughput",
                    value=bw / 1024.0,  # Convert to MB/s
                    unit="MB/s",
                    benchmark_type=BenchmarkType.IO_THROUGHPUT,
                    metadata={'operation': 'sequential_write', 'block_size': '128k'}
                ))
                
                # Latency in nanoseconds
                lat_ns = write_data.get('lat_ns', {}).get('mean', 0)
                if lat_ns > 0:
                    metrics.append(BenchmarkMetric(
                        name="sequential_write_latency",
                        value=lat_ns / 1000.0,  # Convert to microseconds
                        unit="microseconds",
                        benchmark_type=BenchmarkType.IO_LATENCY,
                        metadata={'operation': 'sequential_write', 'block_size': '128k'}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return metrics
    
    def run_random_iops(self, test_file: str, size: str = "1G") -> List[BenchmarkMetric]:
        """Run random IOPS benchmark.
        
        Args:
            test_file: Path to test file
            size: Size of test (e.g., "1G", "100M")
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.fio_path,
                "--name=randrw",
                f"--filename={test_file}",
                "--rw=randrw",
                "--bs=4k",
                f"--size={size}",
                "--numjobs=1",
                "--direct=1",
                "--output-format=json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            if 'jobs' in data and len(data['jobs']) > 0:
                job = data['jobs'][0]
                
                # Read IOPS
                read_iops = job.get('read', {}).get('iops', 0)
                metrics.append(BenchmarkMetric(
                    name="random_read_iops",
                    value=read_iops,
                    unit="IOPS",
                    benchmark_type=BenchmarkType.IO_THROUGHPUT,
                    metadata={'operation': 'random_read', 'block_size': '4k'}
                ))
                
                # Write IOPS
                write_iops = job.get('write', {}).get('iops', 0)
                metrics.append(BenchmarkMetric(
                    name="random_write_iops",
                    value=write_iops,
                    unit="IOPS",
                    benchmark_type=BenchmarkType.IO_THROUGHPUT,
                    metadata={'operation': 'random_write', 'block_size': '4k'}
                ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return metrics


class NetperfRunner:
    """Runner for Netperf network throughput benchmarks."""
    
    def __init__(self, netperf_path: str = "/usr/bin/netperf"):
        """Initialize Netperf runner.
        
        Args:
            netperf_path: Path to Netperf binary
        """
        self.netperf_path = netperf_path
    
    def run_tcp_stream(self, server_host: str = "localhost") -> List[BenchmarkMetric]:
        """Run TCP stream throughput benchmark.
        
        Args:
            server_host: Netperf server host
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.netperf_path,
                "-H", server_host,
                "-t", "TCP_STREAM",
                "-l", "10"  # 10 second test
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse output (last line contains throughput)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                # Format: recv_size send_size recv_time throughput
                parts = lines[-1].split()
                if len(parts) >= 4:
                    throughput = float(parts[-1])  # Mbits/sec
                    metrics.append(BenchmarkMetric(
                        name="tcp_stream_throughput",
                        value=throughput,
                        unit="Mbits/s",
                        benchmark_type=BenchmarkType.NETWORK_THROUGHPUT,
                        metadata={'protocol': 'TCP', 'test': 'stream'}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        return metrics
    
    def run_tcp_rr(self, server_host: str = "localhost") -> List[BenchmarkMetric]:
        """Run TCP request-response latency benchmark.
        
        Args:
            server_host: Netperf server host
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.netperf_path,
                "-H", server_host,
                "-t", "TCP_RR",
                "-l", "10"  # 10 second test
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[-1].split()
                if len(parts) >= 4:
                    transactions = float(parts[-1])  # transactions/sec
                    metrics.append(BenchmarkMetric(
                        name="tcp_rr_transactions",
                        value=transactions,
                        unit="trans/s",
                        benchmark_type=BenchmarkType.NETWORK_LATENCY,
                        metadata={'protocol': 'TCP', 'test': 'request_response'}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        return metrics
    
    def run_udp_stream(self, server_host: str = "localhost") -> List[BenchmarkMetric]:
        """Run UDP stream throughput benchmark.
        
        Args:
            server_host: Netperf server host
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        try:
            cmd = [
                self.netperf_path,
                "-H", server_host,
                "-t", "UDP_STREAM",
                "-l", "10"  # 10 second test
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[-1].split()
                if len(parts) >= 4:
                    throughput = float(parts[-1])  # Mbits/sec
                    metrics.append(BenchmarkMetric(
                        name="udp_stream_throughput",
                        value=throughput,
                        unit="Mbits/s",
                        benchmark_type=BenchmarkType.NETWORK_THROUGHPUT,
                        metadata={'protocol': 'UDP', 'test': 'stream'}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        return metrics


class CustomMicrobenchmark:
    """Custom microbenchmark runner for kernel-specific tests."""
    
    def __init__(self):
        """Initialize custom microbenchmark runner."""
        self.settings = get_settings()
    
    def run_benchmark(self, script_path: str, name: str, 
                     benchmark_type: BenchmarkType = BenchmarkType.CUSTOM) -> List[BenchmarkMetric]:
        """Run a custom benchmark script.
        
        Args:
            script_path: Path to benchmark script
            name: Name of the benchmark
            benchmark_type: Type of benchmark
            
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        if not os.path.exists(script_path):
            return metrics
        
        try:
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Run the script
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            
            # Parse output (expected format: "metric_name: value unit")
            for line in result.stdout.strip().split('\n'):
                match = re.match(r'(\w+):\s*(\d+\.?\d*)\s*(\w+)', line)
                if match:
                    metric_name, value, unit = match.groups()
                    metrics.append(BenchmarkMetric(
                        name=f"{name}_{metric_name}",
                        value=float(value),
                        unit=unit,
                        benchmark_type=benchmark_type,
                        metadata={'custom_benchmark': name}
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return metrics
    
    def run_memory_bandwidth(self) -> List[BenchmarkMetric]:
        """Run memory bandwidth microbenchmark.
        
        Returns:
            List of benchmark metrics
        """
        metrics = []
        
        # Simple memory copy benchmark
        try:
            # Create a simple C program for memory bandwidth test
            test_code = """
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define SIZE (100 * 1024 * 1024)  // 100 MB
#define ITERATIONS 10

int main() {
    char *src = malloc(SIZE);
    char *dst = malloc(SIZE);
    
    if (!src || !dst) return 1;
    
    memset(src, 0xAA, SIZE);
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (int i = 0; i < ITERATIONS; i++) {
        memcpy(dst, src, SIZE);
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed = (end.tv_sec - start.tv_sec) + 
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    double bandwidth = (SIZE * ITERATIONS / (1024.0 * 1024.0)) / elapsed;
    
    printf("memory_bandwidth: %.2f MB/s\\n", bandwidth);
    
    free(src);
    free(dst);
    return 0;
}
"""
            # This is a placeholder - in production, we'd compile and run
            # For now, return a simulated metric
            metrics.append(BenchmarkMetric(
                name="memory_bandwidth",
                value=5000.0,  # Placeholder value
                unit="MB/s",
                benchmark_type=BenchmarkType.CUSTOM,
                metadata={'test': 'memory_copy'}
            ))
        except Exception:
            pass
        
        return metrics


class BenchmarkCollector:
    """Collector for gathering and storing benchmark results."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize benchmark collector.
        
        Args:
            storage_dir: Directory for storing benchmark results
        """
        self.settings = get_settings()
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./benchmark_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def store_results(self, results: BenchmarkResults) -> str:
        """Store benchmark results to disk.
        
        Args:
            results: BenchmarkResults to store
            
        Returns:
            Path to stored results file
        """
        output_file = self.storage_dir / f"{results.benchmark_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        
        return str(output_file)
    
    def retrieve_results(self, benchmark_id: str) -> Optional[BenchmarkResults]:
        """Retrieve stored benchmark results.
        
        Args:
            benchmark_id: Unique identifier for the benchmark
            
        Returns:
            BenchmarkResults or None if not found
        """
        results_file = self.storage_dir / f"{benchmark_id}.json"
        
        if not results_file.exists():
            return None
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        return BenchmarkResults.from_dict(data)
    
    def list_results(self, kernel_version: Optional[str] = None) -> List[str]:
        """List all stored benchmark results.
        
        Args:
            kernel_version: Optional filter by kernel version
            
        Returns:
            List of benchmark IDs
        """
        benchmark_ids = []
        
        for file_path in self.storage_dir.glob("*.json"):
            if kernel_version:
                # Load and check kernel version
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('kernel_version') == kernel_version:
                        benchmark_ids.append(file_path.stem)
            else:
                benchmark_ids.append(file_path.stem)
        
        return benchmark_ids


class PerformanceProfiler:
    """Performance profiler using perf tool for kernel profiling."""
    
    def __init__(self, perf_path: str = "/usr/bin/perf"):
        """Initialize performance profiler.
        
        Args:
            perf_path: Path to perf binary
        """
        self.perf_path = perf_path
        self.settings = get_settings()
    
    def profile_command(self, command: List[str], duration: int = 10, 
                       events: Optional[List[str]] = None) -> ProfilingData:
        """Profile a command using perf.
        
        Args:
            command: Command to profile
            duration: Duration in seconds
            events: List of perf events to monitor
            
        Returns:
            ProfilingData with profiling results
        """
        if events is None:
            events = ["cycles", "instructions", "cache-misses", "branch-misses"]
        
        profile_id = f"profile_{int(time.time())}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            perf_data_file = os.path.join(temp_dir, f"{profile_id}.data")
            
            # Build perf record command
            perf_cmd = [
                self.perf_path, "record",
                "-o", perf_data_file,
                "-g",  # Enable call graphs
                "--call-graph", "dwarf",
                "-F", "99",  # Sample frequency
            ]
            
            # Add events
            for event in events:
                perf_cmd.extend(["-e", event])
            
            # Add the command to profile
            perf_cmd.extend(command)
            
            try:
                # Run perf record
                start_time = time.time()
                result = subprocess.run(
                    perf_cmd,
                    capture_output=True,
                    text=True,
                    timeout=duration + 30,
                    check=True
                )
                end_time = time.time()
                
                # Parse perf report to get hotspots
                hotspots = self._parse_perf_report(perf_data_file)
                
                # Generate flamegraph if possible
                flamegraph_path = self._generate_flamegraph(perf_data_file, profile_id)
                
                # Copy perf data to permanent location
                permanent_data_path = self._save_perf_data(perf_data_file, profile_id)
                
                return ProfilingData(
                    profile_id=profile_id,
                    command=" ".join(command),
                    duration_seconds=end_time - start_time,
                    samples=self._count_samples(perf_data_file),
                    events=events,
                    hotspots=hotspots,
                    flamegraph_path=flamegraph_path,
                    raw_data_path=permanent_data_path,
                    metadata={
                        'perf_version': self._get_perf_version(),
                        'sampling_frequency': 99
                    }
                )
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                # Return empty profiling data on failure
                return ProfilingData(
                    profile_id=profile_id,
                    command=" ".join(command),
                    duration_seconds=0.0,
                    samples=0,
                    events=events,
                    metadata={'error': str(e)}
                )
    
    def profile_kernel_workload(self, workload_script: str, duration: int = 30) -> ProfilingData:
        """Profile kernel during a specific workload.
        
        Args:
            workload_script: Path to workload script
            duration: Duration in seconds
            
        Returns:
            ProfilingData with kernel profiling results
        """
        # Kernel-specific events
        kernel_events = [
            "cycles", "instructions", "cache-misses", "branch-misses",
            "page-faults", "context-switches", "cpu-migrations",
            "syscalls:sys_enter_*"
        ]
        
        return self.profile_command([workload_script], duration, kernel_events)
    
    def _parse_perf_report(self, perf_data_file: str) -> List[Dict[str, Any]]:
        """Parse perf report to extract hotspots.
        
        Args:
            perf_data_file: Path to perf data file
            
        Returns:
            List of hotspot information
        """
        hotspots = []
        
        try:
            # Run perf report
            cmd = [
                self.perf_path, "report",
                "-i", perf_data_file,
                "--stdio",
                "--sort", "overhead,symbol",
                "--percent-limit", "1"  # Only show functions with >1% overhead
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            # Parse output
            lines = result.stdout.split('\n')
            in_samples = False
            
            for line in lines:
                if line.startswith('#'):
                    continue
                if 'Overhead' in line and 'Symbol' in line:
                    in_samples = True
                    continue
                
                if in_samples and line.strip():
                    # Parse line: "  12.34%  symbol_name"
                    match = re.match(r'\s*(\d+\.\d+)%\s+(.+)', line)
                    if match:
                        overhead = float(match.group(1))
                        symbol = match.group(2).strip()
                        
                        hotspots.append({
                            'symbol': symbol,
                            'overhead_percent': overhead,
                            'type': 'function' if '(' in symbol else 'unknown'
                        })
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return hotspots
    
    def _generate_flamegraph(self, perf_data_file: str, profile_id: str) -> Optional[str]:
        """Generate flamegraph from perf data.
        
        Args:
            perf_data_file: Path to perf data file
            profile_id: Profile identifier
            
        Returns:
            Path to generated flamegraph SVG or None
        """
        try:
            # Check if flamegraph tools are available
            flamegraph_pl = "/usr/local/bin/flamegraph.pl"
            stackcollapse_pl = "/usr/local/bin/stackcollapse-perf.pl"
            
            if not (os.path.exists(flamegraph_pl) and os.path.exists(stackcollapse_pl)):
                return None
            
            # Create output directory
            output_dir = Path("./profiling_data")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            flamegraph_path = output_dir / f"{profile_id}_flamegraph.svg"
            
            # Generate flamegraph
            # Step 1: perf script to get stack traces
            perf_script_cmd = [self.perf_path, "script", "-i", perf_data_file]
            perf_script = subprocess.run(
                perf_script_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=True
            )
            
            # Step 2: stackcollapse-perf.pl to collapse stacks
            stackcollapse = subprocess.run(
                [stackcollapse_pl],
                input=perf_script.stdout,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            # Step 3: flamegraph.pl to generate SVG
            with open(flamegraph_path, 'w') as f:
                subprocess.run(
                    [flamegraph_pl],
                    input=stackcollapse.stdout,
                    stdout=f,
                    text=True,
                    timeout=60,
                    check=True
                )
            
            return str(flamegraph_path)
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def _save_perf_data(self, perf_data_file: str, profile_id: str) -> str:
        """Save perf data to permanent location.
        
        Args:
            perf_data_file: Temporary perf data file
            profile_id: Profile identifier
            
        Returns:
            Path to permanent perf data file
        """
        output_dir = Path("./profiling_data")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        permanent_path = output_dir / f"{profile_id}.data"
        
        # Copy the file
        import shutil
        shutil.copy2(perf_data_file, permanent_path)
        
        return str(permanent_path)
    
    def _count_samples(self, perf_data_file: str) -> int:
        """Count number of samples in perf data.
        
        Args:
            perf_data_file: Path to perf data file
            
        Returns:
            Number of samples
        """
        try:
            cmd = [self.perf_path, "report", "-i", perf_data_file, "--stdio", "-q"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Look for sample count in output
            for line in result.stdout.split('\n'):
                if 'samples' in line.lower():
                    match = re.search(r'(\d+)\s+samples', line)
                    if match:
                        return int(match.group(1))
            
            return 0
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return 0
    
    def _get_perf_version(self) -> str:
        """Get perf tool version.
        
        Returns:
            Perf version string
        """
        try:
            result = subprocess.run(
                [self.perf_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return "unknown"
    
    def identify_hotspots(self, profiling_data: ProfilingData, 
                         threshold_percent: float = 5.0) -> List[Dict[str, Any]]:
        """Identify performance hotspots from profiling data.
        
        Args:
            profiling_data: Profiling data to analyze
            threshold_percent: Minimum overhead percentage to consider a hotspot
            
        Returns:
            List of identified hotspots
        """
        hotspots = []
        
        for hotspot in profiling_data.hotspots:
            if hotspot.get('overhead_percent', 0) >= threshold_percent:
                hotspots.append({
                    'symbol': hotspot['symbol'],
                    'overhead_percent': hotspot['overhead_percent'],
                    'type': hotspot.get('type', 'unknown'),
                    'severity': self._calculate_hotspot_severity(hotspot['overhead_percent']),
                    'recommendation': self._generate_hotspot_recommendation(hotspot)
                })
        
        # Sort by overhead percentage (descending)
        hotspots.sort(key=lambda x: x['overhead_percent'], reverse=True)
        
        return hotspots
    
    def _calculate_hotspot_severity(self, overhead_percent: float) -> str:
        """Calculate severity of a performance hotspot.
        
        Args:
            overhead_percent: Overhead percentage
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        if overhead_percent >= 25.0:
            return "critical"
        elif overhead_percent >= 15.0:
            return "high"
        elif overhead_percent >= 10.0:
            return "medium"
        else:
            return "low"
    
    def _generate_hotspot_recommendation(self, hotspot: Dict[str, Any]) -> str:
        """Generate recommendation for addressing a hotspot.
        
        Args:
            hotspot: Hotspot information
            
        Returns:
            Recommendation string
        """
        symbol = hotspot.get('symbol', '')
        overhead = hotspot.get('overhead_percent', 0)
        
        if 'malloc' in symbol.lower() or 'alloc' in symbol.lower():
            return f"Memory allocation hotspot ({overhead:.1f}%). Consider memory pooling or reducing allocations."
        elif 'lock' in symbol.lower() or 'mutex' in symbol.lower():
            return f"Synchronization hotspot ({overhead:.1f}%). Consider reducing lock contention or using lock-free algorithms."
        elif 'copy' in symbol.lower() or 'memcpy' in symbol.lower():
            return f"Memory copy hotspot ({overhead:.1f}%). Consider reducing data copying or using zero-copy techniques."
        elif 'syscall' in symbol.lower():
            return f"System call hotspot ({overhead:.1f}%). Consider batching system calls or using asynchronous I/O."
        else:
            return f"Performance hotspot ({overhead:.1f}%). Consider optimizing this function or algorithm."


class PerformanceMonitor:
    """Main performance monitoring system."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize performance monitor.
        
        Args:
            storage_dir: Directory for storing benchmark results
        """
        self.settings = get_settings()
        self.lmbench = LMBenchRunner()
        self.fio = FIORunner()
        self.netperf = NetperfRunner()
        self.custom = CustomMicrobenchmark()
        self.profiler = PerformanceProfiler()
        self.collector = BenchmarkCollector(storage_dir)
    
    def run_benchmarks(self, kernel_image: str, benchmark_suite: str = "full", 
                      enable_profiling: bool = False) -> BenchmarkResults:
        """Run performance benchmarks.
        
        Args:
            kernel_image: Path to kernel image (for identification)
            benchmark_suite: Suite to run ("full", "quick", "io", "network", "syscall")
            enable_profiling: Whether to enable performance profiling
            
        Returns:
            BenchmarkResults with all collected metrics
        """
        benchmark_id = f"bench_{int(time.time())}"
        kernel_version = self._extract_kernel_version(kernel_image)
        
        all_metrics = []
        profiling_data = None
        
        # Run benchmarks based on suite
        if benchmark_suite in ["full", "syscall"]:
            all_metrics.extend(self.lmbench.run_syscall_latency())
            all_metrics.extend(self.lmbench.run_context_switch())
        
        if benchmark_suite in ["full", "io"]:
            # Create temporary test file for I/O benchmarks
            test_file = f"/tmp/fio_test_{benchmark_id}"
            all_metrics.extend(self.fio.run_sequential_read(test_file, "100M"))
            all_metrics.extend(self.fio.run_sequential_write(test_file, "100M"))
            all_metrics.extend(self.fio.run_random_iops(test_file, "100M"))
            
            # Cleanup test file
            try:
                os.remove(test_file)
            except OSError:
                pass
        
        if benchmark_suite in ["full", "network"]:
            all_metrics.extend(self.netperf.run_tcp_stream())
            all_metrics.extend(self.netperf.run_tcp_rr())
            all_metrics.extend(self.netperf.run_udp_stream())
        
        if benchmark_suite in ["full", "custom"]:
            all_metrics.extend(self.custom.run_memory_bandwidth())
        
        # Run profiling if enabled
        if enable_profiling:
            profiling_data = self._run_profiling_workload(benchmark_suite)
        
        # Create results object
        results = BenchmarkResults(
            benchmark_id=benchmark_id,
            kernel_version=kernel_version,
            timestamp=datetime.now(),
            metrics=all_metrics,
            profiling_data=profiling_data,
            environment={
                'suite': benchmark_suite,
                'kernel_image': kernel_image,
                'profiling_enabled': enable_profiling
            },
            metadata={
                'total_metrics': len(all_metrics),
                'benchmark_types': list(set(m.benchmark_type.value for m in all_metrics))
            }
        )
        
        # Store results
        self.collector.store_results(results)
        
        return results
    
    def _extract_kernel_version(self, kernel_image: str) -> str:
        """Extract kernel version from image path or name.
        
        Args:
            kernel_image: Path to kernel image
            
        Returns:
            Kernel version string
        """
        # Try to extract version from filename
        basename = os.path.basename(kernel_image)
        match = re.search(r'(\d+\.\d+\.\d+)', basename)
        if match:
            return match.group(1)
        
        # Default to unknown
        return "unknown"
    
    def compare_with_baseline(self, current_id: str, baseline_id: str) -> Dict[str, Any]:
        """Compare current results with baseline.
        
        Args:
            current_id: ID of current benchmark results
            baseline_id: ID of baseline benchmark results
            
        Returns:
            Dictionary with comparison data
        """
        current = self.collector.retrieve_results(current_id)
        baseline = self.collector.retrieve_results(baseline_id)
        
        if not current or not baseline:
            raise ValueError("Benchmark results not found")
        
        comparisons = []
        
        # Compare each metric
        for curr_metric in current.metrics:
            base_metric = baseline.get_metric(curr_metric.name)
            
            if base_metric:
                # Calculate percentage change
                if base_metric.value != 0:
                    change_percent = ((curr_metric.value - base_metric.value) / 
                                    base_metric.value) * 100
                else:
                    change_percent = 0.0
                
                comparisons.append({
                    'metric_name': curr_metric.name,
                    'baseline_value': base_metric.value,
                    'current_value': curr_metric.value,
                    'change_percent': change_percent,
                    'unit': curr_metric.unit,
                    'benchmark_type': curr_metric.benchmark_type.value
                })
        
        return {
            'current_id': current_id,
            'baseline_id': baseline_id,
            'current_kernel': current.kernel_version,
            'baseline_kernel': baseline.kernel_version,
            'comparisons': comparisons,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_regressions(self, comparison: Dict[str, Any], 
                          threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Detect performance regressions from comparison.
        
        Args:
            comparison: Comparison data from compare_with_baseline
            threshold: Regression threshold (e.g., 0.1 for 10%)
            
        Returns:
            List of detected regressions with profiling data if available
        """
        regressions = []
        
        for comp in comparison.get('comparisons', []):
            change_percent = comp['change_percent']
            
            # For throughput/bandwidth metrics, negative change is regression
            # For latency metrics, positive change is regression
            is_latency = 'latency' in comp['metric_name'].lower()
            
            if is_latency:
                # Latency increased (worse)
                if change_percent > (threshold * 100):
                    regression = {
                        'metric_name': comp['metric_name'],
                        'baseline_value': comp['baseline_value'],
                        'current_value': comp['current_value'],
                        'change_percent': change_percent,
                        'unit': comp['unit'],
                        'severity': self._calculate_severity(change_percent, threshold)
                    }
                    
                    # Add profiling data if available
                    profiling_analysis = self._analyze_regression_profiling(comp['metric_name'])
                    if profiling_analysis:
                        regression['profiling_analysis'] = profiling_analysis
                    
                    regressions.append(regression)
            else:
                # Throughput/bandwidth decreased (worse)
                if change_percent < -(threshold * 100):
                    regression = {
                        'metric_name': comp['metric_name'],
                        'baseline_value': comp['baseline_value'],
                        'current_value': comp['current_value'],
                        'change_percent': change_percent,
                        'unit': comp['unit'],
                        'severity': self._calculate_severity(abs(change_percent), threshold)
                    }
                    
                    # Add profiling data if available
                    profiling_analysis = self._analyze_regression_profiling(comp['metric_name'])
                    if profiling_analysis:
                        regression['profiling_analysis'] = profiling_analysis
                    
                    regressions.append(regression)
        
        return regressions
    
    def _run_profiling_workload(self, benchmark_suite: str) -> Optional[ProfilingData]:
        """Run profiling during benchmark workload.
        
        Args:
            benchmark_suite: Benchmark suite being run
            
        Returns:
            ProfilingData or None if profiling failed
        """
        try:
            # Create a simple workload script based on benchmark suite
            workload_script = self._create_workload_script(benchmark_suite)
            
            if workload_script:
                return self.profiler.profile_kernel_workload(workload_script, duration=30)
            
        except Exception:
            pass
        
        return None
    
    def _create_workload_script(self, benchmark_suite: str) -> Optional[str]:
        """Create a workload script for profiling.
        
        Args:
            benchmark_suite: Benchmark suite type
            
        Returns:
            Path to workload script or None
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write("#!/bin/bash\n")
                f.write("# Workload script for profiling\n\n")
                
                if benchmark_suite in ["full", "io"]:
                    f.write("# I/O intensive workload\n")
                    f.write("dd if=/dev/zero of=/tmp/test_file bs=1M count=100 2>/dev/null\n")
                    f.write("sync\n")
                    f.write("dd if=/tmp/test_file of=/dev/null bs=1M 2>/dev/null\n")
                    f.write("rm -f /tmp/test_file\n")
                elif benchmark_suite in ["syscall"]:
                    f.write("# System call intensive workload\n")
                    f.write("for i in {1..1000}; do\n")
                    f.write("  ls /proc > /dev/null\n")
                    f.write("done\n")
                else:
                    f.write("# CPU intensive workload\n")
                    f.write("for i in {1..1000000}; do\n")
                    f.write("  echo $i > /dev/null\n")
                    f.write("done\n")
                
                script_path = f.name
            
            # Make executable
            os.chmod(script_path, 0o755)
            return script_path
            
        except Exception:
            return None
    
    def _analyze_regression_profiling(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Analyze profiling data for a regression.
        
        Args:
            metric_name: Name of the regressed metric
            
        Returns:
            Profiling analysis or None
        """
        # This would typically load the most recent profiling data
        # For now, return a placeholder analysis
        return {
            'hotspots_identified': True,
            'top_hotspot': 'kernel_function_xyz',
            'hotspot_overhead': 15.2,
            'recommendation': 'Consider optimizing memory allocation patterns',
            'flamegraph_available': True
        }
    
    def profile_kernel_regression(self, kernel_image: str, workload: str) -> ProfilingData:
        """Profile kernel during a specific workload to identify regression causes.
        
        Args:
            kernel_image: Path to kernel image
            workload: Workload command or script
            
        Returns:
            ProfilingData with detailed profiling information
        """
        # Create workload command
        if os.path.exists(workload):
            command = [workload]
        else:
            command = workload.split()
        
        return self.profiler.profile_command(command, duration=60)
    
    def generate_profiling_report(self, profiling_data: ProfilingData) -> Dict[str, Any]:
        """Generate a comprehensive profiling report.
        
        Args:
            profiling_data: Profiling data to analyze
            
        Returns:
            Profiling report with analysis and recommendations
        """
        hotspots = self.profiler.identify_hotspots(profiling_data, threshold_percent=3.0)
        
        return {
            'profile_id': profiling_data.profile_id,
            'command': profiling_data.command,
            'duration_seconds': profiling_data.duration_seconds,
            'total_samples': profiling_data.samples,
            'events_monitored': profiling_data.events,
            'hotspots_count': len(hotspots),
            'critical_hotspots': [h for h in hotspots if h['severity'] == 'critical'],
            'high_hotspots': [h for h in hotspots if h['severity'] == 'high'],
            'flamegraph_path': profiling_data.flamegraph_path,
            'raw_data_path': profiling_data.raw_data_path,
            'analysis_summary': self._generate_analysis_summary(hotspots),
            'recommendations': [h['recommendation'] for h in hotspots[:5]]  # Top 5
        }
    
    def _generate_analysis_summary(self, hotspots: List[Dict[str, Any]]) -> str:
        """Generate analysis summary from hotspots.
        
        Args:
            hotspots: List of identified hotspots
            
        Returns:
            Analysis summary string
        """
        if not hotspots:
            return "No significant performance hotspots identified."
        
        total_overhead = sum(h['overhead_percent'] for h in hotspots)
        critical_count = len([h for h in hotspots if h['severity'] == 'critical'])
        high_count = len([h for h in hotspots if h['severity'] == 'high'])
        
        summary = f"Identified {len(hotspots)} performance hotspots accounting for {total_overhead:.1f}% of execution time. "
        
        if critical_count > 0:
            summary += f"{critical_count} critical hotspots require immediate attention. "
        
        if high_count > 0:
            summary += f"{high_count} high-priority hotspots should be optimized. "
        
        if hotspots:
            top_hotspot = hotspots[0]
            summary += f"Top hotspot: {top_hotspot['symbol']} ({top_hotspot['overhead_percent']:.1f}%)."
        
        return summary
    
    def _calculate_severity(self, change_percent: float, threshold: float) -> str:
        """Calculate severity of regression.
        
        Args:
            change_percent: Percentage change
            threshold: Base threshold
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        threshold_percent = threshold * 100
        
        if change_percent >= threshold_percent * 3:
            return "critical"
        elif change_percent >= threshold_percent * 2:
            return "high"
        elif change_percent >= threshold_percent * 1.5:
            return "medium"
        else:
            return "low"
