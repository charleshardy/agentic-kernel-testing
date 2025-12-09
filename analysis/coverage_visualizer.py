"""Coverage visualization for generating HTML reports and interactive browsers.

This module provides functionality for:
- Generating HTML coverage reports
- Creating visual coverage displays with highlighting
- Building interactive coverage browsers
- Displaying covered/uncovered code regions
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import html

from ai_generator.models import CoverageData
from analysis.coverage_analyzer import FileCoverage, LcovParser


@dataclass
class CoverageReport:
    """Represents a complete coverage report."""
    coverage_data: CoverageData
    file_reports: Dict[str, 'FileCoverageReport']
    generated_at: datetime
    report_title: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'coverage_data': self.coverage_data.to_dict(),
            'file_reports': {k: v.to_dict() for k, v in self.file_reports.items()},
            'generated_at': self.generated_at.isoformat(),
            'report_title': self.report_title
        }


@dataclass
class FileCoverageReport:
    """Coverage report for a single file."""
    file_path: str
    file_coverage: FileCoverage
    source_lines: List[str]
    highlighted_html: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'line_coverage': self.file_coverage.line_coverage_percent,
            'branch_coverage': self.file_coverage.branch_coverage_percent,
            'function_coverage': self.file_coverage.function_coverage_percent,
            'lines_found': self.file_coverage.lines_found,
            'lines_hit': self.file_coverage.lines_hit,
            'branches_found': self.file_coverage.branches_found,
            'branches_hit': self.file_coverage.branches_hit,
            'functions_found': self.file_coverage.functions_found,
            'functions_hit': self.file_coverage.functions_hit
        }


class CoverageVisualizer:
    """Main coverage visualizer for generating HTML reports and interactive browsers."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize coverage visualizer.
        
        Args:
            output_dir: Directory for output files (default: ./coverage_reports)
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./coverage_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parser = LcovParser()
    
    def generate_report(self, lcov_file: str, source_dir: str, 
                       report_title: str = "Coverage Report") -> CoverageReport:
        """Generate a complete coverage report from lcov file.
        
        Args:
            lcov_file: Path to lcov trace file
            source_dir: Directory containing source files
            report_title: Title for the report
            
        Returns:
            CoverageReport object
        """
        # Parse lcov file
        file_coverages = self.parser.parse_lcov_file(lcov_file)
        
        # Generate file reports
        file_reports = {}
        for file_path, file_cov in file_coverages.items():
            file_report = self._generate_file_report(file_path, file_cov, source_dir)
            if file_report:
                file_reports[file_path] = file_report
        
        # Aggregate coverage data
        coverage_data = self._aggregate_coverage_data(file_coverages)
        
        return CoverageReport(
            coverage_data=coverage_data,
            file_reports=file_reports,
            generated_at=datetime.now(),
            report_title=report_title
        )
    
    def _aggregate_coverage_data(self, file_coverages: Dict[str, FileCoverage]) -> CoverageData:
        """Aggregate coverage data from file coverages.
        
        Args:
            file_coverages: Dictionary of FileCoverage objects
            
        Returns:
            Aggregated CoverageData
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
                'total_lines_found': total_lines_found,
                'total_lines_hit': total_lines_hit,
                'total_branches_found': total_branches_found,
                'total_branches_hit': total_branches_hit,
                'total_functions_found': total_functions_found,
                'total_functions_hit': total_functions_hit,
                'num_files': len(file_coverages)
            }
        )
    
    def _generate_file_report(self, file_path: str, file_cov: FileCoverage, 
                             source_dir: str) -> Optional[FileCoverageReport]:
        """Generate coverage report for a single file.
        
        Args:
            file_path: Path to source file
            file_cov: FileCoverage object
            source_dir: Source directory
            
        Returns:
            FileCoverageReport or None if file not found
        """
        full_path = Path(source_dir) / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_lines = f.readlines()
            
            # Generate highlighted HTML
            highlighted_html = self._highlight_source(
                source_lines, file_cov.line_details, file_cov.branch_details
            )
            
            return FileCoverageReport(
                file_path=file_path,
                file_coverage=file_cov,
                source_lines=source_lines,
                highlighted_html=highlighted_html
            )
            
        except (IOError, UnicodeDecodeError):
            return None
    
    def _highlight_source(self, source_lines: List[str], 
                         line_details: Dict[int, int],
                         branch_details: Dict[int, List[Tuple[int, int]]]) -> str:
        """Generate HTML with coverage highlighting.
        
        Args:
            source_lines: List of source code lines
            line_details: Line coverage details (line_num -> hit_count)
            branch_details: Branch coverage details (line_num -> [(branch_id, hit_count)])
            
        Returns:
            HTML string with highlighted code
        """
        html_lines = []
        
        for line_num, line in enumerate(source_lines, start=1):
            # Escape HTML
            escaped_line = html.escape(line.rstrip('\n'))
            
            # Determine coverage status
            hit_count = line_details.get(line_num, None)
            has_branches = line_num in branch_details
            
            if hit_count is not None:
                if hit_count > 0:
                    css_class = "covered"
                    title = f"Executed {hit_count} times"
                else:
                    css_class = "uncovered"
                    title = "Not executed"
            else:
                css_class = "neutral"
                title = ""
            
            # Add branch information
            branch_info = ""
            if has_branches:
                branches = branch_details[line_num]
                total_branches = len(branches)
                hit_branches = sum(1 for _, count in branches if count > 0)
                
                if hit_branches == total_branches:
                    branch_class = "branch-covered"
                elif hit_branches > 0:
                    branch_class = "branch-partial"
                else:
                    branch_class = "branch-uncovered"
                
                branch_info = f' <span class="{branch_class}" title="Branches: {hit_branches}/{total_branches}">⑂</span>'
            
            # Build HTML line
            html_line = (
                f'<div class="line {css_class}" data-line="{line_num}">'
                f'<span class="line-number" title="{title}">{line_num}</span>'
                f'<span class="line-content">{escaped_line}</span>'
                f'{branch_info}'
                f'</div>'
            )
            
            html_lines.append(html_line)
        
        return '\n'.join(html_lines)
    
    def generate_html_report(self, report: CoverageReport, output_name: str = "index") -> str:
        """Generate HTML coverage report files.
        
        Args:
            report: CoverageReport object
            output_name: Base name for output files
            
        Returns:
            Path to main HTML file
        """
        # Create output directory
        report_dir = self.output_dir / output_name
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CSS
        css_path = report_dir / "coverage.css"
        self._generate_css(css_path)
        
        # Generate JavaScript
        js_path = report_dir / "coverage.js"
        self._generate_javascript(js_path)
        
        # Generate index page
        index_path = report_dir / "index.html"
        self._generate_index_html(report, index_path)
        
        # Generate file pages
        for file_path, file_report in report.file_reports.items():
            self._generate_file_html(file_report, report_dir)
        
        return str(index_path)
    
    def _generate_index_html(self, report: CoverageReport, output_path: Path) -> None:
        """Generate index HTML page.
        
        Args:
            report: CoverageReport object
            output_path: Path to output file
        """
        cov = report.coverage_data
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(report.report_title)}</title>
    <link rel="stylesheet" href="coverage.css">
    <script src="coverage.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>{html.escape(report.report_title)}</h1>
            <p class="timestamp">Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <section class="summary">
            <h2>Coverage Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Line Coverage</div>
                    <div class="metric-value">{cov.line_coverage * 100:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {cov.line_coverage * 100}%"></div>
                    </div>
                    <div class="metric-detail">{cov.metadata.get('total_lines_hit', 0)} / {cov.metadata.get('total_lines_found', 0)} lines</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Branch Coverage</div>
                    <div class="metric-value">{cov.branch_coverage * 100:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {cov.branch_coverage * 100}%"></div>
                    </div>
                    <div class="metric-detail">{cov.metadata.get('total_branches_hit', 0)} / {cov.metadata.get('total_branches_found', 0)} branches</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Function Coverage</div>
                    <div class="metric-value">{cov.function_coverage * 100:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {cov.function_coverage * 100}%"></div>
                    </div>
                    <div class="metric-detail">{cov.metadata.get('total_functions_hit', 0)} / {cov.metadata.get('total_functions_found', 0)} functions</div>
                </div>
            </div>
        </section>
        
        <section class="file-list">
            <h2>File Coverage</h2>
            <div class="controls">
                <input type="text" id="file-filter" placeholder="Filter files..." onkeyup="filterFiles()">
                <select id="sort-by" onchange="sortFiles()">
                    <option value="name">Sort by Name</option>
                    <option value="coverage">Sort by Coverage</option>
                </select>
            </div>
            <table id="file-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Line Coverage</th>
                        <th>Branch Coverage</th>
                        <th>Function Coverage</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add file rows
        for file_path, file_report in sorted(report.file_reports.items()):
            file_cov = file_report.file_coverage
            safe_path = file_path.replace('/', '_').replace('.', '_')
            file_html = f"{safe_path}.html"
            
            html_content += f"""                    <tr>
                        <td><a href="{file_html}">{html.escape(file_path)}</a></td>
                        <td class="coverage-cell">
                            <span class="coverage-value">{file_cov.line_coverage_percent * 100:.1f}%</span>
                            <div class="mini-bar">
                                <div class="mini-fill" style="width: {file_cov.line_coverage_percent * 100}%"></div>
                            </div>
                        </td>
                        <td class="coverage-cell">
                            <span class="coverage-value">{file_cov.branch_coverage_percent * 100:.1f}%</span>
                            <div class="mini-bar">
                                <div class="mini-fill" style="width: {file_cov.branch_coverage_percent * 100}%"></div>
                            </div>
                        </td>
                        <td class="coverage-cell">
                            <span class="coverage-value">{file_cov.function_coverage_percent * 100:.1f}%</span>
                            <div class="mini-bar">
                                <div class="mini-fill" style="width: {file_cov.function_coverage_percent * 100}%"></div>
                            </div>
                        </td>
                    </tr>
