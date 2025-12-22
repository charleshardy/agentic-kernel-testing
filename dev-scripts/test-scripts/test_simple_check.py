#!/usr/bin/env python3
"""
Simple test to check if basic imports work without pytest
"""

def test_basic_imports():
    """Test basic imports that might be causing issues"""
    try:
        print("Testing basic imports...")
        
        # Test config imports
        from config.settings import Settings
        print("✅ Settings import successful")
        
        # Test API imports
        from api.models import TestResult
        print("✅ API models import successful")
        
        # Test database imports  
        from database.models import TestResultModel
        print("✅ Database models import successful")
        
        # Test AI generator imports
        from ai_generator.test_generator import ITestGenerator
        print("✅ AI generator import successful")
        
        print("All basic imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    exit(0 if success else 1)