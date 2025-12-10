"""Configuration conflict detection system.

This module provides functionality for:
- Analyzing kernel configuration dependencies
- Detecting conflicting configuration options
- Suggesting resolutions for conflicts
- Reporting configuration conflicts
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from execution.kernel_config_testing import KernelConfig, ConfigType


logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of configuration conflicts."""
    MUTUAL_EXCLUSION = "mutual_exclusion"
    DEPENDENCY_MISSING = "dependency_missing"
    ARCHITECTURE_MISMATCH = "architecture_mismatch"
    OPTIMIZATION_CONFLICT = "optimization_conflict"
    DEBUG_CONFLICT = "debug_conflict"
    ALLOCATOR_CONFLICT = "allocator_conflict"
    FEATURE_INCOMPATIBILITY = "feature_incompatibility"


class ConflictSeverity(Enum):
    """Severity levels for configuration conflicts."""
    CRITICAL = "critical"  # Prevents build
    HIGH = "high"         # Likely to cause build failure
    MEDIUM = "medium"     # May cause issues
    LOW = "low"          # Minor incompatibility


@dataclass
class ConfigConflict:
    """Represents a configuration conflict."""
    conflict_type: ConflictType
    severity: ConflictSeverity
    conflicting_options: List[str]
    description: str
    affected_subsystems: List[str] = field(default_factory=list)
    resolution_suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'conflict_type': self.conflict_type.value,
            'severity': self.severity.value,
            'conflicting_options': self.conflicting_options,
            'description': self.description,
            'affected_subsystems': self.affected_subsystems,
            'resolution_suggestions': self.resolution_suggestions,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigConflict':
        """Create from dictionary."""
        return cls(
            conflict_type=ConflictType(data['conflict_type']),
            severity=ConflictSeverity(data['severity']),
            conflicting_options=data['conflicting_options'],
            description=data['description'],
            affected_subsystems=data.get('affected_subsystems', []),
            resolution_suggestions=data.get('resolution_suggestions', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class ConflictReport:
    """Report of configuration conflicts."""
    config: KernelConfig
    conflicts: List[ConfigConflict] = field(default_factory=list)
    has_critical_conflicts: bool = False
    has_build_blocking_conflicts: bool = False
    total_conflicts: int = 0
    conflicts_by_severity: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config': self.config.to_dict(),
            'conflicts': [c.to_dict() for c in self.conflicts],
            'has_critical_conflicts': self.has_critical_conflicts,
            'has_build_blocking_conflicts': self.has_build_blocking_conflicts,
            'total_conflicts': self.total_conflicts,
            'conflicts_by_severity': self.conflicts_by_severity
        }


class ConfigDependencyAnalyzer:
    """Analyzer for configuration dependencies and relationships."""
    
    def __init__(self):
        """Initialize dependency analyzer."""
        # Define known dependency relationships
        self.dependencies = self._build_dependency_rules()
        self.mutual_exclusions = self._build_mutual_exclusion_rules()
        self.architecture_requirements = self._build_architecture_requirements()
    
    def _build_dependency_rules(self) -> Dict[str, List[str]]:
        """Build dependency rules mapping options to their requirements."""
        return {
            # Networking dependencies
            'CONFIG_INET': ['CONFIG_NET'],
            'CONFIG_IPV6': ['CONFIG_INET'],
            'CONFIG_NETFILTER': ['CONFIG_NET'],
            'CONFIG_BRIDGE': ['CONFIG_NET'],
            
            # Filesystem dependencies
            'CONFIG_EXT4_FS': ['CONFIG_BLOCK'],
            'CONFIG_XFS_FS': ['CONFIG_BLOCK'],
            'CONFIG_BTRFS_FS': ['CONFIG_BLOCK'],
            'CONFIG_NFS_FS': ['CONFIG_NET', 'CONFIG_INET'],
            
            # Debug dependencies
            'CONFIG_DEBUG_INFO_DWARF4': ['CONFIG_DEBUG_INFO'],
            'CONFIG_DEBUG_INFO_SPLIT': ['CONFIG_DEBUG_INFO'],
            'CONFIG_FRAME_POINTER': ['CONFIG_DEBUG_KERNEL'],
            'CONFIG_KASAN': ['CONFIG_DEBUG_KERNEL'],
            'CONFIG_UBSAN': ['CONFIG_DEBUG_KERNEL'],
            'CONFIG_KCOV': ['CONFIG_DEBUG_KERNEL'],
            
            # Memory management dependencies
            'CONFIG_SLUB_DEBUG': ['CONFIG_SLUB'],
            'CONFIG_DEBUG_PAGEALLOC': ['CONFIG_DEBUG_KERNEL'],
            'CONFIG_DEBUG_SLAB': ['CONFIG_SLAB'],
            
            # Architecture-specific dependencies
            'CONFIG_X86_64': ['CONFIG_64BIT'],
            'CONFIG_ARM64': ['CONFIG_64BIT'],
            'CONFIG_RISCV': ['CONFIG_64BIT'],  # For riscv64
            
            # Module dependencies
            'CONFIG_MODULE_UNLOAD': ['CONFIG_MODULES'],
            'CONFIG_MODVERSIONS': ['CONFIG_MODULES'],
            'CONFIG_MODULE_SRCVERSION_ALL': ['CONFIG_MODULES'],
            
            # Security dependencies
            'CONFIG_SECURITY_SELINUX': ['CONFIG_SECURITY'],
            'CONFIG_SECURITY_APPARMOR': ['CONFIG_SECURITY'],
            'CONFIG_KEYS': ['CONFIG_SECURITY'],
        }
    
    def _build_mutual_exclusion_rules(self) -> List[Tuple[str, str, str]]:
        """Build mutual exclusion rules as (option1, option2, reason)."""
        return [
            # Optimization conflicts
            ('CONFIG_CC_OPTIMIZE_FOR_SIZE', 'CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE', 
             'Cannot optimize for both size and performance simultaneously'),
            
            # Memory allocator conflicts
            ('CONFIG_SLUB', 'CONFIG_SLAB', 'Cannot use both SLUB and SLAB allocators'),
            ('CONFIG_SLUB', 'CONFIG_SLOB', 'Cannot use both SLUB and SLOB allocators'),
            ('CONFIG_SLAB', 'CONFIG_SLOB', 'Cannot use both SLAB and SLOB allocators'),
            
            # Debug allocator conflicts
            ('CONFIG_SLUB_DEBUG', 'CONFIG_SLOB', 'SLUB_DEBUG conflicts with SLOB allocator'),
            ('CONFIG_DEBUG_SLAB', 'CONFIG_SLUB', 'DEBUG_SLAB conflicts with SLUB allocator'),
            ('CONFIG_DEBUG_SLAB', 'CONFIG_SLOB', 'DEBUG_SLAB conflicts with SLOB allocator'),
            
            # Memory debugging conflicts
            ('CONFIG_KASAN', 'CONFIG_KFENCE', 'KASAN and KFENCE should not be enabled together'),
            ('CONFIG_KASAN', 'CONFIG_SLOB', 'KASAN does not work with SLOB allocator'),
            
            # Architecture conflicts
            ('CONFIG_X86_64', 'CONFIG_ARM64', 'Cannot target both x86_64 and ARM64'),
            ('CONFIG_X86_64', 'CONFIG_ARM', 'Cannot target both x86_64 and ARM'),
            ('CONFIG_X86_64', 'CONFIG_RISCV', 'Cannot target both x86_64 and RISC-V'),
            ('CONFIG_ARM64', 'CONFIG_ARM', 'Cannot target both ARM64 and ARM'),
            ('CONFIG_ARM64', 'CONFIG_RISCV', 'Cannot target both ARM64 and RISC-V'),
            ('CONFIG_ARM', 'CONFIG_RISCV', 'Cannot target both ARM and RISC-V'),
            
            # 32-bit vs 64-bit conflicts
            ('CONFIG_64BIT', 'CONFIG_X86_32', '64-bit conflicts with 32-bit x86'),
            
            # Security conflicts
            ('CONFIG_SECURITY_SELINUX', 'CONFIG_SECURITY_APPARMOR', 
             'SELinux and AppArmor should not both be default security modules'),
        ]
    
    def _build_architecture_requirements(self) -> Dict[str, List[str]]:
        """Build architecture-specific requirements."""
        return {
            'x86_64': ['CONFIG_64BIT', 'CONFIG_X86_64'],
            'arm64': ['CONFIG_ARM64'],
            'arm': ['CONFIG_ARM'],
            'riscv64': ['CONFIG_RISCV', 'CONFIG_64BIT'],
            'riscv32': ['CONFIG_RISCV'],
        }
    
    def analyze_dependencies(self, config: KernelConfig) -> List[str]:
        """Analyze configuration for missing dependencies.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            List of missing dependency descriptions
        """
        missing_deps = []
        
        for option, value in config.options.items():
            if value == 'y' and option in self.dependencies:
                required_deps = self.dependencies[option]
                for dep in required_deps:
                    if config.options.get(dep) != 'y':
                        missing_deps.append(
                            f"{option} requires {dep} to be enabled"
                        )
        
        return missing_deps
    
    def find_mutual_exclusions(self, config: KernelConfig) -> List[Tuple[str, str, str]]:
        """Find mutually exclusive options that are both enabled.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            List of (option1, option2, reason) tuples for conflicts
        """
        conflicts = []
        
        for option1, option2, reason in self.mutual_exclusions:
            if (config.options.get(option1) == 'y' and 
                config.options.get(option2) == 'y'):
                conflicts.append((option1, option2, reason))
        
        return conflicts
    
    def check_architecture_consistency(self, config: KernelConfig) -> List[str]:
        """Check architecture consistency.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            List of architecture inconsistency descriptions
        """
        inconsistencies = []
        
        # Check if required architecture options are present
        if config.architecture in self.architecture_requirements:
            required_options = self.architecture_requirements[config.architecture]
            for option in required_options:
                if config.options.get(option) != 'y':
                    inconsistencies.append(
                        f"Architecture {config.architecture} requires {option} to be enabled"
                    )
        
        # Check for conflicting architecture options
        enabled_archs = []
        arch_options = {
            'CONFIG_X86_64': 'x86_64',
            'CONFIG_ARM64': 'arm64', 
            'CONFIG_ARM': 'arm',
            'CONFIG_RISCV': 'riscv'
        }
        
        for option, arch in arch_options.items():
            if config.options.get(option) == 'y':
                enabled_archs.append((option, arch))
        
        if len(enabled_archs) > 1:
            arch_names = [arch for _, arch in enabled_archs]
            inconsistencies.append(
                f"Multiple architectures enabled: {', '.join(arch_names)}"
            )
        
        return inconsistencies


class ConfigConflictDetector:
    """Main conflict detection engine."""
    
    def __init__(self):
        """Initialize conflict detector."""
        self.dependency_analyzer = ConfigDependencyAnalyzer()
    
    def detect_conflicts(self, config: KernelConfig) -> ConflictReport:
        """Detect all conflicts in a kernel configuration.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            Comprehensive conflict report
        """
        logger.info(f"Detecting conflicts in configuration: {config.name}")
        
        conflicts = []
        
        # Check for dependency conflicts
        dependency_conflicts = self._detect_dependency_conflicts(config)
        conflicts.extend(dependency_conflicts)
        
        # Check for mutual exclusion conflicts
        exclusion_conflicts = self._detect_mutual_exclusion_conflicts(config)
        conflicts.extend(exclusion_conflicts)
        
        # Check for architecture conflicts
        arch_conflicts = self._detect_architecture_conflicts(config)
        conflicts.extend(arch_conflicts)
        
        # Check for optimization conflicts
        opt_conflicts = self._detect_optimization_conflicts(config)
        conflicts.extend(opt_conflicts)
        
        # Check for debug-specific conflicts
        debug_conflicts = self._detect_debug_conflicts(config)
        conflicts.extend(debug_conflicts)
        
        # Generate report
        report = self._generate_conflict_report(config, conflicts)
        
        logger.info(f"Found {len(conflicts)} conflicts in configuration {config.name}")
        return report
    
    def _detect_dependency_conflicts(self, config: KernelConfig) -> List[ConfigConflict]:
        """Detect missing dependency conflicts."""
        conflicts = []
        missing_deps = self.dependency_analyzer.analyze_dependencies(config)
        
        for dep_desc in missing_deps:
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.DEPENDENCY_MISSING,
                severity=ConflictSeverity.HIGH,
                conflicting_options=self._extract_options_from_description(dep_desc),
                description=dep_desc,
                resolution_suggestions=[
                    f"Enable the required dependency option",
                    f"Disable the dependent option if not needed"
                ]
            ))
        
        return conflicts
    
    def _detect_mutual_exclusion_conflicts(self, config: KernelConfig) -> List[ConfigConflict]:
        """Detect mutual exclusion conflicts."""
        conflicts = []
        exclusions = self.dependency_analyzer.find_mutual_exclusions(config)
        
        for option1, option2, reason in exclusions:
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.MUTUAL_EXCLUSION,
                severity=ConflictSeverity.CRITICAL,
                conflicting_options=[option1, option2],
                description=reason,
                resolution_suggestions=[
                    f"Disable {option1} and keep {option2}",
                    f"Disable {option2} and keep {option1}",
                    f"Choose the option most appropriate for your use case"
                ]
            ))
        
        return conflicts
    
    def _detect_architecture_conflicts(self, config: KernelConfig) -> List[ConfigConflict]:
        """Detect architecture-related conflicts."""
        conflicts = []
        arch_issues = self.dependency_analyzer.check_architecture_consistency(config)
        
        for issue in arch_issues:
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.ARCHITECTURE_MISMATCH,
                severity=ConflictSeverity.CRITICAL,
                conflicting_options=self._extract_options_from_description(issue),
                description=issue,
                affected_subsystems=['architecture'],
                resolution_suggestions=[
                    f"Ensure only {config.architecture} architecture options are enabled",
                    f"Review and correct architecture-specific configuration"
                ]
            ))
        
        return conflicts
    
    def _detect_optimization_conflicts(self, config: KernelConfig) -> List[ConfigConflict]:
        """Detect optimization-related conflicts."""
        conflicts = []
        
        # Check for conflicting optimization flags
        size_opt = config.options.get('CONFIG_CC_OPTIMIZE_FOR_SIZE') == 'y'
        perf_opt = config.options.get('CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE') == 'y'
        
        if size_opt and perf_opt:
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.OPTIMIZATION_CONFLICT,
                severity=ConflictSeverity.HIGH,
                conflicting_options=['CONFIG_CC_OPTIMIZE_FOR_SIZE', 'CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE'],
                description="Cannot optimize for both size and performance simultaneously",
                affected_subsystems=['compiler', 'optimization'],
                resolution_suggestions=[
                    "Choose CONFIG_CC_OPTIMIZE_FOR_SIZE for smaller kernels",
                    "Choose CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE for faster kernels",
                    "Use default optimization if unsure"
                ]
            ))
        
        return conflicts
    
    def _detect_debug_conflicts(self, config: KernelConfig) -> List[ConfigConflict]:
        """Detect debug-related conflicts."""
        conflicts = []
        
        # Check for debug options that conflict with allocators
        debug_slab = config.options.get('CONFIG_DEBUG_SLAB') == 'y'
        slub_enabled = config.options.get('CONFIG_SLUB') == 'y'
        slob_enabled = config.options.get('CONFIG_SLOB') == 'y'
        
        if debug_slab and (slub_enabled or slob_enabled):
            allocator = 'SLUB' if slub_enabled else 'SLOB'
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.DEBUG_CONFLICT,
                severity=ConflictSeverity.MEDIUM,
                conflicting_options=['CONFIG_DEBUG_SLAB', f'CONFIG_{allocator}'],
                description=f"DEBUG_SLAB is designed for SLAB allocator, not {allocator}",
                affected_subsystems=['memory', 'debugging'],
                resolution_suggestions=[
                    f"Use CONFIG_SLUB_DEBUG instead of CONFIG_DEBUG_SLAB with {allocator}",
                    "Switch to SLAB allocator if SLAB debugging is required",
                    "Disable debug options if not needed"
                ]
            ))
        
        # Check for KASAN conflicts
        kasan_enabled = config.options.get('CONFIG_KASAN') == 'y'
        if kasan_enabled and slob_enabled:
            conflicts.append(ConfigConflict(
                conflict_type=ConflictType.DEBUG_CONFLICT,
                severity=ConflictSeverity.HIGH,
                conflicting_options=['CONFIG_KASAN', 'CONFIG_SLOB'],
                description="KASAN (Kernel Address Sanitizer) does not work with SLOB allocator",
                affected_subsystems=['memory', 'debugging', 'security'],
                resolution_suggestions=[
                    "Use SLUB or SLAB allocator instead of SLOB when KASAN is enabled",
                    "Disable KASAN if SLOB allocator is required",
                    "Consider using KFENCE as an alternative to KASAN with SLOB"
                ]
            ))
        
        return conflicts
    
    def _extract_options_from_description(self, description: str) -> List[str]:
        """Extract CONFIG options from a description string."""
        import re
        options = re.findall(r'CONFIG_[A-Z0-9_]+', description)
        return list(set(options))  # Remove duplicates
    
    def _generate_conflict_report(self, config: KernelConfig, conflicts: List[ConfigConflict]) -> ConflictReport:
        """Generate a comprehensive conflict report."""
        # Count conflicts by severity
        severity_counts = {}
        for severity in ConflictSeverity:
            severity_counts[severity.value] = 0
        
        for conflict in conflicts:
            severity_counts[conflict.severity.value] += 1
        
        # Determine if there are critical or build-blocking conflicts
        has_critical = severity_counts[ConflictSeverity.CRITICAL.value] > 0
        has_build_blocking = (
            severity_counts[ConflictSeverity.CRITICAL.value] > 0 or
            severity_counts[ConflictSeverity.HIGH.value] > 0
        )
        
        return ConflictReport(
            config=config,
            conflicts=conflicts,
            has_critical_conflicts=has_critical,
            has_build_blocking_conflicts=has_build_blocking,
            total_conflicts=len(conflicts),
            conflicts_by_severity=severity_counts
        )


