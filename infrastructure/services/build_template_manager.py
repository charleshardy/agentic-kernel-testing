"""
Build Template Manager

Manages saving, loading, and deleting build configuration templates.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from infrastructure.models.build_template import (
    BuildTemplate,
    BuildTemplateCreate,
    BuildTemplateUpdate
)


class BuildTemplateManager:
    """
    Manages build configuration templates with file-based persistence.
    
    Templates are stored as JSON files in the infrastructure_state/build_templates/ directory.
    """
    
    def __init__(self, storage_dir: str = "infrastructure_state/build_templates"):
        """
        Initialize the build template manager.
        
        Args:
            storage_dir: Directory to store template files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.storage_dir / "templates.json"
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from disk"""
        if self.templates_file.exists():
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                self.templates: Dict[str, BuildTemplate] = {
                    tid: BuildTemplate(**tdata) for tid, tdata in data.items()
                }
        else:
            self.templates = {}
    
    def _save_templates(self) -> None:
        """Save templates to disk"""
        data = {tid: template.dict() for tid, template in self.templates.items()}
        with open(self.templates_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_template(self, template_data: BuildTemplateCreate) -> BuildTemplate:
        """
        Create a new build template.
        
        Args:
            template_data: Template creation data
            
        Returns:
            Created template
        """
        template_id = str(uuid.uuid4())
        template = BuildTemplate(
            id=template_id,
            **template_data.dict()
        )
        self.templates[template_id] = template
        self._save_templates()
        return template
    
    def get_template(self, template_id: str) -> Optional[BuildTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[BuildTemplate]:
        """
        List all templates.
        
        Returns:
            List of all templates
        """
        return list(self.templates.values())
    
    def update_template(
        self,
        template_id: str,
        update_data: BuildTemplateUpdate
    ) -> Optional[BuildTemplate]:
        """
        Update an existing template.
        
        Args:
            template_id: Template ID
            update_data: Fields to update
            
        Returns:
            Updated template if found, None otherwise
        """
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(template, key, value)
        
        template.updated_at = datetime.utcnow().isoformat()
        self._save_templates()
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
            return True
        return False


# Global instance
_template_manager: Optional[BuildTemplateManager] = None


def get_template_manager() -> BuildTemplateManager:
    """Get the global build template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = BuildTemplateManager()
    return _template_manager
