# Advanced Build Config Implementation Summary

## Overview
Added Advanced Settings section to the Build Job submission form in the Web GUI, allowing users to configure all BuildConfig parameters when submitting build jobs.

## Changes Made

### 1. Frontend Changes (`dashboard/src/components/infrastructure/BuildJobDashboard.tsx`)

**Added Advanced Settings Section** with 4 tabs:

#### Build Paths Tab
- `workspace_root`: Root directory for builds on the build server (default: `/tmp/builds`)
- `output_directory`: Where to place build artifacts (auto-generated if not specified)
- `keep_workspace`: Checkbox to keep workspace after build completes

#### Git Options Tab
- `git_depth`: Shallow clone depth (1 = latest commit only)
- `git_submodules`: Checkbox to clone git submodules

#### Build Config Tab
- `kernel_config`: defconfig name or path to config file (default: `defconfig`)
- `extra_make_args`: Comma-separated make arguments (e.g., `ARCH=arm64, CROSS_COMPILE=aarch64-linux-gnu-`)
- `artifact_patterns`: One pattern per line (glob patterns for artifacts to collect)

#### Environment Tab
- `custom_env`: Custom environment variables (supports JSON object or KEY=VALUE pairs)

**Form Submission Handler** transforms form values into `build_config` object:
- Splits comma-separated `extra_make_args` into array
- Splits newline-separated `artifact_patterns` into array
- Parses `custom_env` as JSON or KEY=VALUE pairs
- Handles checkboxes for boolean values
- Handles numeric inputs for `git_depth`

### 2. Backend Changes (`api/routers/infrastructure.py`)

**Added BuildConfig Import**:
```python
from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildConfig,  # Added
    Toolchain,
    ResourceUtilization,
)
```

**Updated `submit_build_job` Endpoint**:
- Creates `BuildConfig` object from `submission.build_config` dictionary
- Maps all form fields to BuildConfig parameters with appropriate defaults
- Passes BuildConfig to BuildJobConfig for job submission

**BuildConfig Parameters Handled**:
- `workspace_root` (default: `/tmp/builds`)
- `build_directory` (optional, auto-generated if None)
- `output_directory` (optional)
- `keep_workspace` (default: False)
- `kernel_config` (default: `defconfig`)
- `extra_make_args` (default: [])
- `enable_modules` (default: True)
- `build_dtbs` (default: True)
- `custom_env` (default: {})
- `artifact_patterns` (default: standard kernel artifacts)
- `git_depth` (default: 1)
- `git_submodules` (default: False)

## Testing

### Test Scripts Created
1. `test_advanced_build_config.py` - Comprehensive test with all advanced settings
2. `test_simple_build_submit.py` - Progressive tests (no config, empty config, one field)
3. `debug_build_config.py` - Debug BuildConfig object creation

### Current Status
⚠️ **API Server Needs Restart** - The running API server (PID 581336) is still using the old code. The changes have been made to the source files but need to be picked up by restarting the server.

## How to Test

### 1. Restart API Server
```bash
# Find and kill the current API server process
ps aux | grep "python.*api.server"
kill <PID>

# Start the API server again
venv/bin/python -m api.server
```

### 2. Test via curl
```bash
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/torvalds/linux.git",
    "branch": "master",
    "target_architecture": "x86_64",
    "build_config": {
      "workspace_root": "/tmp/test-builds",
      "output_directory": "/tmp/test-builds/output",
      "keep_workspace": true,
      "git_depth": 1,
      "kernel_config": "defconfig",
      "extra_make_args": ["ARCH=x86_64"],
      "custom_env": {"MAKEFLAGS": "-j8"}
    }
  }'
```

### 3. Test via Web GUI
1. Navigate to Infrastructure → Build Jobs
2. Click "Submit Build" button
3. Fill in Basic Settings (Repository URL, Branch, Architecture)
4. Expand "Advanced Settings" section
5. Configure build paths, git options, build config, and environment variables
6. Submit the job
7. Verify the job is created and the advanced settings are applied

### 4. Test via Python Script
```bash
python3 test_advanced_build_config.py
```

## Expected Behavior

### Without Advanced Settings
- Uses default values for all BuildConfig parameters
- workspace_root: `/tmp/builds`
- git_depth: 1
- kernel_config: `defconfig`
- Standard artifact patterns

### With Advanced Settings
- Uses user-provided values
- Custom workspace and output directories
- Custom git clone depth and submodule settings
- Custom kernel config and make arguments
- Custom artifact patterns
- Custom environment variables

## Integration Points

### BuildJobManager
The `BuildJobManager` receives the complete `BuildConfig` object and passes it to:
1. `SSHBuildExecutor` for actual build execution
2. Build job storage for persistence
3. Build flow tracking for progress monitoring

### SSHBuildExecutor
Uses BuildConfig parameters to:
1. Set up workspace directories
2. Clone repository with specified depth and submodules
3. Configure kernel build with specified config
4. Execute make with extra arguments and custom environment
5. Collect artifacts matching specified patterns
6. Clean up workspace based on `keep_workspace` setting

## Files Modified
- `dashboard/src/components/infrastructure/BuildJobDashboard.tsx` - Added Advanced Settings UI
- `api/routers/infrastructure.py` - Added BuildConfig creation from submission

## Files Created
- `test_advanced_build_config.py` - Comprehensive test script
- `test_simple_build_submit.py` - Progressive test script
- `debug_build_config.py` - Debug script
- `ADVANCED_BUILD_CONFIG_IMPLEMENTATION.md` - This document

## Next Steps
1. ✅ Frontend UI implemented
2. ✅ Backend API updated
3. ⏳ **Restart API server to apply changes**
4. ⏳ Test via curl/Python scripts
5. ⏳ Test via Web GUI
6. ⏳ Verify build execution uses advanced settings
7. ⏳ Document user guide for advanced settings

## Notes
- Modal width increased to 800px to accommodate advanced settings tabs
- Form uses Ant Design Tabs component for organized layout
- All fields are optional - defaults are applied if not specified
- Custom environment variables support both JSON and KEY=VALUE formats
- Artifact patterns support glob patterns (e.g., `arch/*/boot/Image`)
