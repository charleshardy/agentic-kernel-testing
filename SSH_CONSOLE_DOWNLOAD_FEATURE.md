# SSH Console Download Feature

## Feature Description
Added download functionality to the SSH Console on the Build Server page, allowing users to save the complete session log (inputs and outputs) to a text file.

## Implementation

### Components Modified
**dashboard/src/components/infrastructure/SSHTerminal.tsx**

### New Features

#### 1. Session Logging
- All terminal inputs and outputs are captured in real-time
- Session log stored in `sessionLogRef` React ref
- Includes:
  - Connection messages
  - Server responses
  - User commands
  - Error messages
  - Disconnection messages

#### 2. Download Button
- **Icon**: Download icon (DownloadOutlined)
- **Location**: Toolbar at the top of the terminal
- **Functionality**: Downloads the complete session log as a text file
- **Filename Format**: `ssh-session-{hostname}-{timestamp}.txt`
  - Example: `ssh-session-pek-lpgtest16-2026-01-16T11-45-30.txt`
- **Processing**: Automatically removes ANSI escape codes for clean, readable output
- **Disabled State**: Button is disabled when there's no session data

#### 3. Clear Button
- **Icon**: Clear icon (ClearOutlined)
- **Location**: Toolbar at the top of the terminal
- **Functionality**: Clears the terminal display and session log
- **Feedback**: Shows success message after clearing

#### 4. Connection Status Indicator
- **Location**: Toolbar at the top of the terminal
- **States**:
  - 🟢 Connected (green): "● Connected to {hostname}"
  - 🔴 Disconnected (red): "● Disconnected"
- **Real-time Updates**: Status updates automatically on connection/disconnection

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ● Connected to pek-lpgtest16    [Download] [Clear]          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Terminal Output Area                                        │
│  (SSH session with xterm.js)                                │
│                                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Technical Details

#### Session Log Capture
```typescript
// Captures all data flowing through the terminal
sessionLogRef.current += data

// Removes ANSI escape codes for clean download
const cleanLog = sessionLogRef.current.replace(/\x1b\[[0-9;]*m/g, '')
```

#### Download Implementation
```typescript
// Creates a downloadable text file
const blob = new Blob([cleanLog], { type: 'text/plain' })
const url = URL.createObjectURL(blob)
const link = document.createElement('a')
link.download = `ssh-session-${hostname}-${timestamp}.txt`
link.click()
```

### User Benefits

1. **Session Documentation**: Save complete SSH sessions for:
   - Troubleshooting records
   - Audit trails
   - Training materials
   - Bug reports

2. **Clean Output**: ANSI escape codes are automatically removed, providing:
   - Readable plain text
   - Easy to share
   - Compatible with any text editor

3. **Timestamped Files**: Each download includes a timestamp:
   - Easy to organize multiple sessions
   - Chronological ordering
   - No filename conflicts

4. **Connection Monitoring**: Visual indicator shows:
   - Current connection status
   - When SSH session is active
   - When connection is lost

### Usage

1. **Open SSH Console**: Click the terminal icon next to any build server
2. **Interact with Server**: Run commands, view outputs
3. **Download Session**: Click the "Download" button in the toolbar
4. **Clear Terminal** (optional): Click "Clear" to reset the display
5. **File Location**: Check your browser's download folder for the session log

### Example Session Log

```
Initializing connection to pek-lpgtest16...
WebSocket connected, establishing SSH session...
Connected to pek-lpgtest16

Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-139-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Last login: Thu Jan 16 11:30:15 2026 from 192.168.1.100
lliu2@pek-lpgtest16:~$ ls -la
total 48
drwxr-xr-x 6 lliu2 lliu2 4096 Jan 16 11:30 .
drwxr-xr-x 3 root  root  4096 Dec 10 10:15 ..
-rw------- 1 lliu2 lliu2  220 Dec 10 10:15 .bash_logout
...
lliu2@pek-lpgtest16:~$ exit
logout

Connection closed (code: 1000)
```

### Future Enhancements

Potential improvements:
1. **Export Formats**: Add JSON, HTML, or Markdown export options
2. **Session Recording**: Add video-like playback of terminal sessions
3. **Search**: Add search functionality within the session log
4. **Filtering**: Filter by command, output, or timestamp
5. **Auto-save**: Automatically save sessions at intervals
6. **Cloud Storage**: Upload sessions to cloud storage services

## Status
**IMPLEMENTED** - Download and clear functionality is now available in the SSH Console on the Build Server page.
