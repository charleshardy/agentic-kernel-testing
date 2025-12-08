"""Notification service for sending alerts through multiple channels."""

import logging
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import requests

from config.settings import get_settings
from integration.notification_models import (
    Notification,
    NotificationResult,
    NotificationChannel as NotificationChannelEnum,
    NotificationSeverity,
    NotificationRecipient
)

logger = logging.getLogger(__name__)


class NotificationChannelBase(ABC):
    """Abstract base class for notification channels."""
    
    @abstractmethod
    def send(self, notification: Notification) -> NotificationResult:
        """Send a notification through this channel."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if this channel is enabled."""
        pass


class EmailChannel(NotificationChannelBase):
    """Email notification channel."""
    
    def __init__(self):
        """Initialize email channel."""
        self.settings = get_settings()
        self.config = self.settings.notification
    
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled."""
        return (
            self.config.enabled and 
            self.config.email_enabled and
            self.config.email_smtp_host is not None and
            self.config.email_from is not None
        )
    
    def send(self, notification: Notification) -> NotificationResult:
        """Send email notification."""
        if not self.is_enabled():
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.EMAIL,
                success=False,
                error_message="Email channel is not enabled or configured"
            )
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{notification.severity.value.upper()}] {notification.title}"
            msg['From'] = self.config.email_from
            
            # Get email recipients
            recipients = [r.email for r in notification.recipients if r.email]
            if not recipients:
                return NotificationResult(
                    notification_id=notification.id,
                    channel=NotificationChannel.EMAIL,
                    success=False,
                    error_message="No email recipients specified"
                )
            
            msg['To'] = ', '.join(recipients)
            
            # Create email body
            text_body = self._format_text_body(notification)
            html_body = self._format_html_body(notification)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
                server.starttls()
                # Note: Add authentication if needed
                # server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent: {notification.id}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.EMAIL,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.EMAIL,
                success=False,
                error_message=str(e)
            )
    
    def _format_text_body(self, notification: Notification) -> str:
        """Format plain text email body."""
        body = f"""
{notification.title}

Severity: {notification.severity.value.upper()}
Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{notification.message}
"""
        if notification.test_id:
            body += f"\nTest ID: {notification.test_id}"
        if notification.failure_id:
            body += f"\nFailure ID: {notification.failure_id}"
        
        if notification.metadata:
            body += "\n\nAdditional Information:\n"
            for key, value in notification.metadata.items():
                body += f"  {key}: {value}\n"
        
        return body
    
    def _format_html_body(self, notification: Notification) -> str:
        """Format HTML email body."""
        severity_colors = {
            NotificationSeverity.INFO: "#0066cc",
            NotificationSeverity.WARNING: "#ff9900",
            NotificationSeverity.ERROR: "#cc0000",
            NotificationSeverity.CRITICAL: "#990000"
        }
        color = severity_colors.get(notification.severity, "#333333")
        
        html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: {color}; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
        .metadata {{ background-color: #f5f5f5; padding: 10px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{notification.title}</h2>
        <p>Severity: {notification.severity.value.upper()} | Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="content">
        <p>{notification.message.replace(chr(10), '<br>')}</p>
"""
        if notification.test_id:
            html += f"<p><strong>Test ID:</strong> {notification.test_id}</p>"
        if notification.failure_id:
            html += f"<p><strong>Failure ID:</strong> {notification.failure_id}</p>"
        
        if notification.metadata:
            html += '<div class="metadata"><h3>Additional Information</h3><ul>'
            for key, value in notification.metadata.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            html += '</ul></div>'
        
        html += """
    </div>
</body>
</html>
"""
        return html


class SlackChannel(NotificationChannelBase):
    """Slack notification channel."""
    
    def __init__(self):
        """Initialize Slack channel."""
        self.settings = get_settings()
        self.config = self.settings.notification
    
    def is_enabled(self) -> bool:
        """Check if Slack notifications are enabled."""
        return (
            self.config.enabled and 
            self.config.slack_enabled and
            self.config.slack_webhook_url is not None
        )
    
    def send(self, notification: Notification) -> NotificationResult:
        """Send Slack notification."""
        if not self.is_enabled():
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.SLACK,
                success=False,
                error_message="Slack channel is not enabled or configured"
            )
        
        try:
            # Format Slack message
            payload = self._format_slack_message(notification)
            
            # Send to Slack webhook
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack notification sent: {notification.id}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.SLACK,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.SLACK,
                success=False,
                error_message=str(e)
            )
    
    def _format_slack_message(self, notification: Notification) -> Dict[str, Any]:
        """Format message for Slack."""
        severity_emojis = {
            NotificationSeverity.INFO: ":information_source:",
            NotificationSeverity.WARNING: ":warning:",
            NotificationSeverity.ERROR: ":x:",
            NotificationSeverity.CRITICAL: ":rotating_light:"
        }
        emoji = severity_emojis.get(notification.severity, ":bell:")
        
        severity_colors = {
            NotificationSeverity.INFO: "#0066cc",
            NotificationSeverity.WARNING: "#ff9900",
            NotificationSeverity.ERROR: "#cc0000",
            NotificationSeverity.CRITICAL: "#990000"
        }
        color = severity_colors.get(notification.severity, "#333333")
        
        # Build fields
        fields = []
        if notification.test_id:
            fields.append({
                "title": "Test ID",
                "value": notification.test_id,
                "short": True
            })
        if notification.failure_id:
            fields.append({
                "title": "Failure ID",
                "value": notification.failure_id,
                "short": True
            })
        
        # Add metadata fields
        for key, value in notification.metadata.items():
            fields.append({
                "title": key,
                "value": str(value),
                "short": True
            })
        
        payload = {
            "text": f"{emoji} *{notification.title}*",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": notification.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": notification.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ] + fields,
                    "text": notification.message
                }
            ]
        }
        
        return payload


