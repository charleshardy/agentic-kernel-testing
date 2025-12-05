"""Compatibility matrix generator for hardware testing results.

This module provides functionality for:
- Creating matrix data structures for hardware configurations
- Populating matrices from test results
- Visualizing and exporting compatibility matrices
- Tracking pass/fail status across hardware configurations
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from enum import Enum

from ai_generator.models import TestResult, TestStatus, HardwareConfig


class MatrixCellStatus(str, Enum):
    """Status of a matrix cell."""
    PASSED = "passed"
    FAILED = "failed"
    MIXED = "mixed"  # Some tests passed, some failed
    NOT_TESTED = "not_tested"
    ERROR = "error"


@dataclass
class MatrixCell:
    """A single cell in the compatibility matrix."""
    hardware_config: HardwareConfig
    test_results: List[TestResult] = field(default_factory=list)
    status: MatrixCellStatus = MatrixCellStatus.NOT_TESTED
    pass_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    total_count: int = 0
    pass_rate: float = 0.0
    
    def update_from_results(self):
        """Update cell statistics from test results."""
        if not self.test_results:
            self.status = MatrixCellStatus.NOT_TESTED
            self.pass_count = 0
            self.fail_count = 0
            self.error_count = 0
            self.total_count = 0
            self.pass_rate = 0.0
            return
        
        self.total_count = len(self.test_results)
        self.pass_count = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
        self.fail_count = sum(
            1 for r in self.test_results 
            if r.status in [TestStatus.FAILED, TestStatus.TIMEOUT]
        )
        self.error_count = sum(1 for r in self.test_results if r.status == TestStatus.ERROR)
        
        # Calculate pass rate
        self.pass_rate = self.pass_count / self.total_count if self.total_count > 0 else 0.0
        
        # Determine overall status
        if self.pass_count == self.total_count:
            self.status = MatrixCellStatus.PASSED
        elif self.fail_count > 0 or self.error_count > 0:
            if self.pass_count > 0:
                self.status = MatrixCellStatus.MIXED
            else:
                self.status = MatrixCellStatus.FAILED if self.fail_count > 0 else MatrixCellStatus.ERROR
        else:
            self.status = MatrixCellStatus.NOT_TESTED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hardware_config': self.hardware_config.to_dict(),
            'status': self.status.value,
            'pass_count': self.pass_count,
            'fail_count': self.fail_count,
            'error_count': self.error_count,
            'total_count': self.total_count,
            'pass_rate': self.pass_rate,
            'test_result_ids': [r.test_id for r in self.test_results]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], test_results: List[TestResult]) -> 'MatrixCell':
        """Create from dictionary."""
        hw_config = HardwareConfig.from_dict(data['hardware_config'])
        result_ids = set(data.get('test_result_ids', []))
        cell_results = [r for r in test_results if r.test_id in result_ids]
        
        cell = cls(
            hardware_config=hw_config,
            test_results=cell_results,
            status=MatrixCellStatus(data.get('status', 'not_tested')),
            pass_count=data.get('pass_count', 0),
            fail_count=data.get('fail_count', 0),
            error_count=data.get('error_count', 0),
            total_count=data.get('total_count', 0),
            pass_rate=data.get('pass_rate', 0.0)
        )
        return cell


@dataclass
class CompatibilityMatrix:
    """Compatibility matrix showing test results across hardware configurations."""
    
    cells: List[MatrixCell] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __len__(self) -> int:
        """Return number of cells in matrix."""
        return len(self.cells)
    
    def add_cell(self, cell: MatrixCell):
        """Add a cell to the matrix."""
        self.cells.append(cell)
        self.updated_at = datetime.now()
    
    def get_cell_by_config(self, config: HardwareConfig) -> Optional[MatrixCell]:
        """Get cell for a specific hardware configuration."""
        for cell in self.cells:
            if self._configs_match(cell.hardware_config, config):
                return cell
        return None
    
    def _configs_match(self, config1: HardwareConfig, config2: HardwareConfig) -> bool:
        """Check if two hardware configurations match."""
        return (
            config1.architecture == config2.architecture and
            config1.cpu_model == config2.cpu_model and
            config1.memory_mb == config2.memory_mb and
            config1.is_virtual == config2.is_virtual
        )
    
    def get_architectures(self) -> Set[str]:
        """Get all architectures in the matrix."""
        return {cell.hardware_config.architecture for cell in self.cells}
    
    def get_cells_by_architecture(self, architecture: str) -> List[MatrixCell]:
        """Get all cells for a specific architecture."""
        return [cell for cell in self.cells if cell.hardware_config.architecture == architecture]
    
    def get_cells_by_status(self, status: MatrixCellStatus) -> List[MatrixCell]:
        """Get all cells with a specific status."""
        return [cell for cell in self.cells if cell.status == status]
    
    def get_overall_pass_rate(self) -> float:
        """Calculate overall pass rate across all cells."""
        total_tests = sum(cell.total_count for cell in self.cells)
        total_passed = sum(cell.pass_count for cell in self.cells)
        return total_passed / total_tests if total_tests > 0 else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the matrix."""
        return {
            'total_configurations': len(self.cells),
            'architectures': list(self.get_architectures()),
            'passed_configs': len(self.get_cells_by_status(MatrixCellStatus.PASSED)),
            'failed_configs': len(self.get_cells_by_status(MatrixCellStatus.FAILED)),
            'mixed_configs': len(self.get_cells_by_status(MatrixCellStatus.MIXED)),
            'not_tested_configs': len(self.get_cells_by_status(MatrixCellStatus.NOT_TESTED)),
            'overall_pass_rate': self.get_overall_pass_rate(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cells': [cell.to_dict() for cell in self.cells],
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], test_results: List[TestResult]) -> 'CompatibilityMatrix':
        """Create from dictionary."""
        cells = [MatrixCell.from_dict(cell_data, test_results) for cell_data in data.get('cells', [])]
        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            cells=cells,
            metadata=data.get('metadata', {}),
            created_at=created_at,
            updated_at=updated_at
        )


