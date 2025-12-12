def test_basic():
    assert True

def test_imports():
    try:
        import pytest
        import hypothesis
        print("Basic imports work")
        assert True
    except ImportError as e:
        print(f"Import error: {e}")
        assert False