/**
 * Connection Status Component
 * Displays real-time connection health and provides manual reconnection controls
 */

import React from 'react'
import { Badge, Button, Tooltip, Space, Typography, Popover, Descriptions } from 'antd'
import { 
  WifiOutlined, 
  DisconnectOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'

const { Text } = Typography

export interface ConnectionStatusProps {
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
  showDetails?: boolean
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
  showDetails = true
}) => {
  // Get status badge configuration
  const getStatusBadge = () => {
    switch (connectionHealth) {
      case 'healthy':
        return {
          status: 'success' as const,
          text: 'Connected',
          icon: <WifiOutlined />,
          color: '#52c41a'
        }
      case 'degraded':
        return {
          status: 'warning' as const,
          text: 'Degraded',
          icon: <ExclamationCircleOutlined />,
          color: '#faad14'
        }
      case 'disconnected':
      default:
        return {
          status: 'error' as const,
          text: 'Disconnected',
          icon: <DisconnectOutlined />,
          color: '#ff4d4f'
        }
    }
  }

  const statusBadge = getStatusBadge()

  // Connection details for popover
  const connectionDetails = (
    <div style={{ width: 300 }}>
      <Descriptions size="small" column={1}>
        <Descriptions.Item label="Overall Status">
          <Badge status={statusBadge.status} text={statusBadge.text} />
        </Descriptions.Item>
        
        <Descriptions.Item label="Last Update">
          {lastUpdate ? (
            <Text>{lastUpdate.toLocaleTimeString()}</Text>
          ) : (
            <Text type="secondary">Never</Text>
          )}
        </Descriptions.Item>
        
        <Descriptions.Item label="Updates Received">
          <Text>{updateCount}</Text>
        </Descriptions.Item>

        {webSocketStatus && (
          <Descriptions.Item label="WebSocket">
            <Space>
              <Badge 
                status={webSocketStatus.isConnected ? 'success' : webSocketStatus.isConnecting ? 'processing' : 'error'} 
                text={webSocketStatus.isConnected ? 'Connected' : webSocketStatus.isConnecting ? 'Connecting...' : 'Disconnected'} 
              />
              {webSocketStatus.connectionAttempts > 0 && (
                <Text type="secondary">({webSocketStatus.connectionAttempts} attempts)</Text>
              )}
            </Space>
          </Descriptions.Item>
        )}

        {sseStatus && (
          <Descriptions.Item label="Server-Sent Events">
            <Space>
              <Badge 
                status={sseStatus.isConnected ? 'success' : sseStatus.isConnecting ? 'processing' : 'error'} 
                text={sseStatus.isConnected ? 'Connected' : sseStatus.isConnecting ? 'Connecting...' : 'Disconnected'} 
              />
              {sseStatus.connectionAttempts > 0 && (
                <Text type="secondary">({sseStatus.connectionAttempts} attempts)</Text>
              )}
            </Space>
          </Descriptions.Item>
        )}

        {errors.length > 0 && (
          <Descriptions.Item label="Recent Errors">
            <div style={{ maxHeight: 100, overflowY: 'auto' }}>
              {errors.slice(-3).map((error, index) => (
                <div key={index}>
                  <Text type="danger" style={{ fontSize: '12px' }}>
                    {error}
                  </Text>
                </div>
              ))}
            </div>
          </Descriptions.Item>
        )}
      </Descriptions>

      <div style={{ marginTop: 12, textAlign: 'center' }}>
        <Button 
          size="small" 
          icon={<ReloadOutlined />} 
          onClick={onReconnect}
          disabled={connectionHealth === 'healthy'}
        >
          Reconnect
        </Button>
      </div>
    </div>
  )

  if (!showDetails) {
    // Simple badge version
    return (
      <Tooltip title={`Connection: ${statusBadge.text}`}>
        <Badge status={statusBadge.status} />
      </Tooltip>
    )
  }

  // Full status display
  return (
    <Space size="small">
      <Popover 
        content={connectionDetails} 
        title="Connection Status" 
        trigger="hover"
        placement="bottomRight"
      >
        <Space size="small" style={{ cursor: 'pointer' }}>
          <span style={{ color: statusBadge.color }}>
            {statusBadge.icon}
          </span>
          <Text style={{ color: statusBadge.color, fontSize: '12px' }}>
            {statusBadge.text}
          </Text>
          <InfoCircleOutlined style={{ color: '#1890ff', fontSize: '12px' }} />
        </Space>
      </Popover>

      {connectionHealth !== 'healthy' && (
        <Button 
          size="small" 
          type="text" 
          icon={<ReloadOutlined />} 
          onClick={onReconnect}
          style={{ padding: '0 4px' }}
        />
      )}

      {lastUpdate && (
        <Text type="secondary" style={{ fontSize: '11px' }}>
          {updateCount > 0 && `${updateCount} updates`}
        </Text>
      )}
    </Space>
  )
}

export default ConnectionStatus