# SSH WebSocket Connection Bug Fix

## Issue
The SSH terminal WebSocket connection was experiencing error messages when clients disconnected:
- "Cannot call 'receive' once a disconnect message has been received"
- "Unexpected ASGI message 'websocket.send', after sending 'websocket.close'"

## Root Cause
Race condition in the bidirectional communication tasks. When the WebSocket client disconnected, both the read and write tasks continued trying to operate on the closed WebSocket connection, causing error messages.

## Solution
Improved task cancellation and error handling in `api/routers/ssh_websocket.py`:

1. **Proper Task Cancellation**: Changed from `asyncio.gather()` to `asyncio.wait()` with `FIRST_COMPLETED` to properly cancel remaining tasks when one completes
2. **Better Error Handling**: Added specific handling for `RuntimeError` when WebSocket is already disconnected
3. **Graceful Cleanup**: Added `asyncio.CancelledError` handling in both read and write tasks

## Changes Made

### api/routers/ssh_websocket.py
- Replaced `asyncio.gather()` with `asyncio.wait()` for better task management
- Added task cancellation when either read or write task completes
- Added `RuntimeError` handling for disconnect scenarios
- Added `asyncio.CancelledError` handling for graceful task cancellation

## Testing
Verified with Python WebSocket client that:
- ✅ WebSocket connection establishes successfully
- ✅ SSH session is created and interactive shell opens
- ✅ Data flows bidirectionally (client → SSH and SSH → client)
- ✅ Clean disconnection without error messages
- ✅ Proper resource cleanup (SSH channel and client closed)

## Status
**FIXED** - The WebSocket SSH terminal connection now works correctly with clean error handling and proper resource cleanup.

## Usage
The SSH terminal can be accessed from the Build Server panel by clicking the terminal icon next to any registered build server. The WebSocket endpoint is:
```
ws://localhost:8000/ws/ssh/{server_id}?hostname={hostname}&username={username}
```

Frontend component: `dashboard/src/components/infrastructure/SSHTerminal.tsx`
Backend endpoint: `api/routers/ssh_websocket.py`
