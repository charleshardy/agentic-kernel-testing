"""
Environment Readiness Manager

Manages environment readiness state, persistence, tracking, and notifications.
Implements automatic environment status updates on successful validation,
readiness state persistence, and readiness notification and alerting.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from .models import ValidationResult


logger = logging.getLogger(__name__)


class ReadinessStatus(Enum):
    """Environment readiness status levels"""
    UNKNOWN = "unknown"
    NOT_READY = "not_ready"
    READY = "ready"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ReadinessState:
    """Represents the readiness state of an environment"""
    environment_id: str
    status: ReadinessStatus
    last_validation: datetime
    validation_count: int = 0
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_failure_reason: Optional[str] = None
    readiness_score: float = 0.0  # 0.0 to 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_validation'] = self.last_validation.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReadinessState':
        """Create from dictionary"""
        data = data.copy()
        data['status'] = ReadinessStatus(data['status'])
        data['last_validation'] = datetime.fromisoformat(data['last_validation'])
        return cls(**data)


@dataclass
class ReadinessNotification:
    """Represents a readiness notification"""
    environment_id: str
    level: NotificationLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ReadinessManager:
    """
    Manages environment readiness state, persistence, and notifications.
    
    Provides comprehensive readiness tracking with:
    - Automatic status updates on validation results
    - Persistent state storage and recovery
    - Readiness scoring and trend analysis
    - Notification and alerting system
    - Historical readiness tracking
    """
    
    def __init__(self, state_file_path: str = "deployment/readiness_state.json"):
        """
        Initialize readiness manager.
        
        Args:
            state_file_path: Path to persistent state file
        """
        self.state_file_path = Path(state_file_path)
        self.environment_states: Dict[str, ReadinessState] = {}
        self.notification_history: List[ReadinessNotification] = []
        self.notification_subscribers: Set[callable] = set()
        
        # Configuration
        self.max_history_entries = 1000
        self.notification_retention_days = 30
        self.readiness_threshold = 80.0  # Minimum score for "ready" status
        self.degraded_threshold = 60.0   # Below this is "degraded"
        
        # Load existing state
        asyncio.create_task(self._load_state())
    
    async def _load_state(self):
        """Load readiness state from persistent storage"""
        try:
            if self.state_file_path.exists():
                with open(self.state_file_path, 'r') as f:
                    data = json.load(f)
                
                # Load environment states
                for env_id, state_data in data.get('environment_states', {}).items():
                    self.environment_states[env_id] = ReadinessState.from_dict(state_data)
                
                # Load notification history
                for notif_data in data.get('notification_history', []):
                    notification = ReadinessNotification(
                        environment_id=notif_data['environment_id'],
                        level=NotificationLevel(notif_data['level']),
                        message=notif_data['message'],
                        timestamp=datetime.fromisoformat(notif_data['timestamp']),
                        details=notif_data.get('details', {}),
                        acknowledged=notif_data.get('acknowledged', False)
                    )
                    self.notification_history.append(notification)
                
                logger.info(f"Loaded readiness state for {len(self.environment_states)} environments")
            else:
                logger.info("No existing readiness state file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load readiness state: {e}")
            # Continue with empty state
    
    async def _save_state(self):
        """Save readiness state to persistent storage"""
        try:
            # Ensure directory exists
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            data = {
                'environment_states': {
                    env_id: state.to_dict() 
                    for env_id, state in self.environment_states.items()
                },
                'notification_history': [
                    notif.to_dict() for notif in self.notification_history[-self.max_history_entries:]
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            # Write to temporary file first, then rename for atomicity
            temp_file = self.state_file_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_file.rename(self.state_file_path)
            logger.debug("Saved readiness state to persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to save readiness state: {e}")
    
    async def update_environment_readiness(self, 
                                         environment_id: str, 
                                         validation_result: ValidationResult) -> ReadinessState:
        """
        Update environment readiness based on validation result.
        
        Args:
            environment_id: Environment identifier
            validation_result: Result of readiness validation
            
        Returns:
            Updated readiness state
        """
        logger.info(f"Updating readiness for environment {environment_id}")
        
        # Get or create environment state
        if environment_id not in self.environment_states:
            self.environment_states[environment_id] = ReadinessState(
                environment_id=environment_id,
                status=ReadinessStatus.UNKNOWN,
                last_validation=datetime.now(),
                validation_count=0
            )
        
        state = self.environment_states[environment_id]
        previous_status = state.status
        
        # Update validation tracking
        state.validation_count += 1
        state.last_validation = validation_result.timestamp
        
        # Update success/failure counters
        if validation_result.is_ready:
            state.consecutive_successes += 1
            state.consecutive_failures = 0
            state.last_failure_reason = None
        else:
            state.consecutive_failures += 1
            state.consecutive_successes = 0
            state.last_failure_reason = ", ".join(validation_result.failed_checks)
        
        # Calculate readiness score
        state.readiness_score = self._calculate_readiness_score(validation_result, state)
        
        # Determine new status
        new_status = self._determine_readiness_status(validation_result, state)
        state.status = new_status
        
        # Update metadata
        state.metadata.update({
            'last_validation_success_rate': validation_result.success_rate,
            'failed_checks_count': len(validation_result.failed_checks),
            'warnings_count': len(validation_result.warnings),
            'checks_performed_count': len(validation_result.checks_performed)
        })
        
        # Generate notifications if status changed
        if new_status != previous_status:
            await self._generate_status_change_notification(
                environment_id, previous_status, new_status, validation_result
            )
        
        # Generate alerts for critical issues
        if validation_result.has_failures and state.consecutive_failures >= 3:
            await self._generate_failure_alert(environment_id, validation_result, state)
        
        # Save state
        await self._save_state()
        
        logger.info(f"Updated readiness for {environment_id}: {new_status.value} "
                   f"(score: {state.readiness_score:.1f})")
        
        return state
    
    def _calculate_readiness_score(self, 
                                 validation_result: ValidationResult, 
                                 state: ReadinessState) -> float:
        """
        Calculate readiness score based on validation result and history.
        
        Args:
            validation_result: Current validation result
            state: Current environment state
            
        Returns:
            Readiness score from 0.0 to 100.0
        """
        # Base score from current validation
        base_score = validation_result.success_rate
        
        # Apply historical performance weighting
        if state.validation_count > 1:
            # Weight recent performance more heavily
            success_rate = state.consecutive_successes / min(state.validation_count, 10)
            historical_weight = 0.3
            base_score = (base_score * (1 - historical_weight)) + (success_rate * 100 * historical_weight)
        
        # Apply penalties for consecutive failures
        if state.consecutive_failures > 0:
            failure_penalty = min(state.consecutive_failures * 10, 50)  # Max 50% penalty
            base_score = max(0, base_score - failure_penalty)
        
        # Apply bonus for consecutive successes
        if state.consecutive_successes > 3:
            success_bonus = min((state.consecutive_successes - 3) * 2, 10)  # Max 10% bonus
            base_score = min(100, base_score + success_bonus)
        
        return round(base_score, 1)
    
    def _determine_readiness_status(self, 
                                  validation_result: ValidationResult, 
                                  state: ReadinessState) -> ReadinessStatus:
        """
        Determine readiness status based on validation result and score.
        
        Args:
            validation_result: Current validation result
            state: Current environment state
            
        Returns:
            New readiness status
        """
        # Check for offline status (no recent validation)
        time_since_validation = datetime.now() - state.last_validation
        if time_since_validation > timedelta(hours=1):
            return ReadinessStatus.OFFLINE
        
        # Check for maintenance mode (manual override)
        if state.metadata.get('maintenance_mode', False):
            return ReadinessStatus.MAINTENANCE
        
        # Determine status based on readiness score and validation result
        if not validation_result.is_ready:
            # Has critical failures
            critical_failures = [
                check for check in validation_result.failed_checks
                if check in ['kernel_compatibility', 'network_connectivity', 'tool_functionality']
            ]
            
            if critical_failures or state.consecutive_failures >= 5:
                return ReadinessStatus.NOT_READY
            else:
                return ReadinessStatus.DEGRADED
        
        # Environment passed validation
        if state.readiness_score >= self.readiness_threshold:
            return ReadinessStatus.READY
        elif state.readiness_score >= self.degraded_threshold:
            return ReadinessStatus.DEGRADED
        else:
            return ReadinessStatus.NOT_READY
    
    async def _generate_status_change_notification(self, 
                                                 environment_id: str,
                                                 previous_status: ReadinessStatus,
                                                 new_status: ReadinessStatus,
                                                 validation_result: ValidationResult):
        """Generate notification for status changes"""
        # Determine notification level
        if new_status == ReadinessStatus.NOT_READY:
            level = NotificationLevel.ERROR
        elif new_status == ReadinessStatus.DEGRADED:
            level = NotificationLevel.WARNING
        elif new_status == ReadinessStatus.READY and previous_status in [ReadinessStatus.NOT_READY, ReadinessStatus.DEGRADED]:
            level = NotificationLevel.INFO
        elif new_status == ReadinessStatus.OFFLINE:
            level = NotificationLevel.CRITICAL
        else:
            level = NotificationLevel.INFO
        
        message = f"Environment {environment_id} status changed from {previous_status.value} to {new_status.value}"
        
        details = {
            'previous_status': previous_status.value,
            'new_status': new_status.value,
            'validation_success_rate': validation_result.success_rate,
            'failed_checks': validation_result.failed_checks,
            'warnings': validation_result.warnings
        }
        
        await self._send_notification(environment_id, level, message, details)
    
    async def _generate_failure_alert(self, 
                                    environment_id: str,
                                    validation_result: ValidationResult,
                                    state: ReadinessState):
        """Generate alert for repeated failures"""
        message = (f"Environment {environment_id} has failed validation "
                  f"{state.consecutive_failures} consecutive times")
        
        details = {
            'consecutive_failures': state.consecutive_failures,
            'last_failure_reason': state.last_failure_reason,
            'failed_checks': validation_result.failed_checks,
            'readiness_score': state.readiness_score
        }
        
        await self._send_notification(
            environment_id, 
            NotificationLevel.CRITICAL, 
            message, 
            details
        )
    
    async def _send_notification(self, 
                               environment_id: str,
                               level: NotificationLevel,
                               message: str,
                               details: Dict[str, Any] = None):
        """Send notification to subscribers"""
        notification = ReadinessNotification(
            environment_id=environment_id,
            level=level,
            message=message,
            details=details or {}
        )
        
        # Add to history
        self.notification_history.append(notification)
        
        # Clean up old notifications
        cutoff_date = datetime.now() - timedelta(days=self.notification_retention_days)
        self.notification_history = [
            n for n in self.notification_history 
            if n.timestamp > cutoff_date
        ]
        
        # Notify subscribers
        for subscriber in self.notification_subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(notification)
                else:
                    subscriber(notification)
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")
        
        logger.info(f"Sent {level.value} notification for {environment_id}: {message}")
    
    def subscribe_to_notifications(self, callback: callable):
        """
        Subscribe to readiness notifications.
        
        Args:
            callback: Function to call when notifications are generated
                     Can be sync or async function
        """
        self.notification_subscribers.add(callback)
        logger.info(f"Added notification subscriber: {callback.__name__}")
    
    def unsubscribe_from_notifications(self, callback: callable):
        """Unsubscribe from readiness notifications"""
        self.notification_subscribers.discard(callback)
        logger.info(f"Removed notification subscriber: {callback.__name__}")
    
    def get_environment_readiness(self, environment_id: str) -> Optional[ReadinessState]:
        """
        Get current readiness state for an environment.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            ReadinessState if environment exists, None otherwise
        """
        return self.environment_states.get(environment_id)
    
    def get_all_environment_readiness(self) -> Dict[str, ReadinessState]:
        """Get readiness state for all environments"""
        return self.environment_states.copy()
    
    def get_ready_environments(self) -> List[str]:
        """Get list of environment IDs that are ready for test execution"""
        return [
            env_id for env_id, state in self.environment_states.items()
            if state.status == ReadinessStatus.READY
        ]
    
    def get_not_ready_environments(self) -> List[str]:
        """Get list of environment IDs that are not ready for test execution"""
        return [
            env_id for env_id, state in self.environment_states.items()
            if state.status in [ReadinessStatus.NOT_READY, ReadinessStatus.DEGRADED, ReadinessStatus.OFFLINE]
        ]
    
    def get_recent_notifications(self, 
                               environment_id: Optional[str] = None,
                               level: Optional[NotificationLevel] = None,
                               hours: int = 24) -> List[ReadinessNotification]:
        """
        Get recent notifications with optional filtering.
        
        Args:
            environment_id: Filter by environment ID
            level: Filter by notification level
            hours: Number of hours to look back
            
        Returns:
            List of matching notifications
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        notifications = [
            n for n in self.notification_history
            if n.timestamp > cutoff_time
        ]
        
        if environment_id:
            notifications = [n for n in notifications if n.environment_id == environment_id]
        
        if level:
            notifications = [n for n in notifications if n.level == level]
        
        return sorted(notifications, key=lambda n: n.timestamp, reverse=True)
    
    async def mark_environment_maintenance(self, 
                                         environment_id: str, 
                                         maintenance_mode: bool,
                                         reason: str = None):
        """
        Mark environment as in maintenance mode.
        
        Args:
            environment_id: Environment identifier
            maintenance_mode: True to enable maintenance mode, False to disable
            reason: Optional reason for maintenance
        """
        if environment_id not in self.environment_states:
            self.environment_states[environment_id] = ReadinessState(
                environment_id=environment_id,
                status=ReadinessStatus.UNKNOWN,
                last_validation=datetime.now()
            )
        
        state = self.environment_states[environment_id]
        state.metadata['maintenance_mode'] = maintenance_mode
        
        if maintenance_mode:
            state.status = ReadinessStatus.MAINTENANCE
            state.metadata['maintenance_reason'] = reason or "Manual maintenance mode"
            message = f"Environment {environment_id} entered maintenance mode"
            if reason:
                message += f": {reason}"
        else:
            # Remove maintenance mode, status will be updated on next validation
            state.metadata.pop('maintenance_reason', None)
            message = f"Environment {environment_id} exited maintenance mode"
        
        await self._send_notification(
            environment_id,
            NotificationLevel.INFO,
            message,
            {'maintenance_mode': maintenance_mode, 'reason': reason}
        )
        
        await self._save_state()
        logger.info(f"Set maintenance mode for {environment_id}: {maintenance_mode}")
    
    def get_readiness_statistics(self) -> Dict[str, Any]:
        """
        Get overall readiness statistics.
        
        Returns:
            Dictionary with readiness statistics
        """
        if not self.environment_states:
            return {
                'total_environments': 0,
                'ready_count': 0,
                'not_ready_count': 0,
                'degraded_count': 0,
                'offline_count': 0,
                'maintenance_count': 0,
                'average_readiness_score': 0.0,
                'overall_readiness_rate': 0.0
            }
        
        status_counts = {}
        total_score = 0
        
        for state in self.environment_states.values():
            status = state.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            total_score += state.readiness_score
        
        ready_count = status_counts.get('ready', 0)
        total_count = len(self.environment_states)
        
        return {
            'total_environments': total_count,
            'ready_count': ready_count,
            'not_ready_count': status_counts.get('not_ready', 0),
            'degraded_count': status_counts.get('degraded', 0),
            'offline_count': status_counts.get('offline', 0),
            'maintenance_count': status_counts.get('maintenance', 0),
            'average_readiness_score': total_score / total_count,
            'overall_readiness_rate': (ready_count / total_count) * 100.0,
            'status_distribution': status_counts
        }
    
    async def cleanup_old_data(self):
        """Clean up old notifications and state data"""
        # Clean up old notifications
        cutoff_date = datetime.now() - timedelta(days=self.notification_retention_days)
        initial_count = len(self.notification_history)
        
        self.notification_history = [
            n for n in self.notification_history 
            if n.timestamp > cutoff_date
        ]
        
        cleaned_count = initial_count - len(self.notification_history)
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old notifications")
            await self._save_state()