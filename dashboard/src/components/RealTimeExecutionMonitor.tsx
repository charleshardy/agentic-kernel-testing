import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Progress,
  Tooltip,
  message,
  Badge,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  EyeOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import apiService from '../services/api'

interface RealTimeExecutionMonitorProps {
  onViewExecution?: (planId: string) => void
}

interface ExecutionMetrics {
  orchestrator_status: string
  active_tests: number
  queued_tests: number
  available_environments: number
  total_environments: number
  completed_tests_today: number
  failed_tests_today: number
  average_execution_time: number
  system_load: string
  timestamp: string
}

const RealTimeExecutionMonitor: React.FC<RealTimeExecutionMonitorProps> = ({
  onViewExecution
}) => {
  const [wsConnected, setWsConnected] = useState(false)
  const [liveMetrics, setLiveMetrics] = useState<ExecutionMetrics | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()

  // Fetch active executions
  const { data: executions, isLoading } = useQuery(
    'activeExecutions',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 5000, // Fallback polling every 5 seconds
    }
  )

  // Fetch execution metrics
  const { data: metrics } = useQuery(
    'executionMetrics',
    () => apiService.getExecutionMetrics(),
    {
      refetchInterval: 10000, // Update metrics every 10 seconds
    }
  )

  // Cancel execution mutation
  const cancelMutation = useMutation(
    (planId: string) => apiService.cancelExecution(planId),
    {
      onSuccess: (data, planId) => {
        message.success(`Execution ${planId} cancelled successfully`)
        queryClient.invalidateQueries('activeExecutions')
      },
      onError: (error: any) => {
        message.error(`Failed to cancel execution: ${error.message}`)
      },
    }
  )

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const wsUrl = 'ws://localhost:8000/api/v1/execution/ws'
        const ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connected for real-time execution updates')
          setWsConnected(true)
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            if (data.type === 'status_update') {
              setLiveMetrics(data.data)
              // Invalidate queries to refresh data
              queryClient.invalidateQueries('activeExecutions')
            } else if (data.type === 'execution_started') {
              message.info(`New execution started: ${data.test_count} tests`)
              queryClient.invalidateQueries('activeExecutions')
            } else if (data.type === 'execution_cancelled') {
              message.info(`Execution ${data.plan_id} was cancelled`)
              queryClient.invalidateQueries('activeExecutions')
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
        
        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setWsConnected(false)
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000)
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          setWsConnected(false)
        }
        
        wsRef.current = ws
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        setWsConnected(false)
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [queryClient])

  const handleCancelExecution = (planId: string) => {
    cancelMutation.mutate(planId)
  }

  const handleViewExecution = (planId: string) => {
    if (onViewExecution) {
      onViewExecution(planId)
    } else {
      // Default behavior - could navigate to detailed view
      console.log('View execution:', planId)
    }
  }

  const columns = [
    {
      title: 'Execution ID',
      dataIndex: 'plan_id',
      key: 'plan_id',
      render: (id: string) => (
        <Tooltip title={id}>
          <code>{id.slice(0, 8)}...</code>
        </Tooltip>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'overall_status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          running: 'blue',
          completed: 'green',
          failed: 'red',
          queued: 'orange',
          cancelled: 'default',
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number, record: any) => (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Progress
            percent={Math.round(progress * 100)}
            size="small"
            status={record.overall_status === 'failed' ? 'exception' : 'normal'}
          />
          <span style={{ fontSize: '12px', color: '#666' }}>
            {record.completed_tests || 0}/{record.total_tests || 0} tests
          </span>
        </Space>
      ),
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => {
        if (!date) return 'Not started'
        const startTime = new Date(date)
        return (
          <Tooltip title={startTime.toLocaleString()}>
            <span>{startTime.toLocaleTimeString()}</span>
          </Tooltip>
        )
      },
    },
    {
      title: 'ETA',
      dataIndex: 'estimated_completion',
      key: 'estimated_completion',
      render: (date: string) => {
        if (!date) return 'Unknown'
        const eta = new Date(date)
        const now = new Date()
        const diff = eta.getTime() - now.getTime()
        if (diff <= 0) return <Tag color="red">Overdue</Tag>
        const minutes = Math.floor(diff / 60000)
        return (
          <Tooltip title={eta.toLocaleString()}>
            <Tag icon={<ClockCircleOutlined />}>{minutes}m</Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewExecution(record.plan_id)}
          >
            View
          </Button>
          {record.overall_status === 'running' && (
            <Button
              type="text"
              icon={<StopOutlined />}
              onClick={() => handleCancelExecution(record.plan_id)}
              loading={cancelMutation.isLoading}
              danger
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ]

  // Use live metrics if available, otherwise fall back to API metrics
  const currentMetrics = liveMetrics || metrics

  return (
    <div>
      {/* Connection Status */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Badge 
            status={wsConnected ? 'processing' : 'default'} 
            text={wsConnected ? 'Live Updates Connected' : 'Polling Mode'} 
          />
          {currentMetrics && (
            <Tag color={currentMetrics.orchestrator_status === 'healthy' ? 'green' : 'orange'}>
              Orchestrator: {currentMetrics.orchestrator_status}
            </Tag>
          )}
        </Space>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => queryClient.invalidateQueries('activeExecutions')}
        >
          Refresh
        </Button>
      </div>

      {/* Real-time Metrics */}
      {currentMetrics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Active Tests"
                value={currentMetrics.active_tests}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Queued Tests"
                value={currentMetrics.queued_tests}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Available Environments"
                value={currentMetrics.available_environments}
                suffix={`/ ${currentMetrics.total_environments}`}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Completed Today"
                value={currentMetrics.completed_tests_today}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Active Executions Table */}
      <Card title="Active Test Executions" extra={
        <Space>
          <span style={{ fontSize: '12px', color: '#666' }}>
            Last updated: {currentMetrics?.timestamp ? new Date(currentMetrics.timestamp).toLocaleTimeString() : 'Unknown'}
          </span>
        </Space>
      }>
        <Table
          columns={columns}
          dataSource={executions}
          loading={isLoading}
          rowKey="plan_id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} executions`,
          }}
          locale={{
            emptyText: 'No active executions'
          }}
        />
      </Card>
    </div>
  )
}

export default RealTimeExecutionMonitor