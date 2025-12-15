import React, { useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, List, Tag, Space, Typography, Alert } from 'antd'
import {
  ExperimentOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useDashboardStore } from '../store'
import apiService from '../services/api'
import webSocketService from '../services/websocket'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const {
    systemMetrics,
    activeExecutions,
    recentResults,
    isConnected,
    setSystemMetrics,
    updateActiveExecutions,
    addTestResult,
  } = useDashboardStore()

  // Fetch system metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery(
    'systemMetrics',
    () => apiService.getSystemMetrics(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      onSuccess: (data) => setSystemMetrics(data),
    }
  )

  // Fetch active executions
  const { data: executions } = useQuery(
    'activeExecutions',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
      onSuccess: (data) => updateActiveExecutions(data),
    }
  )

  // Fetch recent test results
  const { data: resultsData } = useQuery(
    'recentResults',
    () => apiService.getTestResults({ page: 1, page_size: 10 }),
    {
      refetchInterval: 15000, // Refresh every 15 seconds
    }
  )

  // Note: WebSocket events removed - using HTTP polling instead via React Query

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return '#52c41a'
      case 'failed': return '#ff4d4f'
      case 'running': return '#1890ff'
      case 'pending': return '#faad14'
      default: return '#d9d9d9'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'running': return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'pending': return <ClockCircleOutlined style={{ color: '#faad14' }} />
      default: return <WarningOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  // Mock data for charts (replace with real data)
  const testTrendData = [
    { time: '00:00', passed: 45, failed: 5, running: 10 },
    { time: '04:00', passed: 52, failed: 3, running: 8 },
    { time: '08:00', passed: 48, failed: 7, running: 12 },
    { time: '12:00', passed: 55, failed: 2, running: 15 },
    { time: '16:00', passed: 50, failed: 4, running: 9 },
    { time: '20:00', passed: 47, failed: 6, running: 11 },
  ]

  const statusDistribution = [
    { name: 'Passed', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.7) : 35, color: '#52c41a' },
    { name: 'Failed', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.1) : 5, color: '#ff4d4f' },
    { name: 'Running', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.15) : 8, color: '#1890ff' },
    { name: 'Pending', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.05) : 2, color: '#faad14' },
  ]

  if (!isConnected) {
    return (
      <Alert
        message="Connection Lost"
        description="Unable to connect to the testing system. Please check your connection and try again."
        type="error"
        showIcon
        style={{ margin: '20px 0' }}
      />
    )
  }

  return (
    <div>
      <Title level={2}>Dashboard</Title>
      
      {/* System Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Tests"
              value={systemMetrics?.active_tests || 0}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Queued Tests"
              value={systemMetrics?.queued_tests || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Available Environments"
              value={systemMetrics?.available_environments || 0}
              suffix={`/ ${systemMetrics?.total_environments || 0}`}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="System Load"
              value={systemMetrics ? Math.round(systemMetrics.cpu_usage * 100) : 0}
              suffix="%"
              prefix={<LoadingOutlined />}
              valueStyle={{ 
                color: systemMetrics && systemMetrics.cpu_usage > 0.8 ? '#ff4d4f' : '#52c41a' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Resource Usage */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Resource Usage" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>CPU Usage</Text>
                <Progress 
                  percent={systemMetrics ? Math.round(systemMetrics.cpu_usage * 100) : 0}
                  status={systemMetrics && systemMetrics.cpu_usage > 0.8 ? 'exception' : 'normal'}
                />
              </div>
              <div>
                <Text>Memory Usage</Text>
                <Progress 
                  percent={systemMetrics ? Math.round(systemMetrics.memory_usage * 100) : 0}
                  status={systemMetrics && systemMetrics.memory_usage > 0.9 ? 'exception' : 'normal'}
                />
              </div>
              <div>
                <Text>Disk Usage</Text>
                <Progress 
                  percent={systemMetrics ? Math.round(systemMetrics.disk_usage * 100) : 0}
                  status={systemMetrics && systemMetrics.disk_usage > 0.9 ? 'exception' : 'normal'}
                />
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Test Status Distribution" size="small">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Test Trends and Active Executions */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="Test Execution Trends (24h)" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={testTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="passed" stroke="#52c41a" strokeWidth={2} />
                <Line type="monotone" dataKey="failed" stroke="#ff4d4f" strokeWidth={2} />
                <Line type="monotone" dataKey="running" stroke="#1890ff" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Active Executions" size="small">
            <List
              size="small"
              dataSource={activeExecutions}
              renderItem={(execution) => (
                <List.Item>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text strong>{execution.plan_id.slice(0, 8)}...</Text>
                      <Tag color={getStatusColor(execution.overall_status)}>
                        {execution.overall_status}
                      </Tag>
                    </div>
                    <Progress 
                      percent={Math.round(execution.progress * 100)}
                      size="small"
                      status={execution.overall_status === 'failed' ? 'exception' : 'normal'}
                    />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {execution.completed_tests}/{execution.total_tests} tests completed
                    </Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Recent Test Results */}
      <Row>
        <Col span={24}>
          <Card title="Recent Test Results" size="small">
            <List
              dataSource={resultsData?.results || recentResults}
              renderItem={(result) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getStatusIcon(result.status)}
                    title={
                      <Space>
                        <Text>{result.test_id}</Text>
                        <Tag color={getStatusColor(result.status)}>
                          {result.status}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary">
                          Execution time: {result.execution_time.toFixed(2)}s
                        </Text>
                        <Text type="secondary">
                          {new Date(result.timestamp).toLocaleString()}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard