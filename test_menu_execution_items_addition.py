#!/usr/bin/env python3
"""
Test script to verify both Test Execution menu items are added correctly.
"""

import subprocess
import time
import requests
import json
from pathlib import Path

def test_menu_execution_items():
    """Test that both Test Execution and Test Execution Debug menu items exist."""
    
    print("🧪 Testing Menu Execution Items Addition")
    print("=" * 50)
    
    # Read the DashboardLayout file
    layout_file = Path("dashboard/src/components/Layout/DashboardLayout.tsx")
    
    if not layout_file.exists():
        print("❌ DashboardLayout.tsx not found")
        return False
    
    content = layout_file.read_text()
    
    # Check for both menu items
    test_execution_found = "key: '/test-execution'" in content and "label: 'Test Execution'" in content
    test_execution_debug_found = "key: '/test-execution-debug'" in content and "label: 'Test Execution Debug'" in content
    
    print(f"✅ Test Execution menu item: {'Found' if test_execution_found else 'Missing'}")
    print(f"✅ Test Execution Debug menu item: {'Found' if test_execution_debug_found else 'Missing'}")
    
    # Verify they are separate items (not the same)
    execution_lines = [line.strip() for line in content.split('\n') if "key: '/test-execution" in line]
    print(f"📊 Found {len(execution_lines)} test execution menu items:")
    for i, line in enumerate(execution_lines, 1):
        print(f"   {i}. {line}")
    
    # Check menu order
    menu_items_section = content[content.find("const menuItems = ["):content.find("]", content.find("const menuItems = ["))]
    
    test_execution_pos = menu_items_section.find("'/test-execution',")
    test_execution_debug_pos = menu_items_section.find("'/test-execution-debug',")
    
    if test_execution_pos != -1 and test_execution_debug_pos != -1:
        if test_execution_pos < test_execution_debug_pos:
            print("✅ Menu order: Test Execution appears before Test Execution Debug")
        else:
            print("⚠️  Menu order: Test Execution Debug appears before Test Execution")
    
    # Verify both routes exist in App.tsx
    app_file = Path("dashboard/src/App.tsx")
    if app_file.exists():
        app_content = app_file.read_text()
        
        test_execution_route = 'path="/test-execution"' in app_content
        test_execution_debug_route = 'path="/test-execution-debug"' in app_content
        
        print(f"✅ /test-execution route: {'Found' if test_execution_route else 'Missing'}")
        print(f"✅ /test-execution-debug route: {'Found' if test_execution_debug_route else 'Missing'}")
    
    success = test_execution_found and test_execution_debug_found and len(execution_lines) == 2
    
    print("\n" + "=" * 50)
    print(f"🎯 Menu Update Result: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("✅ Both Test Execution menu items added successfully")
        print("✅ Users can now access both regular and debug execution pages")
    else:
        print("❌ Menu update incomplete - check the implementation")
    
    return success

if __name__ == "__main__":
    test_menu_execution_items()