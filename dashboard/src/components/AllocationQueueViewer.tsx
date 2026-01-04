import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Button, 
  Tooltip, 
  Progress, 
  Select, 
  Input, 
  Popconfirm,
  Alert,
  Statistic,
  Row,
  Col,
  Badge,
  Dropdown,
  Menu,
  notification,
  Typography,
  Divider
} from 'antd'
import { 
  ClockCircleOutlined, 
  ArrowUpOutlined, 
  ArrowDownOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FilterOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  SettingOutlined,
  BulbOutlined,
  WarningOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { AllocationRequest, AllocationStatus, EnvironmentType } from '../types/environment'

const { Search } = Input
const { Text, Title } = Typography

interface AllocationQueueViewerProps {
  queue: AllocationRequest[]
  estimatedWaitTimes: Map<string, number>
  onPriorityChange: (requestId: string, priority: number) => void
  onCancelRequest?: (requestId: string) => void
  onBulkCancel?: (requestIds: string[]) => void
  onRefresh?: () => void
  realTimeUpdates?: boolean
  lastUpdateTime?: Date
  enableBulkOperations?: boolean
  enableAdvancedFiltering?: boolean
  showQueueAnalytics?: boolean
}

const AllocationQueueViewer: React.FC<AllocationQueueViewerProps> = ({
  queue,
  estimatedWaitTimes,
  onPriorityChange,
  onCancelRequest,
  onBulkCancel,
  onRefresh,
  realTimeUpdates = false,
  lastUpdateTime,
  enableBulkOperations = true,
  enableAdvancedFiltering = true,
  showQueueAnalytics = true
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [filterStatus, setFilterStatus] = useState<AllocationStatus | 'all'>('all')
  const [filterArchitecture, setFilterArchitecture] = useState<string>('all')
  const [searchText, setSearchText] = useState('')
  const [sortField, setSortField] = useState<string>('position')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  // Filter and sort queue data
  const filteredAndSortedQueue = useMemo(() => {
    let filtered = queue.filter(request => {
      // Status filter
      if (filterStatus !== 'all' && request.status !== filterStatus) {
        return false
      }
      
      // Architecture filter
      if (filterArchitecture !== 'all' && request.requirements.architecture !== filterArchitecture) {
        return false
      }
      
      // Search filter
      if (searchText && !request.testId.toLowerCase().includes(searchText.toLowerCase()) &&
          !request.id.toLowerCase().includes(searchText.toLowerCase())) {
        return false
      }
      
      return true
    })

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any
      
      switch (sortField) {
        case 'priority':
          aValue = a.priority
          bValue = b.priority
          break
        case 'submittedAt':
          aValue = new Date(a.submittedAt).getTime()
          bValue = new Date(b.submittedAt).getTime()
          break
        case 'estimatedWait':
          aValue = estimatedWaitTimes.get(a.id) || 0
          bValue = estimatedWaitTimes.get(b.id) || 0
          break
        case 'testId':
          aValue = a.testId
          bValue = b.testId
          break
        default: // position
          aValue = queue.indexOf(a)
          bValue = queue.indexOf(b)
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    return filtered
  }, [queue, filterStatus, filterArchitecture, searchText, sortField, sortOrder, estimatedWaitTimes])

  // Queue analytics
  const queueAnalytics = useMemo(() => {
    const totalRequests = queue.length
    const pendingRequests = queue.filter(r => r.status === AllocationStatus.PENDING).length
    const allocatedRequests = queue.filter(r => r.status === AllocationStatus.ALLOCATED).length
    const failedRequests = queue.filter(r => r.status === AllocationStatus.FAILED).length
    
    const totalWaitTime = Array.from(estimatedWaitTimes.values()).reduce((sum, time) => sum + time, 0)
    const avgWaitTime = totalRequests > 0 ? totalWaitTime / totalRequests : 0
    const maxWaitTime = Math.max(...Array.from(estimatedWaitTimes.values()), 0)
    
    const architectureBreakdown = queue.reduce((acc, req) => {
      const arch = req.requirements.architecture
      acc[arch] = (acc[arch] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const priorityBreakdown = queue.reduce((acc, req) => {
      const priority = req.priority >= 8 ? 'high' : req.priority >= 5 ? 'medium' : 'low'
      acc[priority] = (acc[priority] || 0) + 1
      return acc
    }, { high: 0, medium: 0, low: 0 })

    return {
      totalRequests,
      pendingRequests,
      allocatedRequests,
      failedRequests,
      avgWaitTime,
      maxWaitTime,
      architectureBreakdown,
      priorityBreakdown,
      allocationRate: totalRequests > 0 ? (allocatedRequests / totalRequests) * 100 : 0
    }
  }, [queue, estimatedWaitTimes])

  const formatWaitTime = useCallback((seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.round((seconds % 3600) / 60)
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
  }, [])

  const getPriorityColor = useCallback((priority: number) => {
    if (priority >= 8) return 'red'
    if (priority >= 6) return 'orange'
    if (priority >= 4) return 'blue'
    return 'default'
  }, [])

  const getPriorityLabel = useCallback((priority: number) => {
    if (priority >= 8) return 'Critical'
    if (priority >= 6) return 'High'
    if (priority >= 4) return 'Medium'
    return 'Low'
  }, [])

  const getStatusIcon = useCallback((status: AllocationStatus) => {
    switch (status) {
      case AllocationStatus.PENDING:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
      case AllocationStatus.ALLOCATED:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case AllocationStatus.FAILED:
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case AllocationStatus.CANCELLED:
        return <CloseCircleOutlined style={{ color: '#8c8c8c' }} />
      default:
        return <ClockCircleOutlined />
    }
  }, [])

  const handlePriorityChange = useCallback((requestId: string, newPriority: number) => {
    onPriorityChange(requestId, newPriority)
    notification.success({
      message: 'Priority Updated',
      description: `Request priority changed to ${newPriority}`,
      duration: 2
    })
  }, [onPriorityChange])

  const handleCancelRequest = useCallback((requestId: string) => {
    if (onCancelRequest) {
      onCancelRequest(requestId)
      notification.info({
        message: 'Request Cancelled',
        description: 'Allocation request has been cancelled',
        duration: 3
      })
    }
  }, [onCancelRequest])

  const handleBulkCancel = useCallback(() => {
    if (onBulkCancel && selectedRowKeys.length > 0) {
      onBulkCancel(selectedRowKeys as string[])
      setSelectedRowKeys([])
      notification.info({
        message: 'Bulk Cancellation',
        description: `${selectedRowKeys.length} requests have been cancelled`,
        duration: 3
      })
    }
  }, [onBulkCancel, selectedRowKeys])

  const handleSort = useCallback((field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }, [sortField, sortOrder])

  const clearFilters = useCallback(() => {
    setFilterStatus('all')
    setFilterArchitecture('all')
    setSearchText('')
    setSortField('position')
    setSortOrder('asc')
  }, [])

  // Get unique architectures for filter
  const availableArchitectures = useMemo(() => {
    return Array.from(new Set(queue.map(req => req.requirements.architecture)))
  }, [queue])

  const columns = [
    {
      title: (
        <Space>
          Position
          <Button 
            type="text" 
            size="small" 
            icon={sortField === 'position' ? (sortOrder === 'asc' ? <SortAscendingOutlined /> : <SortDescendingOutlined />) : <SortAscendingOutlined />}
            onClick={() => handleSort('position')}
          />
        </Space>
      ),
      key: 'position',
      width: 100,
      render: (_: any, record: AllocationRequest) => {
        const originalIndex = queue.findIndex(r => r.id === record.id)
        const isMovingUp = originalIndex > filteredAndSortedQueue.findIndex(r => r.id === record.id)
        const isMovingDown = originalIndex < filteredAndSortedQueue.findIndex(r => r.id === record.id)
        
        return (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
              #{originalIndex + 1}
            </div>
            {(isMovingUp || isMovingDown) && (
              <div style={{ fontSize: '10px', color: isMovingUp ? '#52c41a' : '#ff4d4f' }}>
                {isMovingUp ? '↑' : '↓'}
              </div>
            )}
          </div>
        )
      }
    },
    {
      title: (
        <Space>
          Test ID
          <Button 
            type="text" 
            size="small" 
            icon={sortField === 'testId' ? (sortOrder === 'asc' ? <SortAscendingOutlined /> : <SortDescendingOutlined />) : <SortAscendingOutlined />}
            onClick={() => handleSort('testId')}
          />
        </Space>
      ),
      dataIndex: 'testId',
      key: 'testId',
      width: 150,
      render: (testId: string, record: AllocationRequest) => (
        <Tooltip title={`Full ID: ${testId}`}>
          <div>
            <Text code style={{ fontSize: '12px' }}>
              {testId.slice(0, 12)}...
            </Text>
            <div style={{ fontSize: '10px', color: '#666' }}>
              {record.id.slice(0, 8)}...
            </div>
          </div>
        </Tooltip>
      )
    },
    {
      title: (
        <Space>
          Priority
          <Button 
            type="text" 
            size="small" 
            icon={sortField === 'priority' ? (sortOrder === 'asc' ? <SortAscendingOutlined /> : <SortDescendingOutlined />) : <SortAscendingOutlined />}
            onClick={() => handleSort('priority')}
          />
        </Space>
      ),
      dataIndex: 'priority',
      key: 'priority',
      width: 140,
      render: (priority: number, record: AllocationRequest) => (
        <Space direction="vertical" size="small">
          <Space>
            <Tag color={getPriorityColor(priority)}>
              {priority} - {getPriorityLabel(priority)}
            </Tag>
          </Space>
          <Space.Compact size="small">
            <Tooltip title="Increase priority">
              <Button 
                size="small" 
                icon={<ArrowUpOutlined />}
                onClick={() => handlePriorityChange(record.id, Math.min(priority + 1, 10))}
                disabled={priority >= 10}
              />
            </Tooltip>
            <Tooltip title="Decrease priority">
              <Button 
                size="small" 
                icon={<ArrowDownOutlined />}
                onClick={() => handlePriorityChange(record.id, Math.max(priority - 1, 1))}
                disabled={priority <= 1}
              />
            </Tooltip>
          </Space.Compact>
        </Space>
      )
    },
    {
      title: 'Requirements',
      dataIndex: 'requirements',
      key: 'requirements',
      width: 200,
      render: (requirements: any) => (
        <Space direction="vertical" size="small">
          <Space wrap size="small">
            <Tag color="blue">{requirements.architecture}</Tag>
            {requirements.preferredEnvironmentType && (
              <Tag color="green">{requirements.preferredEnvironmentType}</Tag>
            )}
          </Space>
          <div style={{ fontSize: '11px', color: '#666' }}>
            <div>{requirements.minCpuCores} cores, {requirements.minMemoryMB}MB RAM</div>
            {requirements.requiredFeatures.length > 0 && (
              <div>Features: {requirements.requiredFeatures.join(', ')}</div>
            )}
            <div>Isolation: {requirements.isolationLevel}</div>
          </div>
        </Space>
      )
    },
    {
      title: (
        <Space>
          Est. Wait
          <Button 
            type="text" 
            size="small" 
            icon={sortField === 'estimatedWait' ? (sortOrder === 'asc' ? <SortAscendingOutlined /> : <SortDescendingOutlined />) : <SortAscendingOutlined />}
            onClick={() => handleSort('estimatedWait')}
          />
        </Space>
      ),
      key: 'estimatedWait',
      width: 120,
      render: (_: any, record: AllocationRequest) => {
        const waitTime = estimatedWaitTimes.get(record.id) || 0
        const isLongWait = waitTime > 300 // 5 minutes
        
        return (
          <Tooltip title={`Estimated wait time: ${waitTime} seconds`}>
            <Space direction="vertical" size="small">
              <Space>
                <ClockCircleOutlined style={{ color: isLongWait ? '#ff4d4f' : '#52c41a' }} />
                <Text style={{ color: isLongWait ? '#ff4d4f' : undefined }}>
                  {formatWaitTime(waitTime)}
                </Text>
              </Space>
              {record.estimatedStartTime && (
                <div style={{ fontSize: '10px', color: '#666' }}>
                  ETA: {new Date(record.estimatedStartTime).toLocaleTimeString()}
                </div>
              )}
            </Space>
          </Tooltip>
        )
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: AllocationStatus, record: AllocationRequest) => (
        <Space direction="vertical" size="small">
          <Space>
            {getStatusIcon(status)}
            <Tag color={
              status === AllocationStatus.PENDING ? 'orange' : 
              status === AllocationStatus.ALLOCATED ? 'green' : 
              status === AllocationStatus.FAILED ? 'red' : 'default'
            }>
              {status.toUpperCase()}
            </Tag>
          </Space>
          {status === AllocationStatus.FAILED && (
            <Tooltip title="Click to view error details">
              <Button size="small" type="link" icon={<ExclamationCircleOutlined />}>
                Details
              </Button>
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: (
        <Space>
          Submitted
          <Button 
            type="text" 
            size="small" 
            icon={sortField === 'submittedAt' ? (sortOrder === 'asc' ? <SortAscendingOutlined /> : <SortDescendingOutlined />) : <SortAscendingOutlined />}
            onClick={() => handleSort('submittedAt')}
          />
        </Space>
      ),
      dataIndex: 'submittedAt',
      key: 'submittedAt',
      width: 120,
      render: (submittedAt: Date) => {
        const submitTime = new Date(submittedAt)
        const now = new Date()
        const diffMinutes = Math.floor((now.getTime() - submitTime.getTime()) / 60000)
        
        return (
          <div style={{ fontSize: '12px' }}>
            <div>{submitTime.toLocaleTimeString()}</div>
            <div style={{ color: '#666', fontSize: '10px' }}>
              {diffMinutes < 60 ? `${diffMinutes}m ago` : `${Math.floor(diffMinutes / 60)}h ago`}
            </div>
          </div>
        )
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: any, record: AllocationRequest) => (
        <Space>
          <Tooltip title="View details">
            <Button 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => setExpandedRows(prev => 
                prev.includes(record.id) 
                  ? prev.filter(id => id !== record.id)
                  : [...prev, record.id]
              )}
            />
          </Tooltip>
          {onCancelRequest && record.status === AllocationStatus.PENDING && (
            <Popconfirm
              title="Cancel this allocation request?"
              description="This action cannot be undone."
              onConfirm={() => handleCancelRequest(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Tooltip title="Cancel request">
                <Button 
                  size="small" 
                  icon={<DeleteOutlined />}
                  danger
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  const rowSelection = enableBulkOperations ? {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record: AllocationRequest) => ({
      disabled: record.status !== AllocationStatus.PENDING
    })
  } : undefined

  return (
    <Card 
      title={
        <Space>
          <ClockCircleOutlined />
          <Title level={4} style={{ margin: 0 }}>Allocation Queue</Title>
          <Badge count={queueAnalytics.totalRequests} showZero color="blue" />
          {realTimeUpdates && (
            <Tooltip title="Live updates enabled">
              <ThunderboltOutlined style={{ color: '#52c41a' }} />
            </Tooltip>
          )}
        </Space>
      }
      extra={
        <Space>
          {lastUpdateTime && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Updated: {lastUpdateTime.toLocaleTimeString()}
            </Text>
          )}
          {onRefresh && (
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={onRefresh}
              title="Refresh queue"
            />
          )}
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item key="export" icon={<SettingOutlined />}>
                  Export Queue Data
                </Menu.Item>
                <Menu.Item key="analytics" icon={<BulbOutlined />}>
                  Queue Analytics
                </Menu.Item>
              </Menu>
            }
          >
            <Button size="small" icon={<SettingOutlined />} />
          </Dropdown>
        </Space>
      }
    >
      {/* Queue Analytics Dashboard */}
      {showQueueAnalytics && queueAnalytics.totalRequests > 0 && (
        <div style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Total Requests"
                value={queueAnalytics.totalRequests}
                prefix={<ClockCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Avg Wait Time"
                value={formatWaitTime(queueAnalytics.avgWaitTime)}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: queueAnalytics.avgWaitTime > 300 ? '#ff4d4f' : '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Allocation Rate"
                value={queueAnalytics.allocationRate}
                precision={1}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: queueAnalytics.allocationRate > 80 ? '#52c41a' : '#faad14' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Failed Requests"
                value={queueAnalytics.failedRequests}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: queueAnalytics.failedRequests > 0 ? '#ff4d4f' : '#52c41a' }}
              />
            </Col>
          </Row>
          
          <Divider />
          
          {/* Priority and Architecture Breakdown */}
          <Row gutter={16}>
            <Col span={12}>
              <div>
                <Text strong>Priority Breakdown:</Text>
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    <Tag color="red">Critical: {queueAnalytics.priorityBreakdown.high}</Tag>
                    <Tag color="orange">Medium: {queueAnalytics.priorityBreakdown.medium}</Tag>
                    <Tag color="blue">Low: {queueAnalytics.priorityBreakdown.low}</Tag>
                  </Space>
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div>
                <Text strong>Architecture Breakdown:</Text>
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    {Object.entries(queueAnalytics.architectureBreakdown).map(([arch, count]) => (
                      <Tag key={arch} color="geekblue">{arch}: {count}</Tag>
                    ))}
                  </Space>
                </div>
              </div>
            </Col>
          </Row>
        </div>
      )}

      {/* Filters and Controls */}
      {enableAdvancedFiltering && (
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col span={6}>
              <Search
                placeholder="Search by Test ID or Request ID"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
                size="small"
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Status"
                value={filterStatus}
                onChange={setFilterStatus}
                size="small"
                style={{ width: '100%' }}
              >
                <Select.Option value="all">All Status</Select.Option>
                <Select.Option value={AllocationStatus.PENDING}>Pending</Select.Option>
                <Select.Option value={AllocationStatus.ALLOCATED}>Allocated</Select.Option>
                <Select.Option value={AllocationStatus.FAILED}>Failed</Select.Option>
                <Select.Option value={AllocationStatus.CANCELLED}>Cancelled</Select.Option>
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="Architecture"
                value={filterArchitecture}
                onChange={setFilterArchitecture}
                size="small"
                style={{ width: '100%' }}
              >
                <Select.Option value="all">All Architectures</Select.Option>
                {availableArchitectures.map(arch => (
                  <Select.Option key={arch} value={arch}>{arch}</Select.Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Space>
                <Button 
                  size="small" 
                  icon={<FilterOutlined />} 
                  onClick={clearFilters}
                >
                  Clear Filters
                </Button>
                {enableBulkOperations && selectedRowKeys.length > 0 && (
                  <Popconfirm
                    title={`Cancel ${selectedRowKeys.length} selected requests?`}
                    description="This action cannot be undone."
                    onConfirm={handleBulkCancel}
                    okText="Yes"
                    cancelText="No"
                  >
                    <Button 
                      size="small" 
                      danger
                      icon={<DeleteOutlined />}
                    >
                      Cancel Selected ({selectedRowKeys.length})
                    </Button>
                  </Popconfirm>
                )}
              </Space>
            </Col>
            <Col span={4}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Showing {filteredAndSortedQueue.length} of {queue.length} requests
              </Text>
            </Col>
          </Row>
        </div>
      )}

      {/* Queue Status Alerts */}
      {queueAnalytics.maxWaitTime > 600 && (
        <Alert
          message="Long Wait Times Detected"
          description={`Some requests have estimated wait times over ${formatWaitTime(queueAnalytics.maxWaitTime)}. Consider adding more environments or adjusting priorities.`}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" type="link">
              View Recommendations
            </Button>
          }
        />
      )}

      {queueAnalytics.failedRequests > 0 && (
        <Alert
          message={`${queueAnalytics.failedRequests} Failed Allocation${queueAnalytics.failedRequests > 1 ? 's' : ''}`}
          description="Some allocation requests have failed. Review the requirements or try again."
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" type="link">
              View Failed Requests
            </Button>
          }
        />
      )}

      {/* Main Queue Table */}
      {filteredAndSortedQueue.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          {queue.length === 0 ? (
            <div>
              <ClockCircleOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', marginBottom: '8px' }}>No allocation requests in queue</div>
              <div style={{ fontSize: '14px' }}>Submit a test to see allocation requests here</div>
            </div>
          ) : (
            <div>
              <FilterOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', marginBottom: '8px' }}>No requests match current filters</div>
              <Button type="link" onClick={clearFilters}>Clear all filters</Button>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Queue Progress Indicator */}
          <div style={{ marginBottom: 16 }}>
            <Space align="center">
              <Text>Queue Progress:</Text>
              <Progress 
                percent={Math.round(queueAnalytics.allocationRate)}
                size="small"
                style={{ width: 200 }}
                strokeColor={queueAnalytics.allocationRate > 80 ? '#52c41a' : '#faad14'}
              />
              <Text style={{ fontSize: '12px', color: '#666' }}>
                {queueAnalytics.allocatedRequests} / {queueAnalytics.totalRequests} allocated
              </Text>
              {realTimeUpdates && (
                <Badge status="processing" text="Live" />
              )}
            </Space>
          </div>
          
          <Table
            columns={columns}
            dataSource={filteredAndSortedQueue}
            rowKey="id"
            size="small"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} requests`
            }}
            rowSelection={rowSelection}
            scroll={{ x: 1200 }}
            expandable={{
              expandedRowKeys: expandedRows,
              onExpand: (expanded, record) => {
                setExpandedRows(prev => 
                  expanded 
                    ? [...prev, record.id]
                    : prev.filter(id => id !== record.id)
                )
              },
              expandedRowRender: (record) => (
                <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <div>
                        <Text strong>Request Details:</Text>
                        <div style={{ marginTop: 8, fontSize: '12px' }}>
                          <div><strong>Request ID:</strong> {record.id}</div>
                          <div><strong>Test ID:</strong> {record.testId}</div>
                          <div><strong>Submitted:</strong> {new Date(record.submittedAt).toLocaleString()}</div>
                          {record.estimatedStartTime && (
                            <div><strong>Estimated Start:</strong> {new Date(record.estimatedStartTime).toLocaleString()}</div>
                          )}
                        </div>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div>
                        <Text strong>Hardware Requirements:</Text>
                        <div style={{ marginTop: 8, fontSize: '12px' }}>
                          <div><strong>Architecture:</strong> {record.requirements.architecture}</div>
                          <div><strong>CPU Cores:</strong> {record.requirements.minCpuCores}</div>
                          <div><strong>Memory:</strong> {record.requirements.minMemoryMB}MB</div>
                          <div><strong>Isolation:</strong> {record.requirements.isolationLevel}</div>
                          {record.requirements.requiredFeatures.length > 0 && (
                            <div><strong>Features:</strong> {record.requirements.requiredFeatures.join(', ')}</div>
                          )}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </div>
              )
            }}
            rowClassName={(record) => {
              if (record.status === AllocationStatus.FAILED) return 'queue-row-failed'
              if (record.status === AllocationStatus.ALLOCATED) return 'queue-row-allocated'
              if (record.priority >= 8) return 'queue-row-high-priority'
              return ''
            }}
          />
        </>
      )}
      
      {/* Custom CSS for row styling */}
      <style>{`
        .queue-row-failed {
          background-color: #fff2f0 !important;
        }
        .queue-row-allocated {
          background-color: #f6ffed !important;
        }
        .queue-row-high-priority {
          background-color: #fff7e6 !important;
        }
        .queue-row-failed:hover,
        .queue-row-allocated:hover,
        .queue-row-high-priority:hover {
          background-color: #e6f7ff !important;
        }
      `}</style>
    </Card>
  )
}

export default AllocationQueueViewer