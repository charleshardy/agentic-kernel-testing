"""Property Generator for Agentic AI Test Requirements.

Generates correctness properties from parsed EARS requirements.
Properties are universally quantified statements that can be
verified through property-based testing.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import (
    EARSPattern,
    ParsedRequirement,
    PropertyPattern,
    CorrectnessProperty,
)


class PropertyGenerator:
    """Generates correctness properties from EARS requirements.
    
    Maps EARS patterns to property patterns and generates
    universally quantified properties suitable for property-based testing.
    """
    
    # Mapping from EARS patterns to likely property patterns
    PATTERN_MAPPING = {
        EARSPattern.UBIQUITOUS: [PropertyPattern.INVARIANT],
        EARSPattern.EVENT_DRIVEN: [PropertyPattern.INVARIANT, PropertyPattern.METAMORPHIC],
        EARSPattern.STATE_DRIVEN: [PropertyPattern.INVARIANT],
        EARSPattern.UNWANTED: [PropertyPattern.ERROR_CONDITION],
        EARSPattern.OPTIONAL: [PropertyPattern.INVARIANT],
        EARSPattern.COMPLEX: [PropertyPattern.INVARIANT, PropertyPattern.METAMORPHIC],
    }
    
    # Keywords that suggest specific property patterns
    PATTERN_KEYWORDS = {
        PropertyPattern.ROUND_TRIP: [
            'parse', 'serialize', 'encode', 'decode', 'convert',
            'format', 'transform', 'marshal', 'unmarshal', 'store', 'load',
        ],
        PropertyPattern.IDEMPOTENCE: [
            'idempotent', 'same result', 'no additional effect',
            'repeated', 'multiple times', 'again',
        ],
        PropertyPattern.METAMORPHIC: [
            'filter', 'sort', 'search', 'find', 'select',
            'greater', 'less', 'more', 'fewer',
        ],
        PropertyPattern.CONFLUENCE: [
            'order', 'sequence', 'independent', 'commutative',
        ],
    }
    
    def __init__(self, llm_provider: Optional[Any] = None):
        """Initialize the property generator.
        
        Args:
            llm_provider: Optional LLM provider for intelligent generation
        """
        self.llm_provider = llm_provider
    
    def generate_properties(self, req: ParsedRequirement) -> List[CorrectnessProperty]:
        """Generate correctness properties from a requirement.
        
        Args:
            req: ParsedRequirement to generate properties for
            
        Returns:
            List of CorrectnessProperty objects
        """
        properties = []
        
        # Identify the best property pattern
        pattern = self.identify_property_pattern(req)
        
        # Generate the main property
        main_property = self._generate_main_property(req, pattern)
        if main_property:
            properties.append(main_property)
        
        # Generate additional properties based on pattern
        if pattern == PropertyPattern.ROUND_TRIP:
            round_trip = self.generate_round_trip_property(req)
            if round_trip:
                properties.append(round_trip)
        
        # If there's a trigger condition, generate a precondition property
        if req.trigger:
            precondition_prop = self._generate_precondition_property(req)
            if precondition_prop:
                properties.append(precondition_prop)
        
        return properties
    
    def identify_property_pattern(self, req: ParsedRequirement) -> PropertyPattern:
        """Identify the most appropriate property pattern for a requirement.
        
        Args:
            req: ParsedRequirement to analyze
            
        Returns:
            PropertyPattern that best fits the requirement
        """
        text_lower = req.text.lower()
        
        # Check for keyword matches
        for pattern, keywords in self.PATTERN_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return pattern
        
        # Fall back to EARS pattern mapping
        default_patterns = self.PATTERN_MAPPING.get(req.pattern, [PropertyPattern.INVARIANT])
        return default_patterns[0]
    
    def generate_round_trip_property(self, req: ParsedRequirement) -> Optional[CorrectnessProperty]:
        """Generate a round-trip property for serialization requirements.
        
        Args:
            req: ParsedRequirement involving data transformation
            
        Returns:
            CorrectnessProperty for round-trip verification, or None
        """
        # Extract the transformation from the response
        response_lower = req.response.lower()
        
        # Identify the operation pair
        operation_pairs = [
            ('parse', 'format'),
            ('serialize', 'deserialize'),
            ('encode', 'decode'),
            ('marshal', 'unmarshal'),
            ('store', 'load'),
            ('save', 'load'),
            ('write', 'read'),
        ]
        
        operation = None
        for op1, op2 in operation_pairs:
            if op1 in response_lower or op2 in response_lower:
                operation = (op1, op2)
                break
        
        if not operation:
            return None
        
        prop_id = f"PROP-{uuid.uuid4().hex[:8]}"
        
        return CorrectnessProperty(
            id=prop_id,
            name=f"Round-trip {operation[0]}/{operation[1]}",
            description=f"Verifies that {operation[0]} followed by {operation[1]} preserves data",
            pattern=PropertyPattern.ROUND_TRIP,
            universal_quantifier=f"For any valid input data",
            property_statement=f"{operation[1]}({operation[0]}(x)) == x",
            requirement_ids=[req.id],
            input_types=["Any"],
            preconditions=["Input is valid according to schema"],
            postconditions=["Output equals original input"],
        )
    
    def generate_invariant_property(self, req: ParsedRequirement) -> Optional[CorrectnessProperty]:
        """Generate an invariant property for state change requirements.
        
        Args:
            req: ParsedRequirement involving state changes
            
        Returns:
            CorrectnessProperty for invariant verification, or None
        """
        prop_id = f"PROP-{uuid.uuid4().hex[:8]}"
        
        # Extract what should be preserved
        invariant_keywords = ['maintain', 'preserve', 'keep', 'ensure', 'guarantee']
        response_lower = req.response.lower()
        
        invariant_desc = "system state"
        for keyword in invariant_keywords:
            if keyword in response_lower:
                # Try to extract what follows the keyword
                idx = response_lower.find(keyword)
                invariant_desc = req.response[idx:idx+50].strip()
                break
        
        return CorrectnessProperty(
            id=prop_id,
            name=f"Invariant: {req.system}",
            description=f"Verifies that {invariant_desc} is preserved",
            pattern=PropertyPattern.INVARIANT,
            universal_quantifier=f"For any operation on {req.system}",
            property_statement=f"invariant(before) implies invariant(after)",
            requirement_ids=[req.id],
            input_types=[req.system],
            preconditions=[f"{req.system} is in valid state"],
            postconditions=[f"Invariant is preserved"],
        )
    
    def _generate_main_property(self, req: ParsedRequirement, pattern: PropertyPattern) -> CorrectnessProperty:
        """Generate the main property for a requirement.
        
        Args:
            req: ParsedRequirement to generate property for
            pattern: PropertyPattern to use
            
        Returns:
            CorrectnessProperty object
        """
        prop_id = f"PROP-{uuid.uuid4().hex[:8]}"
        
        # Build the universal quantifier
        if req.trigger:
            quantifier = f"For any {req.system} and any trigger where {req.trigger}"
        elif req.state:
            quantifier = f"For any {req.system} while {req.state}"
        else:
            quantifier = f"For any {req.system}"
        
        # Build the property statement
        property_statement = f"the {req.system} SHALL {req.response}"
        
        # Build preconditions
        preconditions = []
        if req.trigger:
            preconditions.append(f"Trigger: {req.trigger}")
        if req.state:
            preconditions.append(f"State: {req.state}")
        if req.options:
            preconditions.append(f"Option: {req.options}")
        
        return CorrectnessProperty(
            id=prop_id,
            name=f"Property: {req.system} - {req.pattern.value}",
            description=f"Verifies: {req.text[:100]}...",
            pattern=pattern,
            universal_quantifier=quantifier,
            property_statement=property_statement,
            requirement_ids=[req.id],
            input_types=[req.system],
            preconditions=preconditions,
            postconditions=[req.response],
        )
    
    def _generate_precondition_property(self, req: ParsedRequirement) -> Optional[CorrectnessProperty]:
        """Generate a property for precondition verification.
        
        Args:
            req: ParsedRequirement with trigger condition
            
        Returns:
            CorrectnessProperty for precondition verification, or None
        """
        if not req.trigger:
            return None
        
        prop_id = f"PROP-{uuid.uuid4().hex[:8]}"
        
        return CorrectnessProperty(
            id=prop_id,
            name=f"Precondition: {req.trigger[:30]}...",
            description=f"Verifies behavior when trigger condition is met",
            pattern=PropertyPattern.METAMORPHIC,
            universal_quantifier=f"For any {req.system} where {req.trigger}",
            property_statement=f"trigger({req.trigger}) implies response({req.response})",
            requirement_ids=[req.id],
            input_types=[req.system, "trigger_condition"],
            preconditions=[req.trigger],
            postconditions=[req.response],
        )
    
    def annotate_property(self, prop: CorrectnessProperty, req_id: str) -> CorrectnessProperty:
        """Annotate a property with requirement traceability.
        
        Args:
            prop: CorrectnessProperty to annotate
            req_id: Requirement ID for traceability
            
        Returns:
            Annotated CorrectnessProperty
        """
        if req_id not in prop.requirement_ids:
            prop.requirement_ids.append(req_id)
        
        prop.metadata['annotated_at'] = datetime.now().isoformat()
        prop.metadata['validates'] = f"Requirements {', '.join(prop.requirement_ids)}"
        
        return prop
    
    def generate_from_specification(self, requirements: List[ParsedRequirement]) -> List[CorrectnessProperty]:
        """Generate properties for all requirements in a specification.
        
        Args:
            requirements: List of ParsedRequirement objects
            
        Returns:
            List of CorrectnessProperty objects
        """
        all_properties = []
        
        for req in requirements:
            properties = self.generate_properties(req)
            all_properties.extend(properties)
        
        return all_properties


def generate_properties_from_requirement(req: ParsedRequirement) -> List[CorrectnessProperty]:
    """Convenience function to generate properties from a requirement.
    
    Args:
        req: ParsedRequirement to generate properties for
        
    Returns:
        List of CorrectnessProperty objects
    """
    generator = PropertyGenerator()
    return generator.generate_properties(req)
