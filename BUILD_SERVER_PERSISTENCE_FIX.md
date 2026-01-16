# Build Server Persistence Bug Fix

## Issue
Build servers registered through the Build Servers page were disappearing after the API server restarted or reloaded. The server "pek-lpgtest16" would be successfully registered but then lost from the list.

## Root Cause
The infrastructure API (`api/routers/infrastructure.py`) was using in-memory storage (`_build_servers` dictionary) without any persistence mechanism. When the API server restarted or reloaded (e.g., due to code changes), all registered build servers were lost.

## Solution
Implemented JSON file-based persistence for infrastructure resources:

1. **Created persistence directory**: `infrastructure_state/`
2. **Added persistence functions**:
   - `load_from_file()`: Load data from JSON files on startup
   - `save_to_file()`: Save data to JSON files after modifications
3. **Persistence files**:
   - `build_servers.json`: Build server registrations
   - `hosts.json`: QEMU host registrations
   - `boards.json`: Physical board registrations
   - `build_jobs.json`: Build job data
   - `pipelines.json`: Pipeline data

## Changes Made

### api/routers/infrastructure.py
- Added JSON file persistence imports (`json`, `os`, `pathlib`)
- Created `PERSISTENCE_DIR` and file path constants
- Implemented `load_from_file()` and `save_to_file()` helper functions
- Modified data initialization to load from files on startup
- Added `save_to_file()` calls after:
  - Build server registration
  - Maintenance mode changes
  - Build server decommissioning

## Testing
Verified the fix works correctly:
1. ✅ Registered build server "pek-lpgtest16" successfully
2. ✅ Data persisted to `infrastructure_state/build_servers.json`
3. ✅ Restarted API server
4. ✅ Build server still appears in the list after restart
5. ✅ All server details preserved (hostname, IP, resources, SSH credentials)

## Files Created
- `infrastructure_state/build_servers.json`: Contains all registered build servers

## Status
**FIXED** - Build servers now persist across API server restarts and reloads.

## Future Improvements
For production use, consider:
1. Migrating to proper database storage (SQLAlchemy models already exist in `database/`)
2. Adding database models for BuildServer, Host, and Board
3. Implementing proper database migrations
4. Adding transaction support for data consistency

## Usage
Build servers can now be registered through the Build Servers page and will remain in the system even after:
- API server restarts
- Code changes that trigger auto-reload
- System reboots (as long as the `infrastructure_state/` directory is preserved)

The persistence is automatic and requires no additional configuration.
