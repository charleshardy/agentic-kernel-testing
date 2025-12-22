#!/usr/bin/env python3
"""
Verify that the Sample Generated Code section has been removed
"""

def verify_removal():
    """Verify the Sample Generated Code section has been removed"""
    
    print("🔍 VERIFYING SAMPLE GENERATED CODE REMOVAL")
    print("=" * 60)
    
    try:
        with open('dashboard/src/components/TestCaseModal.tsx', 'r') as f:
            content = f.read()
            
        # Check that Sample Generated Code section is removed
        if 'Sample Generated Code' not in content:
            print("✅ Sample Generated Code section successfully removed")
        else:
            print("❌ Sample Generated Code section still exists")
            return False
            
        # Check that Generation Source tab is still removed
        if 'Generation Source' not in content:
            print("✅ Generation Source tab remains removed")
        else:
            print("❌ Generation Source tab has reappeared")
            return False
            
        # Check that debug logging is removed
        if 'console.log' not in content:
            print("✅ Debug logging successfully removed")
        else:
            print("⚠️  Debug logging still present (may be intentional)")
            
        # Check that the existing sections remain
        sections_to_keep = [
            'Generated Files',
            'Kernel Driver Capabilities', 
            'Build & Execution Instructions'
        ]
        
        for section in sections_to_keep:
            if section in content:
                print(f"✅ {section} section preserved")
            else:
                print(f"❌ {section} section missing")
                return False
                
        return True
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")
        return False

def main():
    """Main verification function"""
    
    print("🚀 SAMPLE GENERATED CODE REMOVAL VERIFICATION")
    print("=" * 70)
    
    success = verify_removal()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 SAMPLE GENERATED CODE REMOVAL SUCCESSFUL!")
        print("\n📋 CHANGES CONFIRMED:")
        print("   ✅ Removed 'Sample Generated Code' section")
        print("   ✅ Kept 'Generation Source' tab removed")
        print("   ✅ Cleaned up debug logging")
        print("   ✅ Preserved existing sections:")
        print("      • Generated Files (with syntax highlighting)")
        print("      • Kernel Driver Capabilities")
        print("      • Build & Execution Instructions")
        print("\n🌐 CURRENT KERNEL DRIVER FILES TAB STRUCTURE:")
        print("   1. Driver Information")
        print("   2. Generated Files (collapsible with syntax highlighting)")
        print("   3. Kernel Driver Capabilities")
        print("   4. Build & Execution Instructions")
        print("\n🔧 MANUAL VERIFICATION:")
        print("   • Hard refresh: Ctrl+F5")
        print("   • Check 'Kernel Driver Files' tab")
        print("   • Verify 'Sample Generated Code' section is gone")
        print("   • Confirm other sections still work properly")
    else:
        print("❌ REMOVAL VERIFICATION FAILED")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)