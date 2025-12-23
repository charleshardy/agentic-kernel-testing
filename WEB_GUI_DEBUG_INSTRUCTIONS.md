# Web GUI Debug Instructions

## Current Status

✅ **API Backend**: Fully working - executions are created and returned correctly
✅ **Authentication**: Working - login endpoints functional
✅ **AI Test Generation**: Working - creates execution plans
✅ **Active Executions Endpoint**: Working - returns execution plans in correct format

❓ **Web GUI**: Issue persists - executions not showing in Test Execution page

## Debug Tools Created

### 1. Direct API Test Component
- **Location**: Added to Test Execution page (`/test-execution`)
- **Purpose**: Tests API directly from browser without React Query
- **Usage**: Click "Run Complete Test" button

### 2. Execution Debug Page
- **URL**: http://localhost:3000/execution-debug
- **Purpose**: Detailed debugging of React Query and API calls
- **Features**: 
  - Shows React Query status
  - Manual API testing
  - Direct fetch testing
  - Debug logs
  - Browser environment info

### 3. Test Creation Script
- **File**: `create_test_for_gui.py`
- **Purpose**: Creates a test via API that should appear in Web GUI
- **Usage**: `python3 create_test_for_gui.py`

## Debugging Steps

### Step 1: Verify API is Working
```bash
# Run the test creation script
python3 create_test_for_gui.py

# Should output:
# ✅ Login successful
# ✅ AI test generated successfully!
# ✅ Our test is in active executions!
```

### Step 2: Test Web GUI API Connection
1. Open Web GUI: http://localhost:3000
2. Navigate to Test Execution page (`/test-execution`)
3. Look for "Direct API Test" section
4. Click "Run Complete Test"
5. Check the results in the test output

**Expected Results:**
- ✅ Health check OK
- ✅ Login successful
- ✅ AI test generated
- ✅ Active executions: X found
- ✅ API service executions: X found

### Step 3: Use Execution Debug Page
1. Open: http://localhost:3000/execution-debug
2. Click "Test Manual API Call"
3. Click "Test Direct Fetch"
4. Click "Force React Query Refresh"
5. Check all the debug information

**What to Look For:**
- React Query Status: Should show data and no errors
- Current Executions: Should list execution plans
- Debug Logs: Should show successful API calls
- Browser Environment: Should show auth token present

### Step 4: Check Browser Console
1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for these messages:
   - `🔍 Fetching active executions...`
   - `✅ Active executions response: {...}`
   - `📊 Found X active executions: [...]`

### Step 5: Check Network Tab
1. Open browser developer tools (F12)
2. Go to Network tab
3. Filter by "execution"
4. Look for calls to `/execution/active`
5. Check:
   - Status should be 200
   - Response should contain `{"success": true, "data": {"executions": [...]}}`

## Common Issues and Solutions

### Issue 1: No API Calls in Network Tab
**Cause**: React Query not making requests
**Solution**: Check React Query configuration, force refresh

### Issue 2: 401 Authentication Errors
**Cause**: Missing or invalid auth token
**Solution**: Check localStorage for `auth_token`, try manual login

### Issue 3: CORS Errors
**Cause**: Browser blocking cross-origin requests
**Solution**: Verify API server CORS configuration

### Issue 4: Empty Executions Array
**Cause**: No active executions or wrong status filtering
**Solution**: Create new test via API, check execution status

### Issue 5: React Query Caching Issues
**Cause**: Stale cache preventing updates
**Solution**: Use "Force React Query Refresh" button

## Expected Behavior

When working correctly:

1. **Test Generation**: 
   - User clicks "AI Generate Tests" in Web GUI
   - Form submission creates execution plan via API
   - Plan appears in "Active Test Executions" table

2. **Real-time Updates**:
   - Table refreshes every 5 seconds
   - New executions appear automatically
   - Status updates in real-time

3. **Table Display**:
   - Shows execution ID, status, progress, timing
   - Status should be "QUEUED" initially
   - May change to "RUNNING" then "COMPLETED"

## Files Modified for Debugging

1. `dashboard/src/components/DirectAPITest.tsx` - Direct API testing component
2. `dashboard/src/pages/ExecutionDebug.tsx` - Comprehensive debug page
3. `dashboard/src/pages/TestExecution.tsx` - Added DirectAPITest component
4. `dashboard/src/App.tsx` - Added debug route
5. `create_test_for_gui.py` - Script to create test for verification

## Next Steps Based on Debug Results

### If API Tests Pass but Web GUI Doesn't Show Executions:
- Check React Query configuration
- Verify component mounting and rendering
- Check for JavaScript errors in console

### If API Tests Fail:
- Check network connectivity
- Verify API server is running
- Check authentication token

### If Everything Looks Correct but Still Not Working:
- Clear browser cache and localStorage
- Try incognito/private browsing mode
- Check for browser extensions blocking requests
- Verify Web GUI is using correct API URL

## Success Criteria

The issue is resolved when:
1. ✅ API tests pass in browser
2. ✅ React Query shows data without errors
3. ✅ Executions appear in the table
4. ✅ Real-time updates work (5-second polling)
5. ✅ New AI-generated tests appear automatically

## Contact Information

If the issue persists after following these steps, provide:
1. Screenshots of the debug pages
2. Browser console logs
3. Network tab screenshots
4. Results from `create_test_for_gui.py`