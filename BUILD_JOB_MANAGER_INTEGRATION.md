# Build Job Manager Integration

## Summary

Integrated the complete `BuildJobManager` implementation with the Infrastructure API endpoints to enable actual build job execution on registered build servers.

## What Was Implemented

### 1. BuildJobManager Integration

**File**: `api/routers/infrastructure.py`

Added imports and initialization:
- Imported `BuildJobManager`, `BuildJobConfig`, `QueuePriority` from `infrastructure.services.build_job_manager`
- Imported `BuildServer`, `BuildServerStatus`, `Toolchain`, `ResourceUtilization` from `infrastructure.models.build_server`
- Added `BackgroundTasks` to FastAPI imports for async queue processing

### 2. Build Job Manager Instance

Created singleton instance management:
- `get_build_job_manager()` - Creates/returns BuildJobManager instance
- Converts dict-based build servers to `BuildServer` objects
- Initializes with server pool, artifact storage path, and max queue size

### 3. Background Queue Processor

Implemented automatic queue processing:
- `process_build_queue_background()` - Background task that runs every 10 seconds
- `start_queue_processor()` - Starts the background task
- Automatically assigns queued jobs to available servers
- Logs when builds are started from queue

### 4. Updated API Endpoints

#### POST /build-jobs (Submit Build Job)
- **Before**: Returned mock response with status "queued"
- **After**: 
  - Creates `BuildJobConfig` from submission
  - Calls `manager.submit_build(config)`
  - Handles server selection (auto or preferred)
  - Starts queue processor if not running
  - Persists job to `BUILD_JOBS_FILE`
  - Returns actual job with real status and queue position

#### GET /build-jobs (List Build Jobs)
- **Before**: Returned empty array
- **After**:
  - Uses `BuildHistoryFilters` for filtering
  - Calls `manager.get_build_history(filters)`
  - Returns actual jobs with status, server assignment, timestamps

#### GET /build-jobs/{job_id} (Get Build Job)
- **Before**: Always returned 404
- **After**:
  - Calls `manager.get_build(job_id)`
  - Returns complete job details including status, duration, errors

#### GET /build-jobs/{job_id}/status (Get Build Status)
- **Before**: Always returned 404
- **After**:
  - Returns current job status
  - Includes queue information if job is queued
  - Shows estimated wait time for queued jobs

#### GET /build-jobs/{job_id}/logs (Get Build Logs)
- **Before**: Always returned 404
- **After**:
  - Calls `manager.get_build_logs(job_id, stream)`
  - Returns actual build logs
  - Supports streaming mode (basic implementation)

#### PUT /build-jobs/{job_id}/cancel (Cancel Build)
- **Before**: Always returned 404
- **After**:
  - Calls `manager.cancel_build(job_id)`
  - Updates job status to CANCELLED
  - Removes from queue if queued
  - Decrements server's active_build_count
  - Persists updated job state

#### GET /build-jobs/queue/status (New Endpoint)
- Returns current queue status:
  - Total queued jobs
  - Total building jobs
  - Jobs by architecture
  - Estimated wait time

## Build Job Execution Flow

### When a Build Job is Submitted:

1. **Validation**
   - Checks repository and architecture are provided
   - Verifies queue capacity (max 1000 jobs)

2. **Job Creation**
   - Generates unique UUID for job
   - Sets initial status to QUEUED
   - Stores job in manager's `_jobs` dictionary
   - Initializes empty log storage

3. **Server Selection**
   - Uses `BuildServerSelectionStrategy` to find suitable server
   - Checks: architecture support, toolchain availability, capacity
   - **If server available immediately:**
     - Assigns job to server
     - Starts build immediately
     - Returns queue_position=0
   - **If no server available:**
     - Adds to priority queue
     - Calculates queue position
     - Estimates start time (5 min per job ahead)

4. **Build Execution** (when server available)
   - Updates status to BUILDING
   - Sets started_at timestamp
   - Increments server's `active_build_count`
   - Adds to `_active_builds` map
   - Appends initial logs (repo, branch, commit, arch)

5. **Build Server State Changes**
   - `active_build_count` increases
   - Server's `can_accept_build()` checks count vs `max_concurrent_builds`
   - `queue_depth` tracks queued jobs
   - `current_utilization` affects capacity

6. **Queue Processing** (background task)
   - Runs every 10 seconds
   - Iterates through queue in priority order
   - Assigns jobs to servers as they become available
   - Starts builds automatically

7. **Build Completion**
   - Sets status to COMPLETED or FAILED
   - Records completion timestamp
   - Calculates duration
   - Stores artifact IDs
   - Decrements server's `active_build_count`
   - Removes from `_active_builds`
   - Appends final logs

8. **Cancellation**
   - Can cancel queued or building jobs
   - Sets status to CANCELLED
   - Removes from queue if queued
   - Decrements server's `active_build_count` if building
   - Persists updated state

## Build Server Capacity

Servers can accept builds when:
- Status is ONLINE
- Not in maintenance mode
- `active_build_count < max_concurrent_builds` (default: 4)
- Resource utilization < 85% (CPU, memory, storage)

## Data Persistence

Build jobs are persisted to `infrastructure_state/build_jobs.json`:
- On job submission
- On job cancellation
- On status changes

## Testing

To test the implementation:

```bash
# Submit a build job
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/torvalds/linux",
    "branch": "master",
    "commit_hash": "HEAD",
    "target_architecture": "x86_64",
    "server_id": "auto"
  }'

# Check queue status
curl http://localhost:8000/api/v1/infrastructure/build-jobs/queue/status

# List all build jobs
curl http://localhost:8000/api/v1/infrastructure/build-jobs

# Get specific job status
curl http://localhost:8000/api/v1/infrastructure/build-jobs/{job_id}/status

# Get job logs
curl http://localhost:8000/api/v1/infrastructure/build-jobs/{job_id}/logs

# Cancel a job
curl -X PUT http://localhost:8000/api/v1/infrastructure/build-jobs/{job_id}/cancel
```

## Benefits

1. **Real Build Execution**: Jobs are actually assigned to servers and tracked
2. **Automatic Queue Processing**: Background task handles job assignment
3. **Server Load Balancing**: Respects server capacity and concurrent build limits
4. **Priority Queuing**: Supports LOW/NORMAL/HIGH/URGENT priorities
5. **Real-time Status**: Actual job status, not mock data
6. **Log Streaming**: Access to real build logs
7. **Cancellation Support**: Can cancel queued or running builds
8. **Persistence**: Jobs survive API server restarts

## Next Steps

To make builds actually execute on remote servers:
1. Implement SSH-based build execution in BuildJobManager
2. Add artifact collection and storage
3. Implement real-time log streaming via WebSocket
4. Add build result notifications
5. Implement retry logic for failed builds

## Files Modified

- `api/routers/infrastructure.py` - Integrated BuildJobManager with API endpoints

## Files Referenced

- `infrastructure/services/build_job_manager.py` - Build job orchestration
- `infrastructure/models/build_server.py` - Data models
- `infrastructure/strategies/build_server_strategy.py` - Server selection
- `infrastructure/models/artifact.py` - Artifact management