"""
        
        html_content += """                </tbody>
            </table>
        </section>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_file_html(self, file_report: FileCoverageReport, report_dir: Path) -> None:
        """Generate HTML page for a single file.
        
        Args:
            file_report: FileCoverageReport object
            report_dir: Directory for output
        """
        safe_path = file_report.file_path.replace('/', '_').replace('.', '_')
        output_path = report_dir / f"{safe_path}.html"
        
        file_cov = file_report.file_coverage
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage: {html.escape(file_report.file_path)}</title>
    <link rel="stylesheet" href="coverage.css">
    <script src="coverage.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1><a href="index.html">← Back</a> {html.escape(file_report.file_path)}</h1>
        </header>
        
        <section class="file-summary">
            <div class="metrics">
                <div class="metric-inline">
                    <span class="label">Lines:</span>
                    <span class="value">{file_cov.line_coverage_percent * 100:.1f}%</span>
                    <span class="detail">({file_cov.lines_hit}/{file_cov.lines_found})</span>
                </div>
                <div class="metric-inline">
                    <span class="label">Branches:</span>
                    <span class="value">{file_cov.branch_coverage_percent * 100:.1f}%</span>
                    <span class="detail">({file_cov.branches_hit}/{file_cov.branches_found})</span>
                </div>
                <div class="metric-inline">
                    <span class="label">Functions:</span>
                    <span class="value">{file_cov.function_coverage_percent * 100:.1f}%</span>
                    <span class="detail">({file_cov.functions_hit}/{file_cov.functions_found})</span>
                </div>
            </div>
        </section>
        
        <section class="source-code">
            <div class="code-container">
{file_report.highlighted_html}
            </div>
        </section>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_css(self, output_path: Path) -> None:
        """Generate CSS stylesheet.
        
        Args:
            output_path: Path to output file
        """
        css_content = """/* Coverage Report Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f5f5f5;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    min-height: 100vh;
}

header {
    border-bottom: 3px solid #4CAF50;
    padding-bottom: 20px;
    margin-bottom: 30px;
}

header h1 {
    font-size: 2em;
    color: #2c3e50;
}

header h1 a {
    color: #4CAF50;
    text-decoration: none;
    margin-right: 10px;
}

header h1 a:hover {
    text-decoration: underline;
}

.timestamp {
    color: #7f8c8d;
    font-size: 0.9em;
    margin-top: 5px;
}

.summary {
    margin-bottom: 40px;
}

h2 {
    font-size: 1.5em;
    color: #2c3e50;
    margin-bottom: 20px;
}

.metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.metric {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #4CAF50;
}

.metric-label {
    font-size: 0.9em;
    color: #7f8c8d;
    margin-bottom: 5px;
}

.metric-value {
    font-size: 2em;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
}

.metric-detail {
    font-size: 0.85em;
    color: #95a5a6;
    margin-top: 5px;
}

.progress-bar {
    height: 8px;
    background: #ecf0f1;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #45a049);
    transition: width 0.3s ease;
}

.file-list {
    margin-top: 40px;
}

.controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

#file-filter {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1em;
}

#sort-by {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1em;
    background: white;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

thead {
    background: #34495e;
    color: white;
}

th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
}

tbody tr {
    border-bottom: 1px solid #ecf0f1;
    transition: background 0.2s;
}

tbody tr:hover {
    background: #f8f9fa;
}

td {
    padding: 12px;
}

td a {
    color: #3498db;
    text-decoration: none;
}

td a:hover {
    text-decoration: underline;
}

.coverage-cell {
    min-width: 150px;
}

.coverage-value {
    display: inline-block;
    min-width: 50px;
    font-weight: 600;
}

.mini-bar {
    height: 4px;
    background: #ecf0f1;
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
}

.mini-fill {
    height: 100%;
    background: #4CAF50;
}

/* File view styles */
.file-summary {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.metric-inline {
    display: inline-block;
    margin-right: 30px;
}

.metric-inline .label {
    color: #7f8c8d;
    margin-right: 5px;
}

.metric-inline .value {
    font-weight: bold;
    color: #2c3e50;
    margin-right: 5px;
}

.metric-inline .detail {
    color: #95a5a6;
    font-size: 0.9em;
}

.source-code {
    margin-top: 20px;
}

.code-container {
    background: #282c34;
    border-radius: 8px;
    overflow-x: auto;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.5;
}

.line {
    display: flex;
    align-items: stretch;
    min-height: 20px;
}

.line:hover {
    background: rgba(255, 255, 255, 0.05);
}

.line-number {
    display: inline-block;
    width: 60px;
    padding: 2px 10px;
    text-align: right;
    color: #636d83;
    background: #21252b;
    border-right: 1px solid #181a1f;
    user-select: none;
    flex-shrink: 0;
}

.line-content {
    padding: 2px 10px;
    color: #abb2bf;
    white-space: pre;
    flex: 1;
}

.line.covered {
    background: rgba(76, 175, 80, 0.15);
}

.line.covered .line-number {
    background: rgba(76, 175, 80, 0.3);
    color: #4CAF50;
    font-weight: bold;
}

.line.uncovered {
    background: rgba(244, 67, 54, 0.15);
}

.line.uncovered .line-number {
    background: rgba(244, 67, 54, 0.3);
    color: #f44336;
    font-weight: bold;
}

.line.neutral .line-number {
    color: #636d83;
}

.branch-covered {
    color: #4CAF50;
    margin-left: 5px;
    font-weight: bold;
}

.branch-partial {
    color: #FF9800;
    margin-left: 5px;
    font-weight: bold;
}

.branch-uncovered {
    color: #f44336;
    margin-left: 5px;
    font-weight: bold;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .metrics {
        grid-template-columns: 1fr;
    }
    
    table {
        font-size: 0.9em;
    }
    
    .code-container {
        font-size: 11px;
    }
}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def _generate_javascript(self, output_path: Path) -> None:
        """Generate JavaScript for interactive features.
        
        Args:
            output_path: Path to output file
        """
        js_content = """// Coverage Report Interactive Features

