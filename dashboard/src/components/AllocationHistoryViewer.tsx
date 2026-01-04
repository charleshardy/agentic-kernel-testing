import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { 
  Card, 
  Timeline, 
  Tag, 
  Space, 
  Empty, 
  Button, 
  Select, 
  DatePicker, 
  Input, 
  Table, 
  Tooltip, 
  Badge, 
  Statistic, 
  Row, 
  Col,
  Drawer,
  Descriptions,
  Alert,
  Switch,
  Dropdown,
  Menu,
  Typography,
  Divider,
  Progress
} from 'antd'
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  StopOutlined,
  FilterOutlined,
  ExportOutlined,
  SearchOutlined,
  ReloadOutlined,
  BarChartOutlined,
  EyeOutlined,
  DownloadOutlined,
  CalendarOutlined,
  BugOutlined,
  LinkOutlined
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import dayjs, { Dayjs } from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { AllocationEvent, Environment, AllocationRequest } from '../types/environment'
import apiService from '../services/api'
import useRealTimeUpdates from '../hooks/useRealTimeUpdates'

dayjs.extend(relativeTime)

const { RangePicker } = DatePicker
const { Search } = Input
const { Text, Title } = Typography

interface AllocationHistoryViewerProps {
  autoRefresh?: boolean
  refreshInterval?: number
  planId?: string
  environmentId?: string
  testId?: string
  showAnalytics?: boolean
  enableExport?: boolean
  enableFiltering?: boolean
  maxEvents?: number
}

interface HistoryFilter {
  eventTypes: string[]
  environmentIds: string[]
  testIds: string[]
  dateRange: [Dayjs, Dayjs] | null
  searchQuery: string
  severity: string[]
}

interface AllocationAnalytics {
  totalEvents: number
  successfulAllocations: number
  failedAllocations: number
  averageAllocationTime: number
  mostActiveEnvironment: string
  peakUsageTime: string
  failureRate: number
  queueWaitTimes: number[]
}

