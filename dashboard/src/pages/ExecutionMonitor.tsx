import React, { useState, useEffect } from 'react'
import {
  Card,
  Steps,
  Progress,
  Typography,
  Row,
  Col,
  Timeline,
  Tag,
  Space,
  Button,
  Table,
  Statistic,
  Alert,
  Spin,
  Badge,
  Divider,
  Tabs,
} from 'antd'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  CloudServerOutlined,
  CodeOutlined,
  BarChartOutlined,
  EyeOutlined,
  ReloadOutlined,
  SettingOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import EnvironmentManagementDashboard from '../components/EnvironmentManagementDashboard'

const { Title, Text } = Typography

interface ExecutionStage {
  id: string
  name: string
  status: 'waiting' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
  duration?: number
  details?: any
  progress?: number
}

interface EnvironmentInfo {
  id: string
  type: string
  status: 'allocating' | 'ready' | 'running' | 'cleanup' | 'available'
  architecture: string
  assignedTests: string[]
  resources: {
    cpu: number
    memory: number
    disk: number
  }
}

const ExecutionMonitor: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const planId = searchParams.get('planId')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [activeTab, setActiveTab] = useState('execution')

  // Fetch execution details with real-time updates
  const { data: executionData, isLoading, refetch } = useQuery(
    ['executionMonitor', planId],
    () => planId ? apiService.getExecutionStatus(planId) : null,
    {
      enabled: !!planId,
      refetchInterval: autoRefresh ? 2000 : false, // Refresh every 2 seconds
      refetchOnWindowFocus: true,
    }
  )

  // Fetch available executions if no specific plan is selected
  const { data: availableExecutions } = useQuery(
    'availableExecutions',
    () => apiService.getActiveExecutions(),
    {
      enabled: !planId,
      refetchInterval: 5000,
    }
  )

  // Mock data for demonstration - replace with real API calls
  const [stages, setStages] = useState<ExecutionStage[]>([
    {
      id: 'validation',
      name: 'Plan Validation',
      status: 'completed',
      startTime: '2024-12-25T10:00:00Z',
      endTime: '2024-12-25T10:00:05Z',
      duration: 5,
      progress: 100,
    },
    {
      id: 'environment',
      name: 'Environment Allocation',
      status: 'running',
      startTime: '2024-12-25T10:00:05Z',
      progress: 65,
    },
    {
      id: 'deployment',
      name: 'Test Deployment',
      status: 'waiting',
      progress: 0,
    },
    {
      id: 'execution',
      name: 'Test Execution',
      status: 'waiting',
      progress: 0,
    },
    {
      id: 'collection',
      name: 'Result Collection',
      status: 'waiting',
      progress: 0,
    },
    {
      id: 'cleanup',
      name: 'Environment Cleanup',
      status: 'waiting',
      progress: 0,
    },
  ])

  const [environments, setEnvironments] = useState<EnvironmentInfo[]>([
    {
      id: 'env-qemu-x86-1',
      type: 'QEMU x86_64',
      status: 'ready',
      architecture: 'x86_64',
      assignedTests: ['test_fd3601e1', 'test_a7b2c3d4'],
      resources: { cpu: 45, memory: 60, disk: 30 },
    },
    {
      id: 'env-qemu-arm-1',
      type: 'QEMU ARM64',
      status: 'allocating',
      architecture: 'arm64',
      assignedTests: ['test_e5f6g7h8'],
      resources: { cpu: 0, memory: 0, disk: 0 },
    },
  ])

  // Simulate real-time updates
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      // Simulate stage progression
      setStages(prev => prev.map(stage => {
        if (stage.status === 'running' && stage.progress !== undefined) {
          const newProgress = Math.min(stage.progress + Math.random() * 10, 100)
          if (newProgress >= 100) {
            return {
              ...stage,
              status: 'completed',
              progress: 100,
              endTime: new Date().toISOString(),
              duration: stage.startTime ? 
                Math.floor((Date.now() - new Date(stage.startTime).getTime()) / 1000) : 0
            }
          }
          return { ...stage, progress: newProgress }
        }
        return stage
      }))

      // Simulate environment updates
      setEnvironments(prev => prev.map(env => {
        if (env.status === 'allocating') {
          return {
            ...env,
            status: 'ready',
            resources: {
              cpu: Math.floor(Math.random() * 50) + 20,
              memory: Math.floor(Math.random() * 40) + 30,
              disk: Math.floor(Math.random() * 30) + 15,
            }
          }
        }
        if (env.status === 'ready' && Math.random() > 0.7) {
          return { ...env, status: 'running' }
        }
        return env
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const getStageIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'running': return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'failed': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getEnvironmentStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'green'
      case 'running': return 'blue'
      case 'allocating': return 'orange'
      case 'cleanup': return 'purple'
      default: return 'default'
    }
  }

  const environmentColumns = [
    {
      title: 'Environment ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => <Text code>{id}</Text>
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Architecture',
      dataIndex: 'architecture',
      key: 'architecture',
      render: (arch: string) => <Tag color="blue">{arch}</Tag>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge 
          status={status === 'running' ? 'processing' : status === 'ready' ? 'success' : 'default'} 
          text={status.toUpperCase()} 
        />
      )
    },
    {
      title: 'Assigned Tests',
      dataIndex: 'assignedTests',
      key: 'assignedTests',
      render: (tests: string[]) => (
        <Space wrap>
          {tests.map(test => (
            <Tag key={test}>{test.slice(0, 8)}...</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Resources',
      key: 'resources',
      render: (_, env: EnvironmentInfo) => (
        <Space direction="vertical" size="small">
          <div>CPU: <Progress percent={env.resources.cpu} size="small" /></div>
          <div>Memory: <Progress percent={env.resources.memory} size="small" /></div>
          <div>Disk: <Progress percent={env.resources.disk} size="small" /></div>
        </Space>
      )
    }
  ]

  if (!planId) {
    return (
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <Title level={2}>Execution Monitor</Title>
            <Text type="secondary">Select an execution plan to monitor in real-time</Text>
          </div>
        </div>

        <Card title="Available Execution Plans">
          {availableExecutions && availableExecutions.length > 0 ? (
            <div>
              <Text style={{ marginBottom: 16, display: 'block' }}>
                Click on any execution plan below to start monitoring:
              </Text>
              {availableExecutions.map((execution: any) => (
                <Card 
                  key={execution.plan_id}
                  size="small" 
                  style={{ marginBottom: 12, cursor: 'pointer' }}
                  onClick={() => {
                    window.location.href = `/execution-monitor?planId=${execution.plan_id}`
                  }}
                  hoverable
                >
                  <Row justify="space-between" align="middle">
                    <Col>
                      <Space direction="vertical" size="small">
                        <Text strong>
                          {execution.test_plan_name || `Plan ID: ${execution.plan_id.slice(0, 8)}...`}
                        </Text>
                        <Text type="secondary">
                          Status: <Tag color={execution.overall_status === 'running' ? 'blue' : 'orange'}>
                            {execution.overall_status.toUpperCase()}
                          </Tag>
                          {execution.created_by && (
                            <span style={{ marginLeft: 8 }}>
                              by {execution.created_by}
                            </span>
                          )}
                        </Text>
                      </Space>
                    </Col>
                    <Col>
                      <Space direction="vertical" size="small" align="end">
                        <Text>{execution.total_tests} tests</Text>
                        <Progress 
                          percent={Math.round(execution.progress * 100)} 
                          size="small" 
                          style={{ width: 100 }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Alert
                message="No Active Executions"
                description={
                  <div>
                    <p>There are currently no active execution plans to monitor.</p>
                    <p>Go to the <a href="/tests">Test Execution</a> page to start some tests first.</p>
                  </div>
                }
                type="info"
                showIcon
              />
            </div>
          )}
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Loading execution details...</Text>
        </div>
      </div>
    )
  }

  const currentStage = stages.find(s => s.status === 'running') || stages[0]
  const completedStages = stages.filter(s => s.status === 'completed').length
  const totalStages = stages.length
  const overallProgress = (completedStages / totalStages) * 100

  // Navigation helper functions
  const navigateToEnvironmentManagement = () => {
    const url = planId ? `/environment-management?planId=${planId}` : '/environment-management'
    navigate(url)
  }

  const handleTabChange = (key: string) => {
    setActiveTab(key)
  }

  // Tab items for integrated view
  const tabItems = [
    {
      key: 'execution',
      label: (
        <Space>
          <BarChartOutlined />
          Execution Progress
        </Space>
      ),
      children: null, // Will be set below
    },
    {
      key: 'environments',
      label: (
        <Space>
          <CloudServerOutlined />
          Environment Allocation
        </Space>
      ),
      children: null, // Will be set below
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={2}>Execution Monitor</Title>
          <Text type="secondary">
            Real-time monitoring for execution plan: <Text code>{planId}</Text>
            {executionData?.test_plan_name && (
              <span> - {executionData.test_plan_name}</span>
            )}
          </Text>
        </div>
        <Space>
          <Button
            icon={<SwapOutlined />}
            onClick={navigateToEnvironmentManagement}
            type="default"
          >
            Environment View
          </Button>
          <Button
            icon={<EyeOutlined />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            type={autoRefresh ? 'primary' : 'default'}
          >
            {autoRefresh ? 'Live' : 'Paused'}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Overall Progress */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={24} align="middle">
          <Col span={18}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Overall Execution Progress</Text>
              <Text type="secondary" style={{ marginLeft: 16 }}>
                Stage {completedStages + 1} of {totalStages}: {currentStage.name}
              </Text>
            </div>
            <Progress 
              percent={overallProgress} 
              status={currentStage.status === 'failed' ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Estimated Time Remaining"
              value={executionData?.estimated_completion ? 
                Math.max(0, Math.floor((new Date(executionData.estimated_completion).getTime() - Date.now()) / 60000)) : 
                '--'}
              suffix="min"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Integrated Tabs View */}
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={[
          {
            key: 'execution',
            label: (
              <Space>
                <BarChartOutlined />
                Execution Progress
              </Space>
            ),
            children: (
              <Row gutter={24}>
                {/* Execution Stages */}
                <Col span={16}>
                  <Card 
                    title={
                      <Space>
                        <BarChartOutlined />
                        Execution Stages
                      </Space>
                    }
                    style={{ marginBottom: 24 }}
                  >
                    <Steps
                      direction="vertical"
                      current={stages.findIndex(s => s.status === 'running')}
                      status={currentStage.status === 'failed' ? 'error' : 'process'}
                      items={stages.map((stage, index) => ({
                        title: stage.name,
                        status: 
                          stage.status === 'completed' ? 'finish' :
                          stage.status === 'running' ? 'process' :
                          stage.status === 'failed' ? 'error' : 'wait',
                        icon: getStageIcon(stage.status),
                        description: (
                          <div>
                            {stage.status === 'running' && stage.progress !== undefined && (
                              <Progress 
                                percent={Math.round(stage.progress)} 
                                size="small" 
                                style={{ marginBottom: 8 }}
                              />
                            )}
                            <Space>
                              {stage.startTime && (
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  Started: {new Date(stage.startTime).toLocaleTimeString()}
                                </Text>
                              )}
                              {stage.duration && (
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  Duration: {stage.duration}s
                                </Text>
                              )}
                            </Space>
                          </div>
                        )
                      }))}
                    />
                  </Card>

                  {/* Environment Allocation Summary */}
                  <Card
                    title={
                      <Space>
                        <CloudServerOutlined />
                        Environment Allocation Summary
                        <Badge count={environments.length} style={{ backgroundColor: '#52c41a' }} />
                      </Space>
                    }
                    extra={
                      <Button 
                        size="small" 
                        type="link"
                        onClick={() => setActiveTab('environments')}
                      >
                        View Details
                      </Button>
                    }
                  >
                    <Table
                      columns={environmentColumns}
                      dataSource={environments}
                      rowKey="id"
                      size="small"
                      pagination={false}
                    />
                  </Card>
                </Col>

                {/* Real-time Activity Feed */}
                <Col span={8}>
                  <Card
                    title={
                      <Space>
                        <ClockCircleOutlined />
                        Activity Timeline
                      </Space>
                    }
                    style={{ marginBottom: 24 }}
                  >
                    <Timeline
                      items={[
                        {
                          color: 'green',
                          children: (
                            <div>
                              <Text strong>Plan Validation Completed</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                10:00:05 - All test cases validated successfully
                              </Text>
                            </div>
                          ),
                        },
                        {
                          color: 'blue',
                          children: (
                            <div>
                              <Text strong>Environment Allocation Started</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                10:00:05 - Allocating 2 environments
                              </Text>
                            </div>
                          ),
                        },
                        {
                          color: 'blue',
                          children: (
                            <div>
                              <Text strong>QEMU x86_64 Environment Ready</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                10:00:12 - env-qemu-x86-1 allocated
                              </Text>
                            </div>
                          ),
                        },
                        {
                          color: 'orange',
                          children: (
                            <div>
                              <Text strong>QEMU ARM64 Environment Allocating</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                10:00:15 - env-qemu-arm-1 in progress
                              </Text>
                            </div>
                          ),
                        },
                      ]}
                    />
                  </Card>

                  {/* Current Stage Details */}
                  <Card
                    title={
                      <Space>
                        <CodeOutlined />
                        Current Stage Details
                      </Space>
                    }
                  >
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      {getStageIcon(currentStage.status)}
                      <Title level={4} style={{ marginTop: 16, marginBottom: 8 }}>
                        {currentStage.name}
                      </Title>
                      <Text type="secondary">
                        {currentStage.status === 'running' ? 'In Progress' : 
                         currentStage.status === 'completed' ? 'Completed' : 'Waiting'}
                      </Text>
                      
                      {currentStage.status === 'running' && currentStage.progress !== undefined && (
                        <div style={{ marginTop: 16 }}>
                          <Progress
                            type="circle"
                            percent={Math.round(currentStage.progress)}
                            width={80}
                          />
                        </div>
                      )}

                      <Divider />
                      
                      <div style={{ textAlign: 'left' }}>
                        <Text strong>Stage Details:</Text>
                        <div style={{ marginTop: 8 }}>
                          {currentStage.id === 'environment' && (
                            <div>
                              <Text>• Provisioning virtual environments</Text><br />
                              <Text>• Configuring network interfaces</Text><br />
                              <Text>• Installing test dependencies</Text><br />
                              <Text>• Validating environment readiness</Text>
                            </div>
                          )}
                          {currentStage.id === 'execution' && (
                            <div>
                              <Text>• Deploying test scripts</Text><br />
                              <Text>• Starting test processes</Text><br />
                              <Text>• Monitoring test progress</Text><br />
                              <Text>• Collecting real-time logs</Text>
                            </div>
                          )}
                          {currentStage.id === 'validation' && (
                            <div>
                              <Text>• Validating test case syntax</Text><br />
                              <Text>• Checking resource requirements</Text><br />
                              <Text>• Verifying dependencies</Text><br />
                              <Text>• Creating execution schedule</Text>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'environments',
            label: (
              <Space>
                <CloudServerOutlined />
                Environment Allocation
              </Space>
            ),
            children: (
              <EnvironmentManagementDashboard
                planId={planId || undefined}
                autoRefresh={autoRefresh}
                refreshInterval={2000}
              />
            ),
          },
        ]}
      />
    </div>
  )
}

export default ExecutionMonitor