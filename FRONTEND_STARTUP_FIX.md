# Frontend Startup Fix

## Problem
The Test Cases page was showing "Unable to load test cases" error.

## Root Cause
The issue was that the frontend development server wasn't running. The error occurred because:

1. **Backend was not running** - The API server needs to be started first
2. **Frontend was not running** - The React development server needs to be started
3. **Wrong npm script** - The script is `npm run dev`, not `npm start`

## Solution

### 1. Start the Backend API Server
```bash
# In the project root directory
python3 -m api.server &
```

This starts the API server on `http://localhost:8000` with:
- Health endpoint: `http://localhost:8000/api/v1/health`
- API documentation: `http://localhost:8000/docs`
- Test cases endpoint: `http://localhost:8000/api/v1/tests`

### 2. Start the Frontend Development Server
```bash
# In the dashboard directory
cd dashboard
npm run dev
```

This starts the React development server on `http://localhost:3001` (or another port if 3001 is busy).

### 3. Access the Application
Open your browser and navigate to:
- Frontend: `http://localhost:3001`
- Navigate to "Test Cases" page

## Verification Steps

1. **Check Backend Health**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   Should return: `{"success":true,"message":"System is healthy",...}`

2. **Check Test Cases API**:
   ```bash
   curl http://localhost:8000/api/v1/tests
   ```
   Should return: `{"success":true,"data":{"tests":[],...}}`

3. **Check Frontend**:
   - Open `http://localhost:3001` in browser
   - Navigate to "Test Cases" page
   - Should show "Test Cases (0 tests)" with empty table

## Additional Improvements Made

### Enhanced Error Handling
Added better error reporting in the TestCases component:

```typescript
const { data: testCasesData, isLoading, error, refetch } = useQuery(
  ['testCases', searchText, filters, dateRange],
  () => apiService.getTests({...}),
  {
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    onError: (error) => {
      console.error('Failed to fetch test cases:', error)
    },
    onSuccess: (data) => {
      console.log('Successfully fetched test cases:', data)
    }
  }
)
```

### Better Error Display
```typescript
if (error && !isLoading) {
  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>Unable to load test cases</Title>
        <p>Error: {error instanceof Error ? error.message : 'Unknown error'}</p>
        <Space>
          <Button onClick={() => refetch()} type="primary">Retry</Button>
          <Button onClick={() => window.location.reload()}>Reload Page</Button>
        </Space>
      </div>
    </div>
  )
}
```

## Testing the Complete Flow

1. **Start both servers** (backend and frontend)
2. **Navigate to Test Cases page** - should show empty state
3. **Generate some test cases** using "AI Generate Tests"
4. **Verify tests appear** in the list immediately
5. **Test bulk operations** like delete, export, etc.
6. **Verify error handling** by stopping the backend and seeing proper error messages

## Common Issues and Solutions

### "Unable to load test cases"
- **Cause**: Backend not running or network error
- **Solution**: Start backend with `python3 -m api.server`

### "Connection refused" errors
- **Cause**: Backend not accessible
- **Solution**: Check if backend is running on port 8000

### Frontend not loading
- **Cause**: Frontend server not running
- **Solution**: Run `npm run dev` in dashboard directory

### Authentication errors
- **Cause**: Demo authentication failing
- **Solution**: Backend automatically handles demo auth, check backend logs

This fix ensures both servers are running and the application works correctly.