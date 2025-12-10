"""Webhook endpoints for CI/CD integration."""

import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header, status

from ..models import APIResponse, WebhookEvent
from ..auth import get_current_user
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

# Store webhook events for demonstration
webhook_events = []


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    if not secret:
        return True  # Skip verification if no secret configured
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Handle different signature formats
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/webhooks/github", response_model=APIResponse)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """Handle GitHub webhook events."""
    try:
        # Get raw payload
        payload = await request.body()
        
        # Verify signature if secret is configured
        if settings.vcs_webhook_secret and x_hub_signature_256:
            if not verify_webhook_signature(payload, x_hub_signature_256, settings.vcs_webhook_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse payload
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Process different event types
        if x_github_event == "push":
            return await handle_github_push(data)
        elif x_github_event == "pull_request":
            return await handle_github_pull_request(data)
        elif x_github_event == "release":
            return await handle_github_release(data)
        else:
            # Log unsupported event but don't fail
            webhook_events.append({
                "event_type": f"github_{x_github_event}",
                "timestamp": datetime.utcnow(),
                "data": {"message": f"Unsupported event type: {x_github_event}"}
            })
            
            return APIResponse(
                success=True,
                message=f"Received {x_github_event} event (not processed)",
                data={"event_type": x_github_event}
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


async def handle_github_push(data: Dict[str, Any]) -> APIResponse:
    """Handle GitHub push events."""
    repository = data.get("repository", {})
    commits = data.get("commits", [])
    ref = data.get("ref", "")
    
    # Extract branch name
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
    
    # Process each commit
    for commit in commits:
        commit_sha = commit.get("id")
        commit_message = commit.get("message", "")
        author = commit.get("author", {}).get("name", "unknown")
        modified_files = commit.get("modified", [])
        
        # Create webhook event
        event = {
            "event_type": "code_push",
            "repository": repository.get("full_name"),
            "branch": branch,
            "commit_sha": commit_sha,
            "commit_message": commit_message,
            "author": author,
            "modified_files": modified_files,
            "timestamp": datetime.utcnow()
        }
        webhook_events.append(event)
        
        # TODO: Trigger code analysis and test generation
        # This would integrate with the AI test generator
        print(f"Processing push to {repository.get('full_name')} on {branch}")
        print(f"Commit: {commit_sha[:8]} - {commit_message}")
        print(f"Modified files: {len(modified_files)}")
    
    return APIResponse(
        success=True,
        message=f"Processed push event with {len(commits)} commits",
        data={
            "repository": repository.get("full_name"),
            "branch": branch,
            "commits_processed": len(commits)
        }
    )


async def handle_github_pull_request(data: Dict[str, Any]) -> APIResponse:
    """Handle GitHub pull request events."""
    action = data.get("action")
    pull_request = data.get("pull_request", {})
    repository = data.get("repository", {})
    
    pr_number = pull_request.get("number")
    pr_title = pull_request.get("title", "")
    base_branch = pull_request.get("base", {}).get("ref", "")
    head_branch = pull_request.get("head", {}).get("ref", "")
    head_sha = pull_request.get("head", {}).get("sha", "")
    
    # Only process certain actions
    if action in ["opened", "synchronize", "reopened"]:
        event = {
            "event_type": "pull_request",
            "action": action,
            "repository": repository.get("full_name"),
            "pr_number": pr_number,
            "pr_title": pr_title,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "head_sha": head_sha,
            "timestamp": datetime.utcnow()
        }
        webhook_events.append(event)
        
        # TODO: Trigger comprehensive testing for PR
        print(f"Processing PR #{pr_number} in {repository.get('full_name')}")
        print(f"Action: {action}")
        print(f"Title: {pr_title}")
        print(f"Branch: {head_branch} -> {base_branch}")
        
        return APIResponse(
            success=True,
            message=f"Processed pull request {action} event",
            data={
                "repository": repository.get("full_name"),
                "pr_number": pr_number,
                "action": action,
                "head_sha": head_sha
            }
        )
    
    return APIResponse(
        success=True,
        message=f"Ignored pull request {action} event",
        data={"action": action}
    )


async def handle_github_release(data: Dict[str, Any]) -> APIResponse:
    """Handle GitHub release events."""
    action = data.get("action")
    release = data.get("release", {})
    repository = data.get("repository", {})
    
    if action == "published":
        tag_name = release.get("tag_name", "")
        release_name = release.get("name", "")
        
        event = {
            "event_type": "release_published",
            "repository": repository.get("full_name"),
            "tag_name": tag_name,
            "release_name": release_name,
            "timestamp": datetime.utcnow()
        }
        webhook_events.append(event)
        
        # TODO: Trigger release validation testing
        print(f"Processing release {tag_name} in {repository.get('full_name')}")
        
        return APIResponse(
            success=True,
            message="Processed release published event",
            data={
                "repository": repository.get("full_name"),
                "tag_name": tag_name,
                "release_name": release_name
            }
        )
    
    return APIResponse(
        success=True,
        message=f"Ignored release {action} event",
        data={"action": action}
    )


@router.post("/webhooks/gitlab", response_model=APIResponse)
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(..., alias="X-Gitlab-Event"),
    x_gitlab_token: Optional[str] = Header(None, alias="X-Gitlab-Token")
):
    """Handle GitLab webhook events."""
    try:
        # Verify token if configured
        if settings.vcs_webhook_secret and x_gitlab_token:
            if x_gitlab_token != settings.vcs_webhook_secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook token"
                )
        
        # Get payload
        payload = await request.body()
        data = json.loads(payload.decode('utf-8'))
        
        # Process different event types
        if x_gitlab_event == "Push Hook":
            return await handle_gitlab_push(data)
        elif x_gitlab_event == "Merge Request Hook":
            return await handle_gitlab_merge_request(data)
        else:
            return APIResponse(
                success=True,
                message=f"Received {x_gitlab_event} event (not processed)",
                data={"event_type": x_gitlab_event}
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitLab webhook processing failed: {str(e)}"
        )


async def handle_gitlab_push(data: Dict[str, Any]) -> APIResponse:
    """Handle GitLab push events."""
    project = data.get("project", {})
    commits = data.get("commits", [])
    ref = data.get("ref", "")
    
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
    
    event = {
        "event_type": "gitlab_push",
        "project": project.get("path_with_namespace"),
        "branch": branch,
        "commits_count": len(commits),
        "timestamp": datetime.utcnow()
    }
    webhook_events.append(event)
    
    return APIResponse(
        success=True,
        message=f"Processed GitLab push with {len(commits)} commits",
        data={
            "project": project.get("path_with_namespace"),
            "branch": branch,
            "commits_processed": len(commits)
        }
    )


async def handle_gitlab_merge_request(data: Dict[str, Any]) -> APIResponse:
    """Handle GitLab merge request events."""
    object_attributes = data.get("object_attributes", {})
    project = data.get("project", {})
    
    action = object_attributes.get("action")
    mr_id = object_attributes.get("iid")
    title = object_attributes.get("title", "")
    source_branch = object_attributes.get("source_branch", "")
    target_branch = object_attributes.get("target_branch", "")
    
    if action in ["open", "update", "reopen"]:
        event = {
            "event_type": "gitlab_merge_request",
            "action": action,
            "project": project.get("path_with_namespace"),
            "mr_id": mr_id,
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "timestamp": datetime.utcnow()
        }
        webhook_events.append(event)
        
        return APIResponse(
            success=True,
            message=f"Processed GitLab merge request {action} event",
            data={
                "project": project.get("path_with_namespace"),
                "mr_id": mr_id,
                "action": action
            }
        )
    
    return APIResponse(
        success=True,
        message=f"Ignored GitLab merge request {action} event",
        data={"action": action}
    )


@router.get("/webhooks/events", response_model=APIResponse)
async def list_webhook_events(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List recent webhook events."""
    # Sort by timestamp (newest first) and limit
    sorted_events = sorted(
        webhook_events,
        key=lambda x: x.get("timestamp", datetime.min),
        reverse=True
    )[:limit]
    
    # Convert datetime objects to ISO strings
    for event in sorted_events:
        if "timestamp" in event and isinstance(event["timestamp"], datetime):
            event["timestamp"] = event["timestamp"].isoformat()
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(sorted_events)} webhook events",
        data={
            "events": sorted_events,
            "total_events": len(webhook_events)
        }
    )


@router.delete("/webhooks/events", response_model=APIResponse)
async def clear_webhook_events(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear webhook events history (admin only)."""
    if "system:admin" not in current_user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    
    cleared_count = len(webhook_events)
    webhook_events.clear()
    
    return APIResponse(
        success=True,
        message=f"Cleared {cleared_count} webhook events",
        data={"cleared_events": cleared_count}
    )