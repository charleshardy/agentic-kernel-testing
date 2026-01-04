/**
 * Real-Time Status Monitor Component
 * Provides comprehensive monitoring and management of real-time connections
 * with advanced health monitoring and automatic recovery
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Card, Alert, Space, Button, Progress, Typography, Statistic, Row, Col, notification } from 'antd'
import { 
  WifiOutlined, 
  DisconnectOutlined, 
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  LineChartOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

export interface RealTimeStatusMonitorProps {
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
  onDisconnect?: () => void
  enableAutoRecovery?: boolean
  recoveryThreshold?: number // seconds without updates before attempting recovery
  showDetailedMetrics?: boolean
}

const RealTimeStatusMonitor: React.FC<RealTimeStatusMonitorProps> = ({
  isConnected,
  connectionHealth,
  lastUpdate,
  updateCount,
  errors,
  webSocketStatus,
  sseStatus,
  onReconnect,
  onDisconnect,
  enableAutoRecovery = true,
  recoveryThreshold = 30,
  showDetailedMetrics = true
}) => {
  const [autoRecoveryEnabled, setAutoRecoveryEnabled] = useState(enableAutoRecovery)
  const [recoveryAttempts, setRecoveryAttempts] = useState(0)
  const [lastRecoveryAttempt, setLastRecoveryAttempt] = useState<Date | null>(null)
  const [connectionMetrics, setConnectionMetrics] = useState({
    uptime: 0,
    downtime: 0,
    totalReconnections: 0,
    averageLatency: 0,
    dataTransferred: 0
  })

  // Auto-recovery logic
  useEffect(() => {
    if (!autoRecoveryEnabled || connectionHealth === 'healthy') {
      return
    }

    const checkConnectionHealth = () => {
      const now = new Date()
      const timeSinceLastUpdate = lastUpdate ? (now.getTime() - lastUpdate.getTime()) / 1000 : Infinity
      
      if (timeSinceLastUpdate > recoveryThreshold && (connectionHealth === 'degraded' || connectionHealth === 'disconnected')) {
        console.log(`🔄 Auto-recovery triggered: ${timeSinceLastUpdate}s since last update`)
        
        // Limit recovery attempts to prevent infinite loops
        if (recoveryAttempts < 3) {
          setRecoveryAttempts(prev => prev + 1)
          setLastRecoveryAttempt(now)
          onReconnect()
          
          notification.info({
            message: 'Auto-Recovery Triggered',
            description: `Attempting to restore connection (attempt ${recoveryAttempts + 1}/3)`,
            duration: 3
          })
        } else {
          notification.warning({
            message: 'Auto-Recovery Disabled',
            description: 'Maximum recovery attempts reached. Manual intervention required.',
            duration: 5
          })
          setAutoRecoveryEnabled(false)
        }
      }
    }

    const interval = setInterval(checkConnectionHealth, 10000) // Check every 10 seconds
    return () => clearInterval(interval)
  }, [autoRecoveryEnabled, connectionHealth, lastUpdate, recoveryThreshold, recoveryAttempts, onReconnect])

  // Reset recovery attempts when connection becomes healthy
  useEffect(() => {
    if (connectionHealth === 'healthy') {
      setRecoveryAttempts(0)
      setLastRecoveryAttempt(null)
    }
  }, [connectionHealth])

  // Update connection metrics
  useEffect(() => {
    const updateMetrics = () => {
      setConnectionMetrics(prev => ({
        ...prev,
        uptime: connectionHealth === 'healthy' ? prev.uptime + 1 : prev.uptime,
        downtime: connectionHealth === 'disconnected' ? prev.downtime + 1 : prev.downtime,
        dataTransferred: updateCount * 0.5 // Rough estimate in KB
      }))
    }

    const interval = setInterval(updateMetrics, 1000)
    return () => clearInterval(interval)
  }, [connectionHealth, updateCount])

  const getHealthIcon = () => {
    switch (connectionHealth) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '24px' }} />
      case 'degraded':
        return <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: '24px' }} />
      case 'disconnected':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '24px' }} />
      default:
        return <WifiOutlined style={{ fontSize: '24px' }} />
    }
  }

  const getHealthColor = () => {
    switch (connectionHealth) {
      case 'healthy': return '#52c41a'
      case 'degraded': return '#faad14'
      case 'disconnected': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }

  const getConnectionQuality = () => {
    if (connectionHealth === 'healthy') return 100
    if (connectionHealth === 'degraded') return 60
    return 20
  }

  const handleManualReconnect = () => {
    setRecoveryAttempts(0)
    setAutoRecoveryEnabled(true)
    onReconnect()
    
    notification.info({
      message: 'Manual Reconnection',
      description: 'Attempting to restore connection...',
      duration: 2
    })
  }

  return (
    <Card
      title={
        <Space>
          {getHealthIcon()}
          <span>Real-Time Connection Status</span>
          {connectionHealth === 'healthy' && (
            <ThunderboltOutlined style={{ color: '#52c41a' }} />
          )}
        </Space>
      }
      size="small"
      extra={
        <Space>
          {connectionHealth !== 'healthy' && (
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={handleManualReconnect}
              type="primary"
            >
              Reconnect
            </Button>
          )}
          {onDisconnect && (
            <Button
              size="small"
              icon={<DisconnectOutlined />}
              onClick={onDisconnect}
              danger
            >
              Disconnect
            </Button>
          )}
        </Space>
      }
    >
      {/* Connection Health Alert */}
      {connectionHealth !== 'healthy' && (
        <Alert
          message={
            connectionHealth === 'degraded' 
              ? 'Connection Degraded' 
              : 'Connection Lost'
          }
          description={
            connectionHealth === 'degraded'
              ? 'Some real-time features may be limited. Data will be refreshed periodically.'
              : 'Real-time updates are unavailable. Please check your connection.'
          }
          type={connectionHealth === 'degraded' ? 'warning' : 'error'}
          showIcon
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" onClick={handleManualReconnect}>
              Retry
            </Button>
          }
        />
      )}

      {/* Connection Quality */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>Connection Quality</Text>
        <Progress
          percent={getConnectionQuality()}
          strokeColor={getHealthColor()}
          size="small"
          style={{ marginTop: 4 }}
        />
      </div>

      {/* Connection Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Statistic
            title="Updates Received"
            value={updateCount}
            prefix={<LineChartOutlined />}
            valueStyle={{ fontSize: '16px' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Last Update"
            value={lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ fontSize: '14px' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Uptime"
            value={formatUptime(connectionMetrics.uptime)}
            valueStyle={{ fontSize: '14px' }}
          />
        </Col>
      </Row>

      {/* Detailed Connection Status */}
      {showDetailedMetrics && (
        <div style={{ marginBottom: 16 }}>
          <Text strong>Connection Details</Text>
          
          {/* WebSocket Status */}
          {webSocketStatus && (
            <div style={{ marginTop: 8, marginBottom: 8 }}>
              <Space>
                <ApiOutlined />
                <Text>WebSocket:</Text>
                {webSocketStatus.isConnected ? (
                  <Text type="success">Connected</Text>
                ) : webSocketStatus.isConnecting ? (
                  <Text type="warning">Connecting...</Text>
                ) : (
                  <Text type="danger">Disconnected</Text>
                )}
                {webSocketStatus.connectionAttempts > 0 && (
                  <Text type="secondary">({webSocketStatus.connectionAttempts} attempts)</Text>
                )}
              </Space>
            </div>
          )}

          {/* SSE Status */}
          {sseStatus && (
            <div style={{ marginTop: 8, marginBottom: 8 }}>
              <Space>
                <ApiOutlined />
                <Text>Server-Sent Events:</Text>
                {sseStatus.isConnected ? (
                  <Text type="success">Connected</Text>
                ) : sseStatus.isConnecting ? (
                  <Text type="warning">Connecting...</Text>
                ) : (
                  <Text type="danger">Disconnected</Text>
                )}
                {sseStatus.connectionAttempts > 0 && (
                  <Text type="secondary">({sseStatus.connectionAttempts} attempts)</Text>
                )}
              </Space>
            </div>
          )}
        </div>
      )}

      {/* Auto-Recovery Status */}
      {enableAutoRecovery && (
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Text strong>Auto-Recovery:</Text>
            <Text type={autoRecoveryEnabled ? 'success' : 'warning'}>
              {autoRecoveryEnabled ? 'Enabled' : 'Disabled'}
            </Text>
            {recoveryAttempts > 0 && (
              <Text type="secondary">
                ({recoveryAttempts}/3 attempts)
              </Text>
            )}
            {lastRecoveryAttempt && (
              <Text type="secondary">
                Last: {lastRecoveryAttempt.toLocaleTimeString()}
              </Text>
            )}
          </Space>
        </div>
      )}

      {/* Recent Errors */}
      {errors.length > 0 && (
        <div>
          <Text strong>Recent Issues</Text>
          <div style={{ 
            marginTop: 8, 
            maxHeight: 100, 
            overflow: 'auto',
            backgroundColor: '#fff2f0',
            padding: 8,
            borderRadius: 4,
            border: '1px solid #ffccc7'
          }}>
            {errors.slice(-3).map((error, index) => (
              <div key={index} style={{ 
                fontSize: '12px', 
                color: '#ff4d4f', 
                marginBottom: 4 
              }}>
                • {error}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

export default RealTimeStatusMonitor