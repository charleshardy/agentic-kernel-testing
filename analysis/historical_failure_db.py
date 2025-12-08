"""Historical failure database for pattern matching and resolution tracking.

This module implements storage and retrieval of historical test failures,
enabling pattern matching to identify similar issues and track resolutions.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import asdict

from ai_generator.models import (
    TestResult, FailureAnalysis, FailureInfo, TestStatus
)


class FailurePattern:
    """Represents a pattern of failures for matching."""
    
    def __init__(
        self,
        pattern_id: str,
        signature: str,
        error_pattern: str,
        root_cause: str,
        occurrence_count: int = 1,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        resolution: Optional[str] = None,
        resolution_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize failure pattern.
        
        Args:
            pattern_id: Unique identifier for the pattern
            signature: Failure signature hash
            error_pattern: Type of error pattern
            root_cause: Root cause description
            occurrence_count: Number of times this pattern has occurred
            first_seen: First occurrence timestamp
            last_seen: Last occurrence timestamp
            resolution: Resolution description if resolved
            resolution_date: Date when resolved
            metadata: Additional metadata
        """
        self.pattern_id = pattern_id
        self.signature = signature
        self.error_pattern = error_pattern
        self.root_cause = root_cause
        self.occurrence_count = occurrence_count
        self.first_seen = first_seen or datetime.now()
        self.last_seen = last_seen or datetime.now()
        self.resolution = resolution
        self.resolution_date = resolution_date
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'pattern_id': self.pattern_id,
            'signature': self.signature,
            'error_pattern': self.error_pattern,
            'root_cause': self.root_cause,
            'occurrence_count': self.occurrence_count,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'resolution': self.resolution,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'metadata': json.dumps(self.metadata)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailurePattern':
        """Create from dictionary."""
        return cls(
            pattern_id=data['pattern_id'],
            signature=data['signature'],
            error_pattern=data['error_pattern'],
            root_cause=data['root_cause'],
            occurrence_count=data['occurrence_count'],
            first_seen=datetime.fromisoformat(data['first_seen']),
            last_seen=datetime.fromisoformat(data['last_seen']),
            resolution=data.get('resolution'),
            resolution_date=datetime.fromisoformat(data['resolution_date']) if data.get('resolution_date') else None,
            metadata=json.loads(data['metadata']) if isinstance(data.get('metadata'), str) else data.get('metadata', {})
        )


