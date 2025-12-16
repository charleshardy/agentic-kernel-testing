# Bulk Delete Error Fix

## Problem
After deleting all test cases using the bulk delete operation, the Web GUI shows an error:
```
Something went wrong
An error occurred while rendering this component.
Error details
Successfully deleted 20 test cases
```

## Root Causes Identified

### 1. **Simulated API Calls**
The bulk delete handler was only simulating deletions with `setTimeout` instead of calling the actual API:
```javascript
// OLD - Simulated deletion
await new Promise(resolve => setTimeout(resolve, 300))
// TODO: Call actual API - apiService.deleteTest(test.id)
```

### 2. **State Inconsistency**
After "deleting" tests (simulation), the component would refresh data, but since tests weren't actually deleted from the backend, there was a mismatch between UI state and actual data.

### 3. **Unsafe Array Operations**
The filtering and statistics calculations didn't handle edge cases when:
- `testCasesData.tests` is undefined or null
- Individual test objects have missing properties
- All tests are deleted (empty array state)

### 4. **Selected Row Keys Not Cleared**
When all tests were deleted, `selectedRowKeys` still contained IDs of non-existent tests, causing rendering issues.

## Fixes Implemented

### 1. **Real API Calls**
```javascript
// NEW - Actual API deletion
await apiService.deleteTest(test.id)
```

### 2. **Better Error Handling in Bulk Delete**
```javascript
const handleBulkDelete = async (tests: TestCase[]) => {
  let successCount = 0
  let failureCount = 0
  
  for (let i = 0; i < tests.length; i++) {
    try {
      await apiService.deleteTest(test.id)
      successCount++
    } catch (error) {
      failureCount++
    }
  }
  
  // Clear selected rows immediately
  setSelectedRowKeys([])
  
  // Show appropriate message
  if (failureCount === 0) {
    message.success(`Successfully deleted ${successCount} test cases`)
  } else {
    message.warning(`Deleted ${successCount}, ${failureCount} failed`)
  }
  
  // Safe refresh with fallback
  try {
    await refetch()
  } catch (error) {
    window.location.reload()
  }
}
```

### 3. **Safe Array Operations**
```javascript
// Safe filtering with error handling
const filteredTests = React.useMemo(() => {
  try {
    if (!testCasesData?.tests || !Array.isArray(testCasesData.tests)) {
      return []
    }
    
    let filtered = testCasesData.tests
    
    // Each filter operation wrapped in try-catch
    if (searchText) {
      filtered = filtered.filter(test => {
        try {
          return (
            (test.name && test.name.toLowerCase().includes(searchLower)) ||
            (test.description && test.description.toLowerCase().includes(searchLower))
          )
        } catch (error) {
          console.warn('Error filtering test:', test, error)
          return false
        }
      })
    }
    
    return filtered
  } catch (error) {
    console.error('Error in filteredTests calculation:', error)
    return []
  }
}, [testCasesData?.tests, searchText, filters, dateRange])
```

### 4. **Safe Statistics Calculation**
```javascript
// Safe statistics with error handling
const totalTests = filteredTests?.length || 0
const neverRunTests = React.useMemo(() => {
  try {
    return filteredTests.filter(t => !t?.metadata?.last_execution).length
  } catch (error) {
    console.warn('Error calculating neverRunTests:', error)
    return 0
  }
}, [filteredTests])
```

### 5. **Automatic Selected Row Cleanup**
```javascript
// Clear selected rows if they no longer exist
React.useEffect(() => {
  if (selectedRowKeys.length > 0 && filteredTests.length > 0) {
    const existingIds = new Set(filteredTests.map(test => test.id))
    const validSelectedKeys = selectedRowKeys.filter(key => existingIds.has(key))
    
    if (validSelectedKeys.length !== selectedRowKeys.length) {
      setSelectedRowKeys(validSelectedKeys)
    }
  } else if (selectedRowKeys.length > 0 && filteredTests.length === 0) {
    // Clear all selections if no tests remain
    setSelectedRowKeys([])
  }
}, [filteredTests, selectedRowKeys])
```

### 6. **Safe Props Passing**
```javascript
<TestCaseTable
  tests={filteredTests || []}
  selectedRowKeys={selectedRowKeys || []}
  pagination={{
    total: (filteredTests || []).length,
  }}
/>
```

### 7. **Error Boundary Fallback**
```javascript
// Show retry option if data loading fails
if (!testCasesData && !isLoading) {
  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>Unable to load test cases</Title>
        <Button onClick={() => refetch()} type="primary">
          Retry
        </Button>
      </div>
    </div>
  )
}
```

## Testing the Fix

To verify the fix works:

1. **Start the backend**: `python -m api.server`
2. **Start the frontend**: `cd dashboard && npm start`
3. **Create some test cases** using AI generation
4. **Select all test cases** using the "All" quick select button
5. **Click "Delete"** and confirm the bulk deletion
6. **Verify**: The page should show "0 test cases" without any errors

## Prevention

To prevent similar issues in the future:

1. **Always use real API calls** instead of simulations in production code
2. **Add error boundaries** around components that handle dynamic data
3. **Use safe array operations** with null/undefined checks
4. **Clear related state** when data changes (like selected items)
5. **Add comprehensive error handling** for async operations
6. **Test edge cases** like empty states and error conditions

This fix ensures the Web GUI handles bulk deletion gracefully and maintains a consistent state even when all test cases are deleted.