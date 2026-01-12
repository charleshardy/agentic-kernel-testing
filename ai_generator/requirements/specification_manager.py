"""Specification Manager for Agentic AI Test Requirements.

Manages test specifications with:
- YAML/JSON storage
- Version tracking
- CRUD operations
- Export to multiple formats
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .models import (
    TestSpecification,
    ParsedRequirement,
    CorrectnessProperty,
    GeneratedTest,
    EARSPattern,
)
from .parser import RequirementParser
from .property_generator import PropertyGenerator
from .test_generator import PropertyTestGenerator


@dataclass
class SpecificationUpdate:
    """Update to a specification."""
    name: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[ParsedRequirement]] = None
    properties: Optional[List[CorrectnessProperty]] = None
    glossary: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SpecificationManager:
    """Manages test specifications.
    
    Provides:
    - CRUD operations for specifications
    - YAML/JSON storage
    - Version tracking
    - Export to multiple formats
    - Automatic test regeneration
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the specification manager.
        
        Args:
            storage_path: Path to store specifications (default: ./specifications)
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./specifications")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._specifications: Dict[str, TestSpecification] = {}
        
        # Services
        self._parser = RequirementParser()
        self._property_generator = PropertyGenerator()
        self._test_generator = PropertyTestGenerator()
        
        # Load existing specifications
        self._load_specifications()
    
    def create_specification(
        self,
        name: str,
        description: str = "",
        requirements: Optional[List[ParsedRequirement]] = None,
        glossary: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TestSpecification:
        """Create a new test specification.
        
        Args:
            name: Specification name
            description: Specification description
            requirements: Optional list of requirements
            glossary: Optional glossary of terms
            metadata: Optional metadata
            
        Returns:
            Created TestSpecification
        """
        spec_id = f"spec_{uuid.uuid4().hex[:8]}"
        
        spec = TestSpecification(
            id=spec_id,
            name=name,
            description=description,
            requirements=requirements or [],
            properties=[],
            tests=[],
            glossary=glossary or {},
            metadata=metadata or {},
        )
        
        # Store in cache and persist
        self._specifications[spec_id] = spec
        self._save_specification(spec)
        
        return spec
    
    def get_specification(self, spec_id: str) -> Optional[TestSpecification]:
        """Get a specification by ID.
        
        Args:
            spec_id: Specification identifier
            
        Returns:
            TestSpecification object or None
        """
        return self._specifications.get(spec_id)
    
    def list_specifications(self) -> List[TestSpecification]:
        """List all specifications.
        
        Returns:
            List of TestSpecification objects
        """
        return list(self._specifications.values())
    
    def update_specification(
        self,
        spec_id: str,
        updates: SpecificationUpdate
    ) -> Optional[TestSpecification]:
        """Update an existing specification.
        
        Args:
            spec_id: Specification identifier
            updates: Updates to apply
            
        Returns:
            Updated TestSpecification or None if not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Apply updates
        if updates.name is not None:
            spec.name = updates.name
        if updates.description is not None:
            spec.description = updates.description
        if updates.requirements is not None:
            spec.requirements = updates.requirements
        if updates.properties is not None:
            spec.properties = updates.properties
        if updates.glossary is not None:
            spec.glossary = updates.glossary
        if updates.metadata is not None:
            spec.metadata.update(updates.metadata)
        
        # Update timestamp
        spec.updated_at = datetime.now()
        
        # Persist changes
        self._save_specification(spec)
        
        return spec
    
    def delete_specification(self, spec_id: str) -> bool:
        """Delete a specification.
        
        Args:
            spec_id: Specification identifier
            
        Returns:
            True if deleted, False if not found
        """
        if spec_id not in self._specifications:
            return False
        
        # Remove from cache
        del self._specifications[spec_id]
        
        # Remove from storage
        spec_file = self.storage_path / f"{spec_id}.yaml"
        if spec_file.exists():
            spec_file.unlink()
        
        return True
    
    def add_requirement(
        self,
        spec_id: str,
        requirement_text: str
    ) -> Optional[ParsedRequirement]:
        """Add a requirement to a specification.
        
        Args:
            spec_id: Specification identifier
            requirement_text: EARS-formatted requirement text
            
        Returns:
            ParsedRequirement or None if spec not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Parse the requirement
        req = self._parser.parse_requirement(requirement_text)
        
        # Add to specification
        spec.requirements.append(req)
        spec.updated_at = datetime.now()
        
        # Persist
        self._save_specification(spec)
        
        return req
    
    def remove_requirement(self, spec_id: str, req_id: str) -> Optional[TestSpecification]:
        """Remove a requirement from a specification.
        
        Args:
            spec_id: Specification identifier
            req_id: Requirement identifier
            
        Returns:
            Updated TestSpecification or None if not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Find and remove requirement
        for i, req in enumerate(spec.requirements):
            if req.id == req_id:
                spec.requirements.pop(i)
                spec.updated_at = datetime.now()
                self._save_specification(spec)
                return spec
        
        return None
    
    def add_requirement(
        self,
        spec_id: str,
        requirement: ParsedRequirement
    ) -> Optional[TestSpecification]:
        """Add a parsed requirement to a specification.
        
        Args:
            spec_id: Specification identifier
            requirement: ParsedRequirement object
            
        Returns:
            Updated TestSpecification or None if spec not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Add to specification
        spec.requirements.append(requirement)
        spec.updated_at = datetime.now()
        
        # Persist
        self._save_specification(spec)
        
        return spec
    
    def add_properties(
        self,
        spec_id: str,
        properties: List[CorrectnessProperty]
    ) -> Optional[TestSpecification]:
        """Add properties to a specification.
        
        Args:
            spec_id: Specification identifier
            properties: List of CorrectnessProperty objects
            
        Returns:
            Updated TestSpecification or None if spec not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Add properties (avoid duplicates by ID)
        existing_ids = {p.id for p in spec.properties}
        for prop in properties:
            if prop.id not in existing_ids:
                spec.properties.append(prop)
                existing_ids.add(prop.id)
        
        spec.updated_at = datetime.now()
        self._save_specification(spec)
        
        return spec
    
    def remove_property(self, spec_id: str, prop_id: str) -> Optional[TestSpecification]:
        """Remove a property from a specification.
        
        Args:
            spec_id: Specification identifier
            prop_id: Property identifier
            
        Returns:
            Updated TestSpecification or None if not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Find and remove property
        for i, prop in enumerate(spec.properties):
            if prop.id == prop_id:
                spec.properties.pop(i)
                spec.updated_at = datetime.now()
                self._save_specification(spec)
                return spec
        
        return None
    
    def add_tests(
        self,
        spec_id: str,
        tests: List[GeneratedTest]
    ) -> Optional[TestSpecification]:
        """Add tests to a specification.
        
        Args:
            spec_id: Specification identifier
            tests: List of GeneratedTest objects
            
        Returns:
            Updated TestSpecification or None if spec not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Add tests (avoid duplicates by ID)
        existing_ids = {t.id for t in spec.tests}
        for test in tests:
            if test.id not in existing_ids:
                spec.tests.append(test)
                existing_ids.add(test.id)
        
        spec.updated_at = datetime.now()
        self._save_specification(spec)
        
        return spec
    
    def remove_test(self, spec_id: str, test_id: str) -> Optional[TestSpecification]:
        """Remove a test from a specification.
        
        Args:
            spec_id: Specification identifier
            test_id: Test identifier
            
        Returns:
            Updated TestSpecification or None if not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        # Find and remove test
        for i, test in enumerate(spec.tests):
            if test.id == test_id:
                spec.tests.pop(i)
                spec.updated_at = datetime.now()
                self._save_specification(spec)
                return spec
        
        return None
    
    async def generate_properties(self, spec_id: str) -> List[CorrectnessProperty]:
        """Generate properties for all requirements in a specification.
        
        Args:
            spec_id: Specification identifier
            
        Returns:
            List of generated CorrectnessProperty objects
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return []
        
        properties = []
        for req in spec.requirements:
            req_properties = await self._property_generator.generate_properties(req)
            properties.extend(req_properties)
        
        # Update specification
        spec.properties = properties
        spec.updated_at = datetime.now()
        self._save_specification(spec)
        
        return properties
    
    def generate_tests(self, spec_id: str) -> List[GeneratedTest]:
        """Generate tests for all properties in a specification.
        
        Args:
            spec_id: Specification identifier
            
        Returns:
            List of generated GeneratedTest objects
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return []
        
        tests = []
        for prop in spec.properties:
            test = self._test_generator.generate_test(prop)
            tests.append(test)
        
        # Update specification
        spec.tests = tests
        spec.updated_at = datetime.now()
        self._save_specification(spec)
        
        return tests
    
    async def regenerate_tests(self, spec_id: str) -> List[GeneratedTest]:
        """Regenerate all tests for a specification.
        
        This regenerates properties from requirements, then tests from properties.
        
        Args:
            spec_id: Specification identifier
            
        Returns:
            List of regenerated tests
        """
        # First regenerate properties
        await self.generate_properties(spec_id)
        
        # Then regenerate tests
        return self.generate_tests(spec_id)
    
    def export_specification(
        self,
        spec_id: str,
        format: str = "yaml"
    ) -> Optional[str]:
        """Export specification to a format.
        
        Args:
            spec_id: Specification identifier
            format: Export format (yaml, json, markdown, html)
            
        Returns:
            Exported content or None if not found
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            return None
        
        if format == "yaml":
            return self._export_yaml(spec)
        elif format == "json":
            return self._export_json(spec)
        elif format == "markdown":
            return self._export_markdown(spec)
        elif format == "html":
            return self._export_html(spec)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_specification(
        self,
        content: str,
        format: str = "yaml"
    ) -> TestSpecification:
        """Import a specification from content.
        
        Args:
            content: Specification content
            format: Content format (yaml, json)
            
        Returns:
            Imported TestSpecification
        """
        if format == "yaml":
            data = yaml.safe_load(content)
        elif format == "json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        spec = TestSpecification.from_dict(data)
        
        # Store in cache and persist
        self._specifications[spec.id] = spec
        self._save_specification(spec)
        
        return spec
    
    def _save_specification(self, spec: TestSpecification) -> None:
        """Save a specification to storage.
        
        Args:
            spec: TestSpecification to save
        """
        spec_file = self.storage_path / f"{spec.id}.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(spec.to_dict(), f, default_flow_style=False)
    
    def _load_specifications(self) -> None:
        """Load all specifications from storage."""
        for spec_file in self.storage_path.glob("*.yaml"):
            try:
                with open(spec_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:
                        spec = TestSpecification.from_dict(data)
                        self._specifications[spec.id] = spec
            except Exception as e:
                print(f"Warning: Failed to load {spec_file}: {e}")
    
    def _export_yaml(self, spec: TestSpecification) -> str:
        """Export specification to YAML."""
        return yaml.dump(spec.to_dict(), default_flow_style=False)
    
    def _export_json(self, spec: TestSpecification) -> str:
        """Export specification to JSON."""
        return json.dumps(spec.to_dict(), indent=2)
    
    def _export_markdown(self, spec: TestSpecification) -> str:
        """Export specification to Markdown."""
        lines = [
            f"# {spec.name}",
            "",
            f"**Version:** {spec.version}",
            f"**Created:** {spec.created_at.isoformat()}",
            f"**Updated:** {spec.updated_at.isoformat()}",
            "",
            "## Description",
            "",
            spec.description,
            "",
            "## Requirements",
            "",
        ]
        
        for req in spec.requirements:
            lines.append(f"### {req.id}")
            lines.append("")
            lines.append(f"**Pattern:** {req.pattern.value}")
            lines.append("")
            lines.append(f"> {req.text}")
            lines.append("")
            if req.trigger:
                lines.append(f"- **Trigger:** {req.trigger}")
            if req.state:
                lines.append(f"- **State:** {req.state}")
            lines.append(f"- **System:** {req.system}")
            lines.append(f"- **Response:** {req.response}")
            lines.append("")
        
        if spec.properties:
            lines.extend([
                "## Correctness Properties",
                "",
            ])
            for prop in spec.properties:
                lines.append(f"### {prop.name}")
                lines.append("")
                lines.append(f"**Pattern:** {prop.pattern.value}")
                lines.append("")
                lines.append(f"**Universal Quantifier:** {prop.universal_quantifier}")
                lines.append("")
                lines.append(f"**Property:** {prop.property_statement}")
                lines.append("")
                lines.append(f"**Requirements:** {', '.join(prop.requirement_ids)}")
                lines.append("")
        
        if spec.tests:
            lines.extend([
                "## Generated Tests",
                "",
            ])
            for test in spec.tests:
                lines.append(f"### {test.name}")
                lines.append("")
                lines.append(f"- **Property:** {test.property_id}")
                lines.append(f"- **Requirements:** {', '.join(test.requirement_ids)}")
                lines.append(f"- **Iterations:** {test.iterations}")
                lines.append("")
        
        if spec.glossary:
            lines.extend([
                "## Glossary",
                "",
            ])
            for term, definition in spec.glossary.items():
                lines.append(f"- **{term}:** {definition}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _export_html(self, spec: TestSpecification) -> str:
        """Export specification to HTML."""
        # Convert markdown to basic HTML
        md_content = self._export_markdown(spec)
        
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{spec.name}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 1px solid #ccc; }",
            "h3 { color: #888; }",
            "blockquote { background: #f9f9f9; border-left: 4px solid #ccc; padding: 10px; margin: 10px 0; }",
            "code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }",
            "pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }",
            ".metadata { color: #666; font-size: 0.9em; }",
            "</style>",
            "</head>",
            "<body>",
        ]
        
        # Simple markdown to HTML conversion
        in_code_block = False
        for line in md_content.split('\n'):
            if line.startswith('```'):
                if in_code_block:
                    html_lines.append("</pre>")
                    in_code_block = False
                else:
                    html_lines.append("<pre>")
                    in_code_block = True
            elif in_code_block:
                html_lines.append(line)
            elif line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('> '):
                html_lines.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.startswith('- '):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith('**') and ':**' in line:
                # Metadata line
                html_lines.append(f"<p class='metadata'>{line}</p>")
            elif line:
                html_lines.append(f"<p>{line}</p>")
        
        html_lines.extend([
            "</body>",
            "</html>",
        ])
        
        return '\n'.join(html_lines)


# Convenience functions

def create_specification(
    name: str,
    description: str = "",
    storage_path: Optional[str] = None
) -> TestSpecification:
    """Create a new specification.
    
    Args:
        name: Specification name
        description: Specification description
        storage_path: Optional storage path
        
    Returns:
        Created TestSpecification
    """
    manager = SpecificationManager(storage_path)
    return manager.create_specification(name, description)


def load_specification(
    spec_id: str,
    storage_path: Optional[str] = None
) -> Optional[TestSpecification]:
    """Load a specification by ID.
    
    Args:
        spec_id: Specification identifier
        storage_path: Optional storage path
        
    Returns:
        TestSpecification or None
    """
    manager = SpecificationManager(storage_path)
    return manager.get_specification(spec_id)
