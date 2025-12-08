"""Data models for notification system."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class NotificationSeverity(str, Enum):
    """Severity levels for notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"


@dataclass
class NotificationRecipient:
    """Recipient of a notification."""
    name: str
    email: Optional[str] = None
    slack_user_id: Optional[str] = None
    teams_user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationRecipient':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Notification:
    """A notification to be sent."""
    id: str
    title: str
    message: str
    severity: NotificationSeverity
    channels: List[NotificationChannel] = field(default_factory=list)
    recipients: List[NotificationRecipient] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    test_id: Optional[str] = None
    failure_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate notification."""
        if not self.id:
            raise ValueError("Notification id cannot be empty")
        if not self.title:
            raise ValueError("Notification title cannot be empty")
        if not self.message:
            raise ValueError("Notification message cannot be empty")
        if isinstance(self.severity, str):
            self.severity = NotificationSeverity(self.severity)
        self.channels = [
            NotificationChannel(c) if isinstance(c, str) else c 
            for c in self.channels
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['channels'] = [c.value for c in self.channels]
        data['recipients'] = [r.to_dict() for r in self.recipients]
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create from dictionary."""
        recipients_data = data.pop('recipients', [])
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        
        recipients = [NotificationRecipient.from_dict(r) for r in recipients_data]
        
        return cls(**data, recipients=recipients, timestamp=timestamp)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Notification':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class NotificationResult:
    """Result of sending a notification."""
    notification_id: str
    channel: NotificationChannel
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['channel'] = self.channel.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationResult':
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        return cls(**data, timestamp=timestamp)