function filterFiles() {
    const input = document.getElementById('file-filter');
    const filter = input.value.toLowerCase();
    const table = document.getElementById('file-table');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const fileCell = row.getElementsByTagName('td')[0];
        
        if (fileCell) {
            const fileName = fileCell.textContent || fileCell.innerText;
            if (fileName.toLowerCase().indexOf(filter) > -1) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    }
}

function sortFiles() {
    const select = document.getElementById('sort-by');
    const sortBy = select.value;
    const table = document.getElementById('file-table');
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    rows.sort((a, b) => {
        if (sortBy === 'name') {
            const nameA = a.getElementsByTagName('td')[0].textContent.toLowerCase();
            const nameB = b.getElementsByTagName('td')[0].textContent.toLowerCase();
            return nameA.localeCompare(nameB);
        } else if (sortBy === 'coverage') {
            const covA = parseFloat(a.getElementsByTagName('td')[1].textContent);
            const covB = parseFloat(b.getElementsByTagName('td')[1].textContent);
            return covA - covB;
        }
        return 0;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Coverage report loaded');
});
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
    
    def generate_json_report(self, report: CoverageReport, output_path: str) -> str:
        """Generate JSON coverage report.
        
        Args:
            report: CoverageReport object
            output_path: Path to output file
            
        Returns:
            Path to generated JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return output_path
