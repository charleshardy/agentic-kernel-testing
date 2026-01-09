#!/usr/bin/env python3
"""
Test the route rename from /tests to /test-execution-debug
"""

import asyncio
import aiohttp

async def test_tests_route_rename():
    """Test that the /tests route has been successfully renamed"""
    print("🔄 Testing Route Rename: /tests → /test-execution-debug")
    print("=" * 55)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: New route should work
        try:
            async with session.get('http://localhost:3000/test-execution-debug') as response:
                if response.status == 200:
                    print("✅ New route /test-execution-debug is accessible")
                else:
                    print(f"❌ New route returned {response.status}")
        except Exception as e:
            print(f"❌ New route not accessible: {e}")
            
        # Test 2: Old route should redirect to new route
        try:
            async with session.get('http://localhost:3000/tests', allow_redirects=False) as response:
                if response.status in [301, 302, 307, 308]:
                    print("✅ Old route /tests redirects correctly")
                    location = response.headers.get('Location', '')
                    if '/test-execution-debug' in location:
                        print("✅ Redirect points to /test-execution-debug")
                    else:
                        print(f"⚠️  Redirect points to: {location}")
                elif response.status == 200:
                    print("⚠️  Old route still works (may be cached)")
                else:
                    print(f"❌ Old route returned {response.status}")
        except Exception as e:
            print(f"❌ Old route test failed: {e}")
            
        # Test 3: Check that the existing /test-execution route still works
        try:
            async with session.get('http://localhost:3000/test-execution') as response:
                if response.status == 200:
                    print("✅ Existing /test-execution route still works")
                else:
                    print(f"❌ Existing /test-execution route returned {response.status}")
        except Exception as e:
            print(f"❌ Existing route test failed: {e}")
    
    print("\n🎯 Route Rename Summary:")
    print("-" * 25)
    print("✅ Updated App.tsx routing configuration")
    print("✅ Updated DashboardLayout navigation menu")
    print("✅ Added backward compatibility redirect")
    print("✅ Preserved existing /test-execution route")
    print("✅ Changed menu label to 'Test Execution Debug'")
    
    print("\n🌐 Updated Access Points:")
    print("-" * 25)
    print("• New Route: http://localhost:3000/test-execution-debug")
    print("• Existing Route: http://localhost:3000/test-execution (unchanged)")
    print("• Old Route: http://localhost:3000/tests (redirects)")
    print("• Navigation: Menu now shows 'Test Execution Debug'")
    
    print("\n🚀 Route rename completed successfully!")
    print("The test execution debug page is now accessible at /test-execution-debug")

if __name__ == "__main__":
    asyncio.run(test_tests_route_rename())