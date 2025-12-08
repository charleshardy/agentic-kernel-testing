"""Data models for VCS integration."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class VCSProvider(str, Enum):
    """Supported VCS providers."""
    GITHUB = "github"
    GITLAB = "gitlab"


class EventType(str, Enum):
    """Types of VCS events."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    BRANCH_UPDATE = "branch_update"
    COMMIT = "commit"
    TAG = "tag"


class PRAction(str, Enum):
    """Pull request actions."""
    OPENED = "opened"
    CLOSED = "closed"
    REOPENED = "reopened"
    SYNCHRONIZED = "synchronized"
    MERGED = "merged"


class TestStatusState(str, Enum):
    """Test status states for VCS reporting."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class Repository:
    """VCS repository information."""
    name: str
    full_name: str
    owner: str
    url: str
    clone_url: str
    default_branch: str = "main"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Repository':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Author:
    """Commit author information."""
    name: str
    email: str
    username: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Author':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CommitInfo:
    """Detailed commit information."""
    sha: str
    message: str
    author: Author
    timestamp: datetime
    url: str
    added_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['author'] = self.author.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommitInfo':
        """Create from dictionary."""
        author_data = data.pop('author')
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        author = Author.from_dict(author_data)
        return cls(**data, author=author, timestamp=timestamp)


@dataclass
class PullRequest:
    """Pull request information."""
    number: int
    title: str
    description: str
    author: Author
    source_branch: str
    target_branch: str
    url: str
    action: PRAction
    commits: List[CommitInfo] = field(default_factory=list)
    is_merged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['author'] = self.author.to_dict()
        data['action'] = self.action.value
        data['commits'] = [c.to_dict() for c in self.commits]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PullRequest':
        """Create from dictionary."""
        author_data = data.pop('author')
        commits_data = data.pop('commits', [])
        author = Author.from_dict(author_data)
        commits = [CommitInfo.from_dict(c) for c in commits_data]
        return cls(**data, author=author, commits=commits)


@dataclass
class VCSEvent:
    """VCS event from webhook."""
    event_id: str
    provider: VCSProvider
    event_type: EventType
    repository: Repository
    timestamp: datetime
    commits: List[CommitInfo] = field(default_factory=list)
    pull_request: Optional[PullRequest] = None
    branch: Optional[str] = None
    ref: Optional[str] = None
    before_sha: Optional[str] = None
    after_sha: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate VCS event."""
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if isinstance(self.provider, str):
            self.provider = VCSProvider(self.provider)
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['provider'] = self.provider.value
        data['event_type'] = self.event_type.value
        data['repository'] = self.repository.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        data['commits'] = [c.to_dict() for c in self.commits]
        if self.pull_request:
            data['pull_request'] = self.pull_request.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VCSEvent':
        """Create from dictionary."""
        repo_data = data.pop('repository')
        commits_data = data.pop('commits', [])
        pr_data = data.pop('pull_request', None)
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        
        repository = Repository.from_dict(repo_data)
        commits = [CommitInfo.from_dict(c) for c in commits_data]
        pull_request = PullRequest.from_dict(pr_data) if pr_data else None
        
        return cls(**data, repository=repository, commits=commits,
                   pull_request=pull_request, timestamp=timestamp)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VCSEvent':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class TestStatus:
    """Test status to report back to VCS."""
    state: TestStatusState
    description: str
    target_url: Optional[str] = None
    context: str = "agentic-testing"
    
    def __post_init__(self):
        """Validate test status."""
        if isinstance(self.state, str):
            self.state = TestStatusState(self.state)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['state'] = self.state.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestStatus':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class StatusReport:
    """Complete status report for VCS."""
    commit_sha: str
    status: TestStatus
    repository: Repository
    timestamp: datetime = field(default_factory=datetime.now)
    test_results_summary: Dict[str, Any] = field(default_factory=dict)
    logs_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.to_dict()
        data['repository'] = self.repository.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusReport':
        """Create from dictionary."""
        status_data = data.pop('status')
        repo_data = data.pop('repository')
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        
        status = TestStatus.from_dict(status_data)
        repository = Repository.from_dict(repo_data)
        
        return cls(**data, status=status, repository=repository, timestamp=timestamp)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StatusReport':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
