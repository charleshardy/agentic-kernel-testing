"""Minimal test to check pytest functionality."""

def test_simple():
    """Simple test that should always pass."""
    assert 1 + 1 == 2

def test_import():
    """Test that imports work in pytest context."""
    import sys
    sys.path.insert(0, '.')
    from ai_generator.models import TestCase, TestType
    
    test = TestCase(
        id="test_001",
        name="Test",
        description="Test",
        test_type=TestType.UNIT,
        target_subsystem="test"
    )
    assert test.id == "test_001"