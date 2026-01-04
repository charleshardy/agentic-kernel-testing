import React from 'react'
import { 
  Card, 
  Progress, 
  Statistic, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Tag, 
  Tooltip,
  Alert,
  Badge
} from 'antd'
import { 
  CloudServerOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  HddOutlined,
  WarningOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { CapacityMetrics, AllocationLikelihood } from '../types/environment'

const { Text, Title } = Typography

interface CapacityIndicatorProps {
  capacityMetrics: CapacityMetrics
  allocationLikelihoods?: AllocationLikelihood[]
  showDetails?: boolean
  size?: 'small' | 'default' | 'large'
}

/**
 * Component for displaying system capacity and availability indicators
 * Shows available capacity, idle environments, and allocation likelihood
 * based on current resource utilization
 */
const CapacityIndicator: React.FC<CapacityIndicatorProps> = ({
  capacityMetrics,
  allocationLikelihoods = [],
  showDetails = true,
  size = 'default'
}) => {
  // Get capacity status color
  const getCapacityStatusColor = (percentage: number) => {
    if (percentage >= 70) return '#52c41a' // Green
    if (percentage >= 40) return '#faad14' // Orange
    return '#ff4d4f' // Red
  }

  // Get utilization status
  const getUtilizationStatus = (percentage: number) => {
    if (percentage >= 90) return 'exception'
    if (percentage >= 70) return 'active'
    return 'normal'
  }

  // Calculate availability score
  const calculateAvailabilityScore = () => {
    const capacityWeight = 0.4
    const utilizationWeight = 0.3
    const healthWeight = 0.3
    
    const capacityScore = capacityMetrics.capacityPercentage
    const utilizationScore = Math.max(0, 100 - capacityMetrics.utilizationPercentage)
    const healthScore = capacityMetrics.totalEnvironments > 0 
      ? ((capacityMetrics.readyEnvironments + capacityMetrics.runningEnvironments) / capacityMetrics.totalEnvironments) * 100
      : 0
    
    return Math.round(
      capacityScore * capacityWeight + 
      utilizationScore * utilizationWeight + 
      healthScore * healthWeight
    )
  }

  // Get average allocation likelihood
  const getAverageAllocationLikelihood = () => {
    if (allocationLikelihoods.length === 0) return 0
    const total = allocationLikelihoods.reduce((sum, item) => sum + item.likelihood, 0)
    return Math.round(total / allocationLikelihoods.length)
  }

  const availabilityScore = calculateAvailabilityScore()
  const avgAllocationLikelihood = getAverageAllocationLikelihood()

  if (size === 'small') {
    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <CloudServerOutlined />
            <Text strong>Capacity</Text>
          </Space>
          <Tag color={getCapacityStatusColor(capacityMetrics.capacityPercentage)}>
            {Math.round(capacityMetrics.capacityPercentage)}%
          </Tag>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ flex: 1 }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>Available</Text>
            <div>{capacityMetrics.readyEnvironments}/{capacityMetrics.totalEnvironments}</div>
          </div>
          <div style={{ flex: 1 }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>Idle</Text>
            <div>{capacityMetrics.idleEnvironments}</div>
          </div>
        </div>
      </Space>
    )
  }

  return (
    <Card 
      title={
        <Space>
          <CloudServerOutlined />
          System Capacity & Availability
          <Badge 
            count={capacityMetrics.pendingRequestsCount} 
            style={{ backgroundColor: '#faad14' }}
            title="Pending allocation requests"
          />
        </Space>
      }
      size={size}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Overall Availability Score */}
        <div style={{ textAlign: 'center' }}>
          <Statistic
            title="System Availability Score"
            value={availabilityScore}
            suffix="%"
            valueStyle={{ 
              color: getCapacityStatusColor(availabilityScore),
              fontSize: '32px'
            }}
          />
          <Progress
            percent={availabilityScore}
            status={getUtilizationStatus(100 - availabilityScore)}
            strokeWidth={12}
            showInfo={false}
          />
        </div>

        {/* Environment Status Overview */}
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="Total"
                value={capacityMetrics.totalEnvironments}
                prefix={<CloudServerOutlined />}
                valueStyle={{ fontSize: '20px' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="Ready"
                value={capacityMetrics.readyEnvironments}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ fontSize: '20px', color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="Idle"
                value={capacityMetrics.idleEnvironments}
                prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ fontSize: '20px', color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="Running"
                value={capacityMetrics.runningEnvironments}
                prefix={<DatabaseOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ fontSize: '20px', color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Resource Utilization */}
        <div>
          <Title level={5} style={{ marginBottom: 16 }}>
            <Space>
              <HddOutlined />
              Resource Utilization
            </Space>
          </Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text>CPU</Text>
                  <Text>{Math.round(capacityMetrics.averageCpuUtilization)}%</Text>
                </div>
                <Progress
                  percent={Math.round(capacityMetrics.averageCpuUtilization)}
                  status={getUtilizationStatus(capacityMetrics.averageCpuUtilization)}
                  size="small"
                  showInfo={false}
                />
              </div>
            </Col>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text>Memory</Text>
                  <Text>{Math.round(capacityMetrics.averageMemoryUtilization)}%</Text>
                </div>
                <Progress
                  percent={Math.round(capacityMetrics.averageMemoryUtilization)}
                  status={getUtilizationStatus(capacityMetrics.averageMemoryUtilization)}
                  size="small"
                  showInfo={false}
                />
              </div>
            </Col>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text>Disk</Text>
                  <Text>{Math.round(capacityMetrics.averageDiskUtilization)}%</Text>
                </div>
                <Progress
                  percent={Math.round(capacityMetrics.averageDiskUtilization)}
                  status={getUtilizationStatus(capacityMetrics.averageDiskUtilization)}
                  size="small"
                  showInfo={false}
                />
              </div>
            </Col>
          </Row>
        </div>

        {/* Allocation Likelihood */}
        {capacityMetrics.pendingRequestsCount > 0 && (
          <div>
            <Title level={5} style={{ marginBottom: 16 }}>
              <Space>
                <InfoCircleOutlined />
                Allocation Likelihood
                <Tooltip title="Average likelihood of successful allocation for pending requests">
                  <InfoCircleOutlined style={{ color: '#1890ff', fontSize: '14px' }} />
                </Tooltip>
              </Space>
            </Title>
            <div style={{ 
              padding: 16, 
              background: '#f5f5f5', 
              borderRadius: 6,
              border: '1px solid #d9d9d9'
            }}>
              <Row gutter={16} align="middle">
                <Col flex="auto">
                  <div>
                    <Text type="secondary">Average allocation success rate</Text>
                    <div style={{ marginTop: 8 }}>
                      <Progress
                        percent={avgAllocationLikelihood}
                        status={avgAllocationLikelihood >= 70 ? 'normal' : avgAllocationLikelihood >= 40 ? 'active' : 'exception'}
                        strokeWidth={8}
                      />
                    </div>
                  </div>
                </Col>
                <Col>
                  <Statistic
                    value={avgAllocationLikelihood}
                    suffix="%"
                    valueStyle={{ 
                      fontSize: '24px',
                      color: getCapacityStatusColor(avgAllocationLikelihood)
                    }}
                  />
                </Col>
              </Row>
            </div>
          </div>
        )}

        {/* Detailed Allocation Likelihood */}
        {showDetails && allocationLikelihoods.length > 0 && (
          <div>
            <Title level={5} style={{ marginBottom: 16 }}>Request Details</Title>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {allocationLikelihoods.slice(0, 5).map((item) => (
                <div 
                  key={item.requestId}
                  style={{ 
                    padding: 12, 
                    border: '1px solid #f0f0f0', 
                    borderRadius: 4,
                    background: '#fafafa'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <Text strong>{item.requestId.slice(0, 12)}...</Text>
                    <Tag color={getCapacityStatusColor(item.likelihood)}>
                      {item.likelihood}% likely
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
                    <span>{item.compatibleEnvironments} compatible environments</span>
                    <span>~{Math.round(item.estimatedWaitTime / 60)}min wait</span>
                  </div>
                  {item.reasoning.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {item.reasoning[0]}
                      </Text>
                    </div>
                  )}
                </div>
              ))}
              {allocationLikelihoods.length > 5 && (
                <Text type="secondary" style={{ textAlign: 'center', fontSize: '12px' }}>
                  ... and {allocationLikelihoods.length - 5} more requests
                </Text>
              )}
            </Space>
          </div>
        )}

        {/* Warnings and Alerts */}
        {capacityMetrics.capacityPercentage < 30 && (
          <Alert
            message="Low Capacity Warning"
            description={`Only ${capacityMetrics.readyEnvironments} environments are ready. Consider provisioning additional capacity.`}
            type="warning"
            showIcon
            icon={<WarningOutlined />}
          />
        )}

        {capacityMetrics.utilizationPercentage > 85 && (
          <Alert
            message="High Utilization Alert"
            description="System resource utilization is high. Performance may be impacted."
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
          />
        )}

        {capacityMetrics.errorEnvironments > 0 && (
          <Alert
            message="Environment Errors Detected"
            description={`${capacityMetrics.errorEnvironments} environments are in error state and need attention.`}
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
          />
        )}
      </Space>
    </Card>
  )
}

export default CapacityIndicator