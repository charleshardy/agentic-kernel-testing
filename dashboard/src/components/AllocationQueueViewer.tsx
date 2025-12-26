import React, { useState, useCallback, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Button, 
  Tooltip, 
  Progress, 
  Typography, 
  InputNumber, 
  Popconfirm,
  Badge,
  Empty,
  Divider,
  Row,
  Col,
  Statistic,
  Alert
} from 'antd'
import { 
  ClockCircleOutlined, 
  ArrowUpOutlined, 
  ArrowDownOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  FieldTimeOutlined,
  TeamOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { AllocationQueueViewerProps, AllocationRequest, AllocationStatus } from '../types/environment'

const { Text, Title } = Typography

/**
 * AllocationQueueViewer component showing pending allocation requests
 * Displays queue position, estimated wait times, and priority management controls
 */
const AllocationQueueViewer: React.FC<AllocationQueueViewerProps> = ({
  queue,
  estimatedWaitTimes,
  onPriorityChange
}) => {
  const [selectedRequests, setSelectedRequests] = useState<string[]>([])
  const [editingPriority, setEditingPriority] = useState<string | null>(null)

  // Sort queue by priority (lower number = higher priority) and submission time
  const sortedQueue = useMemo(() => {
    return [...queue].sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority
      }
      return new Date(a.submittedAt).getTime() - new Date(b.submittedAt).getTime()
    })
  }, [queue])

  // Calculate queue statistics
  const queueStats = useMemo(() => {
    const totalRequests = queue.length
    const highPriorityRequests = queue.filter(req => req.priority <= 2).length
    const mediumPriorityRequests = queue.filter(req => req.priority >= 3 && req.priority <= 5).length
    const lowPriorityRequests = queue.filter(req => req.priority > 5).length
    const averageWaitTime = Object.values(estimatedWaitTimes).reduce((sum, time) => sum + time, 0) / totalRequests || 0

    return {
      totalRequests,
      highPriorityRequests,
      mediumPriorityRequests,
      lowPriorityRequests,
      averageWaitTime: Math.round(averageWaitTime)
    }
  }, [queue, estimatedWaitTimes])

  // Format wait time for display
  const formatWaitTime = useCallback((seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.round((seconds % 3600) / 60)
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
    }
  }, [])

  // Get priority color and label
  const getPriorityDisplay = useCallback((priority: number) => {
    if (priority <= 2) {
      return { color: 'red', label: 'High', icon: <ThunderboltOutlined /> }
    } else if (priority <= 5) {
      return { color: 'orange', label: 'Medium', icon: <ClockCircleOutlined /> }
    } else {
      return { color: 'blue', label: 'Low', icon: <FieldTimeOutlined /> }
    }
  }, [])

  // Get status color
  const getStatusColor = useCallback((status: AllocationStatus): string => {
    switch (status) {
      case AllocationStatus.QUEUED:
        return 'processing'
      case AllocationStatus.ALLOCATING:
        return 'warning'
      case AllocationStatus.ALLOCATED:
        return 'success'
      case AllocationStatus.FAILED:
        return 'error'
      case AllocationStatus.CANCELLED:
        return 'default'
      default:
        return 'default'
    }
  }, [])

  // Handle priority change
  const handlePriorityChange = useCallback((requestId: string, newPriority: number) => {
    if (newPriority >= 1 && newPriority <= 10) {
      onPriorityChange(requestId, newPriority)
      setEditingPriority(null)
    }
  }, [onPriorityChange])

  // Handle row selection
  const handleRowSelection = {
    selectedRowKeys: selectedRequests,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedRequests(selectedRowKeys as string[])
    }
  }

  // Table columns configuration
  const columns: ColumnsType<AllocationRequest> = [
    {
      title: 'Position',
      key: 'position',
      width: 80,
      render: (_, record) => {
        const position = sortedQueue.findIndex(req => req.id === record.id) + 1
        return (
          <Badge 
            count={position} 
            style={{ backgroundColor: position <= 3 ? '#f50' : position <= 10 ? '#fa8c16' : '#1890ff' }}
          />
        )
      }
    },
    {
      title: 'Test ID',
      dataIndex: 'testId',
      key: 'testId',
      width: 150,
      render: (testId: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {testId.length > 20 ? `${testId.slice(0, 20)}...` : testId}
        </Text>
      )
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 120,
      render: (priority: number, record) => {
        const { color, label, icon } = getPriorityDisplay(priority)
        
        if (editingPriority === record.id) {
          return (
            <Space>
              <InputNumber
                min={1}
                max={10}
                defaultValue={priority}
                size="small"
                style={{ width: 60 }}
                onPressEnter={(e) => {
                  const value = (e.target as HTMLInputElement).value
                  handlePriorityChange(record.id, parseInt(value))
                }}
                onBlur={(e) => {
                  const value = e.target.value
                  if (value) {
                    handlePriorityChange(record.id, parseInt(value))
                  } else {
                    setEditingPriority(null)
                  }
                }}
                autoFocus
              />
            </Space>
          )
        }

        return (
          <Space>
            <Tag 
              color={color} 
              icon={icon}
              style={{ cursor: 'pointer' }}
              onClick={() => setEditingPriority(record.id)}
            >
              {label} ({priority})
            </Tag>
          </Space>
        )
      }
    },
    {
      title: 'Requirements',
      key: 'requirements',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>
            <strong>Arch:</strong> {record.requirements.architecture}
          </Text>
          <Text style={{ fontSize: '12px' }}>
            <strong>Memory:</strong> {record.requirements.minMemoryMB}MB
          </Text>
          <Text style={{ fontSize: '12px' }}>
            <strong>CPU:</strong> {record.requirements.minCpuCores} cores
          </Text>
          {record.requirements.requiredFeatures.length > 0 && (
            <Text style={{ fontSize: '12px' }}>
              <strong>Features:</strong> {record.requirements.requiredFeatures.join(', ')}
            </Text>
          )}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: AllocationStatus) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Wait Time',
      key: 'waitTime',
      width: 120,
      render: (_, record) => {
        const waitTime = estimatedWaitTimes.get ? estimatedWaitTimes.get(record.id) : estimatedWaitTimes[record.id]
        const submittedAt = new Date(record.submittedAt)
        const elapsedTime = Math.floor((Date.now() - submittedAt.getTime()) / 1000)
        
        return (
          <Space direction="vertical" size="small">
            <Tooltip title={`Estimated total wait time: ${formatWaitTime(waitTime || 0)}`}>
              <Text style={{ fontSize: '12px' }}>
                <ClockCircleOutlined /> {formatWaitTime(waitTime || 0)}
              </Text>
            </Tooltip>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              Waiting: {formatWaitTime(elapsedTime)}
            </Text>
          </Space>
        )
      }
    },
    {
      title: 'Submitted',
      dataIndex: 'submittedAt',
      key: 'submittedAt',
      width: 120,
      render: (submittedAt: Date) => {
        const date = new Date(submittedAt)
        return (
          <Tooltip title={date.toLocaleString()}>
            <Text style={{ fontSize: '12px' }}>
              {date.toLocaleTimeString()}
            </Text>
          </Tooltip>
        )
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="Increase Priority">
            <Button
              size="small"
              icon={<ArrowUpOutlined />}
              disabled={record.priority <= 1}
              onClick={() => handlePriorityChange(record.id, record.priority - 1)}
            />
          </Tooltip>
          <Tooltip title="Decrease Priority">
            <Button
              size="small"
              icon={<ArrowDownOutlined />}
              disabled={record.priority >= 10}
              onClick={() => handlePriorityChange(record.id, record.priority + 1)}
            />
          </Tooltip>
          <Popconfirm
            title="Cancel this allocation request?"
            description="This action cannot be undone."
            onConfirm={() => {
              // TODO: Implement cancel request functionality
              console.log('Cancel request:', record.id)
            }}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Cancel Request">
              <Button
                size="small"
                icon={<DeleteOutlined />}
                danger
                disabled={record.status !== AllocationStatus.QUEUED}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  if (queue.length === 0) {
    return (
      <Card
        title={
          <Space>
            <TeamOutlined />
            Allocation Queue
            <Badge count={0} style={{ backgroundColor: '#52c41a' }} />
          </Space>
        }
      >
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              No allocation requests in queue
              <br />
              <Text type="secondary">All tests are either allocated or completed</Text>
            </span>
          }
        />
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <TeamOutlined />
          Allocation Queue
          <Badge count={queue.length} style={{ backgroundColor: '#1890ff' }} />
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="Queue updates in real-time">
            <InfoCircleOutlined style={{ color: '#1890ff' }} />
          </Tooltip>
        </Space>
      }
    >
      {/* Queue Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="Total Requests"
            value={queueStats.totalRequests}
            prefix={<TeamOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="High Priority"
            value={queueStats.highPriorityRequests}
            prefix={<ThunderboltOutlined />}
            valueStyle={{ color: '#f5222d' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Medium Priority"
            value={queueStats.mediumPriorityRequests}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#fa8c16' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Avg Wait Time"
            value={queueStats.averageWaitTime}
            suffix="s"
            prefix={<FieldTimeOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
      </Row>

      <Divider />

      {/* Priority Legend */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>Priority Levels: </Text>
        <Space>
          <Tag color="red" icon={<ThunderboltOutlined />}>High (1-2)</Tag>
          <Tag color="orange" icon={<ClockCircleOutlined />}>Medium (3-5)</Tag>
          <Tag color="blue" icon={<FieldTimeOutlined />}>Low (6-10)</Tag>
        </Space>
      </div>

      {/* Queue Progress Indicator */}
      {queueStats.totalRequests > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text strong>Queue Composition:</Text>
          <Progress
            percent={100}
            success={{ 
              percent: (queueStats.highPriorityRequests / queueStats.totalRequests) * 100 
            }}
            strokeColor={{
              '0%': '#f5222d',
              '50%': '#fa8c16',
              '100%': '#1890ff'
            }}
            showInfo={false}
            size="small"
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginTop: 4 }}>
            <Text type="secondary">High Priority: {queueStats.highPriorityRequests}</Text>
            <Text type="secondary">Medium Priority: {queueStats.mediumPriorityRequests}</Text>
            <Text type="secondary">Low Priority: {queueStats.lowPriorityRequests}</Text>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {selectedRequests.length > 0 && (
        <Alert
          message={`${selectedRequests.length} request(s) selected`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          action={
            <Space>
              <Button size="small" onClick={() => setSelectedRequests([])}>
                Clear Selection
              </Button>
              <Popconfirm
                title={`Cancel ${selectedRequests.length} selected request(s)?`}
                onConfirm={() => {
                  // TODO: Implement bulk cancel functionality
                  console.log('Bulk cancel:', selectedRequests)
                  setSelectedRequests([])
                }}
              >
                <Button size="small" danger>
                  Cancel Selected
                </Button>
              </Popconfirm>
            </Space>
          }
        />
      )}

      {/* Queue Table */}
      <Table
        columns={columns}
        dataSource={sortedQueue}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} requests`
        }}
        rowSelection={handleRowSelection}
        scroll={{ x: 1000 }}
        rowClassName={(record, index) => {
          const position = index + 1
          if (position <= 3) return 'high-priority-row'
          if (position <= 10) return 'medium-priority-row'
          return 'low-priority-row'
        }}
      />

      <style jsx>{`
        .high-priority-row {
          background-color: #fff2f0;
        }
        .medium-priority-row {
          background-color: #fff7e6;
        }
        .low-priority-row {
          background-color: #f6ffed;
        }
      `}</style>
    </Card>
  )
}

export default AllocationQueueViewer