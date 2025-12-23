import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Switch,
  Select,
  Input,
  Tooltip,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ClearOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Text } = Typography
const { TextArea } = Input

interface LogEntry {
  timestamp: string
  level: 'INFO' | 'ERROR' | 'WARNING' | 'DEBUG'
  source: string
  message: string
  planId?: string
  testId?: string
}

interface ExecutionConsoleProps {
  planId?: string
  height?: number
  autoScroll?: boolean
}

const ExecutionConsole: React.FC<ExecutionConsoleProps> = ({
  planId,
  height = 400,
  autoScroll = true
}) => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isStreaming, setIsStreaming] = useState(true)
  const [logLevel, setLogLevel] = useState<string>('INFO')
  const [searchTerm, setSearchTerm] = useState('')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const consoleRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Mock log data for demonstration
  useEffect(() => {
    if (!isStreaming) return

    const mockLogs: LogEntry[] = [
      {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'ExecutionService',
        message: `Starting execution plan ${planId?.slice(0, 8)}... with 3 test cases`,
        planId
      },
      {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'EnvironmentManager',
        message: 'Provisioned environment env-001 (x86_64, 2048MB)',
      },
      {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'TestRunner',
        message: 'Executing test: Test test_real_execution - normal operation',
        planId,
        testId: 'test-001'
      },
      {
        timestamp: new Date().toISOString(),
        level: 'DEBUG',
        source: 'MockRunner',
        message: 'Mock test execution completed in 1.2s',
        planId,
        testId: 'test-001'
      },
      {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'TestRunner',
        message: 'Test test-001 completed with status: PASSED',
        planId,
        testId: 'test-001'
      }
    ]

    // Simulate real-time log streaming
    const interval = setInterval(() => {
      if (logs.length < 20) { // Limit for demo
        const newLog = mockLogs[logs.length % mockLogs.length]
        setLogs(prev => [...prev, {
          ...newLog,
          timestamp: new Date().toISOString(),
          message: `${newLog.message} (${Date.now()})`
        }])
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [isStreaming, logs.length, planId])

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const getLogColor = (level: string) => {
    switch (level) {
      case 'ERROR': return '#ff4d4f'
      case 'WARNING': return '#faad14'
      case 'DEBUG': return '#722ed1'
      case 'INFO': 
      default: return '#52c41a'
    }
  }

  const filteredLogs = logs.filter(log => {
    const levelMatch = logLevel === 'ALL' || log.level === logLevel
    const searchMatch = !searchTerm || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.source.toLowerCase().includes(searchTerm.toLowerCase())
    const planMatch = !planId || log.planId === planId
    
    return levelMatch && searchMatch && planMatch
  })

  const clearLogs = () => {
    setLogs([])
  }

  const downloadLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp}] ${log.level} ${log.source}: ${log.message}`
    ).join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `execution-logs-${planId?.slice(0, 8) || 'all'}-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  return (
    <Card
      title={
        <Space>
          <Text strong>Execution Console</Text>
          {planId && <Text type="secondary">({planId.slice(0, 8)}...)</Text>}
        </Space>
      }
      extra={
        <Space>
          <Select
            value={logLevel}
            onChange={setLogLevel}
            size="small"
            style={{ width: 80 }}
            options={[
              { label: 'ALL', value: 'ALL' },
              { label: 'INFO', value: 'INFO' },
              { label: 'ERROR', value: 'ERROR' },
              { label: 'WARNING', value: 'WARNING' },
              { label: 'DEBUG', value: 'DEBUG' },
            ]}
          />
          
          <Input
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            style={{ width: 120 }}
          />
          
          <Tooltip title={isStreaming ? 'Pause streaming' : 'Resume streaming'}>
            <Button
              size="small"
              icon={isStreaming ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => setIsStreaming(!isStreaming)}
              type={isStreaming ? 'primary' : 'default'}
            />
          </Tooltip>
          
          <Tooltip title="Clear logs">
            <Button
              size="small"
              icon={<ClearOutlined />}
              onClick={clearLogs}
            />
          </Tooltip>
          
          <Tooltip title="Download logs">
            <Button
              size="small"
              icon={<DownloadOutlined />}
              onClick={downloadLogs}
            />
          </Tooltip>
          
          <Tooltip title="Toggle fullscreen">
            <Button
              size="small"
              icon={<FullscreenOutlined />}
              onClick={toggleFullscreen}
            />
          </Tooltip>
        </Space>
      }
      style={{
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 1000 : 'auto',
        height: isFullscreen ? '100vh' : 'auto',
      }}
    >
      <div
        ref={consoleRef}
        style={{
          height: isFullscreen ? 'calc(100vh - 120px)' : height,
          overflow: 'auto',
          backgroundColor: '#001529',
          color: '#fff',
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          fontSize: '12px',
          padding: '8px',
          borderRadius: '4px',
        }}
      >
        {filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
            {isStreaming ? 'Waiting for logs...' : 'No logs to display'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} style={{ marginBottom: '2px', lineHeight: '1.4' }}>
              <span style={{ color: '#666' }}>
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              {' '}
              <span style={{ 
                color: getLogColor(log.level),
                fontWeight: 'bold',
                minWidth: '60px',
                display: 'inline-block'
              }}>
                {log.level}
              </span>
              {' '}
              <span style={{ color: '#1890ff' }}>
                {log.source}:
              </span>
              {' '}
              <span style={{ color: '#fff' }}>
                {log.message}
              </span>
              {log.testId && (
                <span style={{ color: '#722ed1', marginLeft: '8px' }}>
                  [test:{log.testId.slice(0, 8)}...]
                </span>
              )}
            </div>
          ))
        )}
      </div>
      
      <div style={{ 
        marginTop: '8px', 
        fontSize: '11px', 
        color: '#666',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>
          {filteredLogs.length} entries
          {planId && ` • Plan: ${planId.slice(0, 8)}...`}
        </span>
        <Space>
          <span>Auto-scroll:</span>
          <Switch
            size="small"
            checked={autoScroll}
            onChange={(checked) => {
              // Auto-scroll logic would be handled by parent component
            }}
          />
        </Space>
      </div>
    </Card>
  )
}

export default ExecutionConsole