class ConflictResolutionSuggester:
    """Suggests resolutions for configuration conflicts."""
    
    def __init__(self):
        """Initialize resolution suggester."""
        pass
    
    def suggest_resolutions(self, conflict_report: ConflictReport) -> Dict[str, Any]:
        """Suggest resolutions for all conflicts in a report.
        
        Args:
            conflict_report: Conflict report to analyze
            
        Returns:
            Dictionary with resolution suggestions
        """
        suggestions = {
            'automatic_fixes': [],
            'manual_actions': [],
            'alternative_configs': [],
            'priority_order': []
        }
        
        # Sort conflicts by severity (critical first)
        sorted_conflicts = sorted(
            conflict_report.conflicts,
            key=lambda c: self._severity_priority(c.severity)
        )
        
        for conflict in sorted_conflicts:
            conflict_suggestions = self._suggest_conflict_resolution(conflict)
            
            if conflict_suggestions['can_auto_fix']:
                suggestions['automatic_fixes'].append({
                    'conflict': conflict.to_dict(),
                    'fix': conflict_suggestions['auto_fix']
                })
            else:
                suggestions['manual_actions'].append({
                    'conflict': conflict.to_dict(),
                    'actions': conflict_suggestions['manual_actions']
                })
            
            suggestions['priority_order'].append({
                'conflict_type': conflict.conflict_type.value,
                'severity': conflict.severity.value,
                'options': conflict.conflicting_options,
                'priority': self._severity_priority(conflict.severity)
            })
        
        # Suggest alternative configurations if many conflicts
        if len(conflict_report.conflicts) > 5:
            suggestions['alternative_configs'] = self._suggest_alternative_configs(
                conflict_report.config
            )
        
        return suggestions
    
    def _severity_priority(self, severity: ConflictSeverity) -> int:
        """Get numeric priority for severity (lower number = higher priority)."""
        priority_map = {
            ConflictSeverity.CRITICAL: 1,
            ConflictSeverity.HIGH: 2,
            ConflictSeverity.MEDIUM: 3,
            ConflictSeverity.LOW: 4
        }
        return priority_map[severity]
    
    def _suggest_conflict_resolution(self, conflict: ConfigConflict) -> Dict[str, Any]:
        """Suggest resolution for a specific conflict."""
        if conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            return self._resolve_mutual_exclusion(conflict)
        elif conflict.conflict_type == ConflictType.DEPENDENCY_MISSING:
            return self._resolve_missing_dependency(conflict)
        elif conflict.conflict_type == ConflictType.ARCHITECTURE_MISMATCH:
            return self._resolve_architecture_mismatch(conflict)
        else:
            return {
                'can_auto_fix': False,
                'manual_actions': conflict.resolution_suggestions
            }
    
    def _resolve_mutual_exclusion(self, conflict: ConfigConflict) -> Dict[str, Any]:
        """Resolve mutual exclusion conflicts."""
        if len(conflict.conflicting_options) == 2:
            option1, option2 = conflict.conflicting_options
            return {
                'can_auto_fix': True,
                'auto_fix': {
                    'action': 'disable_one_option',
                    'options': [
                        {'disable': option1, 'keep': option2},
                        {'disable': option2, 'keep': option1}
                    ],
                    'recommendation': f"Disable {option2} (keep {option1})"
                }
            }
        else:
            return {
                'can_auto_fix': False,
                'manual_actions': conflict.resolution_suggestions
            }
    
    def _resolve_missing_dependency(self, conflict: ConfigConflict) -> Dict[str, Any]:
        """Resolve missing dependency conflicts."""
        return {
            'can_auto_fix': True,
            'auto_fix': {
                'action': 'enable_dependency',
                'description': 'Enable required dependency options',
                'changes': [
                    f"Enable missing dependencies for {opt}" 
                    for opt in conflict.conflicting_options
                ]
            }
        }
    
    def _resolve_architecture_mismatch(self, conflict: ConfigConflict) -> Dict[str, Any]:
        """Resolve architecture mismatch conflicts."""
        return {
            'can_auto_fix': False,
            'manual_actions': [
                "Review target architecture selection",
                "Ensure only one architecture is selected",
                "Verify architecture-specific options match target"
            ]
        }
    
    def _suggest_alternative_configs(self, config: KernelConfig) -> List[Dict[str, Any]]:
        """Suggest alternative configurations with fewer conflicts."""
        alternatives = []
        
        # Suggest simpler configuration types
        if config.config_type == ConfigType.MAXIMAL:
            alternatives.append({
                'type': 'default',
                'description': 'Use default configuration to avoid debug-related conflicts',
                'expected_benefit': 'Fewer debug option conflicts'
            })
        
        if config.config_type in [ConfigType.MAXIMAL, ConfigType.DEFAULT]:
            alternatives.append({
                'type': 'minimal',
                'description': 'Use minimal configuration for maximum compatibility',
                'expected_benefit': 'Minimal conflicts, smaller kernel'
            })
        
        return alternatives