const AllocationHistoryViewer: React.FC<AllocationHistoryViewerProps> = ({
  autoRefresh = true,
  refreshInterval = 5000,
  planId,
  environmentId,
  testId,
  showAnalytics = true,
  enableExport = true,
  enableFiltering = true,
  maxEvents = 1000
}) => {
  const [viewMode, setViewMode] = useState<'timeline' | 'table'>('timeline')
  const [filter, setFilter] = useState<HistoryFilter>({
    eventTypes: [],
    environmentIds: [],
    testIds: [],
    dateRange: null,
    searchQuery: '',
    severity: []
  })
  const [selectedEvent, setSelectedEvent] = useState<AllocationEvent | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  // Real-time updates for allocation events
  const realTimeUpdates = useRealTimeUpdates({
    enableWebSocket: false, // Disabled to prevent connection errors
    enableSSE: false, // Disabled to prevent connection errors
    onAllocationEvent: useCallback((event: AllocationEvent) => {
      console.log('📊 New allocation event received:', event)
      // The query will automatically refetch due to real-time updates
    }, [])
  })

  // Generate mock data for demonstration
  const mockHistoryData = useMemo(() => {
    const events: AllocationEvent[] = []
    const eventTypes = ['allocated', 'deallocated', 'failed', 'queued']
    const environments = ['env-001-qemu-x86', 'env-002-qemu-arm', 'env-003-docker', 'env-004-physical']
    const tests = ['test-kernel-boot', 'test-network-stack', 'test-filesystem', 'test-memory-mgmt']
    
    for (let i = 0; i < 50; i++) {
      const timestamp = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000) // Last 7 days
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)]
      const envId = environments[Math.floor(Math.random() * environments.length)]
      const testIdValue = tests[Math.floor(Math.random() * tests.length)]
      
      events.push({
        id: `event-${i}`,
        type: eventType as any,
        environmentId: eventType === 'queued' ? '' : envId,
        testId: testIdValue,
        timestamp,
        metadata: {
          duration: eventType === 'allocated' ? Math.floor(Math.random() * 300) + 30 : undefined,
          priority: eventType === 'queued' ? Math.floor(Math.random() * 10) + 1 : undefined,
          reason: eventType === 'deallocated' ? ['completed', 'timeout', 'cancelled'][Math.floor(Math.random() * 3)] : undefined,
          error: eventType === 'failed' ? ['timeout', 'resource_exhausted', 'configuration_error'][Math.floor(Math.random() * 3)] : undefined,
          queuePosition: eventType === 'queued' ? Math.floor(Math.random() * 20) + 1 : undefined,
          resourceUsage: eventType === 'allocated' ? {
            cpu: Math.floor(Math.random() * 100),
            memory: Math.floor(Math.random() * 100),
            disk: Math.floor(Math.random() * 100)
          } : undefined
        }
      })
    }
    
    return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }, [])

  const allocationHistory = mockHistoryData

  // Calculate analytics
  const analytics = useMemo((): AllocationAnalytics => {
    const events = allocationHistory
    const allocatedEvents = events.filter((e: AllocationEvent) => e.type === 'allocated')
    const failedEvents = events.filter((e: AllocationEvent) => e.type === 'failed')
    const queuedEvents = events.filter((e: AllocationEvent) => e.type === 'queued')
    
    const environmentCounts = events.reduce((acc: Record<string, number>, event: AllocationEvent) => {
      if (event.environmentId) {
        acc[event.environmentId] = (acc[event.environmentId] || 0) + 1
      }
      return acc
    }, {})
    
    const mostActiveEnvironment = Object.entries(environmentCounts)
      .sort(([,a], [,b]) => (b as number) - (a as number))[0]?.[0] || 'N/A'
    
    const avgAllocationTime = allocatedEvents.length > 0 
      ? allocatedEvents.reduce((sum: number, event: AllocationEvent) => sum + (event.metadata?.duration || 0), 0) / allocatedEvents.length
      : 0
    
    const queueWaitTimes = queuedEvents
      .map((event: AllocationEvent) => event.metadata?.duration || 0)
      .filter((time: number) => time > 0)
    
    return {
      totalEvents: events.length,
      successfulAllocations: allocatedEvents.length,
      failedAllocations: failedEvents.length,
      averageAllocationTime: avgAllocationTime,
      mostActiveEnvironment,
      peakUsageTime: 'N/A', // Would be calculated from real data
      failureRate: events.length > 0 ? (failedEvents.length / events.length) * 100 : 0,
      queueWaitTimes
    }
  }, [allocationHistory])

  // Apply filters to history data
  const filteredHistory = useMemo(() => {
    let filtered = allocationHistory

    if (filter.eventTypes.length > 0) {
      filtered = filtered.filter((event: AllocationEvent) => filter.eventTypes.includes(event.type))
    }

    if (filter.environmentIds.length > 0) {
      filtered = filtered.filter((event: AllocationEvent) => 
        event.environmentId && filter.environmentIds.includes(event.environmentId)
      )
    }

    if (filter.testIds.length > 0) {
      filtered = filtered.filter((event: AllocationEvent) => 
        event.testId && filter.testIds.includes(event.testId)
      )
    }

    if (filter.dateRange) {
      const [start, end] = filter.dateRange
      filtered = filtered.filter((event: AllocationEvent) => {
        const eventDate = dayjs(event.timestamp)
        return eventDate.isAfter(start) && eventDate.isBefore(end)
      })
    }

    if (filter.searchQuery) {
      const query = filter.searchQuery.toLowerCase()
      filtered = filtered.filter((event: AllocationEvent) => 
        event.testId?.toLowerCase().includes(query) ||
        event.environmentId?.toLowerCase().includes(query) ||
        event.type.toLowerCase().includes(query) ||
        JSON.stringify(event.metadata).toLowerCase().includes(query)
      )
    }

    return filtered
  }, [allocationHistory, filter])

  // Event type options for filtering
  const eventTypeOptions = [
    { label: 'Allocated', value: 'allocated', color: 'green' },
    { label: 'Deallocated', value: 'deallocated', color: 'blue' },
    { label: 'Failed', value: 'failed', color: 'red' },
    { label: 'Queued', value: 'queued', color: 'orange' }
  ]

  // Get unique environment and test IDs for filtering
  const uniqueEnvironmentIds = [...new Set(allocationHistory.map((e: AllocationEvent) => e.environmentId).filter(Boolean))]
  const uniqueTestIds = [...new Set(allocationHistory.map((e: AllocationEvent) => e.testId).filter(Boolean))]

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'allocated': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'deallocated': return <StopOutlined style={{ color: '#1890ff' }} />
      case 'failed': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'queued': return <ClockCircleOutlined style={{ color: '#faad14' }} />
      default: return <ClockCircleOutlined />
    }
  }

  const getEventColor = (type: string) => {
    switch (type) {
      case 'allocated': return 'green'
      case 'deallocated': return 'blue'
      case 'failed': return 'red'
      case 'queued': return 'orange'
      default: return 'default'
    }
  }

  const formatRelativeTime = (timestamp: Date) => {
    return dayjs(timestamp).fromNow()
  }

  const handleEventClick = (event: AllocationEvent) => {
    setSelectedEvent(event)
    setDrawerVisible(true)
  }

  const handleExport = async (format: 'csv' | 'json') => {
    setIsExporting(true)
    try {
      const data = filteredHistory.map((event: AllocationEvent) => ({
        timestamp: event.timestamp.toISOString(),
        type: event.type,
        environmentId: event.environmentId || '',
        testId: event.testId || '',
        metadata: JSON.stringify(event.metadata)
      }))

      if (format === 'csv') {
        const csv = [
          'Timestamp,Type,Environment ID,Test ID,Metadata',
          ...data.map((row: any) => 
            `${row.timestamp},${row.type},${row.environmentId},${row.testId},"${row.metadata}"`
          )
        ].join('\n')
        
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `allocation-history-${Date.now()}.csv`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const json = JSON.stringify(data, null, 2)
        const blob = new Blob([json], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `allocation-history-${Date.now()}.json`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const clearFilters = () => {
    setFilter({
      eventTypes: [],
      environmentIds: [],
      testIds: [],
      dateRange: null,
      searchQuery: '',
      severity: []
    })
  }

  const hasActiveFilters = filter.eventTypes.length > 0 || 
                          filter.environmentIds.length > 0 || 
                          filter.testIds.length > 0 || 
                          filter.dateRange !== null || 
                          filter.searchQuery !== ''

  // Table columns for table view
  const tableColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: Date) => (
        <Tooltip title={dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')}>
          <Text style={{ fontSize: '12px' }}>
            {formatRelativeTime(timestamp)}
          </Text>
        </Tooltip>
      ),
      sorter: (a: AllocationEvent, b: AllocationEvent) => 
        b.timestamp.getTime() - a.timestamp.getTime()
    },
    {
      title: 'Event',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => (
        <Tag color={getEventColor(type)} icon={getEventIcon(type)}>
          {type.toUpperCase()}
        </Tag>
      ),
      filters: eventTypeOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value: any, record: AllocationEvent) => record.type === value
    },
    {
      title: 'Test ID',
      dataIndex: 'testId',
      key: 'testId',
      width: 150,
      render: (testId: string) => (
        <Text code style={{ fontSize: '11px' }}>
          {testId ? testId.slice(0, 20) + (testId.length > 20 ? '...' : '') : 'N/A'}
        </Text>
      )
    },
    {
      title: 'Environment',
      dataIndex: 'environmentId',
      key: 'environmentId',
      width: 150,
      render: (envId: string) => (
        <Text code style={{ fontSize: '11px' }}>
          {envId ? envId.slice(0, 20) + (envId.length > 20 ? '...' : '') : 'N/A'}
        </Text>
      )
    },
    {
      title: 'Details',
      dataIndex: 'metadata',
      key: 'metadata',
      render: (metadata: any, record: AllocationEvent) => (
        <Space size="small">
          {metadata?.duration && (
            <Tag color="blue">{metadata.duration}s</Tag>
          )}
          {metadata?.priority && (
            <Tag color="orange">P{metadata.priority}</Tag>
          )}
          {metadata?.error && (
            <Tag color="red">{metadata.error}</Tag>
          )}
          <Button 
            size="small" 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => handleEventClick(record)}
          >
            View
          </Button>
        </Space>
      )
    }
  ]

  const exportMenu = (
    <Menu onClick={({ key }) => handleExport(key as 'csv' | 'json')}>
      <Menu.Item key="csv" icon={<DownloadOutlined />}>
        Export as CSV
      </Menu.Item>
      <Menu.Item key="json" icon={<DownloadOutlined />}>
        Export as JSON
      </Menu.Item>
    </Menu>
  )

  return (
    <div>
      {/* Analytics Overview */}
      {showAnalytics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Total Events"
                value={analytics.totalEvents}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Success Rate"
                value={analytics.totalEvents > 0 ? 
                  ((analytics.successfulAllocations / analytics.totalEvents) * 100).toFixed(1) : 0}
                suffix="%"
                valueStyle={{ 
                  color: analytics.failureRate < 10 ? '#3f8600' : 
                         analytics.failureRate < 25 ? '#faad14' : '#cf1322' 
                }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Avg Allocation Time"
                value={analytics.averageAllocationTime.toFixed(1)}
                suffix="s"
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Most Active Env"
                value={analytics.mostActiveEnvironment.slice(0, 12)}
                prefix={<LinkOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card 
        title={
          <Space>
            <ClockCircleOutlined />
            Allocation History
            <Badge count={filteredHistory.length} showZero color="blue" />
            {autoRefresh && realTimeUpdates.isConnected && (
              <Tag color="green">Live Updates</Tag>
            )}
            {hasActiveFilters && (
              <Tag color="orange">Filtered</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Switch
              checkedChildren="Timeline"
              unCheckedChildren="Table"
              checked={viewMode === 'timeline'}
              onChange={(checked) => setViewMode(checked ? 'timeline' : 'table')}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
              size="small"
            >
              Refresh
            </Button>
            {enableExport && (
              <Dropdown overlay={exportMenu} trigger={['click']}>
                <Button 
                  icon={<ExportOutlined />} 
                  loading={isExporting}
                  size="small"
                >
                  Export
                </Button>
              </Dropdown>
            )}
          </Space>
        }
      >
        {/* Filters */}
        {enableFiltering && (
          <div style={{ marginBottom: 16, padding: 16, backgroundColor: '#fafafa', borderRadius: 6 }}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Search
                  placeholder="Search events..."
                  value={filter.searchQuery}
                  onChange={(e) => setFilter(prev => ({ ...prev, searchQuery: e.target.value }))}
                  allowClear
                />
              </Col>
              <Col span={6}>
                <Select
                  mode="multiple"
                  placeholder="Event types"
                  value={filter.eventTypes}
                  onChange={(eventTypes) => setFilter(prev => ({ ...prev, eventTypes }))}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {eventTypeOptions.map(opt => (
                    <Select.Option key={opt.value} value={opt.value}>
                      <Tag color={opt.color}>{opt.label}</Tag>
                    </Select.Option>
                  ))}
                </Select>
              </Col>
              <Col span={6}>
                <Select
                  mode="multiple"
                  placeholder="Environments"
                  value={filter.environmentIds}
                  onChange={(environmentIds) => setFilter(prev => ({ ...prev, environmentIds }))}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {uniqueEnvironmentIds.map((envId: string) => (
                    <Select.Option key={envId} value={envId}>
                      {envId.slice(0, 20)}...
                    </Select.Option>
                  ))}
                </Select>
              </Col>
              <Col span={6}>
                <RangePicker
                  value={filter.dateRange}
                  onChange={(dateRange) => setFilter(prev => ({ ...prev, dateRange: dateRange as [Dayjs, Dayjs] | null }))}
                  style={{ width: '100%' }}
                  showTime
                />
              </Col>
            </Row>
            {hasActiveFilters && (
              <div style={{ marginTop: 8 }}>
                <Button size="small" onClick={clearFilters}>
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Content */}
        {filteredHistory.length === 0 ? (
          <Empty 
            description={hasActiveFilters ? "No events match the current filters" : "No allocation history available"}
            style={{ padding: '40px' }}
          />
        ) : viewMode === 'timeline' ? (
          <Timeline
            items={filteredHistory.slice(0, 100).map((event: AllocationEvent) => ({
              dot: getEventIcon(event.type),
              color: getEventColor(event.type),
              children: (
                <div 
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleEventClick(event)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space>
                      <Tag color={getEventColor(event.type)}>
                        {event.type.toUpperCase()}
                      </Tag>
                      {event.testId && (
                        <Text code style={{ fontSize: '12px' }}>
                          {event.testId.slice(0, 16)}...
                        </Text>
                      )}
                      {event.environmentId && (
                        <Text code style={{ fontSize: '12px', color: '#666' }}>
                          → {event.environmentId.slice(0, 16)}...
                        </Text>
                      )}
                    </Space>
                    <Text style={{ fontSize: '12px', color: '#999' }}>
                      {formatRelativeTime(event.timestamp)}
                    </Text>
                  </div>
                  
                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                      <Space size="small">
                        {event.metadata.duration && (
                          <Tag color="blue">Duration: {event.metadata.duration}s</Tag>
                        )}
                        {event.metadata.priority && (
                          <Tag color="orange">Priority: {event.metadata.priority}</Tag>
                        )}
                        {event.metadata.error && (
                          <Tag color="red">Error: {event.metadata.error}</Tag>
                        )}
                        {event.metadata.reason && (
                          <Tag color="blue">Reason: {event.metadata.reason}</Tag>
                        )}
                      </Space>
                    </div>
                  )}
                </div>
              )
            }))}
          />
        ) : (
          <Table
            dataSource={filteredHistory}
            columns={tableColumns}
            rowKey="id"
            size="small"
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} events`
            }}
            onRow={(record) => ({
              onClick: () => handleEventClick(record)
            })}
          />
        )}
      </Card>

      {/* Event Details Drawer */}
      <Drawer
        title="Event Details"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedEvent && (
          <div>
            <Descriptions title="Event Information" bordered column={1}>
              <Descriptions.Item label="Event ID">
                <Text code>{selectedEvent.id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Type">
                <Tag color={getEventColor(selectedEvent.type)} icon={getEventIcon(selectedEvent.type)}>
                  {selectedEvent.type.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedEvent.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  ({formatRelativeTime(selectedEvent.timestamp)})
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Test ID">
                <Text code>{selectedEvent.testId || 'N/A'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Environment ID">
                <Text code>{selectedEvent.environmentId || 'N/A'}</Text>
              </Descriptions.Item>
            </Descriptions>

            {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
              <>
                <Divider />
                <Title level={5}>Metadata</Title>
                <Descriptions bordered column={1}>
                  {Object.entries(selectedEvent.metadata).map(([key, value]) => (
                    <Descriptions.Item key={key} label={key}>
                      {typeof value === 'object' ? (
                        <pre style={{ fontSize: '12px', margin: 0 }}>
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : (
                        <Text>{String(value)}</Text>
                      )}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </>
            )}

            {selectedEvent.type === 'failed' && selectedEvent.metadata?.error && (
              <>
                <Divider />
                <Alert
                  message="Failure Details"
                  description={`Error: ${selectedEvent.metadata.error}`}
                  type="error"
                  showIcon
                  icon={<BugOutlined />}
                />
              </>
            )}
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default AllocationHistoryViewer