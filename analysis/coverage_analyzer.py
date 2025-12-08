"""Coverage analyzer for collecting and analyzing code coverage data.

This module provides functionality for:
- Integrating with gcov/lcov for coverage collection
- Parsing and merging coverage data
- Calculating line, branch, and function coverage
- Storing and retrieving coverage data
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
import json

from ai_generator.models import CoverageData
from config.settings import get_settings


@dataclass
class FileCoverage:
    """Coverage data for a single file."""
    file_path: str
    lines_found: int = 0
    lines_hit: int = 0
    branches_found: int = 0
    branches_hit: int = 0
    functions_found: int = 0
    functions_hit: int = 0
    line_details: Dict[int, int] = field(default_factory=dict)  # line_num -> hit_count
    branch_details: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)  # line_num -> [(branch_id, hit_count)]
    function_details: Dict[str, int] = field(default_factory=dict)  # func_name -> hit_count
    
    @property
    def line_coverage_percent(self) -> float:
        """Calculate line coverage percentage."""
        if self.lines_found == 0:
            return 0.0
        return self.lines_hit / self.lines_found
    
    @property
    def branch_coverage_percent(self) -> float:
        """Calculate branch coverage percentage."""
        if self.branches_found == 0:
            return 0.0
        return self.branches_hit / self.branches_found
    
    @property
    def function_coverage_percent(self) -> float:
        """Calculate function coverage percentage."""
        if self.functions_found == 0:
            return 0.0
        return self.functions_hit / self.functions_found


class LcovParser:
    """Parser for lcov trace files."""
    
    def parse_lcov_file(self, lcov_path: str) -> Dict[str, FileCoverage]:
        """Parse an lcov trace file.
        
        Args:
            lcov_path: Path to lcov trace file
            
        Returns:
            Dictionary mapping file paths to FileCoverage objects
        """
        if not os.path.exists(lcov_path):
            raise FileNotFoundError(f"Lcov file not found: {lcov_path}")
        
        file_coverages = {}
        current_file = None
        current_coverage = None
        
        with open(lcov_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('SF:'):
                    # Source file
                    file_path = line[3:]
                    current_file = file_path
                    current_coverage = FileCoverage(file_path=file_path)
                
                elif line.startswith('FN:'):
                    # Function definition: FN:<line>,<function_name>
                    if current_coverage:
                        parts = line[3:].split(',', 1)
                        if len(parts) == 2:
                            func_name = parts[1]
                            current_coverage.function_details[func_name] = 0
                            current_coverage.functions_found += 1
                
                elif line.startswith('FNDA:'):
                    # Function data: FNDA:<hit_count>,<function_name>
                    if current_coverage:
                        parts = line[5:].split(',', 1)
                        if len(parts) == 2:
                            hit_count = int(parts[0])
                            func_name = parts[1]
                            current_coverage.function_details[func_name] = hit_count
                            if hit_count > 0:
                                current_coverage.functions_hit += 1
                
                elif line.startswith('DA:'):
                    # Line data: DA:<line_num>,<hit_count>
                    if current_coverage:
                        parts = line[3:].split(',')
                        if len(parts) >= 2:
                            line_num = int(parts[0])
                            hit_count = int(parts[1])
                            current_coverage.line_details[line_num] = hit_count
                            current_coverage.lines_found += 1
                            if hit_count > 0:
                                current_coverage.lines_hit += 1
                
                elif line.startswith('BRDA:'):
                    # Branch data: BRDA:<line_num>,<block_num>,<branch_num>,<hit_count>
                    if current_coverage:
                        parts = line[5:].split(',')
                        if len(parts) >= 4:
                            line_num = int(parts[0])
                            branch_id = int(parts[2])
                            hit_count_str = parts[3]
                            
                            # Handle '-' for branches not taken
                            hit_count = 0 if hit_count_str == '-' else int(hit_count_str)
                            
                            if line_num not in current_coverage.branch_details:
                                current_coverage.branch_details[line_num] = []
                            
                            current_coverage.branch_details[line_num].append((branch_id, hit_count))
                            current_coverage.branches_found += 1
                            if hit_count > 0:
                                current_coverage.branches_hit += 1
                
                elif line == 'end_of_record':
                    # End of file record
                    if current_file and current_coverage:
                        file_coverages[current_file] = current_coverage
                    current_file = None
                    current_coverage = None
        
        return file_coverages


class CoverageCollector:
    """Collector for gathering coverage data from test executions."""
    
    def __init__(self):
        self.settings = get_settings()
        self.gcov_path = self.settings.coverage.gcov_path
        self.lcov_path = self.settings.coverage.lcov_path
        self.parser = LcovParser()
    
    def collect_coverage(self, build_dir: str, output_file: str) -> str:
        """Collect coverage data using lcov.
        
        Args:
            build_dir: Directory containing .gcda files
            output_file: Output path for lcov trace file
            
        Returns:
            Path to generated lcov trace file
        """
        if not os.path.exists(build_dir):
            raise FileNotFoundError(f"Build directory not found: {build_dir}")
        
        # Run lcov to collect coverage
        cmd = [
            self.lcov_path,
            '--capture',
            '--directory', build_dir,
            '--output-file', output_file,
            '--rc', 'lcov_branch_coverage=1'  # Enable branch coverage
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )
            
            if not os.path.exists(output_file):
                raise RuntimeError(f"Coverage file not created: {output_file}")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"lcov failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("lcov timed out after 300 seconds")
    
    def reset_coverage(self, build_dir: str) -> None:
        """Reset coverage counters.
        
        Args:
            build_dir: Directory containing .gcda files
        """
        if not os.path.exists(build_dir):
            return
        
        # Run lcov to zero counters
        cmd = [
            self.lcov_path,
            '--zerocounters',
            '--directory', build_dir
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Non-critical, just log and continue
            pass


class CoverageMerger:
    """Merger for combining multiple coverage data sets."""
    
    def __init__(self):
        self.settings = get_settings()
        self.lcov_path = self.settings.coverage.lcov_path
        self.parser = LcovParser()
    
    def merge_lcov_files(self, input_files: List[str], output_file: str) -> str:
        """Merge multiple lcov trace files.
        
        Args:
            input_files: List of lcov trace file paths
            output_file: Output path for merged trace file
            
        Returns:
            Path to merged lcov trace file
        """
        if not input_files:
            raise ValueError("No input files provided")
        
        # Filter out non-existent files
        existing_files = [f for f in input_files if os.path.exists(f)]
        if not existing_files:
            raise FileNotFoundError("None of the input files exist")
        
        # Build lcov command
        cmd = [self.lcov_path]
        for input_file in existing_files:
            cmd.extend(['--add-tracefile', input_file])
        cmd.extend(['--output-file', output_file])
        cmd.extend(['--rc', 'lcov_branch_coverage=1'])
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
            
            if not os.path.exists(output_file):
                raise RuntimeError(f"Merged coverage file not created: {output_file}")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"lcov merge failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("lcov merge timed out after 300 seconds")
    
    def merge_coverage_data(self, coverage_list: List[FileCoverage]) -> FileCoverage:
        """Merge multiple FileCoverage objects for the same file.
        
        Args:
            coverage_list: List of FileCoverage objects for the same file
            
        Returns:
            Merged FileCoverage object
        """
        if not coverage_list:
            raise ValueError("Empty coverage list")
        
        if len(coverage_list) == 1:
            return coverage_list[0]
        
        # Use first file path
        merged = FileCoverage(file_path=coverage_list[0].file_path)
        
        # Merge line coverage
        all_lines = set()
        for cov in coverage_list:
            all_lines.update(cov.line_details.keys())
        
        for line_num in all_lines:
            hit_count = sum(cov.line_details.get(line_num, 0) for cov in coverage_list)
            merged.line_details[line_num] = hit_count
            merged.lines_found += 1
            if hit_count > 0:
                merged.lines_hit += 1
        
        # Merge function coverage
        all_functions = set()
        for cov in coverage_list:
            all_functions.update(cov.function_details.keys())
        
        for func_name in all_functions:
            hit_count = sum(cov.function_details.get(func_name, 0) for cov in coverage_list)
            merged.function_details[func_name] = hit_count
            merged.functions_found += 1
            if hit_count > 0:
                merged.functions_hit += 1
        
        # Merge branch coverage
        all_branch_lines = set()
        for cov in coverage_list:
            all_branch_lines.update(cov.branch_details.keys())
        
        for line_num in all_branch_lines:
            # Collect all branches for this line
            branch_map = {}
            for cov in coverage_list:
                for branch_id, hit_count in cov.branch_details.get(line_num, []):
                    if branch_id not in branch_map:
                        branch_map[branch_id] = 0
                    branch_map[branch_id] += hit_count
            
            merged.branch_details[line_num] = [(bid, count) for bid, count in branch_map.items()]
            merged.branches_found += len(branch_map)
            merged.branches_hit += sum(1 for count in branch_map.values() if count > 0)
        
        return merged


class CoverageAnalyzer:
    """Main coverage analyzer for collecting, parsing, and analyzing coverage data."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize coverage analyzer.
        
        Args:
            storage_dir: Directory for storing coverage data (default: ./coverage_data)
        """
        self.settings = get_settings()
        self.collector = CoverageCollector()
        self.merger = CoverageMerger()
        self.parser = LcovParser()
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./coverage_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_coverage(self, build_dir: str, test_id: str) -> CoverageData:
        """Collect coverage data from a test execution.
        
        Args:
            build_dir: Directory containing .gcda files
            test_id: Unique identifier for the test
            
        Returns:
            CoverageData object with aggregated coverage metrics
        """
        # Generate output file path
        output_file = str(self.storage_dir / f"{test_id}.info")
        
        # Collect coverage using lcov
        lcov_file = self.collector.collect_coverage(build_dir, output_file)
        
        # Parse the lcov file
        file_coverages = self.parser.parse_lcov_file(lcov_file)
        
        # Aggregate coverage across all files
        return self._aggregate_coverage(file_coverages, test_id)
    
    def merge_coverage(self, test_ids: List[str], merged_id: str) -> CoverageData:
        """Merge coverage data from multiple tests.
        
        Args:
            test_ids: List of test IDs to merge
            merged_id: ID for the merged coverage data
            
        Returns:
            Merged CoverageData object
        """
        # Get lcov files for all test IDs
        input_files = [str(self.storage_dir / f"{tid}.info") for tid in test_ids]
        output_file = str(self.storage_dir / f"{merged_id}.info")
        
        # Merge using lcov
        merged_file = self.merger.merge_lcov_files(input_files, output_file)
        
        # Parse merged file
        file_coverages = self.parser.parse_lcov_file(merged_file)
        
        # Aggregate coverage
        return self._aggregate_coverage(file_coverages, merged_id)
    
    def _aggregate_coverage(self, file_coverages: Dict[str, FileCoverage], coverage_id: str) -> CoverageData:
        """Aggregate coverage data across all files.
        
        Args:
            file_coverages: Dictionary of FileCoverage objects
            coverage_id: Identifier for this coverage data
            
        Returns:
            Aggregated CoverageData object
        """
        total_lines_found = 0
        total_lines_hit = 0
        total_branches_found = 0
        total_branches_hit = 0
        total_functions_found = 0
        total_functions_hit = 0
        
        covered_lines = []
        uncovered_lines = []
        covered_branches = []
        uncovered_branches = []
        
        for file_path, file_cov in file_coverages.items():
            total_lines_found += file_cov.lines_found
            total_lines_hit += file_cov.lines_hit
            total_branches_found += file_cov.branches_found
            total_branches_hit += file_cov.branches_hit
            total_functions_found += file_cov.functions_found
            total_functions_hit += file_cov.functions_hit
            
            # Track covered/uncovered lines
            for line_num, hit_count in file_cov.line_details.items():
                line_ref = f"{file_path}:{line_num}"
                if hit_count > 0:
                    covered_lines.append(line_ref)
                else:
                    uncovered_lines.append(line_ref)
            
            # Track covered/uncovered branches
            for line_num, branches in file_cov.branch_details.items():
                for branch_id, hit_count in branches:
                    branch_ref = f"{file_path}:{line_num}:{branch_id}"
                    if hit_count > 0:
                        covered_branches.append(branch_ref)
                    else:
                        uncovered_branches.append(branch_ref)
        
        # Calculate coverage percentages
        line_coverage = total_lines_hit / total_lines_found if total_lines_found > 0 else 0.0
        branch_coverage = total_branches_hit / total_branches_found if total_branches_found > 0 else 0.0
        function_coverage = total_functions_hit / total_functions_found if total_functions_found > 0 else 0.0
        
        return CoverageData(
            line_coverage=line_coverage,
            branch_coverage=branch_coverage,
            function_coverage=function_coverage,
            covered_lines=covered_lines,
            uncovered_lines=uncovered_lines,
            covered_branches=covered_branches,
            uncovered_branches=uncovered_branches,
            metadata={
                'coverage_id': coverage_id,
                'total_lines_found': total_lines_found,
                'total_lines_hit': total_lines_hit,
                'total_branches_found': total_branches_found,
                'total_branches_hit': total_branches_hit,
                'total_functions_found': total_functions_found,
                'total_functions_hit': total_functions_hit,
                'num_files': len(file_coverages)
            }
        )
    
    def store_coverage(self, coverage_data: CoverageData, coverage_id: str) -> str:
        """Store coverage data to disk.
        
        Args:
            coverage_data: CoverageData object to store
            coverage_id: Unique identifier for the coverage data
            
        Returns:
            Path to stored coverage file
        """
        output_file = self.storage_dir / f"{coverage_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(coverage_data.to_dict(), f, indent=2)
        
        return str(output_file)
    
    def retrieve_coverage(self, coverage_id: str) -> Optional[CoverageData]:
        """Retrieve stored coverage data.
        
        Args:
            coverage_id: Unique identifier for the coverage data
            
        Returns:
            CoverageData object or None if not found
        """
        coverage_file = self.storage_dir / f"{coverage_id}.json"
        
        if not coverage_file.exists():
            return None
        
        with open(coverage_file, 'r') as f:
            data = json.load(f)
        
        return CoverageData.from_dict(data)
    
    def identify_gaps(self, coverage_data: CoverageData) -> List[str]:
        """Identify code paths that have not been tested.
        
        Args:
            coverage_data: CoverageData object to analyze
            
        Returns:
            List of uncovered code paths (lines and branches)
        """
        gaps = []
        
        # Add uncovered lines
        gaps.extend(coverage_data.uncovered_lines)
        
        # Add uncovered branches
        gaps.extend(coverage_data.uncovered_branches)
        
        return gaps
    
    def compare_coverage(self, baseline_id: str, current_id: str) -> Dict[str, float]:
        """Compare two coverage data sets.
        
        Args:
            baseline_id: ID of baseline coverage
            current_id: ID of current coverage
            
        Returns:
            Dictionary with coverage differences
        """
        baseline = self.retrieve_coverage(baseline_id)
        current = self.retrieve_coverage(current_id)
        
        if not baseline or not current:
            raise ValueError("Coverage data not found")
        
        return {
            'line_coverage_diff': current.line_coverage - baseline.line_coverage,
            'branch_coverage_diff': current.branch_coverage - baseline.branch_coverage,
            'function_coverage_diff': current.function_coverage - baseline.function_coverage,
            'baseline_line_coverage': baseline.line_coverage,
            'current_line_coverage': current.line_coverage,
            'baseline_branch_coverage': baseline.branch_coverage,
            'current_branch_coverage': current.branch_coverage,
            'baseline_function_coverage': baseline.function_coverage,
            'current_function_coverage': current.function_coverage
        }