class CompatibilityMatrixGenerator:
    """Generator for compatibility matrices from test results."""
    
    @staticmethod
    def generate_from_results(
        test_results: List[TestResult],
        hardware_configs: Optional[List[HardwareConfig]] = None
    ) -> CompatibilityMatrix:
        """Generate compatibility matrix from test results.
        
        Args:
            test_results: List of test results to analyze
            hardware_configs: Optional list of hardware configs to include (even if not tested)
            
        Returns:
            CompatibilityMatrix populated with results
        """
        matrix = CompatibilityMatrix(
            metadata={
                'total_results': len(test_results),
                'generation_method': 'from_results'
            }
        )
        
        # Group results by hardware configuration
        config_results: Dict[str, List[TestResult]] = {}
        
        for result in test_results:
            config_key = CompatibilityMatrixGenerator._get_config_key(result.environment.config)
            if config_key not in config_results:
                config_results[config_key] = []
            config_results[config_key].append(result)
        
        # Create cells for each configuration with results
        for config_key, results in config_results.items():
            config = results[0].environment.config
            cell = MatrixCell(hardware_config=config, test_results=results)
            cell.update_from_results()
            matrix.add_cell(cell)
        
        # Add cells for hardware configs that weren't tested
        if hardware_configs:
            tested_keys = set(config_results.keys())
            for config in hardware_configs:
                config_key = CompatibilityMatrixGenerator._get_config_key(config)
                if config_key not in tested_keys:
                    cell = MatrixCell(hardware_config=config, test_results=[])
                    cell.update_from_results()
                    matrix.add_cell(cell)
        
        return matrix
    
    @staticmethod
    def _get_config_key(config: HardwareConfig) -> str:
        """Generate a unique key for a hardware configuration."""
        return f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
    
    @staticmethod
    def populate_matrix(
        matrix: CompatibilityMatrix,
        test_results: List[TestResult]
    ) -> CompatibilityMatrix:
        """Populate an existing matrix with new test results.
        
        Args:
            matrix: Existing compatibility matrix
            test_results: New test results to add
            
        Returns:
            Updated compatibility matrix
        """
        # Group new results by configuration
        config_results: Dict[str, List[TestResult]] = {}
        
        for result in test_results:
            config_key = CompatibilityMatrixGenerator._get_config_key(result.environment.config)
            if config_key not in config_results:
                config_results[config_key] = []
            config_results[config_key].append(result)
        
        # Update existing cells or create new ones
        for config_key, results in config_results.items():
            config = results[0].environment.config
            cell = matrix.get_cell_by_config(config)
            
            if cell:
                # Update existing cell
                cell.test_results.extend(results)
                cell.update_from_results()
            else:
                # Create new cell
                cell = MatrixCell(hardware_config=config, test_results=results)
                cell.update_from_results()
                matrix.add_cell(cell)
        
        matrix.updated_at = datetime.now()
        return matrix
    
    @staticmethod
    def merge_matrices(matrices: List[CompatibilityMatrix]) -> CompatibilityMatrix:
        """Merge multiple compatibility matrices into one.
        
        Args:
            matrices: List of matrices to merge
            
        Returns:
            Merged compatibility matrix
        """
        if not matrices:
            return CompatibilityMatrix()
        
        merged = CompatibilityMatrix(
            metadata={
                'merged_from': len(matrices),
                'merge_timestamp': datetime.now().isoformat()
            }
        )
        
        # Collect all test results
        all_results = []
        for matrix in matrices:
            for cell in matrix.cells:
                all_results.extend(cell.test_results)
        
        # Collect all unique hardware configs
        all_configs = []
        seen_keys = set()
        for matrix in matrices:
            for cell in matrix.cells:
                config_key = CompatibilityMatrixGenerator._get_config_key(cell.hardware_config)
                if config_key not in seen_keys:
                    all_configs.append(cell.hardware_config)
                    seen_keys.add(config_key)
        
        # Generate merged matrix
        return CompatibilityMatrixGenerator.generate_from_results(all_results, all_configs)


