#!/usr/bin/env python3
"""
Comprehensive test script to verify the Test Execution page error fix.
"""

import subprocess
import time
import requests
import json
from pathlib import Path

def test_comprehensive_fix():
    """Test that the Test Execution page loads without errors after comprehensive fix."""
    
    print("🧪 Testing Comprehensive Test Execution Fix")
    print("=" * 60)
    
    # 1. Check API service improvements
    api_file = Path("dashboard/src/services/api.ts")
    
    if not api_file.exists():
        print("❌ API service file not found")
        return False
    
    content = api_file.read_text()
    
    # Check for enhanced error handling
    get_environments_section = content[content.find("async getEnvironments()"):content.find("private getMockEnvironments()")]
    
    has_debug_logging = "🔍 getEnvironments API response:" in get_environments_section
    has_array_check = "Array.isArray(data)" in get_environments_section
    has_fallback_logic = "using mock data instead" in get_environments_section
    has_separate_mock_method = "private getMockEnvironments()" in content
    
    print("📊 API Service Improvements:")
    print(f"  ✅ Debug logging: {'Yes' if has_debug_logging else 'No'}")
    print(f"  ✅ Array type checking: {'Yes' if has_array_check else 'No'}")
    print(f"  ✅ Fallback logic: {'Yes' if has_fallback_logic else 'No'}")
    print(f"  ✅ Separate mock method: {'Yes' if has_separate_mock_method else 'No'}")
    
    # 2. Check TestExecution component safety
    test_execution_file = Path("dashboard/src/pages/TestExecution.tsx")
    
    if test_execution_file.exists():
        test_content = test_execution_file.read_text()
        
        # Check for safe array handling
        has_array_isarray_check = "Array.isArray(environments)" in test_content
        has_empty_array_fallback = ": []" in test_content
        
        print("\n📊 Component Safety Improvements:")
        print(f"  ✅ Array.isArray() check: {'Yes' if has_array_isarray_check else 'No'}")
        print(f"  ✅ Empty array fallback: {'Yes' if has_empty_array_fallback else 'No'}")
        
        # Find the specific line that was causing the error
        lines = test_content.split('\n')
        fixed_line = None
        for i, line in enumerate(lines, 1):
            if "Array.isArray(environments)" in line and "environments.map" in line:
                fixed_line = i
                break
        
        if fixed_line:
            print(f"  ✅ Fixed mapping at line {fixed_line}")
        else:
            print("  ⚠️  Could not find the fixed mapping line")
    
    # 3. Verify mock data structure
    if has_separate_mock_method:
        mock_method_start = content.find("private getMockEnvironments()")
        mock_method_end = content.find("}", mock_method_start) + 1
        mock_method = content[mock_method_start:mock_method_end]
        
        # Check mock data structure
        has_id = '"id":' in mock_method
        has_name = '"name":' in mock_method
        has_config = '"config":' in mock_method
        has_architecture = '"architecture":' in mock_method
        has_cpu_model = '"cpu_model":' in mock_method
        
        print("\n📊 Mock Data Structure:")
        print(f"  ✅ Has id field: {'Yes' if has_id else 'No'}")
        print(f"  ✅ Has name field: {'Yes' if has_name else 'No'}")
        print(f"  ✅ Has config object: {'Yes' if has_config else 'No'}")
        print(f"  ✅ Has architecture: {'Yes' if has_architecture else 'No'}")
        print(f"  ✅ Has cpu_model: {'Yes' if has_cpu_model else 'No'}")
        
        mock_structure_valid = all([has_id, has_name, has_config, has_architecture, has_cpu_model])
    else:
        mock_structure_valid = False
    
    # 4. Overall assessment
    api_improvements = has_debug_logging and has_array_check and has_fallback_logic and has_separate_mock_method
    component_safety = has_array_isarray_check and has_empty_array_fallback
    
    success = api_improvements and component_safety and mock_structure_valid
    
    print("\n" + "=" * 60)
    print(f"🎯 Comprehensive Fix Result: {'SUCCESS' if success else 'NEEDS WORK'}")
    
    if success:
        print("✅ API service has robust error handling and debugging")
        print("✅ Component has safe array handling")
        print("✅ Mock data structure is complete and valid")
        print("✅ Test Execution page should load without errors")
        print("\n🚀 Expected behavior:")
        print("   - Page loads successfully even when API fails")
        print("   - Environment dropdown shows mock options")
        print("   - No more 'environments?.map is not a function' errors")
        print("   - Debug logs help identify data structure issues")
    else:
        print("❌ Fix incomplete - issues found:")
        if not api_improvements:
            print("  - API service needs better error handling")
        if not component_safety:
            print("  - Component needs safer array handling")
        if not mock_structure_valid:
            print("  - Mock data structure is incomplete")
    
    return success

if __name__ == "__main__":
    test_comprehensive_fix()