class TeamsChannel(NotificationChannelBase):
    """Microsoft Teams notification channel."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Teams channel."""
        self.settings = get_settings()
        self.webhook_url = webhook_url
    
    def is_enabled(self) -> bool:
        """Check if Teams notifications are enabled."""
        return self.webhook_url is not None
    
    def send(self, notification: Notification) -> NotificationResult:
        """Send Teams notification."""
        if not self.is_enabled():
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.TEAMS,
                success=False,
                error_message="Teams channel is not enabled or configured"
            )
        
        try:
            # Format Teams message
            payload = self._format_teams_message(notification)
            
            # Send to Teams webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Teams notification sent: {notification.id}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.TEAMS,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return NotificationResult(
                notification_id=notification.id,
                channel=NotificationChannelEnum.TEAMS,
                success=False,
                error_message=str(e)
            )
    
    def _format_teams_message(self, notification: Notification) -> Dict[str, Any]:
        """Format message for Microsoft Teams."""
        severity_colors = {
            NotificationSeverity.INFO: "0066cc",
            NotificationSeverity.WARNING: "ff9900",
            NotificationSeverity.ERROR: "cc0000",
            NotificationSeverity.CRITICAL: "990000"
        }
        color = severity_colors.get(notification.severity, "333333")
        
        # Build facts
        facts = [
            {
                "name": "Severity",
                "value": notification.severity.value.upper()
            },
            {
                "name": "Time",
                "value": notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        if notification.test_id:
            facts.append({"name": "Test ID", "value": notification.test_id})
        if notification.failure_id:
            facts.append({"name": "Failure ID", "value": notification.failure_id})
        
        for key, value in notification.metadata.items():
            facts.append({"name": key, "value": str(value)})
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": notification.title,
            "themeColor": color,
            "title": notification.title,
            "sections": [
                {
                    "activityTitle": notification.message,
                    "facts": facts
                }
            ]
        }
        
        return payload


class NotificationDispatcher:
    """Dispatcher for sending notifications through multiple channels."""
    
    def __init__(self, teams_webhook_url: Optional[str] = None):
        """Initialize notification dispatcher."""
        self.settings = get_settings()
        self.channels: Dict[NotificationChannelEnum, NotificationChannelBase] = {}
        
        # Initialize channels
        self.channels[NotificationChannelEnum.EMAIL] = EmailChannel()
        self.channels[NotificationChannelEnum.SLACK] = SlackChannel()
        self.channels[NotificationChannelEnum.TEAMS] = TeamsChannel(teams_webhook_url)
    
    def send_notification(self, notification: Notification) -> List[NotificationResult]:
        """Send notification through all specified channels."""
        results = []
        
        # If no channels specified, use all enabled channels
        if not notification.channels:
            notification.channels = [
                ch for ch, handler in self.channels.items()
                if handler.is_enabled()
            ]
        
        # Send through each channel
        for channel_type in notification.channels:
            if channel_type in self.channels:
                handler = self.channels[channel_type]
                result = handler.send(notification)
                results.append(result)
            else:
                logger.warning(f"Unknown notification channel: {channel_type}")
                results.append(NotificationResult(
                    notification_id=notification.id,
                    channel=channel_type,
                    success=False,
                    error_message=f"Unknown channel: {channel_type}"
                ))
        
        return results
    
    def filter_by_severity(
        self, 
        notification: Notification, 
        min_severity: NotificationSeverity
    ) -> bool:
        """Check if notification meets minimum severity threshold."""
        severity_order = {
            NotificationSeverity.INFO: 0,
            NotificationSeverity.WARNING: 1,
            NotificationSeverity.ERROR: 2,
            NotificationSeverity.CRITICAL: 3
        }
        
        return severity_order[notification.severity] >= severity_order[min_severity]
    
    def route_notification(
        self,
        notification: Notification,
        routing_rules: Optional[Dict[NotificationSeverity, List[NotificationChannelEnum]]] = None
    ) -> Notification:
        """Route notification to appropriate channels based on severity."""
        if routing_rules is None:
            # Default routing rules
            routing_rules = {
                NotificationSeverity.INFO: [NotificationChannelEnum.SLACK],
                NotificationSeverity.WARNING: [NotificationChannelEnum.SLACK],
                NotificationSeverity.ERROR: [NotificationChannelEnum.SLACK, NotificationChannelEnum.EMAIL],
                NotificationSeverity.CRITICAL: [
                    NotificationChannelEnum.SLACK, 
                    NotificationChannelEnum.EMAIL, 
                    NotificationChannelEnum.TEAMS
                ]
            }
        
        # Apply routing rules
        if notification.severity in routing_rules:
            notification.channels = routing_rules[notification.severity]
        
        return notification
    
    def send_critical_failure_notification(
        self,
        title: str,
        message: str,
        test_id: Optional[str] = None,
        failure_id: Optional[str] = None,
        recipients: Optional[List[NotificationRecipient]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[NotificationResult]:
        """Send a critical failure notification."""
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=title,
            message=message,
            severity=NotificationSeverity.CRITICAL,
            test_id=test_id,
            failure_id=failure_id,
            recipients=recipients or [],
            metadata=metadata or {}
        )
        
        # Route based on severity
        notification = self.route_notification(notification)
        
        # Send notification
        return self.send_notification(notification)