class MatrixVisualizer:
    """Visualizer for compatibility matrices."""
    
    @staticmethod
    def to_text_table(matrix: CompatibilityMatrix) -> str:
        """Generate a text table representation of the matrix.
        
        Args:
            matrix: Compatibility matrix to visualize
            
        Returns:
            Text table as string
        """
        if not matrix.cells:
            return "Empty compatibility matrix"
        
        lines = []
        lines.append("=" * 100)
        lines.append("COMPATIBILITY MATRIX")
        lines.append("=" * 100)
        lines.append("")
        
        # Summary
        summary = matrix.get_summary()
        lines.append(f"Total Configurations: {summary['total_configurations']}")
        lines.append(f"Architectures: {', '.join(summary['architectures'])}")
        lines.append(f"Overall Pass Rate: {summary['overall_pass_rate']:.2%}")
        lines.append("")
        
        # Group by architecture
        for arch in sorted(matrix.get_architectures()):
            lines.append(f"\n{arch.upper()}")
            lines.append("-" * 100)
            lines.append(f"{'CPU Model':<30} {'Memory':<10} {'Type':<10} {'Status':<15} {'Pass Rate':<10} {'Tests':<10}")
            lines.append("-" * 100)
            
            cells = matrix.get_cells_by_architecture(arch)
            for cell in sorted(cells, key=lambda c: (c.hardware_config.cpu_model, c.hardware_config.memory_mb)):
                config = cell.hardware_config
                hw_type = "Virtual" if config.is_virtual else "Physical"
                status_symbol = MatrixVisualizer._get_status_symbol(cell.status)
                
                lines.append(
                    f"{config.cpu_model:<30} "
                    f"{config.memory_mb:<10} "
                    f"{hw_type:<10} "
                    f"{status_symbol} {cell.status.value:<12} "
                    f"{cell.pass_rate:>8.1%}  "
                    f"{cell.total_count:>10}"
                )
        
        lines.append("")
        lines.append("=" * 100)
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_status_symbol(status: MatrixCellStatus) -> str:
        """Get symbol for status."""
        symbols = {
            MatrixCellStatus.PASSED: "✓",
            MatrixCellStatus.FAILED: "✗",
            MatrixCellStatus.MIXED: "~",
            MatrixCellStatus.NOT_TESTED: "-",
            MatrixCellStatus.ERROR: "!",
        }
        return symbols.get(status, "?")
    
    @staticmethod
    def to_html(matrix: CompatibilityMatrix) -> str:
        """Generate HTML representation of the matrix.
        
        Args:
            matrix: Compatibility matrix to visualize
            
        Returns:
            HTML as string
        """
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html><head>")
        html.append("<title>Compatibility Matrix</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("table { border-collapse: collapse; width: 100%; margin-top: 20px; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #4CAF50; color: white; }")
        html.append(".passed { background-color: #d4edda; }")
        html.append(".failed { background-color: #f8d7da; }")
        html.append(".mixed { background-color: #fff3cd; }")
        html.append(".not-tested { background-color: #e2e3e5; }")
        html.append(".error { background-color: #f5c6cb; }")
        html.append(".summary { margin-bottom: 20px; }")
        html.append("</style>")
        html.append("</head><body>")
        
        html.append("<h1>Compatibility Matrix</h1>")
        
        # Summary
        summary = matrix.get_summary()
        html.append("<div class='summary'>")
        html.append(f"<p><strong>Total Configurations:</strong> {summary['total_configurations']}</p>")
        html.append(f"<p><strong>Architectures:</strong> {', '.join(summary['architectures'])}</p>")
        html.append(f"<p><strong>Overall Pass Rate:</strong> {summary['overall_pass_rate']:.2%}</p>")
        html.append(f"<p><strong>Updated:</strong> {summary['updated_at']}</p>")
        html.append("</div>")
        
        # Table
        html.append("<table>")
        html.append("<tr>")
        html.append("<th>Architecture</th>")
        html.append("<th>CPU Model</th>")
        html.append("<th>Memory (MB)</th>")
        html.append("<th>Type</th>")
        html.append("<th>Status</th>")
        html.append("<th>Pass Rate</th>")
        html.append("<th>Tests</th>")
        html.append("</tr>")
        
        for cell in sorted(matrix.cells, key=lambda c: (c.hardware_config.architecture, c.hardware_config.cpu_model)):
            config = cell.hardware_config
            hw_type = "Virtual" if config.is_virtual else "Physical"
            status_class = cell.status.value.replace('_', '-')
            
            html.append(f"<tr class='{status_class}'>")
            html.append(f"<td>{config.architecture}</td>")
            html.append(f"<td>{config.cpu_model}</td>")
            html.append(f"<td>{config.memory_mb}</td>")
            html.append(f"<td>{hw_type}</td>")
            html.append(f"<td>{cell.status.value}</td>")
            html.append(f"<td>{cell.pass_rate:.1%}</td>")
            html.append(f"<td>{cell.total_count}</td>")
            html.append("</tr>")
        
        html.append("</table>")
        html.append("</body></html>")
        
        return "\n".join(html)
    
    @staticmethod
    def to_csv(matrix: CompatibilityMatrix) -> str:
        """Generate CSV representation of the matrix.
        
        Args:
            matrix: Compatibility matrix to visualize
            
        Returns:
            CSV as string
        """
        lines = []
        lines.append("Architecture,CPU Model,Memory (MB),Type,Status,Pass Rate,Total Tests,Passed,Failed,Errors")
        
        for cell in sorted(matrix.cells, key=lambda c: (c.hardware_config.architecture, c.hardware_config.cpu_model)):
            config = cell.hardware_config
            hw_type = "Virtual" if config.is_virtual else "Physical"
            
            lines.append(
                f"{config.architecture},"
                f"{config.cpu_model},"
                f"{config.memory_mb},"
                f"{hw_type},"
                f"{cell.status.value},"
                f"{cell.pass_rate:.4f},"
                f"{cell.total_count},"
                f"{cell.pass_count},"
                f"{cell.fail_count},"
                f"{cell.error_count}"
            )
        
        return "\n".join(lines)


class MatrixExporter:
    """Exporter for compatibility matrices to various formats."""
    
    @staticmethod
    def export_to_json(matrix: CompatibilityMatrix, file_path: Path):
        """Export matrix to JSON file.
        
        Args:
            matrix: Compatibility matrix to export
            file_path: Path to output file
        """
        with open(file_path, 'w') as f:
            json.dump(matrix.to_dict(), f, indent=2)
    
    @staticmethod
    def export_to_text(matrix: CompatibilityMatrix, file_path: Path):
        """Export matrix to text file.
        
        Args:
            matrix: Compatibility matrix to export
            file_path: Path to output file
        """
        text = MatrixVisualizer.to_text_table(matrix)
        with open(file_path, 'w') as f:
            f.write(text)
    
    @staticmethod
    def export_to_html(matrix: CompatibilityMatrix, file_path: Path):
        """Export matrix to HTML file.
        
        Args:
            matrix: Compatibility matrix to export
            file_path: Path to output file
        """
        html = MatrixVisualizer.to_html(matrix)
        with open(file_path, 'w') as f:
            f.write(html)
    
    @staticmethod
    def export_to_csv(matrix: CompatibilityMatrix, file_path: Path):
        """Export matrix to CSV file.
        
        Args:
            matrix: Compatibility matrix to export
            file_path: Path to output file
        """
        csv = MatrixVisualizer.to_csv(matrix)
        with open(file_path, 'w') as f:
            f.write(csv)
    
    @staticmethod
    def load_from_json(file_path: Path, test_results: List[TestResult]) -> CompatibilityMatrix:
        """Load matrix from JSON file.
        
        Args:
            file_path: Path to JSON file
            test_results: Test results to associate with matrix
            
        Returns:
            CompatibilityMatrix instance
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return CompatibilityMatrix.from_dict(data, test_results)
