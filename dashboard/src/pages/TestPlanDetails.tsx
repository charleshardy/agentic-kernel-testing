import React, { useState } from 'react'
import {
  Card,
  Descriptions,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Progress,
  Timeline,
  Row,
  Col,
  Statistic,
  Alert,
  Tabs,
  List,
  Badge,
  Tooltip,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  EditOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  BugOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  FileTextOutlined,
  FunctionOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import { useNavigate, useParams } from 'react-router-dom'
import apiService, { EnhancedTestCase, ExecutionPlanStatus } from '../services/api'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface TestPlanExecution {
  id: string
  plan_id: string
  started_at: string
  completed_at?: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  total_tests: number
  passed_tests: number
  failed_tests: number
  duration?: number
  environment: string
}

const TestPlanDetails: React.FC = () => {
  const navigate = useNavigate()
  const { planId } = useParams<{ planId: string }>()
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch test plan details
  const { data: testPlan, isLoading } = useQuery(
    ['testPlan', planId],
    () => {
      // Mock implementation - replace with real API call
      return Promise.resolve(mockTestPlan)
    },
    {
      enabled: !!planId,
    }
  )

  // Fetch test cases in the plan
  const { data: testCases } = useQuery(
    ['testPlanCases', planId],
    () => apiService.getTests({ page: 1, page_size: 1000 }),
    {
      enabled: !!planId,
    }
  )

  // Fetch execution history
  const { data: executionHistory } = useQuery(
    ['testPlanExecutions', planId],
    () => {
      // Mock implementation - replace with real API call
      return Promise.resolve(mockExecutionHistory)
    },
    {
      enabled: !!planId,
    }
  )

  // Mock data
  const mockTestPlan = {
    id: 'plan-001',
    name: 'Kernel Core Tests',
    description: 'Comprehensive testing of kernel core functionality including memory management, process scheduling, and system calls',
    test_ids: ['test_fd3601e1', 'test_a7b2c3d4', 'test_e5f6g7h8'],
    created_by: 'admin',
    created_at: '2024-12-20T10:00:00Z',
    updated_at: '2024-12-24T15:30:00Z',
    status: 'active',
    tags: ['kernel', 'core', 'critical'],
    execution_config: {
      environment_preference: 'qemu-x86',
      priority: 8,
      timeout_minutes: 120,
      retry_failed: true,
      parallel_execution: true,
    },
    statistics: {
      total_executions: 45,
      success_rate: 87.5,
      avg_execution_time: 1800,
      last_execution: '2024-12-24T14:20:00Z',
    },
  }

  const mockExecutionHistory: TestPlanExecution[] = [
    {
      id: 'exec-001',
      plan_id: 'plan-001',
      started_at: '2024-12-24T14:20:00Z',
      completed_at: '2024-12-24T14:50:00Z',
      status: 'completed',
      total_tests: 3,
      passed_tests: 3,
      failed_tests: 0,
      duration: 1800,
      environment: 'qemu-x86-1',
    },
    {
      id: 'exec-002',
      plan_id: 'plan-001',
      started_at: '2024-12-23T16:10:00Z',
      completed_at: '2024-12-23T16:35:00Z',
      status: 'completed',
      total_tests: 3,
      passed_tests: 2,
      failed_tests: 1,
      duration: 1500,
      environment: 'qemu-x86-2',
    },
    {
      id: 'exec-003',
      plan_id: 'plan-001',
      started_at: '2024-12-22T11:30:00Z',
      status: 'running',
      total_tests: 3,
      passed_tests: 1,
      failed_tests: 0,
      environment: 'qemu-x86-1',
    },
  ]

  const getTestTypeIcon = (testType: string) => {
    switch (testType) {
      case 'unit':
        return <BugOutlined style={{ color: '#1890ff' }} />
      case 'integration':
        return <TeamOutlined style={{ color: '#52c41a' }} />
      case 'performance':
        return <ThunderboltOutlined style={{ color: '#faad14' }} />
      case 'security':
        return <SafetyOutlined style={{ color: '#f5222d' }} />
      case 'fuzz':
        return <FunctionOutlined style={{ color: '#722ed1' }} />
      default:
        return <FileTextOutlined style={{ color: '#8c8c8c' }} />
    }
  }

  const getExecutionStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'cancelled':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getExecutionStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'running':
        return 'processing'
      case 'failed':
        return 'error'
      case 'cancelled':
        return 'warning'
      default:
        return 'default'
    }
  }

  const executionColumns = [
    {
      title: 'Execution ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => <Text code>{id.slice(0, 8)}...</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Space>
          {getExecutionStatusIcon(status)}
          <Badge status={getExecutionStatusColor(status)} text={status.toUpperCase()} />
        </Space>
      ),
    },
    {
      title: 'Results',
      key: 'results',
      render: (_: any, record: TestPlanExecution) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>
            <span style={{ color: '#52c41a' }}>✓ {record.passed_tests}</span> / 
            <span style={{ color: '#ff4d4f', marginLeft: 4 }}>✗ {record.failed_tests}</span> / 
            <span style={{ marginLeft: 4 }}>{record.total_tests} total</span>
          </Text>
          <Progress
            percent={Math.round((record.passed_tests / record.total_tests) * 100)}
            size="small"
            status={record.failed_tests > 0 ? 'exception' : 'success'}
          />
        </Space>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number) => (
        <Text>{duration ? `${Math.floor(duration / 60)}m ${duration % 60}s` : 'Running...'}</Text>
      ),
    },
    {
      title: 'Environment',
      dataIndex: 'environment',
      key: 'environment',
      render: (env: string) => <Tag color="blue">{env}</Tag>,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (startedAt: string) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>
            {new Date(startedAt).toLocaleDateString()}
          </Text>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            {new Date(startedAt).toLocaleTimeString()}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: TestPlanExecution) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => navigate(`/execution-monitor?planId=${record.id}`)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <LoadingOutlined style={{ fontSize: 24 }} />
        <div style={{ marginTop: 16 }}>
          <Text>Loading test plan details...</Text>
        </div>
      </div>
    )
  }

  if (!testPlan) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Test Plan Not Found"
          description="The requested test plan could not be found."
          type="error"
          showIcon
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/test-plans')}
            >
              Back to Test Plans
            </Button>
            <Title level={2} style={{ margin: 0 }}>
              {testPlan.name}
            </Title>
            <Tag color={testPlan.status === 'active' ? 'green' : 'orange'}>
              {testPlan.status.toUpperCase()}
            </Tag>
          </Space>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => {
              // Execute test plan
              navigate(`/execution-monitor?planId=${testPlan.id}`)
            }}
          >
            Execute Plan
          </Button>
          <Button
            icon={<EditOutlined />}
            onClick={() => navigate(`/test-plans?edit=${testPlan.id}`)}
          >
            Edit Plan
          </Button>
        </Space>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Executions"
              value={testPlan.statistics.total_executions}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={testPlan.statistics.success_rate}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: testPlan.statistics.success_rate > 80 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Execution Time"
              value={Math.floor(testPlan.statistics.avg_execution_time / 60)}
              suffix="min"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Test Cases"
              value={testPlan.test_ids.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Overview" key="overview">
          <Row gutter={24}>
            <Col span={16}>
              <Card title="Plan Details" style={{ marginBottom: 24 }}>
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="Description" span={2}>
                    {testPlan.description}
                  </Descriptions.Item>
                  <Descriptions.Item label="Created By">
                    {testPlan.created_by}
                  </Descriptions.Item>
                  <Descriptions.Item label="Status">
                    <Tag color={testPlan.status === 'active' ? 'green' : 'orange'}>
                      {testPlan.status.toUpperCase()}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Created">
                    {new Date(testPlan.created_at).toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="Last Updated">
                    {new Date(testPlan.updated_at).toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="Tags" span={2}>
                    <Space wrap>
                      {testPlan.tags.map(tag => (
                        <Tag key={tag} color="blue">{tag}</Tag>
                      ))}
                    </Space>
                  </Descriptions.Item>
                </Descriptions>
              </Card>

              <Card title="Execution Configuration">
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="Environment Preference">
                    <Tag color="blue">{testPlan.execution_config.environment_preference}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Priority">
                    <Tag color={testPlan.execution_config.priority >= 8 ? 'red' : testPlan.execution_config.priority >= 5 ? 'orange' : 'green'}>
                      {testPlan.execution_config.priority}/10
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Timeout">
                    {testPlan.execution_config.timeout_minutes} minutes
                  </Descriptions.Item>
                  <Descriptions.Item label="Retry Failed">
                    <Tag color={testPlan.execution_config.retry_failed ? 'green' : 'default'}>
                      {testPlan.execution_config.retry_failed ? 'Yes' : 'No'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Parallel Execution" span={2}>
                    <Tag color={testPlan.execution_config.parallel_execution ? 'green' : 'default'}>
                      {testPlan.execution_config.parallel_execution ? 'Enabled' : 'Disabled'}
                    </Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>

            <Col span={8}>
              <Card title="Recent Activity" style={{ marginBottom: 24 }}>
                <Timeline
                  items={[
                    {
                      color: 'green',
                      children: (
                        <div>
                          <Text strong>Execution Completed</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            Dec 24, 2:50 PM - All tests passed
                          </Text>
                        </div>
                      ),
                    },
                    {
                      color: 'blue',
                      children: (
                        <div>
                          <Text strong>Plan Updated</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            Dec 24, 3:30 PM - Configuration changed
                          </Text>
                        </div>
                      ),
                    },
                    {
                      color: 'orange',
                      children: (
                        <div>
                          <Text strong>Execution Failed</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            Dec 23, 4:35 PM - 1 test failed
                          </Text>
                        </div>
                      ),
                    },
                  ]}
                />
              </Card>

              <Card title="Quick Stats">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">Last 7 days success rate</Text>
                    <Progress percent={92} size="small" />
                  </div>
                  <div>
                    <Text type="secondary">Average duration trend</Text>
                    <Progress percent={75} size="small" status="active" />
                  </div>
                  <div>
                    <Text type="secondary">Environment utilization</Text>
                    <Progress percent={68} size="small" />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Test Cases" key="testcases">
          <Card>
            <List
              dataSource={testCases?.tests?.filter((test: EnhancedTestCase) => 
                testPlan.test_ids.includes(test.id)
              ) || []}
              renderItem={(test: EnhancedTestCase) => (
                <List.Item
                  key={test.id}
                  actions={[
                    <Button key="view" type="link" icon={<EyeOutlined />}>
                      View
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={getTestTypeIcon(test.test_type)}
                    title={
                      <Space>
                        <Text strong>{test.name}</Text>
                        <Tag color="blue">{test.test_type}</Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary">{test.description}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          Target: {test.target_subsystem} • 
                          Estimated time: {Math.floor(test.execution_time_estimate / 60)}m
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane tab="Execution History" key="history">
          <Card>
            <Table
              columns={executionColumns}
              dataSource={executionHistory}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total, range) =>
                  `${range[0]}-${range[1]} of ${total} executions`,
              }}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default TestPlanDetails