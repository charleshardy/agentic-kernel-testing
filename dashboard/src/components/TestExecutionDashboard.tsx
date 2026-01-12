import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Progress,
  Statistic,
  Table,
  Tag,
  Space,
  Typography,
  Button,
  Alert,
  Timeline,
  Collapse,
  Badge,
  Tooltip,
  Spin,
  Empty,
  Divider,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ExperimentOutlined,
  BugOutlined,
  CodeOutlined,
  SyncOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const { Text, Title, Paragraph } = Typography
const { Panel } = Collapse

interface CounterExample {
  original: any
  shrunk: any
  iteration: number
}

interface TestResult {
  id: string
  test_name: string
  property_id: string
  requirement_ids: string[]
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error'
  iterations_completed: number
  iterations_total: number
  duration_ms?: number
  counter_example?: CounterExample
  error_message?: string
  started_at?: string
  completed_at?: string
}

interface ExecutionSummary {
  total: number
  passed: number
  failed: number
  running: number
  pending: number
  total_iterations: number
  completed_iterations: number
}

interface TestExecutionDashboardProps {
  results: TestResult[]
  summary?: ExecutionSummary
  isRunning?: boolean
  onStart?: () => void
  onStop?: () => void
  onRerun?: (testId: string) => void
  refreshInterval?: number
}