class HistoricalFailureDatabase:
    """Database for storing and querying historical test failures."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize historical failure database.
        
        Args:
            db_path: Path to SQLite database file. If None, uses in-memory database.
        """
        self.db_path = db_path or ":memory:"
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Create failure_patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_patterns (
                pattern_id TEXT PRIMARY KEY,
                signature TEXT NOT NULL,
                error_pattern TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                resolution TEXT,
                resolution_date TEXT,
                metadata TEXT
            )
        """)
        
        # Create failure_instances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_instances (
                instance_id TEXT PRIMARY KEY,
                pattern_id TEXT NOT NULL,
                test_id TEXT NOT NULL,
                failure_message TEXT NOT NULL,
                stack_trace TEXT,
                timestamp TEXT NOT NULL,
                environment_info TEXT,
                FOREIGN KEY (pattern_id) REFERENCES failure_patterns(pattern_id)
            )
        """)
        
        # Create indices for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signature 
            ON failure_patterns(signature)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_pattern 
            ON failure_patterns(error_pattern)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_id 
            ON failure_instances(pattern_id)
        """)
        
        self.conn.commit()
    
    def store_failure_pattern(self, pattern: FailurePattern) -> None:
        """Store a failure pattern in the database.
        
        Args:
            pattern: FailurePattern to store
        """
        cursor = self.conn.cursor()
        
        # Check if pattern already exists
        cursor.execute(
            "SELECT pattern_id FROM failure_patterns WHERE signature = ?",
            (pattern.signature,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing pattern
            cursor.execute("""
                UPDATE failure_patterns
                SET occurrence_count = occurrence_count + 1,
                    last_seen = ?,
                    root_cause = ?,
                    metadata = ?
                WHERE signature = ?
            """, (
                pattern.last_seen.isoformat(),
                pattern.root_cause,
                json.dumps(pattern.metadata),
                pattern.signature
            ))
        else:
            # Insert new pattern
            data = pattern.to_dict()
            cursor.execute("""
                INSERT INTO failure_patterns (
                    pattern_id, signature, error_pattern, root_cause,
                    occurrence_count, first_seen, last_seen,
                    resolution, resolution_date, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['pattern_id'],
                data['signature'],
                data['error_pattern'],
                data['root_cause'],
                data['occurrence_count'],
                data['first_seen'],
                data['last_seen'],
                data['resolution'],
                data['resolution_date'],
                data['metadata']
            ))
        
        self.conn.commit()
    
    def store_failure_instance(
        self,
        instance_id: str,
        pattern_id: str,
        test_result: TestResult
    ) -> None:
        """Store a specific failure instance.
        
        Args:
            instance_id: Unique identifier for this instance
            pattern_id: ID of the pattern this instance belongs to
            test_result: TestResult containing failure information
        """
        cursor = self.conn.cursor()
        
        failure_info = test_result.failure_info
        if not failure_info:
            failure_info = FailureInfo(error_message="Unknown failure")
        
        cursor.execute("""
            INSERT OR REPLACE INTO failure_instances (
                instance_id, pattern_id, test_id, failure_message,
                stack_trace, timestamp, environment_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            instance_id,
            pattern_id,
            test_result.test_id,
            failure_info.error_message,
            failure_info.stack_trace,
            test_result.timestamp.isoformat(),
            json.dumps(test_result.environment.to_dict())
        ))
        
        self.conn.commit()
    
    def find_matching_patterns(
        self,
        signature: str,
        error_pattern: Optional[str] = None,
        limit: int = 10
    ) -> List[FailurePattern]:
        """Find patterns matching the given signature or error pattern.
        
        Args:
            signature: Failure signature to match
            error_pattern: Optional error pattern type to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of matching FailurePattern objects
        """
        cursor = self.conn.cursor()
        
        if error_pattern:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE signature = ? OR error_pattern = ?
                ORDER BY occurrence_count DESC, last_seen DESC
                LIMIT ?
            """, (signature, error_pattern, limit))
        else:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE signature = ?
                ORDER BY occurrence_count DESC, last_seen DESC
                LIMIT ?
            """, (signature, limit))
        
        rows = cursor.fetchall()
        return [FailurePattern.from_dict(dict(row)) for row in rows]
    
    def lookup_by_pattern_id(self, pattern_id: str) -> Optional[FailurePattern]:
        """Look up a pattern by its ID.
        
        Args:
            pattern_id: Pattern ID to look up
            
        Returns:
            FailurePattern if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM failure_patterns WHERE pattern_id = ?",
            (pattern_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return FailurePattern.from_dict(dict(row))
        return None
    
    def get_pattern_instances(
        self,
        pattern_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all instances of a specific pattern.
        
        Args:
            pattern_id: Pattern ID to get instances for
            limit: Maximum number of instances to return
            
        Returns:
            List of failure instance dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM failure_instances
            WHERE pattern_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (pattern_id, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def update_resolution(
        self,
        pattern_id: str,
        resolution: str,
        resolution_date: Optional[datetime] = None
    ) -> bool:
        """Update the resolution for a failure pattern.
        
        Args:
            pattern_id: Pattern ID to update
            resolution: Resolution description
            resolution_date: Date when resolved (defaults to now)
            
        Returns:
            True if pattern was found and updated, False otherwise
        """
        cursor = self.conn.cursor()
        
        if resolution_date is None:
            resolution_date = datetime.now()
        
        cursor.execute("""
            UPDATE failure_patterns
            SET resolution = ?, resolution_date = ?
            WHERE pattern_id = ?
        """, (resolution, resolution_date.isoformat(), pattern_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_resolved_patterns(
        self,
        error_pattern: Optional[str] = None,
        limit: int = 100
    ) -> List[FailurePattern]:
        """Get patterns that have been resolved.
        
        Args:
            error_pattern: Optional error pattern type to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of resolved FailurePattern objects
        """
        cursor = self.conn.cursor()
        
        if error_pattern:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE resolution IS NOT NULL AND error_pattern = ?
                ORDER BY resolution_date DESC
                LIMIT ?
            """, (error_pattern, limit))
        else:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE resolution IS NOT NULL
                ORDER BY resolution_date DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [FailurePattern.from_dict(dict(row)) for row in rows]
    
    def get_unresolved_patterns(
        self,
        error_pattern: Optional[str] = None,
        min_occurrences: int = 1,
        limit: int = 100
    ) -> List[FailurePattern]:
        """Get patterns that have not been resolved.
        
        Args:
            error_pattern: Optional error pattern type to filter by
            min_occurrences: Minimum number of occurrences to include
            limit: Maximum number of results to return
            
        Returns:
            List of unresolved FailurePattern objects
        """
        cursor = self.conn.cursor()
        
        if error_pattern:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE resolution IS NULL 
                  AND error_pattern = ?
                  AND occurrence_count >= ?
                ORDER BY occurrence_count DESC, last_seen DESC
                LIMIT ?
            """, (error_pattern, min_occurrences, limit))
        else:
            cursor.execute("""
                SELECT * FROM failure_patterns
                WHERE resolution IS NULL 
                  AND occurrence_count >= ?
                ORDER BY occurrence_count DESC, last_seen DESC
                LIMIT ?
            """, (min_occurrences, limit))
        
        rows = cursor.fetchall()
        return [FailurePattern.from_dict(dict(row)) for row in rows]
    
    def search_by_root_cause(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[FailurePattern]:
        """Search patterns by root cause description.
        
        Args:
            search_term: Term to search for in root cause
            limit: Maximum number of results to return
            
        Returns:
            List of matching FailurePattern objects
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM failure_patterns
            WHERE root_cause LIKE ?
            ORDER BY occurrence_count DESC, last_seen DESC
            LIMIT ?
        """, (f"%{search_term}%", limit))
        
        rows = cursor.fetchall()
        return [FailurePattern.from_dict(dict(row)) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics about stored patterns
        """
        cursor = self.conn.cursor()
        
        # Total patterns
        cursor.execute("SELECT COUNT(*) FROM failure_patterns")
        total_patterns = cursor.fetchone()[0]
        
        # Resolved patterns
        cursor.execute("SELECT COUNT(*) FROM failure_patterns WHERE resolution IS NOT NULL")
        resolved_patterns = cursor.fetchone()[0]
        
        # Total instances
        cursor.execute("SELECT COUNT(*) FROM failure_instances")
        total_instances = cursor.fetchone()[0]
        
        # Most common error patterns
        cursor.execute("""
            SELECT error_pattern, COUNT(*) as count
            FROM failure_patterns
            GROUP BY error_pattern
            ORDER BY count DESC
            LIMIT 10
        """)
        common_patterns = [
            {"error_pattern": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        return {
            "total_patterns": total_patterns,
            "resolved_patterns": resolved_patterns,
            "unresolved_patterns": total_patterns - resolved_patterns,
            "total_instances": total_instances,
            "resolution_rate": resolved_patterns / total_patterns if total_patterns > 0 else 0.0,
            "common_error_patterns": common_patterns
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class PatternMatcher:
    """Matches new failures against historical patterns."""
    
    def __init__(self, database: HistoricalFailureDatabase):
        """Initialize pattern matcher.
        
        Args:
            database: HistoricalFailureDatabase instance
        """
        self.database = database
    
    def match_failure(
        self,
        failure_analysis: FailureAnalysis,
        signature: str
    ) -> List[Tuple[FailurePattern, float]]:
        """Match a failure against historical patterns.
        
        Args:
            failure_analysis: FailureAnalysis from current failure
            signature: Failure signature
            
        Returns:
            List of (FailurePattern, similarity_score) tuples, sorted by score
        """
        # First, try exact signature match
        exact_matches = self.database.find_matching_patterns(
            signature=signature,
            limit=5
        )
        
        results = []
        
        # Exact signature matches get highest score
        for pattern in exact_matches:
            results.append((pattern, 1.0))
        
        # If we have exact matches, return them
        if results:
            return results
        
        # Otherwise, try matching by error pattern
        if failure_analysis.error_pattern:
            pattern_matches = self.database.find_matching_patterns(
                signature="",  # Empty signature to skip exact match
                error_pattern=failure_analysis.error_pattern,
                limit=10
            )
            
            # Score based on root cause similarity
            for pattern in pattern_matches:
                similarity = self._calculate_similarity(
                    failure_analysis.root_cause,
                    pattern.root_cause
                )
                if similarity > 0.3:  # Threshold for relevance
                    results.append((pattern, similarity))
        
        # Sort by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings.
        
        Uses simple word overlap as similarity metric.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
