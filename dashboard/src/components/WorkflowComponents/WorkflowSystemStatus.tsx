import React from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Badge,
  Space,
  Typography,
  Tag,
  List,
  Tooltip,
  Alert,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  WarningOutlined,
  RobotOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  ApiOutlined,
  MonitorOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService from '../../services/api'

const { Text, Title } = Typography

interface SystemComponent {
  name: string
  status: 'healthy' | 'warning' | 'error' | 'unknown'
  icon: React.ReactNode
  description: string
  metrics?: Record<string, any>
}

const WorkflowSystemStatus: React.FC = () => {
  // Fetch system health
  const { data: healthData, isLoading: healthLoading } = useQuery(
    'systemHealth',
    () => apiService.getHealth(),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
      retry: false,
    }
  )

  // Fetch system metrics
  const { data: metricsData } = useQuery(
    'systemMetrics',
    () => apiService.getSystemMetrics(),
    {
      refetchInterval: 15000, // Refresh every 15 seconds
      retry: false,
    }
  )

  // Fetch active executions for workflow status
  const { data: activeExecutions } = useQuery(
    'activeExecutionsStatus',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds
      retry: false,
    }
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#52c41a'
      case 'warning': return '#faad14'
      case 'error': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <LoadingOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  // Define system components based on health data
  const systemComponents: SystemComponent[] = [
    {
      name: 'API Server',
      status: healthData?.components?.api?.status === 'healthy' ? 'healthy' : 'unknown',
      icon: <ApiOutlined />,
      description: 'REST API and WebSocket services',
      metrics: healthData?.components?.api,
    },
    {
      name: 'Database',
      status: healthData?.components?.database?.status === 'healthy' ? 'healthy' : 'unknown',
      icon: <DatabaseOutlined />,
      description: 'Test results and system data storage',
      metrics: healthData?.components?.database,
    },
    {
      name: 'Test Orchestrator',
      status: healthData?.components?.test_orchestrator?.status === 'healthy' ? 'healthy' : 'unknown',
      icon: <MonitorOutlined />,
      description: 'Test scheduling and execution management',
      metrics: {
        active_tests: healthData?.components?.test_orchestrator?.active_tests || 0,
        queued_tests: healthData?.components?.test_orchestrator?.queued_tests || 0,
      },
    },
    {
      name: 'Environment Manager',
      status: healthData?.components?.environment_manager?.status === 'healthy' ? 'healthy' : 'unknown',
      icon: <CloudServerOutlined />,
      description: 'Virtual and physical test environments',
      metrics: {
        available_environments: healthData?.components?.environment_manager?.available_environments || 0,
        total_environments: healthData?.components?.environment_manager?.total_environments || 0,
      },
    },
    {
      name: 'AI Test Generator',
      status: healthData?.components?.ai_generator?.status === 'healthy' ? 'healthy' : 'warning',
      icon: <RobotOutlined />,
      description: 'LLM-powered test generation services',
      metrics: healthData?.components?.ai_generator,
    },
    {
      name: 'Security Scanner',
      status: healthData?.components?.security_scanner?.status === 'healthy' ? 'healthy' : 'warning',
      icon: <SafetyOutlined />,
      description: 'Vulnerability detection and fuzzing',
      metrics: healthData?.components?.security_scanner,
    },
  ]

  const overallSystemHealth = systemComponents.every(c => c.status === 'healthy') ? 'healthy' :
                             systemComponents.some(c => c.status === 'error') ? 'error' : 'warning'

  return (
    <div>
      {/* Overall System Status */}
      <Card 
        title={
          <Space>
            <MonitorOutlined />
            <span>System Status Overview</span>
            {getStatusIcon(overallSystemHealth)}
          </Space>
        }
        size="small"
        style={{ marginBottom: '16px' }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Statistic
              title="System Health"
              value={overallSystemHealth.toUpperCase()}
              valueStyle={{ color: getStatusColor(overallSystemHealth) }}
              prefix={getStatusIcon(overallSystemHealth)}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="Uptime"
              value={healthData ? Math.round((healthData.uptime || 0) / 60) : 0}
              suffix="min"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="Active Workflows"
              value={activeExecutions?.length || 0}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="System Load"
              value={metricsData ? Math.round(metricsData.cpu_usage * 100) : 0}
              suffix="%"
              prefix={<MonitorOutlined />}
              valueStyle={{ 
                color: metricsData && metricsData.cpu_usage > 0.8 ? '#ff4d4f' : '#52c41a' 
              }}
            />
          </Col>
        </Row>

        {!healthData && (
          <Alert
            message="Backend Offline"
            description="Unable to connect to the backend API. System status information is not available."
            type="warning"
            showIcon
            style={{ marginTop: '16px' }}
          />
        )}
      </Card>

      {/* Component Status Grid */}
      <Row gutter={[16, 16]}>
        {systemComponents.map((component) => (
          <Col xs={24} sm={12} lg={8} key={component.name}>
            <Card
              size="small"
              title={
                <Space>
                  {component.icon}
                  <span>{component.name}</span>
                  <Badge 
                    status={
                      component.status === 'healthy' ? 'success' :
                      component.status === 'warning' ? 'warning' :
                      component.status === 'error' ? 'error' : 'default'
                    }
                  />
                </Space>
              }
              extra={
                <Tag color={getStatusColor(component.status)}>
                  {component.status.toUpperCase()}
                </Tag>
              }
            >
              <div style={{ minHeight: '80px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {component.description}
                </Text>
                
                {component.metrics && (
                  <div style={{ marginTop: '8px' }}>
                    {Object.entries(component.metrics).map(([key, value]) => {
                      if (typeof value === 'number' || typeof value === 'string') {
                        return (
                          <div key={key} style={{ marginBottom: '4px' }}>
                            <Text style={{ fontSize: '11px' }}>
                              <strong>{key.replace(/_/g, ' ')}:</strong> {value}
                            </Text>
                          </div>
                        )
                      }
                      return null
                    })}
                  </div>
                )}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Resource Usage */}
      {metricsData && (
        <Card 
          title="Resource Usage" 
          size="small" 
          style={{ marginTop: '16px' }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <div>
                <Text>CPU Usage</Text>
                <Progress 
                  percent={Math.round(metricsData.cpu_usage * 100)}
                  status={metricsData.cpu_usage > 0.8 ? 'exception' : 'normal'}
                  strokeColor="#1890ff"
                />
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div>
                <Text>Memory Usage</Text>
                <Progress 
                  percent={Math.round(metricsData.memory_usage * 100)}
                  status={metricsData.memory_usage > 0.9 ? 'exception' : 'normal'}
                  strokeColor="#52c41a"
                />
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div>
                <Text>Disk Usage</Text>
                <Progress 
                  percent={Math.round(metricsData.disk_usage * 100)}
                  status={metricsData.disk_usage > 0.9 ? 'exception' : 'normal'}
                  strokeColor="#faad14"
                />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Active Workflows */}
      {activeExecutions && activeExecutions.length > 0 && (
        <Card 
          title="Active Workflow Executions" 
          size="small" 
          style={{ marginTop: '16px' }}
        >
          <List
            size="small"
            dataSource={activeExecutions}
            renderItem={(execution) => (
              <List.Item>
                <List.Item.Meta
                  avatar={getStatusIcon(execution.overall_status)}
                  title={
                    <Space>
                      <Text>{execution.plan_id.slice(0, 12)}...</Text>
                      <Tag color={getStatusColor(execution.overall_status)}>
                        {execution.overall_status}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Progress 
                        percent={Math.round(execution.progress * 100)} 
                        size="small" 
                        showInfo={false}
                      />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {execution.completed_tests}/{execution.total_tests} tests completed
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  )
}

export default WorkflowSystemStatus