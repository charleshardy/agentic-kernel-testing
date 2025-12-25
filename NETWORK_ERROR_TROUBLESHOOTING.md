# "Network or server error occurred" Troubleshooting Guide

## 🎯 Problem
Users encounter "Generation failed: Network or server error occurred" when using "From Function" and "Kernel Test Driver" tabs in AI Generate Tests.

## ✅ Confirmed Working
- ✅ **Backend API**: Running and healthy on port 8000
- ✅ **Direct API Calls**: Working perfectly with curl
- ✅ **Proxy Configuration**: Vite proxy working correctly
- ✅ **Authentication**: Token generation and validation working

## 🔍 Root Cause Analysis
The issue is in the **frontend React application**, not the backend or network infrastructure.

## 🛠️ Solutions Applied

### 1. Enhanced API Service Logging
**File:** `dashboard/src/services/api.ts`

Added comprehensive logging to help diagnose the issue:
- Request logging with parameters
- Response logging with status
- Error logging with full context
- Authentication retry logic with logging

### 2. Improved Error Handling
- Better error message extraction
- Specific handling for "Not implemented" responses
- Network error detection and reporting
- Authentication error handling

### 3. Environment Detection
- Robust development vs production detection
- Automatic proxy vs direct URL selection
- Console logging in development mode

## 🧪 How to Debug

### Step 1: Check Browser Console
1. Open the frontend in your browser
2. Open DevTools (F12) → Console tab
3. Try the AI generation feature
4. Look for these log messages:
   ```
   🔧 API Service: Using proxy URL for development: /api/v1
   🌐 API Request: POST /tests/generate-from-function {...}
   ✅ API Response: 200 /tests/generate-from-function
   ```

### Step 2: Check Network Tab
1. Open DevTools → Network tab
2. Try the AI generation feature
3. Look for the API request to `/api/v1/tests/generate-from-function`
4. Check the request status, headers, and response

### Step 3: Use Debug Tools
Open the debug tools I created:
- `debug_frontend_network_issue.html` - Comprehensive network diagnostics
- Run the "Test Exact Frontend Scenario" to see if the issue reproduces

## 🔧 Manual Testing Steps

### Test 1: Verify Frontend is Running
```bash
# Make sure frontend is running on port 3000
cd dashboard
npm run dev

# Should show: Local: http://localhost:3000/
```

### Test 2: Test Proxy Manually
```bash
# This should work (proxy test)
curl -s http://localhost:3000/api/v1/health

# This should also work (direct test)
curl -s http://localhost:8000/api/v1/health
```

### Test 3: Test Authentication Flow
```bash
# Get token via proxy
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  http://localhost:3000/api/v1/auth/login

# Use token for generation via proxy
curl -s -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:3000/api/v1/tests/generate-from-function?function_name=test&file_path=test.c&subsystem=test&max_tests=1"
```

## 🎯 Most Likely Causes

### 1. Browser Cache Issues
**Solution:** Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)

### 2. Authentication Token Issues
**Symptoms:** 401 errors in network tab
**Solution:** Clear localStorage and try again:
```javascript
// In browser console
localStorage.clear()
location.reload()
```

### 3. CORS Policy Issues
**Symptoms:** CORS errors in console
**Solution:** Ensure frontend is running on localhost:3000

### 4. Frontend Not Running
**Symptoms:** Connection refused errors
**Solution:** Ensure `npm run dev` is running and accessible on port 3000

### 5. Proxy Configuration Issues
**Symptoms:** 404 errors for /api/v1/* requests
**Solution:** Check `dashboard/vite.config.ts` proxy configuration

## 📊 Expected vs Actual Behavior

### Expected (Working)
```
🔧 API Service: Using proxy URL for development: /api/v1
🌐 API Request: POST /tests/generate-from-function {function_name: "kmalloc", ...}
✅ API Response: 200 /tests/generate-from-function
✅ Generated 3 test cases for function kmalloc
```

### Actual (Broken)
```
🌐 API Request: POST /tests/generate-from-function {function_name: "kmalloc", ...}
❌ API Response Error: Network error or timeout
❌ Generation failed: Network or server error occurred
```

## 🚀 Quick Fix Checklist

1. **Restart Frontend**: Stop and restart `npm run dev`
2. **Clear Browser Cache**: Hard refresh (Ctrl+Shift+R)
3. **Check Console**: Look for error messages in browser console
4. **Check Network Tab**: Verify API requests are being made
5. **Test Proxy**: Manually test `http://localhost:3000/api/v1/health`
6. **Check Ports**: Ensure frontend (3000) and backend (8000) are running

## 🔍 Advanced Debugging

### Enable Verbose Logging
The updated API service now includes detailed logging. Check the browser console for:
- API request details
- Response status codes
- Error information
- Authentication flow

### Test with Debug Tools
Use the created debug tools:
1. Open `debug_frontend_network_issue.html`
2. Run "Test All Connections"
3. Run "Test Exact Frontend Scenario"
4. Compare results with expected behavior

## 📝 Files Modified
- `dashboard/src/services/api.ts` - Enhanced logging and error handling
- Created debug tools for troubleshooting

The enhanced logging should help identify exactly where the request is failing in the frontend application.