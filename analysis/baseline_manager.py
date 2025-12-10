"""Performance baseline management system.

This module provides functionality for:
- Creating and storing performance baselines
- Retrieving baselines by kernel version
- Comparing current results with baselines
- Updating baselines with new measurements
- Versioning baselines by kernel version
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric


@dataclass
class PerformanceBaseline:
    """A performance baseline for a specific kernel version."""
    kernel_version: str
    baseline_id: str
    created_at: datetime
    updated_at: datetime
    metrics: List[BenchmarkMetric] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['metrics'] = [m.to_dict() for m in self.metrics]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceBaseline':
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data.pop('created_at'))
        updated_at = datetime.fromisoformat(data.pop('updated_at'))
        metrics_data = data.pop('metrics', [])
        metrics = [BenchmarkMetric.from_dict(m) for m in metrics_data]
        return cls(**data, created_at=created_at, updated_at=updated_at, metrics=metrics)
    
    def get_metric(self, name: str) -> Optional[BenchmarkMetric]:
        """Get a specific metric by name."""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None


class BaselineManager:
    """Manager for performance baselines."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize baseline manager.
        
        Args:
            storage_dir: Directory for storing baselines
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./baseline_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def create_baseline(self, benchmark_results: BenchmarkResults, 
                       baseline_id: Optional[str] = None) -> PerformanceBaseline:
        """Create a new baseline from benchmark results.
        
        Args:
            benchmark_results: BenchmarkResults to use as baseline
            baseline_id: Optional custom baseline ID
            
        Returns:
            Created PerformanceBaseline
        """
        if baseline_id is None:
            baseline_id = f"baseline_{benchmark_results.kernel_version}_{int(datetime.now().timestamp())}"
        
        baseline = PerformanceBaseline(
            kernel_version=benchmark_results.kernel_version,
            baseline_id=baseline_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metrics=benchmark_results.metrics.copy(),
            metadata={
                'source_benchmark_id': benchmark_results.benchmark_id,
                'num_metrics': len(benchmark_results.metrics)
            }
        )
        
        return baseline
    
    def store_baseline(self, baseline: PerformanceBaseline) -> str:
        """Store baseline to disk.
        
        Args:
            baseline: PerformanceBaseline to store
            
        Returns:
            Path to stored baseline file
        """
        # Create version-specific directory
        version_dir = self.storage_dir / baseline.kernel_version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = version_dir / f"{baseline.baseline_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(baseline.to_dict(), f, indent=2)
        
        return str(output_file)
    
    def retrieve_baseline(self, kernel_version: str, 
                         baseline_id: Optional[str] = None) -> Optional[PerformanceBaseline]:
        """Retrieve a baseline for a specific kernel version.
        
        Args:
            kernel_version: Kernel version to retrieve baseline for
            baseline_id: Optional specific baseline ID. If None, returns the latest.
            
        Returns:
            PerformanceBaseline or None if not found
        """
        version_dir = self.storage_dir / kernel_version
        
        if not version_dir.exists():
            return None
        
        if baseline_id:
            # Retrieve specific baseline
            baseline_file = version_dir / f"{baseline_id}.json"
            if not baseline_file.exists():
                return None
            
            with open(baseline_file, 'r') as f:
                data = json.load(f)
            
            return PerformanceBaseline.from_dict(data)
        else:
            # Retrieve latest baseline for this version
            baseline_files = list(version_dir.glob("*.json"))
            if not baseline_files:
                return None
            
            # Sort by modification time, get most recent
            latest_file = max(baseline_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            return PerformanceBaseline.from_dict(data)
    
    def list_baselines(self, kernel_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored baselines.
        
        Args:
            kernel_version: Optional filter by kernel version
            
        Returns:
            List of baseline metadata dictionaries
        """
        baselines = []
        
        if kernel_version:
            # List baselines for specific version
            version_dir = self.storage_dir / kernel_version
            if version_dir.exists():
                for file_path in version_dir.glob("*.json"):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    baselines.append({
                        'kernel_version': data['kernel_version'],
                        'baseline_id': data['baseline_id'],
                        'created_at': data['created_at'],
                        'updated_at': data['updated_at'],
                        'num_metrics': len(data.get('metrics', []))
                    })
        else:
            # List all baselines
            for version_dir in self.storage_dir.iterdir():
                if version_dir.is_dir():
                    for file_path in version_dir.glob("*.json"):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        baselines.append({
                            'kernel_version': data['kernel_version'],
                            'baseline_id': data['baseline_id'],
                            'created_at': data['created_at'],
                            'updated_at': data['updated_at'],
                            'num_metrics': len(data.get('metrics', []))
                        })
        
        return baselines
    
    def update_baseline(self, kernel_version: str, 
                       new_results: BenchmarkResults,
                       baseline_id: Optional[str] = None,
                       merge_strategy: str = "replace") -> PerformanceBaseline:
        """Update an existing baseline with new results.
        
        Args:
            kernel_version: Kernel version of baseline to update
            new_results: New benchmark results to incorporate
            baseline_id: Optional specific baseline ID. If None, updates the latest.
            merge_strategy: How to merge metrics ("replace", "average", "append")
            
        Returns:
            Updated PerformanceBaseline
        """
        # Retrieve existing baseline
        existing = self.retrieve_baseline(kernel_version, baseline_id)
        
        if existing is None:
            # No existing baseline, create new one
            return self.create_baseline(new_results)
        
        # Update based on merge strategy
        if merge_strategy == "replace":
            # Replace all metrics with new ones
            existing.metrics = new_results.metrics.copy()
        elif merge_strategy == "average":
            # Average metrics with same names
            metric_dict = {m.name: m for m in existing.metrics}
            
            for new_metric in new_results.metrics:
                if new_metric.name in metric_dict:
                    # Average the values
                    old_metric = metric_dict[new_metric.name]
                    averaged_value = (old_metric.value + new_metric.value) / 2.0
                    old_metric.value = averaged_value
                else:
                    # Add new metric
                    existing.metrics.append(new_metric)
        elif merge_strategy == "append":
            # Append new metrics (may create duplicates)
            existing.metrics.extend(new_results.metrics)
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")
        
        # Update timestamp
        existing.updated_at = datetime.now()
        
        # Update metadata
        existing.metadata['last_update_source'] = new_results.benchmark_id
        existing.metadata['num_metrics'] = len(existing.metrics)
        
        return existing
    
    def compare_with_baseline(self, current_results: BenchmarkResults,
                             kernel_version: Optional[str] = None,
                             baseline_id: Optional[str] = None) -> Dict[str, Any]:
        """Compare current results with a baseline.
        
        Args:
            current_results: Current benchmark results
            kernel_version: Kernel version for baseline. If None, uses current_results version.
            baseline_id: Optional specific baseline ID
            
        Returns:
            Dictionary with comparison data
        """
        if kernel_version is None:
            kernel_version = current_results.kernel_version
        
        baseline = self.retrieve_baseline(kernel_version, baseline_id)
        
        if baseline is None:
            return {
                'error': 'Baseline not found',
                'kernel_version': kernel_version,
                'baseline_id': baseline_id
            }
        
        comparisons = []
        
        # Compare each metric in current results
        for curr_metric in current_results.metrics:
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
            else:
                # Metric not in baseline
                comparisons.append({
                    'metric_name': curr_metric.name,
                    'baseline_value': None,
                    'current_value': curr_metric.value,
                    'change_percent': None,
                    'unit': curr_metric.unit,
                    'benchmark_type': curr_metric.benchmark_type.value,
                    'note': 'Not in baseline'
                })
        
        return {
            'current_benchmark_id': current_results.benchmark_id,
            'baseline_id': baseline.baseline_id,
            'current_kernel': current_results.kernel_version,
            'baseline_kernel': baseline.kernel_version,
            'baseline_created_at': baseline.created_at.isoformat(),
            'baseline_updated_at': baseline.updated_at.isoformat(),
            'comparisons': comparisons,
            'timestamp': datetime.now().isoformat()
        }
    
    def delete_baseline(self, kernel_version: str, baseline_id: str) -> bool:
        """Delete a specific baseline.
        
        Args:
            kernel_version: Kernel version of baseline
            baseline_id: Baseline ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        version_dir = self.storage_dir / kernel_version
        baseline_file = version_dir / f"{baseline_id}.json"
        
        if baseline_file.exists():
            baseline_file.unlink()
            return True
        
        return False
    
    def get_baseline_versions(self) -> List[str]:
        """Get list of all kernel versions with baselines.
        
        Returns:
            List of kernel version strings
        """
        versions = []
        
        for version_dir in self.storage_dir.iterdir():
            if version_dir.is_dir():
                # Check if directory has any baseline files
                if any(version_dir.glob("*.json")):
                    versions.append(version_dir.name)
        
        return sorted(versions)
