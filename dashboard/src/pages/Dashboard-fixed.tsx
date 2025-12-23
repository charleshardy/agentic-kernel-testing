import React from 'react'
import { Row, Col, Card, Statistic, Progress, List, Tag, Space, Typography, Alert, Badge } from 'antd'
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
import apiService, { ExecutionPlanStatus, TestResult } from '../services/api'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const {
    systemMetrics,
    activeExecutions,
    recentResults,
    isConnected,
    setSystemMetrics,
    setConnectionStatus,
    updateActiveExecutions,
  } = useDashboardStore()

  // Set connection status to true initially
  React.useEffect(() => {
    setConnectionStatus(true)
  }, [setConnectionStatus])

  // Simplified health check with better error handling
  const { data: healthData, isError: healthError } = useQuery(
    'healthData',
    () => apiService.getHealth(),
    {
      refetchInterval: 30000,
      onSuccess: (data) => {
        setConnectionStatus(true)
        const metrics = {
          active_tests: data.components?.test_orchestrator?.active_tests || 0,
          queued_tests: 0,
          available_environments: data.components?.environment_manager?.available_environments || 0,
          total_environments: data.components?.environment_manager?.available_environments || 0,
          cpu_usage: data.metrics?.cpu_usage || 0,
          memory_usage: data.metrics?.memory_usage || 0,
          disk_usage: data.metrics?.disk_usage || 0,
          network_io: {}
        }
        setSystemMetrics(metrics)
      },
      onError: (error) => {
        console.log('Health endpoint not available, using demo mode:', error)
        setConnectionStatus(true)
      },
      retry: false,
    }
  )

  // Simplified active executions fetch
  const { data: executions } = useQuery(
    'activeExecutions',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 10000,
      onSuccess: (data) => updateActiveExecutions(data),
      onError: (error) => {
        console.log('Active executions not available:', error)
        updateActiveExecutions([])
      },
      retry: false,
    }
  )

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

  // Mock data for charts
  const testTrendData = [
    { time: '00:00', passed: 45, failed: 5, running: 10 },
    { time: '04:00', passed: 52, failed: 3, running: 8 },
    { time: '08:00', passed: 48, failed: 7, running: 12 },
    { time: '12:00', passed: 55, failed: 2, running: 15 },
    { time: '16:00', passed: 50, failed: 4, running: 9 },
    { time: '20:00', passed: 47, failed: 6, running: 11 },
  ]

  // Mock recent results
  const mockResults: TestResult[] = [
    {
      test_id: 'kernel-boot-test-001',
      status: 'passed',
      execution_time: 45.2,
      environment: { type: 'qemu', arch: 'x86_64' },
      artifacts: { logs: 'boot.log' },
      timestamp: new Date(Date.now() - 300000).toISOString(),
    },
    {
      test_id: 'memory-stress-test-002',
      status: 'running',
      execution_time: 120.5,
      environment: { type: 'physical', board: 'rpi4' },
      artifacts: { logs: 'stress.log' },
      timestamp: new Date(Date.now() - 600000).toISOString(),
    },
    {
      test_id: 'network-performance-003',
      status: 'failed',
      execution_time: 78.1,
      environment: { type: 'kvm', arch: 'arm64' },
      artifacts: { logs: 'network.log', crash_dump: 'core.dump' },
      timestamp: new Date(Date.now() - 900000).toISOString(),
    },
  ]

  // Mock active executions
  const mockExecutions: ExecutionPlanStatus[] = [
    {
      plan_id: 'exec-plan-001',
      submission_id: 'sub-001',
      overall_status: 'running',
      progress: 0.65,
      completed_tests: 13,
      total_tests: 20,
      failed_tests: 1,
      test_statuses: [],
      started_at: new Date(Date.now() - 600000).toISOString(),
    },
    {
      plan_id: 'exec-plan-002', 
      submission_id: 'sub-002',
      overall_status: 'pending',
      progress: 0.0,
      completed_tests: 0,
      total_tests: 8,
      failed_tests: 0,
      test_statuses: [],
    },
  ]

  const statusDistribution = [
    { name: 'Passed', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.7) : 35, color: '#52c41a' },
    { name: 'Failed', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.1) : 5, color: '#ff4d4f' },
    { name: 'Running', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.15) : 8, color: '#1890ff' },
    { name: 'Pending', value: systemMetrics?.active_tests ? Math.floor(systemMetrics.active_tests * 0.05) : 2, color: '#faad14' },
  ]

  return (
    <div>
      <Title level={2}>Dashboard</Title>
      
      {/* Connection Status */}
      {healthError ? (
        <Alert
          message="Demo Mode - Backend Offline"
          description="The backend API is not available. Showing mock data for demonstration purposes."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      ) : (
        <Alert
          message="Connected to Backend"
          description="Successfully connected to the testing system backend."
          type="success"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* System Status */}
      {healthData && (
        <Row style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card size="small" title="System Status">
              <Space wrap>
                <Badge color="green" text={`API: ${healthData.components?.api?.status || 'healthy'}`} />
                <Badge color="green" text={`Database: ${healthData.components?.database?.status || 'healthy'}`} />
                <Badge color="green" text={`Orchestrator: ${healthData.components?.test_orchestrator?.status || 'healthy'}`} />
                <Badge color="green" text={`Environment Manager: ${healthData.components?.environment_manager?.status || 'healthy'}`} />
                <Text type="secondary">Uptime: {Math.round((healthData.uptime || 0) / 60)} minutes</Text>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

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
              dataSource={activeExecutions.length > 0 ? activeExecutions : mockExecutions}
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
              dataSource={recentResults.length > 0 ? recentResults : mockResults}
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