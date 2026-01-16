import React, { useEffect, useRef, useState } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'
import { message, Button, Space, Tooltip } from 'antd'
import { DownloadOutlined, ClearOutlined } from '@ant-design/icons'

interface SSHTerminalProps {
  serverId: string
  hostname: string
  username: string
  sshKeyPath?: string
  onDownload?: (content: string) => void
}

const SSHTerminal: React.FC<SSHTerminalProps> = ({ serverId, hostname, username, sshKeyPath, onDownload }) => {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<Terminal | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const sessionLogRef = useRef<string>('')
  const [isConnected, setIsConnected] = useState(false)

  // Function to download session log
  const downloadSessionLog = () => {
    if (!sessionLogRef.current) {
      message.warning('No session data to download')
      return
    }

    try {
      // Create a clean version of the log (remove ANSI escape codes)
      const cleanLog = sessionLogRef.current.replace(/\x1b\[[0-9;]*m/g, '')
      
      // Create blob and download
      const blob = new Blob([cleanLog], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      link.download = `ssh-session-${hostname}-${timestamp}.txt`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      message.success('Session log downloaded successfully')
      
      // Call optional callback
      if (onDownload) {
        onDownload(cleanLog)
      }
    } catch (error) {
      console.error('Error downloading session log:', error)
      message.error('Failed to download session log')
    }
  }

  // Function to clear terminal
  const clearTerminal = () => {
    if (xtermRef.current) {
      xtermRef.current.clear()
      sessionLogRef.current = ''
      message.success('Terminal cleared')
    }
  }

  useEffect(() => {
    if (!terminalRef.current) return

    // Create terminal instance
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      rows: 30,
      cols: 120
    })

    // Add addons
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())

    // Open terminal
    term.open(terminalRef.current)
    fitAddon.fit()

    // Store refs
    xtermRef.current = term
    fitAddonRef.current = fitAddon

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/ssh/${serverId}?hostname=${hostname}&username=${username}${sshKeyPath ? `&ssh_key_path=${sshKeyPath}` : ''}`
    
    console.log('[SSH Terminal] Connecting to WebSocket:', wsUrl)
    const initMsg = '\x1b[1;33mInitializing connection to ' + hostname + '...\x1b[0m'
    term.writeln(initMsg)
    sessionLogRef.current += initMsg + '\n'
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[SSH Terminal] WebSocket connection opened')
      setIsConnected(true)
      const msg = '\x1b[1;32mWebSocket connected, establishing SSH session...\x1b[0m'
      term.writeln(msg)
      sessionLogRef.current += msg + '\n'
    }

    ws.onmessage = (event) => {
      console.log('[SSH Terminal] Received message, type:', typeof event.data)
      if (typeof event.data === 'string') {
        term.write(event.data)
        sessionLogRef.current += event.data
      } else if (event.data instanceof Blob) {
        event.data.text().then(text => {
          console.log('[SSH Terminal] Blob data:', text.substring(0, 100))
          term.write(text)
          sessionLogRef.current += text
        })
      } else {
        console.log('[SSH Terminal] Unknown data type:', event.data)
      }
    }

    ws.onerror = (error) => {
      console.error('[SSH Terminal] WebSocket error:', error)
      const msg = '\r\n\x1b[1;31mWebSocket error occurred\x1b[0m'
      term.writeln(msg)
      sessionLogRef.current += msg + '\n'
      message.error('Connection error')
    }

    ws.onclose = (event) => {
      console.log('[SSH Terminal] WebSocket closed - Code:', event.code, 'Reason:', event.reason, 'Clean:', event.wasClean)
      setIsConnected(false)
      let msg = ''
      if (event.code === 1000) {
        msg = '\r\n\x1b[1;32mConnection closed normally\x1b[0m'
        term.writeln(msg)
      } else if (event.code === 1006) {
        msg = '\r\n\x1b[1;31mConnection closed abnormally (no close frame)\x1b[0m\n'
        msg += '\x1b[1;33mThis usually means the server closed the connection unexpectedly.\x1b[0m'
        term.writeln('\r\n\x1b[1;31mConnection closed abnormally (no close frame)\x1b[0m')
        term.writeln('\x1b[1;33mThis usually means the server closed the connection unexpectedly.\x1b[0m')
      } else {
        msg = `\r\n\x1b[1;33mConnection closed (code: ${event.code})\x1b[0m`
        term.writeln(msg)
      }
      sessionLogRef.current += msg + '\n'
    }

    // Handle terminal input - send to WebSocket
    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
        // Log user input (visible characters only)
        if (data.charCodeAt(0) >= 32 || data === '\r' || data === '\n') {
          sessionLogRef.current += data
        }
      }
    })

    // Handle resize
    const handleResize = () => {
      fitAddon.fit()
      // Send resize info to server if needed
      if (ws.readyState === WebSocket.OPEN) {
        const dims = { cols: term.cols, rows: term.rows }
        // Could send resize command to SSH if backend supports it
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
      term.dispose()
    }
  }, [serverId, hostname, username, sshKeyPath])

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <div style={{ 
        padding: '8px 10px', 
        backgroundColor: '#2d2d2d', 
        borderBottom: '1px solid #3e3e3e',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Space>
          <span style={{ color: '#d4d4d4', fontSize: '12px' }}>
            {isConnected ? (
              <span style={{ color: '#0dbc79' }}>● Connected to {hostname}</span>
            ) : (
              <span style={{ color: '#cd3131' }}>● Disconnected</span>
            )}
          </span>
        </Space>
        <Space>
          <Tooltip title="Download session log">
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={downloadSessionLog}
              disabled={!sessionLogRef.current}
            >
              Download
            </Button>
          </Tooltip>
          <Tooltip title="Clear terminal">
            <Button 
              size="small" 
              icon={<ClearOutlined />}
              onClick={clearTerminal}
            >
              Clear
            </Button>
          </Tooltip>
        </Space>
      </div>
      
      {/* Terminal */}
      <div style={{ flex: 1, padding: '10px', backgroundColor: '#1e1e1e', overflow: 'hidden' }}>
        <div ref={terminalRef} style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  )
}

export default SSHTerminal
