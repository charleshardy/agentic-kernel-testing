#!/usr/bin/env python3
"""
Complete test for Kernel Driver UI Enhancement
Tests the full workflow from generation to UI display
"""

import requests
import json
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3001"
WAIT_TIMEOUT = 30

def setup_chrome_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Failed to setup Chrome driver: {e}")
        return None

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def generate_kernel_driver():
    """Generate a kernel driver test case"""
    print("🚀 Generating kernel driver test case...")
    
    params = {
        "function_name": "schedule",
        "file_path": "kernel/sched/core.c",
        "subsystem": "scheduler",
        "test_types": "unit,integration"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/tests/generate-kernel-driver",
            params=params,
            headers={
                "Content-Type": "application/json",
                "Origin": FRONTEND_URL
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Kernel driver generated successfully")
                print(f"   Test case ID: {data['data']['test_case_ids'][0]}")
                print(f"   Generated files: {data['data']['driver_info']['generated_files']}")
                return data['data']['test_case_ids'][0]
            else:
                print(f"❌ Generation failed: {data.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Generation request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Generation request failed: {e}")
        return None

def get_test_case_details(test_id):
    """Get detailed test case information"""
    print(f"📋 Fetching test case details for {test_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/tests/{test_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                test_case = data["data"]
                print("✅ Test case details retrieved")
                print(f"   Name: {test_case.get('name', 'N/A')}")
                print(f"   Generation method: {test_case.get('metadata', {}).get('generation_method', 'N/A')}")
                
                # Check for driver files
                driver_files = test_case.get('metadata', {}).get('driver_files', {})
                if driver_files:
                    print(f"   Driver files found: {list(driver_files.keys())}")
                else:
                    print("   No driver files in metadata")
                
                return test_case
            else:
                print(f"❌ Failed to get test case: {data.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Request failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_frontend_ui(test_id):
    """Test the frontend UI for kernel driver display"""
    print("🌐 Testing frontend UI...")
    
    driver = setup_chrome_driver()
    if not driver:
        print("❌ Failed to setup Chrome driver")
        return False
    
    try:
        # Navigate to test cases page
        print("   Navigating to test cases page...")
        driver.get(f"{FRONTEND_URL}/test-cases")
        
        # Wait for page to load
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.css_selector, "[data-testid='test-cases-page'], .ant-table, h2"))
        )
        print("✅ Test cases page loaded")
        
        # Look for the generated test case
        print(f"   Looking for test case {test_id}...")
        
        # Try to find the test case in the table
        try:
            # Wait a bit for data to load
            time.sleep(3)
            
            # Look for View Details button or test case row
            view_buttons = driver.find_elements(By.xpath, "//button[contains(text(), 'View Details') or contains(text(), 'View')]")
            
            if view_buttons:
                print(f"✅ Found {len(view_buttons)} View Details buttons")
                
                # Click the first View Details button
                view_buttons[0].click()
                print("   Clicked View Details button")
                
                # Wait for modal to open
                WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.css_selector, ".ant-modal, [role='dialog']"))
                )
                print("✅ Test case modal opened")
                
                # Check for kernel driver files tab
                try:
                    kernel_tab = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.xpath, "//div[contains(@class, 'ant-tabs-tab') and contains(., 'Kernel Driver Files')]"))
                    )
                    print("✅ Kernel Driver Files tab found")
                    
                    # Click the kernel driver files tab
                    kernel_tab.click()
                    print("   Clicked Kernel Driver Files tab")
                    
                    # Wait for tab content to load
                    time.sleep(2)
                    
                    # Check for syntax highlighter
                    syntax_elements = driver.find_elements(By.css_selector, ".react-syntax-highlighter, pre[class*='language-'], code[class*='language-']")
                    if syntax_elements:
                        print(f"✅ Syntax highlighting found ({len(syntax_elements)} elements)")
                    else:
                        print("⚠️  No syntax highlighting elements found")
                    
                    # Check for file panels
                    file_panels = driver.find_elements(By.css_selector, ".ant-collapse-item, .ant-collapse-panel")
                    if file_panels:
                        print(f"✅ File panels found ({len(file_panels)} panels)")
                        
                        # Try to expand first panel
                        if file_panels:
                            try:
                                file_panels[0].click()
                                time.sleep(1)
                                print("   Expanded first file panel")
                            except:
                                print("   Could not expand file panel")
                    else:
                        print("⚠️  No file panels found")
                    
                    # Check for copy and download buttons
                    action_buttons = driver.find_elements(By.css_selector, "button[title*='Copy'], button[title*='Download']")
                    if action_buttons:
                        print(f"✅ Action buttons found ({len(action_buttons)} buttons)")
                    else:
                        print("⚠️  No copy/download buttons found")
                    
                    # Check for build instructions
                    build_sections = driver.find_elements(By.xpath, "//div[contains(text(), 'Build') or contains(text(), 'Execution') or contains(text(), 'Safety')]")
                    if build_sections:
                        print(f"✅ Build instruction sections found ({len(build_sections)} sections)")
                    else:
                        print("⚠️  No build instruction sections found")
                    
                    return True
                    
                except TimeoutException:
                    print("❌ Kernel Driver Files tab not found")
                    
                    # Check what tabs are available
                    tabs = driver.find_elements(By.css_selector, ".ant-tabs-tab")
                    tab_names = [tab.text for tab in tabs]
                    print(f"   Available tabs: {tab_names}")
                    
                    return False
                
            else:
                print("❌ No View Details buttons found")
                
                # Check if there are any test cases in the table
                rows = driver.find_elements(By.css_selector, ".ant-table-tbody tr, tr")
                print(f"   Found {len(rows)} table rows")
                
                return False
                
        except Exception as e:
            print(f"❌ Error interacting with UI: {e}")
            return False
            
    except TimeoutException:
        print("❌ Timeout waiting for page to load")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False
    finally:
        driver.quit()

def main():
    """Main test function"""
    print("🧪 Starting Kernel Driver UI Enhancement Test")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API health check failed, aborting tests")
        sys.exit(1)
    
    # Generate kernel driver
    test_id = generate_kernel_driver()
    if not test_id:
        print("❌ Kernel driver generation failed, aborting tests")
        sys.exit(1)
    
    # Wait a moment for the test to be processed
    print("⏳ Waiting for test case to be processed...")
    time.sleep(5)
    
    # Get test case details
    test_case = get_test_case_details(test_id)
    if not test_case:
        print("❌ Failed to get test case details, aborting tests")
        sys.exit(1)
    
    # Test frontend UI
    if test_frontend_ui(test_id):
        print("✅ Frontend UI test passed")
    else:
        print("❌ Frontend UI test failed")
    
    print("=" * 50)
    print("🏁 Test completed")

if __name__ == "__main__":
    main()