const TestExecutionDashboard: React.FC<TestExecutionDashboardProps> = ({
  results,
  summary,
  isRunning = false,
  onStart,
  onStop,
  onRerun,
  refreshInterval = 1000,
}) => {
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  // Calculate summary if not provided
  const calculatedSummary: ExecutionSummary = summary || {
    total: results.length,
    passed: results.filter(r => r.status === 'passed').length,
    failed: results.filter(r => r.status === 'failed').length,
    running: results.filter(r => r.status === 'running').length,
    pending: results.filter(r => r.status === 'pending').length,
    total_iterations: results.reduce((acc, r) => acc + r.iterations_total, 0),
    completed_iterations: results.reduce((acc, r) => acc + r.iterations_completed, 0),
  }

  const overallProgress = calculatedSummary.total_iterations > 0
    ? Math.round((calculatedSummary.completed_iterations / calculatedSummary.total_iterations) * 100)
    : 0

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} spin />
      case 'error':
        return <WarningOutlined style={{ color: '#faad14' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      passed: 'success',
      failed: 'error',
      running: 'processing',
      error: 'warning',
      pending: 'default',
    }
    return colors[status] || 'default'
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  const renderCounterExample = (counterExample: CounterExample) => (
    <Card size="small" style={{ background: '#fff2f0', marginTop: 8 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Text strong>
          <BugOutlined /> Counter-Example Found (Iteration {counterExample.iteration})
        </Text>
        <Divider style={{ margin: '8px 0' }} />
        <Row gutter={16}>
          <Col span={12}>
            <Text type="secondary">Original Input:</Text>
            <pre style={{ 
              background: '#1e1e1e', 
              color: '#d4d4d4', 
              padding: 8, 
              borderRadius: 4,
              fontSize: 11,
              maxHeight: 150,
              overflow: 'auto',
            }}>
              {JSON.stringify(counterExample.original, null, 2)}
            </pre>
          </Col>
          <Col span={12}>
            <Text type="secondary">Shrunk (Minimal):</Text>
            <pre style={{ 
              background: '#1e1e1e', 
              color: '#ce9178', 
              padding: 8, 
              borderRadius: 4,
              fontSize: 11,
              maxHeight: 150,
              overflow: 'auto',
            }}>
              {JSON.stringify(counterExample.shrunk, null, 2)}
            </pre>
          </Col>
        </Row>
      </Space>
    </Card>
  )

  const columns = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>{status.toUpperCase()}</Tag>
        </Space>
      ),
    },
    {
      title: 'Test Name',
      dataIndex: 'test_name',
      key: 'test_name',
      render: (name: string, record: TestResult) => (
        <Space direction="vertical" size="small">
          <Text code>{name}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Property: {record.property_id}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Progress',
      key: 'progress',
      width: 200,
      render: (_: any, record: TestResult) => {
        const percent = record.iterations_total > 0
          ? Math.round((record.iterations_completed / record.iterations_total) * 100)
          : 0
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Progress 
              percent={percent} 
              size="small"
              status={
                record.status === 'failed' ? 'exception' :
                record.status === 'passed' ? 'success' :
                record.status === 'running' ? 'active' : 'normal'
              }
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              {record.iterations_completed} / {record.iterations_total} iterations
            </Text>
          </Space>
        )
      },
    },
    {
      title: 'Duration',
      dataIndex: 'duration_ms',
      key: 'duration',
      width: 100,
      render: (duration: number) => formatDuration(duration),
    },
    {
      title: 'Requirements',
      dataIndex: 'requirement_ids',
      key: 'requirements',
      width: 150,
      render: (ids: string[]) => (
        <Space wrap>
          {ids.slice(0, 3).map(id => (
            <Tag key={id} color="blue">{id}</Tag>
          ))}
          {ids.length > 3 && <Tag>+{ids.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: any, record: TestResult) => (
        <Space>
          {onRerun && record.status !== 'running' && (
            <Tooltip title="Re-run Test">
              <Button
                size="small"
                icon={<SyncOutlined />}
                onClick={() => onRerun(record.id)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  const expandedRowRender = (record: TestResult) => (
    <div style={{ padding: '8px 0' }}>
      {record.counter_example && renderCounterExample(record.counter_example)}
      {record.error_message && (
        <Alert
          message="Error"
          description={record.error_message}
          type="error"
          style={{ marginTop: 8 }}
        />
      )}
      {record.status === 'passed' && (
        <Alert
          message="All iterations passed"
          description={`Successfully completed ${record.iterations_completed} iterations without finding counter-examples.`}
          type="success"
          style={{ marginTop: 8 }}
        />
      )}
    </div>
  )

  if (results.length === 0) {
    return (
      <Card>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No test results yet"
        >
          {onStart && (
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={onStart}>
              Start Execution
            </Button>
          )}
        </Empty>
      </Card>
    )
  }

  return (
    <div className="test-execution-dashboard">
      {/* Summary Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="Total Tests"
              value={calculatedSummary.total}
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Passed"
              value={calculatedSummary.passed}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Failed"
              value={calculatedSummary.failed}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Running"
              value={calculatedSummary.running}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LoadingOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Pending"
              value={calculatedSummary.pending}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Iterations"
              value={calculatedSummary.completed_iterations}
              suffix={`/ ${calculatedSummary.total_iterations}`}
              prefix={<SyncOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Overall Progress */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={16}>
          <Col flex="auto">
            <Text strong>Overall Progress</Text>
            <Progress
              percent={overallProgress}
              status={
                calculatedSummary.failed > 0 ? 'exception' :
                calculatedSummary.running > 0 ? 'active' :
                calculatedSummary.pending === 0 ? 'success' : 'normal'
              }
              strokeWidth={20}
              style={{ marginTop: 8 }}
            />
          </Col>
          <Col>
            <Space>
              {isRunning ? (
                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={onStop}
                >
                  Stop
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={onStart}
                  disabled={calculatedSummary.pending === 0 && calculatedSummary.running === 0}
                >
                  {calculatedSummary.completed_iterations > 0 ? 'Resume' : 'Start'}
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Failed Tests Alert */}
      {calculatedSummary.failed > 0 && (
        <Alert
          message={`${calculatedSummary.failed} test(s) failed`}
          description="Expand failed tests below to see counter-examples and error details."
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Results Table */}
      <Card title="Test Results">
        <Table
          columns={columns}
          dataSource={results}
          rowKey="id"
          expandable={{
            expandedRowRender,
            rowExpandable: record => 
              record.status === 'failed' || 
              record.status === 'error' || 
              record.status === 'passed',
          }}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default TestExecutionDashboard
