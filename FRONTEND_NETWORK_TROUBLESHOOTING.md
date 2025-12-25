# Frontend Network Troubleshooting Guide

## Issue
User reports "Generation failed: Network or server error occurred" when using the "From Function" tab in AI Generate Tests, but this worked two days ago.

## Backend Status ✅
- Backend API server is running on port 8000
- `/api/v1/tests/generate-from-function` endpoint is working correctly
- Authentication is working
- Direct API calls via curl and Python succeed

## Frontend Status ✅
- Frontend development server is running on port 3000
- Vite proxy is configured correctly in `vite.config.ts`

## Potential Issues

### 1. Browser Cache
The browser might be caching old API responses or JavaScript files.

**Solution:**
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- Clear browser cache and cookies for localhost:3000
- Open browser developer tools (F12) and check "Disable cache" in Network tab

### 2. Browser Developer Console Errors
There might be JavaScript errors preventing the API call.

**Solution:**
1. Open browser developer tools (F12)
2. Go to Console tab
3. Try the "From Function" generation again
4. Look for any red error messages
5. Check the Network tab for failed requests

### 3. Proxy Configuration Issues
The Vite proxy might not be forwarding requests correctly.

**Solution:**
1. Check if requests are going to `/api/v1/...` (proxy) or `http://localhost:8000/api/v1/...` (direct)
2. In browser dev tools Network tab, look for the actual request URL
3. If requests are going direct instead of through proxy, there might be a configuration issue

### 4. Authentication Token Issues
The frontend might be using an expired or invalid token.

**Solution:**
1. Clear localStorage: In browser console, run `localStorage.clear()`
2. Refresh the page to get a new token
3. Try the generation again

### 5. CORS Issues
Cross-origin requests might be blocked.

**Solution:**
1. Check browser console for CORS errors
2. Ensure the backend is running with proper CORS headers
3. Verify the proxy is working correctly

## Debugging Steps

### Step 1: Check Browser Console
1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for any error messages
4. Try the "From Function" generation
5. Note any new errors that appear

### Step 2: Check Network Tab
1. In developer tools, go to Network tab
2. Clear existing requests
3. Try the "From Function" generation
4. Look for the API request to `/api/v1/tests/generate-from-function`
5. Check if it's successful (200) or failed (4xx/5xx)
6. Click on the request to see details

### Step 3: Test Direct API Call
Open browser console and run:
```javascript
fetch('/api/v1/tests/generate-from-function?function_name=test&file_path=test.c&subsystem=test&max_tests=1', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

### Step 4: Check Authentication
In browser console, run:
```javascript
console.log('Auth token:', localStorage.getItem('auth_token'))
```

### Step 5: Clear Everything and Restart
1. Clear browser cache and localStorage
2. Restart the frontend development server:
   ```bash
   cd dashboard
   npm run dev
   ```
3. Try again

## Expected Behavior
When working correctly:
1. User fills out "From Function" form
2. Frontend makes POST request to `/api/v1/tests/generate-from-function` with query parameters
3. Backend responds with 200 and generated test data
4. Frontend shows success message and updates test list

## Common Error Messages and Solutions

### "Network or server error occurred"
- Check if backend is running: `curl http://localhost:8000/api/v1/health`
- Check browser console for specific errors
- Try clearing browser cache

### "Generation failed: undefined"
- This was a previous issue that should be fixed
- If still occurring, check the error handling in `useAIGeneration.ts`

### "Not implemented"
- Backend endpoint returned "Not implemented" message
- This should not happen for the function generation endpoint

## Files to Check
- `dashboard/src/services/api.ts` - API service configuration
- `dashboard/src/hooks/useAIGeneration.ts` - Generation hook
- `dashboard/vite.config.ts` - Proxy configuration
- Browser developer tools Console and Network tabs

## Test Files Created
- `test_function_generation_simple.py` - Backend API test
- `debug_frontend_exact_scenario.html` - Frontend simulation test
- `test_frontend_api_debug.html` - Browser-based API test

## Next Steps
1. Follow the debugging steps above
2. Check browser developer tools for specific errors
3. If issue persists, provide the exact error messages from browser console
4. Consider testing in a different browser or incognito mode