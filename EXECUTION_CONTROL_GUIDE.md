# How to Trigger Real Execution Actions in Web GUI

## Overview
The Test Execution page now provides full execution control capabilities. You can start, pause, and cancel execution plans directly from the Web GUI.

## ✅ Enhanced Execution Controls Available

### **Location: Test Execution (Debug Mode) Page** - `/tests`

## Step-by-Step Guide

### 1. **View Queued Executions**
- Navigate to **Test Execution (Debug Mode)** page
- See execution plans with status "QUEUED"
- Each row shows:
  - Execution ID (shortened with tooltip)
  - Status (QUEUED, RUNNING, COMPLETED, etc.)
  - Test count (e.g., "5 tests")
  - Progress information

### 2. **Start Execution** ▶️
**When Available**: Execution status is "QUEUED"

**How to Start**:
1. Find the execution plan you want to start
2. Click the **"Start"** button (▶️ icon) in the Actions column
3. System will:
   - Change status from "QUEUED" to "RUNNING"
   - Update the UI in real-time
   - Show success message
   - Begin actual test execution (when orchestrator is connected)

**API Endpoint**: `POST /api/v1/execution/{plan_id}/start`

### 3. **Cancel Execution** ⏹️
**When Available**: Execution status is "QUEUED" or "RUNNING"

**How to Cancel**:
1. Find the execution plan you want to cancel
2. Click the **"Cancel"** button (⏹️ icon) in the Actions column
3. System will:
   - Stop the execution immediately
   - Change status to "CANCELLED"
   - Clean up resources
   - Show confirmation message

**API Endpoint**: `POST /api/v1/execution/{plan_id}/cancel`

### 4. **Pause Execution** ⏸️
**When Available**: Execution status is "RUNNING"

**How to Pause**:
1. Find the running execution plan
2. Click the **"Pause"** button (⏸️ icon) in the Actions column
3. **Note**: Pause functionality is planned for future implementation

## Action Button States

### **Queued Execution** (`status: "queued"`)
- ✅ **"Start"** button (blue, primary)
- ✅ **"Cancel"** button (red, danger)
- ❌ "Pause" button (not shown)

### **Running Execution** (`status: "running"`)
- ❌ "Start" button (not shown)
- ✅ **"Pause"** button (gray) - *Coming soon*
- ✅ **"Cancel"** button (red, danger)

### **Completed/Failed Execution**
- ❌ No action buttons (execution is finished)
- ✅ **"View Details"** button (to see results)

## Real-Time Updates

The Web GUI automatically updates execution status:
- **Auto-refresh**: Every 5 seconds
- **Manual refresh**: Click the "Refresh" button
- **WebSocket updates**: Real-time notifications (when available)
- **Cache-busting**: Always fetches fresh data

## Example Workflow

### **Starting an AI-Generated Test Batch**:

1. **Generate Tests**:
   ```
   AI Generate Tests → 20 test cases created → 1 execution plan (QUEUED)
   ```

2. **Start Execution**:
   ```
   Test Execution Page → Find execution → Click "Start" → Status: RUNNING
   ```

3. **Monitor Progress**:
   ```
   View Details → See individual test progress → Real-time updates
   ```

4. **Handle Issues** (if needed):
   ```
   Click "Cancel" → Execution stops → Status: CANCELLED
   ```

## Backend Integration

### **What Happens When You Click "Start"**:

1. **API Call**: `POST /execution/{plan_id}/start`
2. **Status Update**: Changes from "queued" to "running"
3. **Orchestrator Integration**: Submits to test orchestrator (when available)
4. **Resource Allocation**: Assigns test environments
5. **Test Execution**: Begins running individual test cases
6. **Real-time Updates**: WebSocket notifications to all connected clients

### **Current Implementation Status**:

- ✅ **Start Execution**: Fully implemented and working
- ✅ **Cancel Execution**: Fully implemented and working
- ✅ **Status Updates**: Real-time UI updates working
- ✅ **API Integration**: Complete backend support
- 🔄 **Pause Execution**: Planned for future implementation
- 🔄 **Orchestrator Integration**: Basic framework in place

## Testing the Functionality

### **Quick Test**:
1. Generate some AI test cases
2. Go to Test Execution page
3. See the queued execution
4. Click "Start" button
5. Watch status change to "RUNNING"
6. Click "View Details" to see test cases
7. Use "Cancel" if needed

### **API Testing**:
```bash
# Generate test cases
curl -X POST "http://localhost:8000/api/v1/tests/generate-from-function?function_name=test_func&file_path=kernel/test.c&max_tests=3"

# Get execution plan ID from response, then start it
curl -X POST "http://localhost:8000/api/v1/execution/{plan_id}/start" \
  -H "Authorization: Bearer {token}"

# Check status
curl "http://localhost:8000/api/v1/execution/active"
```

## Troubleshooting

### **"Start" Button Not Appearing**:
- Check execution status is "QUEUED"
- Refresh the page
- Verify execution plan exists

### **"Not Authenticated" Error**:
- Web GUI handles authentication automatically
- For API calls, ensure proper token is included

### **Execution Not Actually Running**:
- Status changes to "RUNNING" immediately
- Actual test execution depends on orchestrator connection
- Check orchestrator status in system metrics

## Future Enhancements

- **Pause/Resume**: Full pause and resume functionality
- **Batch Operations**: Start/cancel multiple executions
- **Scheduling**: Schedule executions for later
- **Priority Control**: Adjust execution priority
- **Resource Selection**: Choose specific test environments
- **Progress Streaming**: Real-time test output streaming

The execution control system provides a complete interface for managing test execution lifecycles directly from the Web GUI!