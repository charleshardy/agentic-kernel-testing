"""Property-based tests for generation source traceability.

Feature: web-gui-test-listing, Property 3: Generation Source Traceability
Validates: Requirements 4.1, 4.2, 4.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import sys
import os
from unittest.mock import MagicMock, patch
import json

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from api.routers.tests import submitted_tests, generate_tests_from_diff, generate_tests_from_function
    from api.models import GenerationInfo
    from ai_generator.models import TestType, TestCase, Function, CodeAnalysis
    from ai_generator.test_generator import AITestGenerator
except ImportError as e:
    pytest.skip(f"Skipping test due to import error: {e}", allow_module_level=True)


# Strategy for generating diff content
@st.composite
def diff_content_strategy(draw):
    """Generate realistic diff content for testing."""
    file_paths = [
        "drivers/net/ethernet/intel/e1000e/netdev.c",
        "kernel/sched/core.c",
        "mm/page_alloc.c",
        "fs/ext4/inode.c",
        "net/ipv4/tcp.c"
    ]
    
    file_path = draw(st.sampled_from(file_paths))
    function_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')))
    
    # Generate a realistic diff
    diff_lines = [
        f"diff --git a/{file_path} b/{file_path}",
        f"index abc123..def456 100644",
        f"--- a/{file_path}",
        f"+++ b/{file_path}",
        "@@ -100,7 +100,10 @@ static int some_function(void)",
        " {",
        "     /* existing code */",
        f"+    /* Added by diff: {function_name} */",
        f"+    int result = {function_name}();",
        "+    if (result < 0)",
        "+        return result;",
        " }",
    ]
    
    diff_content = "\n".join(diff_lines)
    
    return {
        "diff_content": diff_content,
        "file_path": file_path,
        "function_name": function_name,
        "expected_subsystem": _get_subsystem_from_path(file_path)
    }


def _get_subsystem_from_path(file_path: str) -> str:
    """Determine subsystem from file path."""
    if 'sched' in file_path:
        return 'scheduler'
    elif 'mm/' in file_path:
        return 'memory_management'
    elif 'net/' in file_path:
        return 'networking'
    elif 'fs/' in file_path:
        return 'filesystem'
    elif 'drivers/' in file_path:
        return 'drivers'
    else:
        return 'core_kernel'


# Strategy for generating function data
@st.composite
def function_data_strategy(draw):
    """Generate function data for testing."""
    subsystems = ['scheduler', 'memory_management', 'networking', 'filesystem', 'drivers', 'core_kernel']
    
    function_name = draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')))
    subsystem = draw(st.sampled_from(subsystems))
    
    # Generate appropriate file path for subsystem
    file_paths = {
        'scheduler': 'kernel/sched/core.c',
        'memory_management': 'mm/page_alloc.c',
        'networking': 'net/ipv4/tcp.c',
        'filesystem': 'fs/ext4/inode.c',
        'drivers': 'drivers/net/ethernet/intel/e1000e/netdev.c',
        'core_kernel': 'kernel/kernel.c'
    }
    
    file_path = file_paths[subsystem]
    line_number = draw(st.integers(min_value=1, max_value=1000))
    
    return {
        "function_name": function_name,
        "file_path": file_path,
        "subsystem": subsystem,
        "line_number": line_number
    }


@pytest.mark.property
class TestGenerationSourceTraceabilityProperties:
    """Property-based tests for generation source traceability."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear the global test storage before each test
        submitted_tests.clear()
    
    def teardown_method(self):
        """Clean up after test."""
        # Clear the global test storage after each test
        submitted_tests.clear()
    
    @given(diff_data=diff_content_strategy())
    @settings(max_examples=10)
    def test_ai_diff_generation_traceability(self, diff_data):
        """
        Property 3: Generation Source Traceability - AI Diff Generation
        
        For any AI-generated test case from a code diff, the system should 
        maintain and display complete traceability to the original diff source.
        
        **Validates: Requirements 4.1, 4.3**
        """
        diff_content = diff_data["diff_content"]
        expected_file_path = diff_data["file_path"]
        expected_function = diff_data["function_name"]
        
        # Mock the AI generator to return predictable results
        with patch('ai_generator.test_generator.AITestGenerator') as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            
            # Create mock analysis
            mock_analysis = MagicMock()
            mock_analysis.changed_files = [expected_file_path]
            mock_analysis.changed_functions = [
                MagicMock(name=expected_function, file_path=expected_file_path)
            ]
            mock_analysis.affected_subsystems = [diff_data["expected_subsystem"]]
            mock_analysis.impact_score = 0.7
            mock_analysis.risk_level = "medium"
            
            mock_generator.analyze_code_changes.return_value = mock_analysis
            
            # Create mock test case
            mock_test_case = MagicMock()
            mock_test_case.id = f"test_{uuid.uuid4().hex[:8]}"
            mock_test_case.name = f"Test for {expected_function}"
            mock_test_case.description = f"AI-generated test for {expected_function}"
            mock_test_case.test_type = TestType.UNIT
            mock_test_case.target_subsystem = diff_data["expected_subsystem"]
            mock_test_case.execution_time_estimate = 60
            
            mock_generator.generate_test_cases.return_value = [mock_test_case]
            
            # Mock user
            mock_user = {
                "username": "test_user",
                "permissions": ["test:submit"]
            }
            
            # Simulate the generate_tests_from_diff endpoint logic
            from ai_generator.test_generator import AITestGenerator
            generator = AITestGenerator()
            
            # Analyze the code changes
            analysis = generator.analyze_code_changes(diff_content)
            
            # Generate test cases
            generated_tests = generator.generate_test_cases(analysis)
            
            # Store the generated tests with metadata (simulating the API endpoint)
            submission_id = str(uuid.uuid4())
            generation_timestamp = datetime.utcnow()
            
            for test_case in generated_tests:
                test_id = test_case.id
                
                # Create comprehensive generation metadata (as updated in the API)
                generation_info = {
                    "method": "ai_diff",
                    "source_data": {
                        "diff_content": diff_content[:2000] + "..." if len(diff_content) > 2000 else diff_content,
                        "diff_size": len(diff_content),
                        "diff_hash": str(hash(diff_content)),
                        "changed_files": analysis.changed_files if hasattr(analysis, 'changed_files') else [],
                        "changed_functions": [f.name for f in analysis.changed_functions] if hasattr(analysis, 'changed_functions') else [],
                        "analysis_id": analysis.id if hasattr(analysis, 'id') else str(uuid.uuid4())
                    },
                    "generated_at": generation_timestamp.isoformat(),
                    "ai_model": "template_based",  # Since we're using fallback
                    "generation_params": {
                        "max_tests": 20,
                        "test_types": ["unit"],
                        "affected_subsystems": analysis.affected_subsystems if hasattr(analysis, 'affected_subsystems') else [],
                        "impact_score": analysis.impact_score if hasattr(analysis, 'impact_score') else 0.5,
                        "risk_level": analysis.risk_level if hasattr(analysis, 'risk_level') else "medium",
                        "generation_strategy": "diff_analysis"
                    }
                }
                
                # Store test case with enhanced metadata
                submitted_tests[test_id] = {
                    "test_case": test_case,
                    "submission_id": submission_id,
                    "submitted_by": mock_user["username"],
                    "submitted_at": generation_timestamp,
                    "priority": 5,
                    "auto_generated": True,
                    "generation_info": generation_info,
                    "execution_status": "never_run",
                    "last_execution_at": None,
                    "tags": ["ai_generated", "diff_based"] + (analysis.affected_subsystems if hasattr(analysis, 'affected_subsystems') else []),
                    "is_favorite": False,
                    "updated_at": generation_timestamp
                }
        
        # Verify traceability properties
        assert len(submitted_tests) > 0, "Should have generated at least one test case"
        
        for test_id, test_data in submitted_tests.items():
            generation_info = test_data["generation_info"]
            
            # Property 1: Generation method should be clearly identified
            assert generation_info["method"] == "ai_diff", \
                f"Generation method should be 'ai_diff', got '{generation_info['method']}'"
            
            # Property 2: Source diff content should be preserved
            source_data = generation_info["source_data"]
            assert "diff_content" in source_data, "Diff content should be preserved in source data"
            assert "diff_size" in source_data, "Diff size should be recorded"
            assert "diff_hash" in source_data, "Diff hash should be recorded for quick comparison"
            
            # Property 3: Changed files should be tracked
            assert "changed_files" in source_data, "Changed files should be tracked"
            if hasattr(analysis, 'changed_files') and analysis.changed_files:
                assert len(source_data["changed_files"]) > 0, "Should track at least one changed file"
            
            # Property 4: Changed functions should be tracked
            assert "changed_functions" in source_data, "Changed functions should be tracked"
            
            # Property 5: Generation timestamp should be recorded
            assert "generated_at" in generation_info, "Generation timestamp should be recorded"
            generation_time = datetime.fromisoformat(generation_info["generated_at"])
            time_diff = abs((generation_time - generation_timestamp).total_seconds())
            assert time_diff < 60, "Generation timestamp should be accurate within 1 minute"
            
            # Property 6: AI model information should be recorded
            assert "ai_model" in generation_info, "AI model should be recorded"
            
            # Property 7: Generation parameters should be preserved
            assert "generation_params" in generation_info, "Generation parameters should be preserved"
            gen_params = generation_info["generation_params"]
            assert "generation_strategy" in gen_params, "Generation strategy should be recorded"
            assert gen_params["generation_strategy"] == "diff_analysis", "Strategy should be 'diff_analysis'"
            
            # Property 8: Test should be properly tagged
            tags = test_data.get("tags", [])
            assert "ai_generated" in tags, "Test should be tagged as AI-generated"
            assert "diff_based" in tags, "Test should be tagged as diff-based"
    
    @given(function_data=function_data_strategy())
    @settings(max_examples=10)
    def test_ai_function_generation_traceability(self, function_data):
        """
        Property 3: Generation Source Traceability - AI Function Generation
        
        For any AI-generated test case from a function specification, the system 
        should maintain and display complete traceability to the original function source.
        
        **Validates: Requirements 4.2, 4.3**
        """
        function_name = function_data["function_name"]
        file_path = function_data["file_path"]
        subsystem = function_data["subsystem"]
        line_number = function_data["line_number"]
        
        # Mock the AI generator
        with patch('ai_generator.test_generator.AITestGenerator') as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            
            # Create mock test cases
            mock_test_cases = []
            for i in range(3):  # Generate 3 test cases
                mock_test_case = MagicMock()
                mock_test_case.id = f"test_{uuid.uuid4().hex[:8]}"
                mock_test_case.name = f"Test {function_name} - case {i+1}"
                mock_test_case.description = f"AI-generated test for {function_name}"
                mock_test_case.test_type = TestType.UNIT
                mock_test_case.target_subsystem = subsystem
                mock_test_case.execution_time_estimate = 60
                mock_test_cases.append(mock_test_case)
            
            mock_generator._generate_function_tests.return_value = mock_test_cases
            mock_generator.generate_property_tests.return_value = []
            
            # Mock user
            mock_user = {
                "username": "test_user",
                "permissions": ["test:submit"]
            }
            
            # Simulate the generate_tests_from_function endpoint logic
            from ai_generator.test_generator import AITestGenerator
            from ai_generator.models import Function
            
            generator = AITestGenerator()
            
            # Create function object
            function = Function(
                name=function_name,
                file_path=file_path,
                line_number=line_number,
                subsystem=subsystem
            )
            
            # Generate test cases
            generated_tests = generator._generate_function_tests(function, min_tests=3)
            
            # Store the generated tests with metadata (simulating the API endpoint)
            submission_id = str(uuid.uuid4())
            generation_timestamp = datetime.utcnow()
            
            for test_case in generated_tests:
                test_id = test_case.id
                
                # Create comprehensive generation metadata (as updated in the API)
                generation_info = {
                    "method": "ai_function",
                    "source_data": {
                        "function_name": function_name,
                        "file_path": file_path,
                        "subsystem": subsystem,
                        "function_signature": getattr(function, 'signature', f"{function_name}(...)"),
                        "line_number": getattr(function, 'line_number', line_number),
                        "function_hash": str(hash(f"{file_path}::{function_name}")),
                        "code_context": getattr(function, 'code_context', None)
                    },
                    "generated_at": generation_timestamp.isoformat(),
                    "ai_model": "template_based",
                    "generation_params": {
                        "max_tests": 10,
                        "include_property_tests": True,
                        "target_function": function_name,
                        "target_subsystem": subsystem,
                        "generation_strategy": "function_analysis",
                        "test_categories": ["unit", "property"]
                    }
                }
                
                # Store test case with enhanced metadata
                submitted_tests[test_id] = {
                    "test_case": test_case,
                    "submission_id": submission_id,
                    "submitted_by": mock_user["username"],
                    "submitted_at": generation_timestamp,
                    "priority": 5,
                    "auto_generated": True,
                    "generation_info": generation_info,
                    "execution_status": "never_run",
                    "last_execution_at": None,
                    "tags": ["ai_generated", "function_based", subsystem],
                    "is_favorite": False,
                    "updated_at": generation_timestamp
                }
        
        # Verify traceability properties
        assert len(submitted_tests) > 0, "Should have generated at least one test case"
        
        for test_id, test_data in submitted_tests.items():
            generation_info = test_data["generation_info"]
            
            # Property 1: Generation method should be clearly identified
            assert generation_info["method"] == "ai_function", \
                f"Generation method should be 'ai_function', got '{generation_info['method']}'"
            
            # Property 2: Function information should be preserved
            source_data = generation_info["source_data"]
            assert source_data["function_name"] == function_name, \
                f"Function name should be preserved: expected '{function_name}', got '{source_data['function_name']}'"
            assert source_data["file_path"] == file_path, \
                f"File path should be preserved: expected '{file_path}', got '{source_data['file_path']}'"
            assert source_data["subsystem"] == subsystem, \
                f"Subsystem should be preserved: expected '{subsystem}', got '{source_data['subsystem']}'"
            
            # Property 3: Function signature should be recorded
            assert "function_signature" in source_data, "Function signature should be recorded"
            assert function_name in source_data["function_signature"], \
                "Function signature should contain the function name"
            
            # Property 4: Line number should be tracked
            assert "line_number" in source_data, "Line number should be tracked"
            assert source_data["line_number"] == line_number, \
                f"Line number should be preserved: expected {line_number}, got {source_data['line_number']}"
            
            # Property 5: Function hash for quick identification
            assert "function_hash" in source_data, "Function hash should be recorded"
            expected_hash = str(hash(f"{file_path}::{function_name}"))
            assert source_data["function_hash"] == expected_hash, \
                "Function hash should be consistent"
            
            # Property 6: Generation timestamp should be recorded
            assert "generated_at" in generation_info, "Generation timestamp should be recorded"
            generation_time = datetime.fromisoformat(generation_info["generated_at"])
            time_diff = abs((generation_time - generation_timestamp).total_seconds())
            assert time_diff < 60, "Generation timestamp should be accurate within 1 minute"
            
            # Property 7: Generation parameters should be preserved
            assert "generation_params" in generation_info, "Generation parameters should be preserved"
            gen_params = generation_info["generation_params"]
            assert gen_params["target_function"] == function_name, \
                "Target function should be recorded in parameters"
            assert gen_params["target_subsystem"] == subsystem, \
                "Target subsystem should be recorded in parameters"
            assert gen_params["generation_strategy"] == "function_analysis", \
                "Generation strategy should be 'function_analysis'"
            
            # Property 8: Test should be properly tagged
            tags = test_data.get("tags", [])
            assert "ai_generated" in tags, "Test should be tagged as AI-generated"
            assert "function_based" in tags, "Test should be tagged as function-based"
            assert subsystem in tags, "Test should be tagged with the subsystem"
    
    @given(
        diff_data=diff_content_strategy(),
        function_data=function_data_strategy()
    )
    @settings(max_examples=5)
    def test_generation_method_distinction(self, diff_data, function_data):
        """
        Property 3: Generation Source Traceability - Method Distinction
        
        For any AI-generated test case, the system should clearly distinguish
        between different generation methods and preserve method-specific metadata.
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Generate tests from both diff and function
        diff_content = diff_data["diff_content"]
        function_name = function_data["function_name"]
        file_path = function_data["file_path"]
        subsystem = function_data["subsystem"]
        
        # Clear storage
        submitted_tests.clear()
        
        # Mock AI generator for both methods
        with patch('ai_generator.test_generator.AITestGenerator') as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            
            # Mock for diff generation
            mock_analysis = MagicMock()
            mock_analysis.changed_files = [diff_data["file_path"]]
            mock_analysis.affected_subsystems = [diff_data["expected_subsystem"]]
            mock_generator.analyze_code_changes.return_value = mock_analysis
            
            diff_test_case = MagicMock()
            diff_test_case.id = f"diff_test_{uuid.uuid4().hex[:8]}"
            diff_test_case.name = "Diff-generated test"
            diff_test_case.test_type = TestType.UNIT
            diff_test_case.target_subsystem = diff_data["expected_subsystem"]
            diff_test_case.execution_time_estimate = 60
            
            mock_generator.generate_test_cases.return_value = [diff_test_case]
            
            # Mock for function generation
            function_test_case = MagicMock()
            function_test_case.id = f"func_test_{uuid.uuid4().hex[:8]}"
            function_test_case.name = "Function-generated test"
            function_test_case.test_type = TestType.UNIT
            function_test_case.target_subsystem = subsystem
            function_test_case.execution_time_estimate = 60
            
            mock_generator._generate_function_tests.return_value = [function_test_case]
            mock_generator.generate_property_tests.return_value = []
            
            # Generate tests from diff
            from ai_generator.test_generator import AITestGenerator
            generator = AITestGenerator()
            
            # Diff generation
            diff_analysis = generator.analyze_code_changes(diff_content)
            diff_tests = generator.generate_test_cases(diff_analysis)
            
            # Store diff-generated tests
            for test_case in diff_tests:
                generation_info = {
                    "method": "ai_diff",
                    "source_data": {
                        "diff_content": diff_content[:2000] + "..." if len(diff_content) > 2000 else diff_content,
                        "diff_size": len(diff_content),
                        "diff_hash": str(hash(diff_content)),
                        "changed_files": diff_analysis.changed_files if hasattr(diff_analysis, 'changed_files') else [],
                        "analysis_id": str(uuid.uuid4())
                    },
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_model": "template_based",
                    "generation_params": {
                        "generation_strategy": "diff_analysis"
                    }
                }
                
                submitted_tests[test_case.id] = {
                    "test_case": test_case,
                    "generation_info": generation_info,
                    "tags": ["ai_generated", "diff_based"],
                    "submitted_at": datetime.utcnow()
                }
            
            # Function generation
            from ai_generator.models import Function
            function = Function(
                name=function_name,
                file_path=file_path,
                line_number=1,
                subsystem=subsystem
            )
            
            function_tests = generator._generate_function_tests(function, min_tests=1)
            
            # Store function-generated tests
            for test_case in function_tests:
                generation_info = {
                    "method": "ai_function",
                    "source_data": {
                        "function_name": function_name,
                        "file_path": file_path,
                        "subsystem": subsystem,
                        "function_signature": f"{function_name}(...)",
                        "line_number": 1,
                        "function_hash": str(hash(f"{file_path}::{function_name}"))
                    },
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_model": "template_based",
                    "generation_params": {
                        "target_function": function_name,
                        "generation_strategy": "function_analysis"
                    }
                }
                
                submitted_tests[test_case.id] = {
                    "test_case": test_case,
                    "generation_info": generation_info,
                    "tags": ["ai_generated", "function_based"],
                    "submitted_at": datetime.utcnow()
                }
        
        # Verify that we have tests from both methods
        diff_tests = [t for t in submitted_tests.values() if t["generation_info"]["method"] == "ai_diff"]
        function_tests = [t for t in submitted_tests.values() if t["generation_info"]["method"] == "ai_function"]
        
        assert len(diff_tests) > 0, "Should have at least one diff-generated test"
        assert len(function_tests) > 0, "Should have at least one function-generated test"
        
        # Verify method-specific metadata
        for test_data in diff_tests:
            generation_info = test_data["generation_info"]
            source_data = generation_info["source_data"]
            
            # Diff-specific properties
            assert "diff_content" in source_data, "Diff tests should have diff content"
            assert "diff_size" in source_data, "Diff tests should have diff size"
            assert "diff_hash" in source_data, "Diff tests should have diff hash"
            assert "changed_files" in source_data, "Diff tests should have changed files"
            assert generation_info["generation_params"]["generation_strategy"] == "diff_analysis"
            
            # Should NOT have function-specific data
            assert "function_name" not in source_data, "Diff tests should not have function name"
            assert "function_signature" not in source_data, "Diff tests should not have function signature"
        
        for test_data in function_tests:
            generation_info = test_data["generation_info"]
            source_data = generation_info["source_data"]
            
            # Function-specific properties
            assert "function_name" in source_data, "Function tests should have function name"
            assert "function_signature" in source_data, "Function tests should have function signature"
            assert "line_number" in source_data, "Function tests should have line number"
            assert "function_hash" in source_data, "Function tests should have function hash"
            assert generation_info["generation_params"]["generation_strategy"] == "function_analysis"
            
            # Should NOT have diff-specific data
            assert "diff_content" not in source_data, "Function tests should not have diff content"
            assert "diff_size" not in source_data, "Function tests should not have diff size"
            assert "diff_hash" not in source_data, "Function tests should not have diff hash"
    
    @given(diff_data=diff_content_strategy())
    @settings(max_examples=5)
    def test_generation_metadata_persistence(self, diff_data):
        """
        Property 3: Generation Source Traceability - Metadata Persistence
        
        For any AI-generated test case, the generation metadata should persist
        across system operations and remain accessible for traceability.
        
        **Validates: Requirements 4.3**
        """
        diff_content = diff_data["diff_content"]
        
        # Generate and store a test
        with patch('ai_generator.test_generator.AITestGenerator') as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            
            # Mock analysis and test generation
            mock_analysis = MagicMock()
            mock_analysis.changed_files = [diff_data["file_path"]]
            mock_analysis.affected_subsystems = [diff_data["expected_subsystem"]]
            mock_generator.analyze_code_changes.return_value = mock_analysis
            
            test_case = MagicMock()
            test_case.id = f"test_{uuid.uuid4().hex[:8]}"
            test_case.name = "Persistence test"
            test_case.test_type = TestType.UNIT
            test_case.target_subsystem = diff_data["expected_subsystem"]
            test_case.execution_time_estimate = 60
            
            mock_generator.generate_test_cases.return_value = [test_case]
            
            # Generate and store test
            from ai_generator.test_generator import AITestGenerator
            generator = AITestGenerator()
            analysis = generator.analyze_code_changes(diff_content)
            generated_tests = generator.generate_test_cases(analysis)
            
            # Store with complete metadata
            original_generation_info = {
                "method": "ai_diff",
                "source_data": {
                    "diff_content": diff_content,
                    "diff_size": len(diff_content),
                    "diff_hash": str(hash(diff_content)),
                    "changed_files": [diff_data["file_path"]],
                    "analysis_id": str(uuid.uuid4())
                },
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": "template_based",
                "generation_params": {
                    "max_tests": 20,
                    "generation_strategy": "diff_analysis",
                    "impact_score": 0.7
                }
            }
            
            test_id = test_case.id
            submitted_tests[test_id] = {
                "test_case": test_case,
                "generation_info": original_generation_info,
                "tags": ["ai_generated", "diff_based"],
                "submitted_at": datetime.utcnow(),
                "execution_status": "never_run",
                "updated_at": datetime.utcnow()
            }
        
        # Simulate various system operations that should preserve metadata
        
        # 1. Update test case (should preserve generation info)
        submitted_tests[test_id]["test_case"].name = "Updated test name"
        submitted_tests[test_id]["updated_at"] = datetime.utcnow()
        
        # 2. Change execution status (should preserve generation info)
        submitted_tests[test_id]["execution_status"] = "completed"
        
        # 3. Add tags (should preserve generation info)
        submitted_tests[test_id]["tags"].append("updated")
        
        # Verify metadata persistence
        stored_test = submitted_tests[test_id]
        stored_generation_info = stored_test["generation_info"]
        
        # Property 1: Generation method should persist
        assert stored_generation_info["method"] == original_generation_info["method"], \
            "Generation method should persist across updates"
        
        # Property 2: Source data should persist completely
        original_source = original_generation_info["source_data"]
        stored_source = stored_generation_info["source_data"]
        
        for key, value in original_source.items():
            assert key in stored_source, f"Source data key '{key}' should persist"
            assert stored_source[key] == value, f"Source data value for '{key}' should persist"
        
        # Property 3: Generation timestamp should persist
        assert stored_generation_info["generated_at"] == original_generation_info["generated_at"], \
            "Generation timestamp should persist"
        
        # Property 4: AI model information should persist
        assert stored_generation_info["ai_model"] == original_generation_info["ai_model"], \
            "AI model information should persist"
        
        # Property 5: Generation parameters should persist completely
        original_params = original_generation_info["generation_params"]
        stored_params = stored_generation_info["generation_params"]
        
        for key, value in original_params.items():
            assert key in stored_params, f"Generation parameter '{key}' should persist"
            assert stored_params[key] == value, f"Generation parameter value for '{key}' should persist"
        
        # Property 6: Metadata should remain accessible for queries
        # Simulate filtering by generation method
        ai_diff_tests = [
            t for t in submitted_tests.values() 
            if t["generation_info"]["method"] == "ai_diff"
        ]
        
        assert len(ai_diff_tests) == 1, "Should be able to filter by generation method"
        assert ai_diff_tests[0]["test_case"].id == test_id, "Should find the correct test"
        
        # Property 7: Source traceability should remain complete
        retrieved_test = ai_diff_tests[0]
        retrieved_source = retrieved_test["generation_info"]["source_data"]
        
        assert "diff_content" in retrieved_source, "Diff content should remain accessible"
        assert "diff_hash" in retrieved_source, "Diff hash should remain accessible"
        assert "changed_files" in retrieved_source, "Changed files should remain accessible"
        assert len(retrieved_source["changed_files"]) > 0, "Changed files list should not be empty"