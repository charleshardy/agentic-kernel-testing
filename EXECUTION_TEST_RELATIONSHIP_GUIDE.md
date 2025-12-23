# Finding the Relationship Between Execution IDs and Test Cases

## Overview
When you generate AI test cases, they are grouped into execution plans for efficient processing. Here's how to find the relationship between execution IDs and individual test cases in the Web GUI.

## Current Status: ✅ ENHANCED

I've just enhanced the Web GUI to show the detailed relationship between execution plans and their test cases.

## Where to Find the Relationship

### 1. **Test Execution (Debug Mode) Page** - `/tests`

This is the **primary location** to see execution-to-test-case relationships:

#### **Enhanced Features Added:**
- **Expandable Rows**: Each execution plan row can be expanded to show detailed test cases
- **"View Details" Button**: Click to expand and see all test cases in that execution
- **Detailed Test Information**: Shows test ID, name, type, subsystem, status, and estimated time
- **Real-time Data**: Uses live API data, not mock data

#### **How to Use:**
1. Navigate to **Test Execution (Debug Mode)** page
2. Find your execution plan (e.g., `c3d34982...`)
3. Click the **"View Details"** button or the expand arrow
4. See all individual test cases within that execution plan

#### **Information Displayed:**
- **Execution Plan Level**:
  - Execution ID (shortened with tooltip showing full ID)
  - Overall status (queued, running, completed, failed)
  - Test count (e.g., "20 tests")
  - Progress bar with completion status
  
- **Individual Test Case Level** (when expanded):
  - Test Case ID (shortened with tooltip)
  - Full test name
  - Test type (unit, integration, etc.)
  - Target subsystem
  - Individual test status
  - Estimated execution time

### 2. **Test Cases Page** - `/test-cases`

Shows all individual test cases but doesn't directly show execution plan relationships:
- Lists all 20 individual test cases
- Shows generation method (AI generated)
- Shows test details and metadata
- **Note**: Doesn't show which execution plan they belong to

### 3. **API Endpoints for Programmatic Access**

If you need programmatic access to the relationships:

#### **Get Active Executions:**
```bash
GET /api/v1/execution/active
# Returns: List of execution plans with test counts
```

#### **Get Execution Details:**
```bash
GET /api/v1/execution/{plan_id}/status
# Returns: Detailed execution info including all test cases
```

#### **Example API Response:**
```json
{
  "success": true,
  "data": {
    "plan_id": "e95e1640-0b3a-4722-a062-983431f85b11",
    "total_tests": 5,
    "test_cases": [
      {
        "test_id": "abc123...",
        "name": "Test test_execution_details - normal operation",
        "test_type": "unit",
        "target_subsystem": "kernel/test",
        "execution_status": "never_run"
      }
      // ... more test cases
    ]
  }
}
```

## Visual Guide

### Before Enhancement:
- ❌ Only showed execution ID and basic stats
- ❌ No way to see which test cases were in each execution
- ❌ Had to guess the relationship

### After Enhancement:
- ✅ **Expandable rows** show detailed test case information
- ✅ **"View Details" button** for easy access
- ✅ **Complete test case details** including IDs, names, types, status
- ✅ **Real-time data** from the API
- ✅ **Clear visual hierarchy** showing execution → test cases relationship

## Example Workflow

1. **Generate AI Tests**: Create 20 test cases using AI generation
2. **Check Test Cases Page**: See all 20 individual test cases listed
3. **Go to Test Execution Page**: See 1 execution plan containing those 20 tests
4. **Click "View Details"**: Expand to see the exact mapping of which tests are in that execution
5. **Review Individual Tests**: See each test's ID, name, type, and status

## Key Benefits

- **Traceability**: Clear path from execution plan to individual tests
- **Debugging**: Easy to identify which specific test in an execution is having issues
- **Monitoring**: Track progress of individual tests within a batch execution
- **Management**: Understand resource allocation and test grouping

## Technical Implementation

The enhancement includes:
- **Frontend**: Enhanced `TestExecutionDebug.tsx` with expandable rows
- **Backend**: Enhanced `/execution/{plan_id}/status` endpoint with test case details
- **API Integration**: Real-time data fetching with proper error handling
- **UI/UX**: Intuitive expand/collapse interface with detailed information display

This provides a complete solution for understanding the relationship between execution IDs and their constituent test cases.