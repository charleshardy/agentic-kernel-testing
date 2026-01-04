import React, { useState, useEffect, useMemo } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Select, 
  DatePicker, 
  Space, 
  Tag, 
  Tooltip, 
  Modal,
  Timeline,
  Statistic,
  Row,
  Col,
  Spin,
  Alert,
  Dropdown,
  Menu,
  message
} from 'antd';
import { 
  HistoryOutlined, 
  FilterOutlined, 
  ExportOutlined, 
  ReloadOutlined,
  SearchOutlined,
  DownloadOutlined,
  EyeOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { apiService } from '../services/api';
import type { AllocationEvent, AllocationHistoryResponse } from '../types/environment';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface AllocationHistoryViewerProps {
  environmentId?: string;
  testId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface FilterState {
  eventType?: string;
  environmentId?: string;
  testId?: string;
  timeRange?: [dayjs.Dayjs, dayjs.Dayjs];
  searchText?: string;
}

interface StatisticsData {
  total_events: number;
  event_type_counts: Record<string, number>;
  environment_usage: Record<string, number>;
  hourly_distribution: Record<string, number>;
}

const AllocationHistoryViewer: React.FC<AllocationHistoryViewerProps> = ({
  environmentId,
  testId,
  autoRefresh = false,
  refreshInterval = 30000
}) => {
  const [events, setEvents] = useState<AllocationEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [filters, setFilters] = useState<FilterState>({
    environmentId,
    testId
  });
  const [statistics, setStatistics] = useState<StatisticsData | null>(null);
  const [showStatistics, setShowStatistics] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AllocationEvent | null>(null);
  const [correlations, setCorrelations] = useState<any[]>([]);
  const [showCorrelations, setShowCorrelations] = useState(false);

  // Event type color mapping
  const eventTypeColors: Record<string, string> = {
    allocated: 'green',
    deallocated: 'blue',
    failed: 'red',
    queued: 'orange',
    cancelled: 'gray',
    action_performed: 'purple',
    bulk_action_performed: 'cyan'
  };

  // Load allocation history
  const loadHistory = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize
      };

      if (filters.eventType) params.event_type = filters.eventType;
      if (filters.environmentId) params.environment_id = filters.environmentId;
      if (filters.testId) params.test_id = filters.testId;
      if (filters.timeRange) {
        params.start_time = filters.timeRange[0].toISOString();
        params.end_time = filters.timeRange[1].toISOString();
      }

      const response = await apiService.getEnvironmentAllocationHistory(params);
      const historyData = response as AllocationHistoryResponse;
      
      setEvents(historyData.events);
      setPagination({
        current: historyData.pagination.page,
        pageSize: historyData.pagination.page_size,
        total: historyData.pagination.total_count
      });
    } catch (error) {
      console.error('Failed to load allocation history:', error);
      message.error('Failed to load allocation history');
    } finally {
      setLoading(false);
    }
  };

  // Load statistics
  const loadStatistics = async () => {
    try {
      const params: any = {};
      if (filters.timeRange) {
        params.start_time = filters.timeRange[0].toISOString();
        params.end_time = filters.timeRange[1].toISOString();
      }

      const response = await apiService.client.get('/environments/allocation/statistics', { params });
      setStatistics(response.data.data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
      message.error('Failed to load statistics');
    }
  };

  // Load correlations for a specific environment
  const loadCorrelations = async (envId: string) => {
    try {
      const params: any = {};
      if (filters.timeRange) {
        params.start_time = filters.timeRange[0].toISOString();
        params.end_time = filters.timeRange[1].toISOString();
      }

      const response = await apiService.client.get(`/environments/allocation/correlations/${envId}`, { params });
      setCorrelations(response.data.data.correlations);
      setShowCorrelations(true);
    } catch (error) {
      console.error('Failed to load correlations:', error);
      message.error('Failed to load correlations');
    }
  };

  // Export data
  const exportData = async (format: 'csv' | 'json') => {
    try {
      const params: any = { format };
      if (filters.eventType) params.event_type = filters.eventType;
      if (filters.timeRange) {
        params.start_time = filters.timeRange[0].toISOString();
        params.end_time = filters.timeRange[1].toISOString();
      }

      const response = await apiService.client.get('/environments/allocation/export', { 
        params,
        responseType: 'blob'
      });

      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `allocation_history_${dayjs().format('YYYYMMDD_HHmmss')}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Failed to export data:', error);
      message.error('Failed to export data');
    }
  };

  // Table columns
  const columns: ColumnsType<AllocationEvent> = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix(),
      defaultSortOrder: 'descend'
    },
    {
      title: 'Event Type',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => (
        <Tag color={eventTypeColors[type] || 'default'}>
          {type.toUpperCase()}
        </Tag>
      ),
      filters: Object.keys(eventTypeColors).map(type => ({
        text: type.toUpperCase(),
        value: type
      })),
      onFilter: (value, record) => record.type === value
    },
    {
      title: 'Environment ID',
      dataIndex: 'environment_id',
      key: 'environment_id',
      width: 150,
      render: (envId: string) => envId || '-',
      ellipsis: true
    },
    {
      title: 'Test ID',
      dataIndex: 'test_id',
      key: 'test_id',
      width: 150,
      render: (testId: string) => testId || '-',
      ellipsis: true
    },
    {
      title: 'Metadata',
      dataIndex: 'metadata',
      key: 'metadata',
      render: (metadata: Record<string, any>) => {
        const keys = Object.keys(metadata);
        if (keys.length === 0) return '-';
        
        return (
          <Tooltip title={JSON.stringify(metadata, null, 2)}>
            <Tag>{keys.length} field{keys.length > 1 ? 's' : ''}</Tag>
          </Tooltip>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setSelectedEvent(record)}
          />
          {record.environment_id && (
            <Button
              type="text"
              size="small"
              icon={<BarChartOutlined />}
              onClick={() => loadCorrelations(record.environment_id)}
            />
          )}
        </Space>
      )
    }
  ];

  // Filter events based on search text
  const filteredEvents = useMemo(() => {
    if (!filters.searchText) return events;
    
    const searchLower = filters.searchText.toLowerCase();
    return events.filter(event => 
      event.id.toLowerCase().includes(searchLower) ||
      event.type.toLowerCase().includes(searchLower) ||
      event.environment_id?.toLowerCase().includes(searchLower) ||
      event.test_id?.toLowerCase().includes(searchLower) ||
      JSON.stringify(event.metadata).toLowerCase().includes(searchLower)
    );
  }, [events, filters.searchText]);

  // Auto-refresh effect
  useEffect(() => {
    loadHistory();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadHistory(pagination.current, pagination.pageSize);
      }, refreshInterval);
      
      return () => clearInterval(interval);
    }
  }, [filters, autoRefresh, refreshInterval]);

  // Export menu
  const exportMenu = (
    <Menu>
      <Menu.Item key="csv" onClick={() => exportData('csv')}>
        Export as CSV
      </Menu.Item>
      <Menu.Item key="json" onClick={() => exportData('json')}>
        Export as JSON
      </Menu.Item>
    </Menu>
  );

  return (
    <div className="allocation-history-viewer">
      <Card
        title={
          <Space>
            <HistoryOutlined />
            Allocation History
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<BarChartOutlined />}
              onClick={() => {
                setShowStatistics(true);
                loadStatistics();
              }}
            >
              Statistics
            </Button>
            <Dropdown overlay={exportMenu} trigger={['click']}>
              <Button icon={<ExportOutlined />}>
                Export
              </Button>
            </Dropdown>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => loadHistory(pagination.current, pagination.pageSize)}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        {/* Filters */}
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Input
                placeholder="Search events..."
                prefix={<SearchOutlined />}
                value={filters.searchText}
                onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Event Type"
                value={filters.eventType}
                onChange={(value) => setFilters({ ...filters, eventType: value })}
                allowClear
                style={{ width: '100%' }}
              >
                {Object.keys(eventTypeColors).map(type => (
                  <Option key={type} value={type}>
                    {type.toUpperCase()}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Input
                placeholder="Environment ID"
                value={filters.environmentId}
                onChange={(e) => setFilters({ ...filters, environmentId: e.target.value })}
                allowClear
              />
            </Col>
            <Col span={6}>
              <RangePicker
                value={filters.timeRange}
                onChange={(dates) => setFilters({ ...filters, timeRange: dates as [dayjs.Dayjs, dayjs.Dayjs] })}
                showTime
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={2}>
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={() => loadHistory(1, pagination.pageSize)}
                loading={loading}
              >
                Filter
              </Button>
            </Col>
          </Row>
        </div>

        {/* Events Table */}
        <Table
          columns={columns}
          dataSource={filteredEvents}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} events`,
            onChange: (page, pageSize) => {
              setPagination({ ...pagination, current: page, pageSize: pageSize || 20 });
              loadHistory(page, pageSize);
            }
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Event Details Modal */}
      <Modal
        title="Event Details"
        open={!!selectedEvent}
        onCancel={() => setSelectedEvent(null)}
        footer={null}
        width={600}
      >
        {selectedEvent && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic title="Event ID" value={selectedEvent.id} />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="Event Type" 
                  value={selectedEvent.type.toUpperCase()}
                  valueStyle={{ color: eventTypeColors[selectedEvent.type] }}
                />
              </Col>
              <Col span={12}>
                <Statistic title="Environment ID" value={selectedEvent.environment_id || 'N/A'} />
              </Col>
              <Col span={12}>
                <Statistic title="Test ID" value={selectedEvent.test_id || 'N/A'} />
              </Col>
              <Col span={24}>
                <Statistic 
                  title="Timestamp" 
                  value={dayjs(selectedEvent.timestamp).format('YYYY-MM-DD HH:mm:ss')} 
                />
              </Col>
            </Row>
            
            {Object.keys(selectedEvent.metadata).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>Metadata</h4>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  fontSize: 12,
                  overflow: 'auto',
                  maxHeight: 200
                }}>
                  {JSON.stringify(selectedEvent.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Statistics Modal */}
      <Modal
        title="Allocation Statistics"
        open={showStatistics}
        onCancel={() => setShowStatistics(false)}
        footer={null}
        width={800}
      >
        {statistics && (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Statistic title="Total Events" value={statistics.total_events} />
              </Col>
              <Col span={16}>
                <h4>Event Type Distribution</h4>
                <Space wrap>
                  {Object.entries(statistics.event_type_counts).map(([type, count]) => (
                    <Tag key={type} color={eventTypeColors[type]}>
                      {type.toUpperCase()}: {count}
                    </Tag>
                  ))}
                </Space>
              </Col>
            </Row>
            
            {Object.keys(statistics.environment_usage).length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <h4>Environment Usage</h4>
                <div style={{ maxHeight: 200, overflow: 'auto' }}>
                  {Object.entries(statistics.environment_usage)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 10)
                    .map(([envId, count]) => (
                      <div key={envId} style={{ marginBottom: 8 }}>
                        <Tag>{envId}</Tag>
                        <span style={{ marginLeft: 8 }}>{count} events</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Correlations Modal */}
      <Modal
        title="Event Correlations"
        open={showCorrelations}
        onCancel={() => setShowCorrelations(false)}
        footer={null}
        width={900}
      >
        <Timeline>
          {correlations.map((correlation, index) => (
            <Timeline.Item
              key={index}
              color={eventTypeColors[correlation.event.type]}
            >
              <div>
                <strong>{correlation.event.type.toUpperCase()}</strong>
                <span style={{ marginLeft: 8, color: '#666' }}>
                  {dayjs(correlation.event.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                </span>
                
                {correlation.related_tests.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <h5>Related Test Results:</h5>
                    {correlation.related_tests.map((test: any, testIndex: number) => (
                      <Tag 
                        key={testIndex}
                        color={test.status === 'passed' ? 'green' : 'red'}
                        style={{ marginBottom: 4 }}
                      >
                        {test.test_id}: {test.status}
                      </Tag>
                    ))}
                  </div>
                )}
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </Modal>
    </div>
  );
};

export default AllocationHistoryViewer;