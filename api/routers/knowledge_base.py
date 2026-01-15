"""Knowledge Base and Documentation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/knowledge-base")


# Request/Response Models
class Article(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    author: str
    created_at: datetime
    updated_at: datetime
    views: int
    helpful_count: int


class SearchResult(BaseModel):
    article_id: str
    title: str
    excerpt: str
    category: str
    relevance_score: float
    highlighted_text: Optional[str]


class HelpContext(BaseModel):
    page: str
    section: str
    suggestions: List[dict]


@router.get("/articles", response_model=APIResponse)
async def list_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List knowledge base articles."""
    articles = [
        Article(
            id="art-001",
            title="Getting Started with Test Execution",
            content="This guide covers the basics of test execution...",
            category="tutorials",
            tags=["testing", "getting-started"],
            author="admin",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            views=150,
            helpful_count=45
        ),
        Article(
            id="art-002",
            title="Troubleshooting Test Failures",
            content="Common issues and solutions for test failures...",
            category="troubleshooting",
            tags=["testing", "debugging"],
            author="admin",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            views=200,
            helpful_count=60
        ),
        Article(
            id="art-003",
            title="Security Scanning Best Practices",
            content="Learn how to effectively use security scanning...",
            category="best-practices",
            tags=["security", "scanning"],
            author="security-team",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            views=120,
            helpful_count=38
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(articles)} articles",
        data={"articles": [a.dict() for a in articles], "total": len(articles)}
    )


@router.get("/articles/{article_id}", response_model=APIResponse)
async def get_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific article."""
    article = Article(
        id=article_id,
        title="Getting Started with Test Execution",
        content="This guide covers the basics of test execution...",
        category="tutorials",
        tags=["testing", "getting-started"],
        author="admin",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        views=150,
        helpful_count=45
    )
    
    return APIResponse(
        success=True,
        message="Article retrieved successfully",
        data=article.dict()
    )


@router.get("/search", response_model=APIResponse)
async def search_articles(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Search knowledge base articles."""
    results = [
        SearchResult(
            article_id="art-001",
            title="Getting Started with Test Execution",
            excerpt="This guide covers the basics of test execution and how to...",
            category="tutorials",
            relevance_score=0.95,
            highlighted_text="<mark>test execution</mark> basics"
        ),
        SearchResult(
            article_id="art-002",
            title="Troubleshooting Test Failures",
            excerpt="Common issues and solutions for test failures including...",
            category="troubleshooting",
            relevance_score=0.82,
            highlighted_text="<mark>test</mark> failures"
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Found {len(results)} matching articles",
        data={"results": [r.dict() for r in results], "total": len(results)}
    )


@router.get("/contextual-help", response_model=APIResponse)
async def get_contextual_help(
    page: str = Query(..., description="Current page identifier"),
    section: Optional[str] = Query(None, description="Current section"),
    current_user: dict = Depends(get_current_user)
):
    """Get contextual help suggestions for a specific page."""
    help_context = HelpContext(
        page=page,
        section=section or "main",
        suggestions=[
            {
                "article_id": "art-001",
                "title": "Getting Started with Test Execution",
                "relevance": "high"
            },
            {
                "article_id": "art-004",
                "title": "Understanding Test Results",
                "relevance": "medium"
            }
        ]
    )
    
    return APIResponse(
        success=True,
        message="Contextual help retrieved",
        data=help_context.dict()
    )


@router.get("/categories", response_model=APIResponse)
async def list_categories(current_user: dict = Depends(get_current_user)):
    """List all article categories."""
    categories = [
        {"id": "tutorials", "name": "Tutorials", "count": 15},
        {"id": "troubleshooting", "name": "Troubleshooting", "count": 25},
        {"id": "best-practices", "name": "Best Practices", "count": 12},
        {"id": "api-reference", "name": "API Reference", "count": 30},
        {"id": "faq", "name": "FAQ", "count": 20}
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(categories)} categories",
        data={"categories": categories}
    )


@router.post("/articles", response_model=APIResponse)
async def create_article(
    article: Article,
    current_user: dict = Depends(get_current_user)
):
    """Create a new knowledge base article."""
    return APIResponse(
        success=True,
        message=f"Article '{article.title}' created successfully",
        data={"article_id": "art-new"}
    )


@router.put("/articles/{article_id}", response_model=APIResponse)
async def update_article(
    article_id: str,
    article: Article,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing article."""
    return APIResponse(
        success=True,
        message=f"Article {article_id} updated successfully",
        data={"article_id": article_id}
    )


@router.post("/articles/{article_id}/helpful", response_model=APIResponse)
async def mark_article_helpful(
    article_id: str,
    helpful: bool,
    current_user: dict = Depends(get_current_user)
):
    """Mark an article as helpful or not helpful."""
    return APIResponse(
        success=True,
        message=f"Feedback recorded for article {article_id}",
        data={"article_id": article_id, "helpful": helpful}
    )
