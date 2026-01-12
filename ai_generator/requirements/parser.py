"""EARS Requirement Parser.

Parses requirements written in EARS (Easy Approach to Requirements Syntax)
format into structured representations suitable for property generation.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .models import (
    EARSPattern,
    ParsedRequirement,
    ValidationResult,
    DependencyGraph,
)


class RequirementParser:
    """Parses EARS-formatted requirements into structured representations.
    
    Supports all EARS patterns:
    - Ubiquitous: THE <system> SHALL <response>
    - Event-driven: WHEN <trigger>, THE <system> SHALL <response>
    - State-driven: WHILE <state>, THE <system> SHALL <response>
    - Unwanted: IF <condition>, THEN THE <system> SHALL <response>
    - Optional: WHERE <option>, THE <system> SHALL <response>
    - Complex: Combinations of the above
    """
    
    # EARS pattern regex patterns
    PATTERNS = {
        # WHEN <trigger>, THE <system> SHALL <response>
        EARSPattern.EVENT_DRIVEN: re.compile(
            r'WHEN\s+(.+?),?\s+(?:THEN\s+)?THE\s+(\w+)\s+SHALL\s+(.+)',
            re.IGNORECASE | re.DOTALL
        ),
        # WHILE <state>, THE <system> SHALL <response>
        EARSPattern.STATE_DRIVEN: re.compile(
            r'WHILE\s+(.+?),?\s+THE\s+(\w+)\s+SHALL\s+(.+)',
            re.IGNORECASE | re.DOTALL
        ),
        # IF <condition>, THEN THE <system> SHALL <response>
        EARSPattern.UNWANTED: re.compile(
            r'IF\s+(.+?),?\s+THEN\s+THE\s+(\w+)\s+SHALL\s+(.+)',
            re.IGNORECASE | re.DOTALL
        ),
        # WHERE <option>, THE <system> SHALL <response>
        EARSPattern.OPTIONAL: re.compile(
            r'WHERE\s+(.+?),?\s+THE\s+(\w+)\s+SHALL\s+(.+)',
            re.IGNORECASE | re.DOTALL
        ),
        # THE <system> SHALL <response>
        EARSPattern.UBIQUITOUS: re.compile(
            r'THE\s+(\w+)\s+SHALL\s+(.+)',
            re.IGNORECASE | re.DOTALL
        ),
    }
    
    # Complex pattern with multiple clauses
    COMPLEX_PATTERN = re.compile(
        r'(?:WHERE\s+(.+?),?\s+)?'
        r'(?:WHILE\s+(.+?),?\s+)?'
        r'(?:WHEN\s+(.+?),?\s+)?'
        r'(?:IF\s+(.+?),?\s+THEN\s+)?'
        r'THE\s+(\w+)\s+SHALL\s+(.+)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Ambiguous terms to flag
    AMBIGUOUS_TERMS = [
        'quickly', 'fast', 'slow', 'adequate', 'reasonable',
        'user-friendly', 'easy', 'simple', 'complex', 'efficient',
        'appropriate', 'suitable', 'sufficient', 'minimal', 'optimal',
        'as needed', 'if necessary', 'when possible', 'as appropriate',
    ]
    
    def __init__(self, glossary: Optional[Dict[str, str]] = None):
        """Initialize the parser.
        
        Args:
            glossary: Optional dictionary of defined terms
        """
        self.glossary = glossary or {}
    
    def parse_requirement(self, text: str, req_id: Optional[str] = None) -> ParsedRequirement:
        """Parse a single EARS requirement.
        
        Args:
            text: EARS-formatted requirement text
            req_id: Optional requirement ID (generated if not provided)
            
        Returns:
            ParsedRequirement with extracted components
        """
        text = text.strip()
        req_id = req_id or f"REQ-{uuid.uuid4().hex[:8]}"
        
        # Try complex pattern first
        match = self.COMPLEX_PATTERN.match(text)
        if match:
            where_clause, while_clause, when_clause, if_clause, system, response = match.groups()
            
            # Determine pattern based on which clauses are present
            clause_count = sum(1 for c in [where_clause, while_clause, when_clause, if_clause] if c)
            
            if clause_count > 1:
                pattern = EARSPattern.COMPLEX
            elif where_clause:
                pattern = EARSPattern.OPTIONAL
            elif while_clause:
                pattern = EARSPattern.STATE_DRIVEN
            elif when_clause:
                pattern = EARSPattern.EVENT_DRIVEN
            elif if_clause:
                pattern = EARSPattern.UNWANTED
            else:
                pattern = EARSPattern.UBIQUITOUS
            
            return ParsedRequirement(
                id=req_id,
                text=text,
                pattern=pattern,
                trigger=when_clause or if_clause,
                state=while_clause,
                system=system,
                response=response.strip(),
                options=where_clause,
            )
        
        # Try individual patterns
        for pattern, regex in self.PATTERNS.items():
            match = regex.match(text)
            if match:
                groups = match.groups()
                
                if pattern == EARSPattern.UBIQUITOUS:
                    system, response = groups
                    return ParsedRequirement(
                        id=req_id,
                        text=text,
                        pattern=pattern,
                        system=system,
                        response=response.strip(),
                    )
                elif pattern == EARSPattern.EVENT_DRIVEN:
                    trigger, system, response = groups
                    return ParsedRequirement(
                        id=req_id,
                        text=text,
                        pattern=pattern,
                        trigger=trigger,
                        system=system,
                        response=response.strip(),
                    )
                elif pattern == EARSPattern.STATE_DRIVEN:
                    state, system, response = groups
                    return ParsedRequirement(
                        id=req_id,
                        text=text,
                        pattern=pattern,
                        state=state,
                        system=system,
                        response=response.strip(),
                    )
                elif pattern == EARSPattern.UNWANTED:
                    condition, system, response = groups
                    return ParsedRequirement(
                        id=req_id,
                        text=text,
                        pattern=pattern,
                        trigger=condition,
                        system=system,
                        response=response.strip(),
                    )
                elif pattern == EARSPattern.OPTIONAL:
                    option, system, response = groups
                    return ParsedRequirement(
                        id=req_id,
                        text=text,
                        pattern=pattern,
                        options=option,
                        system=system,
                        response=response.strip(),
                    )
        
        # If no pattern matches, return with UBIQUITOUS as default
        return ParsedRequirement(
            id=req_id,
            text=text,
            pattern=EARSPattern.UBIQUITOUS,
            system="System",
            response=text,
            metadata={"parse_warning": "Could not identify EARS pattern"}
        )
    
    def validate_requirement(self, req: ParsedRequirement) -> ValidationResult:
        """Validate a parsed requirement for completeness and clarity.
        
        Args:
            req: ParsedRequirement to validate
            
        Returns:
            ValidationResult with issues and suggestions
        """
        issues = []
        suggestions = []
        ambiguities = []
        undefined_terms = []
        
        # Check for required components
        if not req.system:
            issues.append("Missing system name")
            suggestions.append("Add a specific system name (e.g., 'THE Parser SHALL...')")
        
        if not req.response:
            issues.append("Missing response/action")
            suggestions.append("Specify what the system SHALL do")
        
        # Check for ambiguous terms
        text_lower = req.text.lower()
        for term in self.AMBIGUOUS_TERMS:
            if term in text_lower:
                ambiguities.append(f"Ambiguous term: '{term}'")
                suggestions.append(f"Replace '{term}' with a measurable criterion")
        
        # Check for undefined terms (words in PascalCase or UPPER_CASE)
        words = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+|[A-Z][A-Z_]+)\b', req.text)
        for word in words:
            if word not in self.glossary and word not in ['THE', 'SHALL', 'WHEN', 'WHILE', 'IF', 'THEN', 'WHERE']:
                undefined_terms.append(word)
        
        if undefined_terms:
            suggestions.append(f"Add definitions for: {', '.join(undefined_terms)}")
        
        # Check for negative statements
        if 'shall not' in text_lower:
            suggestions.append("Consider rephrasing negative statements as positive requirements")
        
        # Check for escape clauses
        escape_clauses = ['where possible', 'if feasible', 'as appropriate', 'when practical']
        for clause in escape_clauses:
            if clause in text_lower:
                issues.append(f"Escape clause detected: '{clause}'")
                suggestions.append(f"Remove '{clause}' and specify exact conditions")
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            ambiguities=ambiguities,
            undefined_terms=undefined_terms,
        )
    
    def parse_specification(self, spec_text: str) -> List[ParsedRequirement]:
        """Parse multiple requirements from a specification text.
        
        Args:
            spec_text: Text containing multiple requirements
            
        Returns:
            List of ParsedRequirement objects
        """
        requirements = []
        
        # Split by numbered requirements (e.g., "1.", "2.", "1.1", etc.)
        req_pattern = re.compile(r'(\d+(?:\.\d+)?)\.\s*(.+?)(?=\d+(?:\.\d+)?\.|$)', re.DOTALL)
        matches = req_pattern.findall(spec_text)
        
        for num, text in matches:
            text = text.strip()
            if text:
                req_id = f"REQ-{num.replace('.', '-')}"
                req = self.parse_requirement(text, req_id)
                requirements.append(req)
        
        # If no numbered requirements found, try line-by-line
        if not requirements:
            lines = spec_text.strip().split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and any(keyword in line.upper() for keyword in ['SHALL', 'WHEN', 'WHILE', 'IF']):
                    req = self.parse_requirement(line, f"REQ-{i}")
                    requirements.append(req)
        
        return requirements
    
    def identify_dependencies(self, reqs: List[ParsedRequirement]) -> DependencyGraph:
        """Identify dependencies between requirements.
        
        Args:
            reqs: List of parsed requirements
            
        Returns:
            DependencyGraph showing relationships
        """
        nodes = [req.id for req in reqs]
        edges = []
        
        # Build a map of system names to requirements
        system_reqs: Dict[str, List[str]] = {}
        for req in reqs:
            if req.system:
                if req.system not in system_reqs:
                    system_reqs[req.system] = []
                system_reqs[req.system].append(req.id)
        
        # Look for references between requirements
        for req in reqs:
            # Check if this requirement references other requirements
            for other_req in reqs:
                if req.id == other_req.id:
                    continue
                
                # Check if the response mentions another system
                if other_req.system and other_req.system.lower() in req.response.lower():
                    edges.append((req.id, other_req.id, "references"))
                
                # Check for explicit requirement references (e.g., "as per REQ-1")
                if other_req.id in req.text:
                    edges.append((req.id, other_req.id, "depends_on"))
        
        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            metadata={"system_groups": system_reqs}
        )
    
    def extract_testable_criteria(self, req: ParsedRequirement) -> List[Dict[str, Any]]:
        """Extract testable criteria from a requirement.
        
        Args:
            req: ParsedRequirement to analyze
            
        Returns:
            List of testable criteria with metadata
        """
        criteria = []
        
        # The main response is always a criterion
        criteria.append({
            "id": f"{req.id}-main",
            "type": "response",
            "text": req.response,
            "testable": True,
            "pattern": req.pattern.value,
        })
        
        # If there's a trigger, it's a precondition
        if req.trigger:
            criteria.append({
                "id": f"{req.id}-trigger",
                "type": "precondition",
                "text": req.trigger,
                "testable": True,
            })
        
        # If there's a state, it's a context condition
        if req.state:
            criteria.append({
                "id": f"{req.id}-state",
                "type": "context",
                "text": req.state,
                "testable": True,
            })
        
        return criteria


def parse_ears_requirement(text: str, glossary: Optional[Dict[str, str]] = None) -> ParsedRequirement:
    """Convenience function to parse a single EARS requirement.
    
    Args:
        text: EARS-formatted requirement text
        glossary: Optional glossary of defined terms
        
    Returns:
        ParsedRequirement object
    """
    parser = RequirementParser(glossary)
    return parser.parse_requirement(text)


def validate_ears_requirement(text: str, glossary: Optional[Dict[str, str]] = None) -> Tuple[ParsedRequirement, ValidationResult]:
    """Convenience function to parse and validate a requirement.
    
    Args:
        text: EARS-formatted requirement text
        glossary: Optional glossary of defined terms
        
    Returns:
        Tuple of (ParsedRequirement, ValidationResult)
    """
    parser = RequirementParser(glossary)
    req = parser.parse_requirement(text)
    validation = parser.validate_requirement(req)
    return req, validation
