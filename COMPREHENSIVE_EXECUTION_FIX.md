# Comprehensive Execution Flow Fix

## Current Issues Identified

1. **Permission Issue**: Demo user lacks `status:read` permission for execution endpoints
2. **API Server Restart Needed**: Auth changes not loaded
3. **Execution Plan Format**: Plans may not be in correct format for Web GUI
4. **Real-time Updates**: WebSocket connection may not be working properly

## Immediate Fix Steps

### Step 1: Restart API Server
The API server needs to be restarted to pick up the auth.py changes:

```bash
# Stop current API server (Ctrl+C)
# Then restart:
python -m api.server
```

### Step 2: Verify Permissions
After restart, demo user should have `status:read` permission:

```bash
curl -s "http://localhost:8000/api/v1/auth/demo-login" -X POST | jq '.data.user_info.permissions'
```

Should include: `["test:submit", "test:read", "test:delete", "status:read"]`

### Step 3: Test Execution Endpoints
```bash
# Get token
TOKEN=$(curl -s "http://localhost:8000/api/v1/auth/demo-login" -X POST | jq -r '.data.access_token')

# Test active executions
curl -s "http://localhost:8000/api/v1/execution/active" -H "Authorization: Bearer $TOKEN" | jq '.'

# Test metrics
curl -s "http://localhost:8000/api/v1/execution/metrics" -H "Authorization: Bearer $TOKEN" | jq '.'
```

## Root Cause Analysis

The execution flow works as follows:

1. **AI Test Generation** → Creates test case + execution plan
2. **Orchestrator Polling** → Detects new execution plans (every 5 seconds)
3. **Queue Processing** → Adds plans to priority queue
4. **Web GUI Polling** → Fetches active executions (every 5 seconds)
5. **Real-time Updates** → WebSocket broadcasts status changes

The break in the chain is at step 4 - the Web GUI can't fetch active executions due to permission errors.

## Testing the Complete Flow

### Manual Test Sequence

1. **Start API Server**:
   ```bash
   python -m api.server
   ```

2. **Start Dashboard**:
   ```bash
   cd dashboard && npm run dev
   ```

3. **Create AI Test** (via Web GUI):
   - Go to Test Cases page
   - Click "AI Generate Tests"
   - Generate from function or diff

4. **Check Test Execution Page**:
   - Should show the test in execution queue
   - Real-time metrics should update

### API Test Sequence

```bash
# 1. Get token
TOKEN=$(curl -s "http://localhost:8000/api/v1/auth/demo-login" -X POST | jq -r '.data.access_token')

# 2. Generate AI test
curl -s "http://localhost:8000/api/v1/tests/generate-from-function" \
  -H "Authorization: Bearer $TOKEN" \
  -d "function_name=test_func&file_path=test.c&subsystem=test&max_tests=1" | jq '.'

# 3. Check active executions
curl -s "http://localhost:8000/api/v1/execution/active" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 4. Force orchestrator poll
curl -s "http://localhost:8000/api/v1/execution/orchestrator/poll" \
  -H "Authorization: Bearer $TOKEN" -X POST | jq '.'
```

## Expected Results

After the fix:

1. **Demo user has correct permissions**
2. **API endpoints return data instead of 403 errors**
3. **Web GUI Test Execution page shows active executions**
4. **Real-time updates work via WebSocket**
5. **AI-generated tests appear in execution queue**

## Troubleshooting

### If Tests Still Don't Appear

1. **Check orchestrator status**:
   ```bash
   curl -s "http://localhost:8000/api/v1/health" | jq '.data.components.test_orchestrator'
   ```

2. **Force orchestrator poll**:
   ```bash
   curl -s "http://localhost:8000/api/v1/execution/orchestrator/poll" \
     -H "Authorization: Bearer $TOKEN" -X POST
   ```

3. **Check browser console** for WebSocket errors

4. **Verify API server logs** for orchestrator startup messages

### If WebSocket Doesn't Connect

1. **Check CORS settings** in api/main.py
2. **Verify WebSocket URL** in RealTimeExecutionMonitor.tsx
3. **Check browser network tab** for WebSocket connection attempts

## Next Steps After Fix

1. **Restart API server** to load auth changes
2. **Test the complete flow** using the sequences above
3. **Verify Web GUI shows executions** in Test Execution page
4. **Confirm real-time updates** work properly

The execution flow should then work end-to-end from AI test generation to real-time execution monitoring.