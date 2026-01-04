/**
 * Queue Status Indicator Component
 * Provides visual indicators for queue status and progress with real-time updates
 */

import React, { useEffect, useState } from 'react'
import { Badge, Progress, Space, Tooltip, Typography, Card, Row, Col } from 'antd'
import { 
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  ThunderboltOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined
} from '@ant-design/icons'
import { AllocationRequest, AllocationStatus } from '../types/environment'

const { Text } = Typography

export interface QueueStatusIndicatorProps {
  queue: AllocationRequest[]
  estimatedWaitTimes: Map<string, number>
  realTimeUpdates?: boolean
  showTrends?: boolean
  compact?: boolean
  onStatusClick?: (status: AllocationStatus) => void
}

interface QueueMetrics {
  total: number
  pending: number
  allocated: number
  failed: number
  cancelled: number
  avgWaitTime: number
  maxWaitTime: number
  allocationRate: number
  throughput: number
}

const QueueStatusIndicator: React.FC<QueueStatusIndicatorProps> = ({
  queue,
  estimatedWaitTimes,
  realTimeUpdates = false,
  showTrends = true,
  compact = false,
  onStatusClick
}) => {
  const [previousMetrics, setPreviousMetrics] = useState<QueueMetrics | null>(null)
  const [isAnimating, setIsAnimating] = useState(false)

  // Calculate current metrics
  const metrics: QueueMetrics = {
    total: queue.length,
    pending: queue.filter(r => r.status === AllocationStatus.PENDING).length,
    allocated: queue.filter(r => r.status === AllocationStatus.ALLOCATED).length,
    failed: queue.filter(r => r.status === AllocationStatus.FAILED).length,
    cancelled: queue.filter(r => r.status === AllocationStatus.CANCELLED).length,
    avgWaitTime: Array.from(estimatedWaitTimes.values()).reduce((sum, time) => sum + time, 0) / Math.max(estimatedWaitTimes.size, 1),
    maxWaitTime: Math.max(...Array.from(estimatedWaitTimes.values()), 0),
    allocationRate: queue.length > 0 ? (queue.filter(r => r.status === AllocationStatus.ALLOCATED).length / queue.length) * 100 : 0,
    throughput: 0 // Would be calculated based on historical data
  }

  // Trigger animation when metrics change significantly
  useEffect(() => {
    if (previousMetrics && realTimeUpdates) {
      const significantChange = 
        Math.abs(metrics.pending - previousMetrics.pending) > 0 ||
        Math.abs(metrics.allocated - previousMetrics.allocated) > 0 ||
        Math.abs(metrics.failed - previousMetrics.failed) > 0

      if (significantChange) {
        setIsAnimating(true)
        setTimeout(() => setIsAnimating(false), 1000)
      }
    }
    setPreviousMetrics(metrics)
  }, [metrics, previousMetrics, realTimeUpdates])

  const formatWaitTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  const getStatusColor = (status: AllocationStatus) => {
    switch (status) {
      case AllocationStatus.PENDING: return '#faad14'
      case AllocationStatus.ALLOCATED: return '#52c41a'
      case AllocationStatus.FAILED: return '#ff4d4f'
      case AllocationStatus.CANCELLED: return '#8c8c8c'
      default: return '#d9d9d9'
    }
  }

  const getStatusIcon = (status: AllocationStatus) => {
    switch (status) {
      case AllocationStatus.PENDING: return <ClockCircleOutlined />
      case AllocationStatus.ALLOCATED: return <CheckCircleOutlined />
      case AllocationStatus.FAILED: return <ExclamationCircleOutlined />
      case AllocationStatus.CANCELLED: return <ClockCircleOutlined />
      default: return <ClockCircleOutlined />
    }
  }

  const getTrendIcon = (current: number, previous: number) => {
    if (!showTrends || !previousMetrics) return null
    if (current > previous) return <TrendingUpOutlined style={{ color: '#52c41a', fontSize: '12px' }} />
    if (current < previous) return <TrendingDownOutlined style={{ color: '#ff4d4f', fontSize: '12px' }} />
    return null
  }

  const getHealthStatus = () => {
    if (metrics.failed > metrics.total * 0.2) return 'error'
    if (metrics.avgWaitTime > 300) return 'warning'
    if (metrics.allocationRate > 80) return 'success'
    return 'processing'
  }

  if (compact) {
    return (
      <Space 
        style={{ 
          animation: isAnimating ? 'queuePulse 1s ease-in-out' : undefined 
        }}
      >
        <Badge 
          count={metrics.total} 
          showZero 
          style={{ backgroundColor: '#1890ff' }}
        />
        <Progress 
          type="circle" 
          size={40}
          percent={Math.round(metrics.allocationRate)}
          strokeColor={getStatusColor(AllocationStatus.ALLOCATED)}
          format={() => `${metrics.allocated}`}
        />
        {realTimeUpdates && (
          <ThunderboltOutlined style={{ color: '#52c41a' }} />
        )}
        
        <style>{`
          @keyframes queuePulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
          }
        `}</style>
      </Space>
    )
  }

  return (
    <Card 
      size="small"
      style={{ 
        animation: isAnimating ? 'queueUpdate 1s ease-in-out' : undefined 
      }}
    >
      <Row gutter={16} align="middle">
        <Col span={6}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
              {metrics.total}
              {getTrendIcon(metrics.total, previousMetrics?.total || 0)}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>Total Requests</Text>
          </div>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div>
              <Space>
                <Text strong>Queue Status:</Text>
                {realTimeUpdates && (
                  <Badge status="processing" text="Live" />
                )}
              </Space>
            </div>
            
            <Space wrap>
              <Tooltip title={`${metrics.pending} pending requests`}>
                <Badge 
                  color={getStatusColor(AllocationStatus.PENDING)}
                  text={
                    <span 
                      style={{ cursor: onStatusClick ? 'pointer' : 'default' }}
                      onClick={() => onStatusClick?.(AllocationStatus.PENDING)}
                    >
                      Pending: {metrics.pending}
                      {getTrendIcon(metrics.pending, previousMetrics?.pending || 0)}
                    </span>
                  }
                />
              </Tooltip>
              
              <Tooltip title={`${metrics.allocated} allocated requests`}>
                <Badge 
                  color={getStatusColor(AllocationStatus.ALLOCATED)}
                  text={
                    <span 
                      style={{ cursor: onStatusClick ? 'pointer' : 'default' }}
                      onClick={() => onStatusClick?.(AllocationStatus.ALLOCATED)}
                    >
                      Allocated: {metrics.allocated}
                      {getTrendIcon(metrics.allocated, previousMetrics?.allocated || 0)}
                    </span>
                  }
                />
              </Tooltip>
              
              {metrics.failed > 0 && (
                <Tooltip title={`${metrics.failed} failed requests`}>
                  <Badge 
                    color={getStatusColor(AllocationStatus.FAILED)}
                    text={
                      <span 
                        style={{ cursor: onStatusClick ? 'pointer' : 'default' }}
                        onClick={() => onStatusClick?.(AllocationStatus.FAILED)}
                      >
                        Failed: {metrics.failed}
                        {getTrendIcon(metrics.failed, previousMetrics?.failed || 0)}
                      </span>
                    }
                  />
                </Tooltip>
              )}
            </Space>
          </Space>
        </Col>
        
        <Col span={6}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress 
                type="circle" 
                size={60}
                percent={Math.round(metrics.allocationRate)}
                strokeColor={
                  metrics.allocationRate > 80 ? '#52c41a' : 
                  metrics.allocationRate > 60 ? '#faad14' : '#ff4d4f'
                }
                format={(percent) => (
                  <div style={{ fontSize: '12px' }}>
                    <div>{percent}%</div>
                    <div style={{ fontSize: '10px' }}>Success</div>
                  </div>
                )}
              />
            </div>
            
            <div style={{ textAlign: 'center', fontSize: '11px', color: '#666' }}>
              <div>Avg Wait: {formatWaitTime(metrics.avgWaitTime)}</div>
              {metrics.maxWaitTime > 300 && (
                <div style={{ color: '#ff4d4f' }}>
                  Max: {formatWaitTime(metrics.maxWaitTime)}
                </div>
              )}
            </div>
          </Space>
        </Col>
      </Row>
      
      {/* Health Status Bar */}
      <div style={{ marginTop: 12 }}>
        <Progress 
          percent={100}
          status={getHealthStatus()}
          size="small"
          showInfo={false}
          strokeColor={
            getHealthStatus() === 'success' ? '#52c41a' :
            getHealthStatus() === 'warning' ? '#faad14' : '#ff4d4f'
          }
        />
        <div style={{ 
          textAlign: 'center', 
          fontSize: '11px', 
          marginTop: 4,
          color: 
            getHealthStatus() === 'success' ? '#52c41a' :
            getHealthStatus() === 'warning' ? '#faad14' : '#ff4d4f'
        }}>
          Queue Health: {
            getHealthStatus() === 'success' ? 'Excellent' :
            getHealthStatus() === 'warning' ? 'Needs Attention' : 'Critical'
          }
        </div>
      </div>
      
      <style>{`
        @keyframes queueUpdate {
          0% { background-color: #ffffff; }
          50% { background-color: #f0f9ff; }
          100% { background-color: #ffffff; }
        }
      `}</style>
    </Card>
  )
}

export default QueueStatusIndicator