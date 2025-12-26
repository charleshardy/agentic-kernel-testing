import React, { useState, useEffect, useMemo } from 'react'
import { 
  Card, 
  Row, 
  Col, 
  Select, 
  Space, 
  Typography, 
  Alert, 
  Statistic,
  Progress,
  Tag,
  Tooltip
} from 'antd'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { 
  CloudServerOutlined, 
  DatabaseOutlined, 
  HddOutlined,
  WifiOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { 
  ResourceUtilizationChartsProps,
  Environment,
  ResourceMetrics,
  ResourceMetric,
  TimeRange
} from '../types/environment'

const { Title, Text } = Typography
const { Option } = Select

/**
 * Resource utilization monitoring component with real-time graphs
 * Displays CPU, memory, disk usage visualization with threshold-based warnings
 */
const ResourceUtilizationCharts: React.FC<ResourceUtilizationChartsProps> = ({
  environments,
  timeRange,
  chartType,
  metrics
}) => {
  const [selectedMetric, setSelectedMetric] = useState<string>('cpu')
  const [selectedEnvironments, setSelectedEnvironments] = useState<string[]>([])
  const [viewMode, setViewMode] = useState<'individual' | 'aggregate'>('aggregate')
  const [warningThreshold] = useState(80)
  const [criticalThreshold] = useState(95)

  // Initialize selected environments
  useEffect(() => {
    if (selectedEnvironments.length === 0 && environments.length > 0) {
      setSelectedEnvironments(environments.slice(0, 5).map(env => env.id))
    }
  }, [environments, selectedEnvironments.length])

  // Calculate aggregate resource utilization
  const aggregateUtilization = useMemo(() => {
    if (environments.length === 0) {
      return { cpu: 0, memory: 0, disk: 0, network: 0 }
    }

    const totals = environments.reduce(
      (acc, env) => ({
        cpu: acc.cpu + env.resources.cpu,
        memory: acc.memory + env.resources.memory,
        disk: acc.disk + env.resources.disk,
        network: acc.network + (env.resources.network.bytesIn + env.resources.network.bytesOut)
      }),
      { cpu: 0, memory: 0, disk: 0, network: 0 }
    )

    return {
      cpu: Math.round(totals.cpu / environments.length),
      memory: Math.round(totals.memory / environments.length),
      disk: Math.round(totals.disk / environments.length),
      network: Math.round(totals.network / environments.length / 1024 / 1024) // Convert to MB
    }
  }, [environments])

  // Get status color for progress bars
  const getProgressStatus = (value: number) => {
    if (value >= criticalThreshold) return 'exception'
    if (value >= warningThreshold) return 'active'
    return 'normal'
  }

  // Get color for chart lines based on threshold
  const getLineColor = (value: number) => {
    if (value >= criticalThreshold) return '#ff4d4f'
    if (value >= warningThreshold) return '#faad14'
    return '#52c41a'
  }

  return (
    <div>
      {/* Controls */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Text strong>View:</Text>
              <Select
                value={viewMode}
                onChange={setViewMode}
                style={{ width: 120 }}
              >
                <Option value="aggregate">Aggregate</Option>
                <Option value="individual">Individual</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Space>
              <Text strong>Metric:</Text>
              <Select
                value={selectedMetric}
                onChange={setSelectedMetric}
                style={{ width: 120 }}
              >
                <Option value="cpu">CPU</Option>
                <Option value="memory">Memory</Option>
                <Option value="disk">Disk</Option>
                <Option value="network">Network</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Aggregate Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <CloudServerOutlined style={{ color: '#1890ff' }} />
                  Average CPU Usage
                </Space>
              }
              value={aggregateUtilization.cpu}
              suffix="%"
              valueStyle={{ 
                color: getLineColor(aggregateUtilization.cpu),
                fontSize: '24px'
              }}
            />
            <Progress
              percent={aggregateUtilization.cpu}
              status={getProgressStatus(aggregateUtilization.cpu)}
              size="small"
              showInfo={false}
            />
            {aggregateUtilization.cpu >= warningThreshold && (
              <div style={{ marginTop: 8 }}>
                <Tag color="warning" icon={<WarningOutlined />}>
                  High Usage
                </Tag>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <DatabaseOutlined style={{ color: '#52c41a' }} />
                  Average Memory Usage
                </Space>
              }
              value={aggregateUtilization.memory}
              suffix="%"
              valueStyle={{ 
                color: getLineColor(aggregateUtilization.memory),
                fontSize: '24px'
              }}
            />
            <Progress
              percent={aggregateUtilization.memory}
              status={getProgressStatus(aggregateUtilization.memory)}
              size="small"
              showInfo={false}
            />
            {aggregateUtilization.memory >= warningThreshold && (
              <div style={{ marginTop: 8 }}>
                <Tag color="warning" icon={<WarningOutlined />}>
                  High Usage
                </Tag>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <HddOutlined style={{ color: '#faad14' }} />
                  Average Disk Usage
                </Space>
              }
              value={aggregateUtilization.disk}
              suffix="%"
              valueStyle={{ 
                color: getLineColor(aggregateUtilization.disk),
                fontSize: '24px'
              }}
            />
            <Progress
              percent={aggregateUtilization.disk}
              status={getProgressStatus(aggregateUtilization.disk)}
              size="small"
              showInfo={false}
            />
            {aggregateUtilization.disk >= warningThreshold && (
              <div style={{ marginTop: 8 }}>
                <Tag color="warning" icon={<WarningOutlined />}>
                  High Usage
                </Tag>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  Active Environments
                </Space>
              }
              value={environments.filter(env => env.status === 'running' || env.status === 'ready').length}
              suffix={`/ ${environments.length}`}
              valueStyle={{ fontSize: '24px' }}
            />
            <Progress
              percent={Math.round((environments.filter(env => env.status === 'running' || env.status === 'ready').length / Math.max(environments.length, 1)) * 100)}
              size="small"
              showInfo={false}
            />
          </Card>
        </Col>
      </Row>

      {/* Simple Chart Placeholder */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card
            title={
              <Space>
                <CloudServerOutlined />
                Resource Utilization Overview
                <Tag color="blue">{chartType}</Tag>
              </Space>
            }
          >
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Text type="secondary">
                Resource utilization charts will be displayed here
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Warnings and Alerts */}
      {environments.some(env => 
        env.resources.cpu >= warningThreshold || 
        env.resources.memory >= warningThreshold || 
        env.resources.disk >= warningThreshold
      ) && (
        <Alert
          message="High Resource Utilization Detected"
          description={
            <div>
              <Text>The following environments are experiencing high resource usage:</Text>
              <ul style={{ marginTop: 8, marginBottom: 0 }}>
                {environments
                  .filter(env => 
                    env.resources.cpu >= warningThreshold || 
                    env.resources.memory >= warningThreshold || 
                    env.resources.disk >= warningThreshold
                  )
                  .map(env => (
                    <li key={env.id}>
                      <Text strong>{env.id.slice(0, 12)}...</Text>
                      {env.resources.cpu >= warningThreshold && (
                        <Tag color="warning" style={{ marginLeft: 8 }}>
                          CPU: {env.resources.cpu}%
                        </Tag>
                      )}
                      {env.resources.memory >= warningThreshold && (
                        <Tag color="warning" style={{ marginLeft: 4 }}>
                          Memory: {env.resources.memory}%
                        </Tag>
                      )}
                      {env.resources.disk >= warningThreshold && (
                        <Tag color="warning" style={{ marginLeft: 4 }}>
                          Disk: {env.resources.disk}%
                        </Tag>
                      )}
                    </li>
                  ))
                }
              </ul>
            </div>
          }
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  )
}

export default ResourceUtilizationCharts