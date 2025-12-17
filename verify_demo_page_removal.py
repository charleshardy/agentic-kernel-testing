#!/usr/bin/env python3
"""
Verify that the Kernel Test Driver Generation Demo page has been removed
"""

import os

def verify_demo_removal():
    """Verify the demo page has been completely removed"""
    
    print("🔍 VERIFYING KERNEL DRIVER DEMO PAGE REMOVAL")
    print("=" * 60)
    
    success = True
    
    # Check if the demo component file is deleted
    demo_file = 'dashboard/src/components/KernelDriverDemo.tsx'
    if not os.path.exists(demo_file):
        print("✅ KernelDriverDemo.tsx file successfully deleted")
    else:
        print("❌ KernelDriverDemo.tsx file still exists")
        success = False
    
    # Check App.tsx for removed import and route
    try:
        with open('dashboard/src/App.tsx', 'r') as f:
            app_content = f.read()
            
        if 'KernelDriverDemo' not in app_content:
            print("✅ KernelDriverDemo import removed from App.tsx")
        else:
            print("❌ KernelDriverDemo import still exists in App.tsx")
            success = False
            
        if '/kernel-driver-demo' not in app_content:
            print("✅ Kernel driver demo route removed from App.tsx")
        else:
            print("❌ Kernel driver demo route still exists in App.tsx")
            success = False
            
    except Exception as e:
        print(f"❌ Error reading App.tsx: {e}")
        success = False
    
    # Check DashboardLayout.tsx for removed menu item
    try:
        with open('dashboard/src/components/Layout/DashboardLayout.tsx', 'r') as f:
            layout_content = f.read()
            
        if 'Kernel Driver Demo' not in layout_content:
            print("✅ Kernel Driver Demo menu item removed from DashboardLayout.tsx")
        else:
            print("❌ Kernel Driver Demo menu item still exists in DashboardLayout.tsx")
            success = False
            
        if '/kernel-driver-demo' not in layout_content:
            print("✅ Kernel driver demo route removed from menu")
        else:
            print("❌ Kernel driver demo route still exists in menu")
            success = False
            
    except Exception as e:
        print(f"❌ Error reading DashboardLayout.tsx: {e}")
        success = False
    
    return success

def main():
    """Main verification function"""
    
    print("🚀 KERNEL DRIVER DEMO PAGE REMOVAL VERIFICATION")
    print("=" * 70)
    
    success = verify_demo_removal()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 KERNEL DRIVER DEMO PAGE REMOVAL SUCCESSFUL!")
        print("\n📋 CHANGES CONFIRMED:")
        print("   ✅ Deleted KernelDriverDemo.tsx component file")
        print("   ✅ Removed import from App.tsx")
        print("   ✅ Removed route from App.tsx")
        print("   ✅ Removed menu item from DashboardLayout.tsx")
        print("   ✅ Removed route reference from navigation")
        print("\n🌐 REMAINING NAVIGATION STRUCTURE:")
        print("   • Dashboard")
        print("   • Test Cases")
        print("   • Test Execution")
        print("   • Test Results")
        print("   • Coverage Analysis")
        print("   • Performance")
        print("   • Settings")
        print("\n🔧 MANUAL VERIFICATION:")
        print("   • Refresh the application")
        print("   • Check that 'Kernel Driver Demo' is no longer in the sidebar")
        print("   • Verify /kernel-driver-demo route returns 404 or redirects")
        print("   • Confirm all other navigation items still work")
    else:
        print("❌ DEMO PAGE REMOVAL VERIFICATION FAILED")
        print("   Please check the errors above and fix any remaining references")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)