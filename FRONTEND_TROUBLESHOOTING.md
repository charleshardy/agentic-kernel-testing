# Frontend Troubleshooting - Generation Source Tab Enhancement

## 🔍 Current Status

The Generation Source tab enhancement has been **successfully implemented** in the code, but you're not seeing it in the web GUI. Here's how to troubleshoot and verify:

## ✅ Backend Verification

### 1. API Server Status
```bash
# Check if API server is running
curl http://localhost:8000/api/v1/health
# Should return: {"success": true, ...}
```

### 2. Generate Test Case
```bash
# Generate a new kernel driver test case
curl -X POST "http://localhost:8000/api/v1/tests/generate-kernel-driver?function_name=kmalloc&file_path=mm/slab.c&subsystem=memory&test_types=unit,integration"
# Should return test_case_ids array
```

### 3. Verify Test Case Has Driver Files
```bash
# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/demo-login" | jq -r '.data.access_token')

# Get test case (replace with actual ID from step 2)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/tests/kernel_driver_XXXXX" | jq '.data.test_metadata.driver_files | keys'
# Should show array of filenames like ["test_kmalloc.c", "Makefile", ...]
```

## 🌐 Frontend Verification

### 1. Frontend Server Status
```bash
# Check if frontend is running
curl -s http://localhost:3000 | grep -i "react"
# Should return HTML with React references
```

### 2. Browser Cache Issues
The most common issue is browser caching. Try these steps:

1. **Hard Refresh**: Press `Ctrl+F5` (or `Cmd+Shift+R` on Mac)
2. **Clear Cache**: Open Developer Tools (F12) → Application → Storage → Clear site data
3. **Incognito Mode**: Open `http://localhost:3000/test-cases` in incognito/private mode

### 3. Check Browser Console
1. Open `http://localhost:3000/test-cases`
2. Press `F12` to open Developer Tools
3. Check Console tab for any JavaScript errors
4. Check Network tab to see if API calls are successful

## 🎯 Expected Behavior

When working correctly, you should see:

### In Test Cases List
- Test cases with names like "Kernel Driver Test for kmalloc"
- "View Details" buttons for each test case

### In Test Case Modal
1. Click "View Details" on a kernel driver test
2. Click "Generation Source" tab
3. Scroll down to find "Generated Files" section
4. See collapsible panels for each file:
   - `test_kmalloc.c` (C/C++ syntax highlighting)
   - `Makefile` (Makefile syntax highlighting)
   - `run_test.sh` (Bash syntax highlighting)
   - `install.sh` (Bash syntax highlighting)
   - `README.md` (Markdown syntax highlighting)
5. Each panel should have:
   - File icon and name
   - Character count
   - Copy to clipboard button
   - Download file button
   - Syntax-highlighted code content

## 🔧 Troubleshooting Steps

### Step 1: Restart Development Server
```bash
# Kill the current frontend server
pkill -f "npm run dev"

# Restart it
cd dashboard
npm run dev
```

### Step 2: Clear Node Modules (if needed)
```bash
cd dashboard
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Step 3: Check for TypeScript Errors
```bash
cd dashboard
npm run build
# Look for any compilation errors
```

### Step 4: Verify React Dependencies
The enhancement uses `react-syntax-highlighter`. Check if it's installed:
```bash
cd dashboard
npm list react-syntax-highlighter
# Should show the installed version
```

If not installed:
```bash
npm install react-syntax-highlighter @types/react-syntax-highlighter
```

## 🎉 Quick Test Script

Run this to verify everything is working:

```python
#!/usr/bin/env python3
import requests

# Generate test case
response = requests.post("http://localhost:8000/api/v1/tests/generate-kernel-driver?function_name=kmalloc&file_path=mm/slab.c&subsystem=memory")
test_id = response.json()['data']['test_case_ids'][0]

# Get auth token
auth = requests.post("http://localhost:8000/api/v1/auth/demo-login")
token = auth.json()['data']['access_token']

# Get test case
test_response = requests.get(f"http://localhost:8000/api/v1/tests/{test_id}", 
                           headers={"Authorization": f"Bearer {token}"})
test_data = test_response.json()['data']

print(f"✅ Test Case: {test_data['name']}")
print(f"✅ Driver Files: {len(test_data['test_metadata']['driver_files'])} files")
print(f"🌐 Open: http://localhost:3000/test-cases")
print(f"🔍 Find: {test_data['name']}")
```

## 📞 If Still Not Working

If you still don't see the enhancement after trying all the above:

1. **Check the exact URL**: Make sure you're going to `http://localhost:3000/test-cases` (not 3001)
2. **Try a different browser**: Sometimes browser-specific issues occur
3. **Check for ad blockers**: Some ad blockers interfere with local development
4. **Verify the test case type**: Make sure you're looking at a kernel driver test (not a regular test)

The enhancement is definitely implemented in the code - it's most likely a caching or refresh issue!