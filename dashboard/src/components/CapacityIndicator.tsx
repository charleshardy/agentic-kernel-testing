import React from 'react'
import { Card, Progress, Row, Col, Statistic, Space, Tag } from 'antd'
import { CloudServerOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { CapacityMetrics } from '../types/environment'

interface CapacityIndicatorProps {
  capacityMetrics: CapacityMetrics
  showDetails: boolean
  size: 'small' | 'default' | 'large'
}

const CapacityIndicator: React.FC<CapacityIndicatorProps> = ({
  capacityMetrics,
  showDetails,
  size
}) => {
  const utilizationPercentage = capacityMetrics.totalCapacity > 0 ? 
    Math.round((capacityMetrics.usedCapacity / capacityMetrics.totalCapacity) * 100) : 0

  const getUtilizationColor = () => {
    if (utilizationPercentage >= 90) return '#ff4d4f'
    if (utilizationPercentage >= 75) return '#faad14'
    if (utilizationPercentage >= 50) return '#1890ff'
    return '#52c41a'
  }

  const getCapacityStatus = () => {
    if (utilizationPercentage >= 90) return { text: 'Critical', color: 'red', icon: <ExclamationCircleOutlined /> }
    if (utilizationPercentage >= 75) return { text: 'High', color: 'orange', icon: <ExclamationCircleOutlined /> }
    if (utilizationPercentage >= 50) return { text: 'Moderate', color: 'blue', icon: <CheckCircleOutlined /> }
    return { text: 'Good', color: 'green', icon: <CheckCircleOutlined /> }
  }

  const status = getCapacityStatus()

  if (!showDetails) {
    return (
      <Space>
        <CloudServerOutlined />
        <Progress 
          percent={utilizationPercentage} 
          size="small" 
          strokeColor={getUtilizationColor()}
          style={{ width: 100 }}
        />
        <Tag color={status.color}>{status.text}</Tag>
      </Space>
    )
  }

  return (
    <Card 
      title={
        <Space>
          <CloudServerOutlined />
          System Capacity Overview
          <Tag color={status.color} icon={status.icon}>
            {status.text}
          </Tag>
        </Space>
      }
      size={size}
    >
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Total Capacity"
              value={capacityMetrics.totalCapacity}
              suffix="environments"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Used Capacity"
              value={capacityMetrics.usedCapacity}
              suffix={`/ ${capacityMetrics.totalCapacity}`}
              valueStyle={{ color: getUtilizationColor() }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Available"
              value={capacityMetrics.availableCapacity}
              suffix="environments"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <div style={{ marginBottom: 8 }}>
            <strong>Capacity Utilization</strong>
          </div>
          <Progress
            percent={utilizationPercentage}
            strokeColor={getUtilizationColor()}
            trailColor="#f0f0f0"
            strokeWidth={20}
            format={(percent) => `${percent}% (${capacityMetrics.usedCapacity}/${capacityMetrics.totalCapacity})`}
          />
        </Col>
      </Row>

      {(capacityMetrics.utilizationRate !== undefined || capacityMetrics.queueLength !== undefined) && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {capacityMetrics.utilizationRate !== undefined && (
            <Col span={12}>
              <Card size="small">
                <Statistic
                  title="Utilization Rate"
                  value={Math.round(capacityMetrics.utilizationRate * 100)}
                  suffix="%"
                  valueStyle={{ 
                    color: capacityMetrics.utilizationRate > 0.8 ? '#ff4d4f' : 
                           capacityMetrics.utilizationRate > 0.6 ? '#faad14' : '#52c41a' 
                  }}
                />
              </Card>
            </Col>
          )}
          {capacityMetrics.queueLength !== undefined && (
            <Col span={12}>
              <Card size="small">
                <Statistic
                  title="Queue Length"
                  value={capacityMetrics.queueLength}
                  suffix="requests"
                  valueStyle={{ 
                    color: capacityMetrics.queueLength > 10 ? '#ff4d4f' : 
                           capacityMetrics.queueLength > 5 ? '#faad14' : '#52c41a' 
                  }}
                />
              </Card>
            </Col>
          )}
        </Row>
      )}
    </Card>
  )
}

export default CapacityIndicator