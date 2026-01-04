import React, { useState, useEffect } from 'react'
import { Badge, Tooltip, Space, Button, Progress, Popover, Typography } from 'antd'
import { 
  WifiOutlined, 
  DisconnectOutlined, 
  ReloadOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  ApiOutlined
} from '@ant-design/icons'

const { Text } = Typography

interface ConnectionStatusProps {
  isConnected: boolean
  connectionHealth: 'healthy' | 'degraded' | 'disconnected'
  lastUpdate: Date | null
  updateCount: number
  errors: string[]
  webSocketStatus?: {
    isConnected: boolean
    isConnecting: boolean
    connectionAttempts: number
    lastError: string | null
  } | null
  sseStatus?: {
    isConnected: boolean
    isConnecting: boolean
    connectionAttempts: number
    lastError: string | null
  } | null
  onReconnect: () => void
  showDetails: boolean
  enableHealthMonitoring?: boolean
  connectionQuality?: number // 0-100 representing connection quality
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  connectionHealth,
  lastUpdate,
  updateCount,
  errors,
  webSocketStatus,
  sseStatus,
  onReconnect,
  showDetails,
  enableHealthMonitoring = true,
  connectionQuality = 100
}) => {
  const [isBlinking, setIsBlinking] = useState(false)
  const [healthHistory, setHealthHistory] = useState<Array<{ time: Date, health: string }>>([])

  // Track connection health changes for blinking animation
  useEffect(() => {
    if (connectionHealth === 'degraded' || connectionHealth === 'disconnected') {
      setIsBlinking(true)
      const timer = setTimeout(() => setIsBlinking(false), 3000)
      return () => clearTimeout(timer)
    }
  }, [connectionHealth])

  // Track health history for monitoring
  useEffect(() => {
    if (enableHealthMonitoring) {
      setHealthHistory(prev => [
        { time: new Date(), health: connectionHealth },
        ...prev.slice(0, 9) // Keep last 10 entries
      ])
    }
  }, [connectionHealth, enableHealthMonitoring])

  const getStatusColor = () => {
    switch (connectionHealth) {
      case 'healthy': return 'success'
      case 'degraded': return 'warning'
      case 'disconnected': return 'error'
      default: return 'default'
    }
  }

  const getStatusText = () => {
    switch (connectionHealth) {
      case 'healthy': return 'Connected'
      case 'degraded': return 'Degraded'
      case 'disconnected': return 'Disconnected'
      default: return 'Unknown'
    }
  }

  const getStatusIcon = () => {
    switch (connectionHealth) {
      case 'healthy': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'degraded': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
      case 'disconnected': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <WifiOutlined />
    }
  }

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Never'
    const now = new Date()
    const diff = now.getTime() - lastUpdate.getTime()
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    return lastUpdate.toLocaleTimeString()
  }

  const getConnectionQualityColor = () => {
    if (connectionQuality >= 80) return '#52c41a'
    if (connectionQuality >= 60) return '#faad14'
    return '#ff4d4f'
  }

  // Detailed connection information for popover
  const connectionDetails = (
    <div style={{ minWidth: 300 }}>
      <div style={{ marginBottom: 16 }}>
        <Text strong>Connection Status</Text>
        <div style={{ marginTop: 8 }}>
          <Space>
            {getStatusIcon()}
            <Text>{getStatusText()}</Text>
            {connectionQuality < 100 && (
              <Progress 
                percent={connectionQuality} 
                size="small" 
                strokeColor={getConnectionQualityColor()}
                format={() => `${connectionQuality}%`}
              />
            )}
          </Space>
        </div>
      </div>

      {/* WebSocket Status */}
      {webSocketStatus && (
        <div style={{ marginBottom: 12 }}>
          <Text strong>WebSocket</Text>
          <div style={{ marginTop: 4, fontSize: '12px' }}>
            <div>
              Status: {webSocketStatus.isConnected ? 
                <Text type="success">Connected</Text> : 
                webSocketStatus.isConnecting ? 
                <Text type="warning">Connecting...</Text> : 
                <Text type="danger">Disconnected</Text>
              }
            </div>
            {webSocketStatus.connectionAttempts > 0 && (
              <div>Attempts: {webSocketStatus.connectionAttempts}</div>
            )}
            {webSocketStatus.lastError && (
              <div style={{ color: '#ff4d4f' }}>
                Error: {webSocketStatus.lastError}
              </div>
            )}
          </div>
        </div>
      )}

      {/* SSE Status */}
      {sseStatus && (
        <div style={{ marginBottom: 12 }}>
          <Text strong>Server-Sent Events</Text>
          <div style={{ marginTop: 4, fontSize: '12px' }}>
            <div>
              Status: {sseStatus.isConnected ? 
                <Text type="success">Connected</Text> : 
                sseStatus.isConnecting ? 
                <Text type="warning">Connecting...</Text> : 
                <Text type="danger">Disconnected</Text>
              }
            </div>
            {sseStatus.connectionAttempts > 0 && (
              <div>Attempts: {sseStatus.connectionAttempts}</div>
            )}
            {sseStatus.lastError && (
              <div style={{ color: '#ff4d4f' }}>
                Error: {sseStatus.lastError}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Update Statistics */}
      <div style={{ marginBottom: 12 }}>
        <Text strong>Update Statistics</Text>
        <div style={{ marginTop: 4, fontSize: '12px' }}>
          <div>Total Updates: {updateCount}</div>
          <div>Last Update: {formatLastUpdate()}</div>
          {lastUpdate && (
            <div>
              Update Rate: {updateCount > 0 ? 
                `${(updateCount / ((Date.now() - lastUpdate.getTime()) / 60000)).toFixed(1)} per min` : 
                'N/A'
              }
            </div>
          )}
        </div>
      </div>

      {/* Recent Errors */}
      {errors.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <Text strong>Recent Errors</Text>
          <div style={{ marginTop: 4, fontSize: '11px', maxHeight: 100, overflow: 'auto' }}>
            {errors.slice(-3).map((error, index) => (
              <div key={index} style={{ color: '#ff4d4f', marginBottom: 2 }}>
                • {error}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Health History */}
      {enableHealthMonitoring && healthHistory.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <Text strong>Health History</Text>
          <div style={{ marginTop: 4, fontSize: '11px' }}>
            {healthHistory.slice(0, 5).map((entry, index) => (
              <div key={index} style={{ marginBottom: 2 }}>
                {entry.time.toLocaleTimeString()}: {entry.health}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ textAlign: 'center', marginTop: 16 }}>
        <Button
          size="small"
          icon={<ReloadOutlined />}
          onClick={onReconnect}
          type="primary"
          disabled={connectionHealth === 'healthy'}
        >
          Reconnect
        </Button>
      </div>
    </div>
  )

  if (!showDetails) {
    return (
      <Popover content={connectionDetails} title="Connection Details" trigger="hover">
        <div style={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: 4,
          animation: isBlinking ? 'connectionBlink 1s infinite' : undefined
        }}>
          <Badge status={getStatusColor()} />
          <Text style={{ fontSize: '12px' }}>{getStatusText()}</Text>
          {connectionHealth === 'healthy' && (
            <ThunderboltOutlined style={{ color: '#52c41a', fontSize: '12px' }} />
          )}
        </div>
      </Popover>
    )
  }

  return (
    <Popover content={connectionDetails} title="Connection Details" trigger="click">
      <Space style={{ 
        cursor: 'pointer',
        animation: isBlinking ? 'connectionBlink 1s infinite' : undefined
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {getStatusIcon()}
          <div style={{ fontSize: '12px' }}>
            <div style={{ fontWeight: 'bold' }}>{getStatusText()}</div>
            <div style={{ color: '#666' }}>
              <ClockCircleOutlined style={{ marginRight: 4 }} />
              Updates: {updateCount}
            </div>
            <div style={{ color: '#666' }}>
              Last: {formatLastUpdate()}
            </div>
            {connectionQuality < 100 && (
              <div style={{ color: getConnectionQualityColor() }}>
                Quality: {connectionQuality}%
              </div>
            )}
          </div>
        </div>
        {connectionHealth !== 'healthy' && (
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              onReconnect()
            }}
            type="link"
            style={{ padding: 0 }}
          >
            Reconnect
          </Button>
        )}
      </Space>
      
      {/* Inject CSS for blinking animation */}
      <style>{`
        @keyframes connectionBlink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </Popover>
  )
}

export default ConnectionStatus