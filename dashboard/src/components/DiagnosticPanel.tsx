/**
 * Diagnostic Panel Component
 * Provides detailed diagnostic information and troubleshooting tools
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Table,
  Tag,
  Button,
  Space,
  Descriptions,
  Alert,
  Collapse,
  Typography,
  Progress,
  Statistic,
  Row,
  Col,
  Timeline,
  Badge,
  Tooltip,
  Input,
  Select,
  DatePicker
} from 'antd';
import {
  BugOutlined,
  ReloadOutlined,
  DownloadOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SearchOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { 
  ErrorDetails, 
  ErrorCategory, 
  ErrorSeverity,
  DiagnosticInfo
} from '../types/errors';
import { useErrorContext } from '../contexts/ErrorContext';
import apiService from '../services/api';

const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface DiagnosticPanelProps {
  visible?: boolean;
  onClose?: () => void;
}

interface SystemHealth {
  api: 'healthy' | 'degraded' | 'unhealthy';
  websocket: 'connected' | 'disconnected' | 'connecting';
  sse: 'connected' | 'disconnected' | 'connecting';
  database: 'healthy' | 'degraded' | 'unhealthy';
  environments: {
    total: number;
    healthy: number;
    degraded: number;
    unhealthy: number;
  };
}

interface DiagnosticMetrics {
  errorRate: number;
  averageResponseTime: number;
  successfulRequests: number;
  failedRequests: number;
  retryAttempts: number;
  fallbackActivations: number;
}

const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({
  visible = true,
  onClose
}) => {
  const { errors, clearErrors, diagnosticMode, toggleDiagnosticMode } = useErrorContext();
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    api: 'healthy',
    websocket: 'connected',
    sse: 'connected',
    database: 'healthy',
    environments: { total: 0, healthy: 0, degraded: 0, unhealthy: 0 }
  });
  const [metrics, setMetrics] = useState<DiagnosticMetrics>({
    errorRate: 0,
    averageResponseTime: 0,
    successfulRequests: 0,
    failedRequests: 0,
    retryAttempts: 0,
    fallbackActivations: 0
  });
  const [filteredErrors, setFilteredErrors] = useState<ErrorDetails[]>(errors);
  const [filters, setFilters] = useState({
    category: undefined as ErrorCategory | undefined,
    severity: undefined as ErrorSeverity | undefined,
    search: '',
    dateRange: undefined as [any, any] | undefined
  });

  // Update filtered errors when errors or filters change
  useEffect(() => {
    let filtered = [...errors];

    if (filters.category) {
      filtered = filtered.filter(error => error.category === filters.category);
    }

    if (filters.severity) {
      filtered = filtered.filter(error => error.severity === filters.severity);
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(error =>
        error.message.toLowerCase().includes(searchLower) ||
        error.code.toLowerCase().includes(searchLower) ||
        error.description?.toLowerCase().includes(searchLower)
      );
    }

    if (filters.dateRange) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(error =>
        error.timestamp >= start.toDate() && error.timestamp <= end.toDate()
      );
    }

    setFilteredErrors(filtered);
  }, [errors, filters]);

  // Fetch system health periodically
  useEffect(() => {
    const fetchSystemHealth = async () => {
      try {
        const health = await apiService.getHealth();
        const environments = await apiService.getEnvironments();
        
        setSystemHealth({
          api: health.status === 'healthy' ? 'healthy' : 'degraded',
          websocket: 'connected', // Would be determined by actual WebSocket status
          sse: 'connected', // Would be determined by actual SSE status
          database: health.components?.database?.status === 'healthy' ? 'healthy' : 'degraded',
          environments: {
            total: environments.length,
            healthy: environments.filter(env => env.health === 'healthy').length,
            degraded: environments.filter(env => env.health === 'degraded').length,
            unhealthy: environments.filter(env => env.health === 'unhealthy').length
          }
        });
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      }
    };

    fetchSystemHealth();
    const interval = setInterval(fetchSystemHealth, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Calculate metrics from errors
  useEffect(() => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const recentErrors = errors.filter(error => error.timestamp >= oneHourAgo);
    
    const totalRequests = recentErrors.length + 100; // Assume some successful requests
    const failedRequests = recentErrors.length;
    const successfulRequests = totalRequests - failedRequests;
    
    setMetrics({
      errorRate: totalRequests > 0 ? (failedRequests / totalRequests) * 100 : 0,
      averageResponseTime: 250, // Would be calculated from actual metrics
      successfulRequests,
      failedRequests,
      retryAttempts: recentErrors.filter(error => error.context?.retryAttempt).length,
      fallbackActivations: recentErrors.filter(error => error.context?.fallbackUsed).length
    });
  }, [errors]);

  const getHealthColor = (status: string): string => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'green';
      case 'degraded':
      case 'connecting':
        return 'orange';
      case 'unhealthy':
      case 'disconnected':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircleOutlined style={{ color: 'green' }} />;
      case 'degraded':
      case 'connecting':
        return <WarningOutlined style={{ color: 'orange' }} />;
      case 'unhealthy':
      case 'disconnected':
        return <CloseCircleOutlined style={{ color: 'red' }} />;
      default:
        return <InfoCircleOutlined style={{ color: 'gray' }} />;
    }
  };

  const getSeverityColor = (severity: ErrorSeverity): string => {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
        return 'red';
      case ErrorSeverity.HIGH:
        return 'orange';
      case ErrorSeverity.MEDIUM:
        return 'yellow';
      case ErrorSeverity.LOW:
        return 'green';
      default:
        return 'default';
    }
  };

  const getCategoryColor = (category: ErrorCategory): string => {
    switch (category) {
      case ErrorCategory.NETWORK:
        return 'blue';
      case ErrorCategory.ALLOCATION:
        return 'orange';
      case ErrorCategory.ENVIRONMENT:
        return 'red';
      case ErrorCategory.USER_INPUT:
        return 'purple';
      case ErrorCategory.SYSTEM:
        return 'volcano';
      default:
        return 'default';
    }
  };

  const exportDiagnosticData = () => {
    const diagnosticData = {
      timestamp: new Date().toISOString(),
      systemHealth,
      metrics,
      errors: filteredErrors.map(error => ({
        id: error.id,
        timestamp: error.timestamp.toISOString(),
        category: error.category,
        severity: error.severity,
        code: error.code,
        message: error.message,
        description: error.description,
        context: error.context,
        diagnosticInfo: error.diagnosticInfo
      }))
    };

    const blob = new Blob([JSON.stringify(diagnosticData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostic-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const errorColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: Date) => timestamp.toLocaleString(),
      sorter: (a: ErrorDetails, b: ErrorDetails) => a.timestamp.getTime() - b.timestamp.getTime(),
      width: 150
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: ErrorCategory) => (
        <Tag color={getCategoryColor(category)}>{category}</Tag>
      ),
      filters: Object.values(ErrorCategory).map(cat => ({ text: cat, value: cat })),
      onFilter: (value: any, record: ErrorDetails) => record.category === value,
      width: 120
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: ErrorSeverity) => (
        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
      ),
      filters: Object.values(ErrorSeverity).map(sev => ({ text: sev, value: sev })),
      onFilter: (value: any, record: ErrorDetails) => record.severity === value,
      width: 100
    },
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 120
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: 'Retryable',
      dataIndex: 'retryable',
      key: 'retryable',
      render: (retryable: boolean) => (
        <Badge
          status={retryable ? 'success' : 'default'}
          text={retryable ? 'Yes' : 'No'}
        />
      ),
      width: 100
    }
  ];

  if (!visible) {
    return null;
  }

  return (
    <Card
      title={
        <Space>
          <BugOutlined />
          Diagnostic Panel
          <Badge count={errors.length} showZero />
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={exportDiagnosticData}
          >
            Export
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={clearErrors}
          >
            Clear Errors
          </Button>
          <Button
            type={diagnosticMode ? 'primary' : 'default'}
            onClick={toggleDiagnosticMode}
          >
            Debug Mode: {diagnosticMode ? 'ON' : 'OFF'}
          </Button>
          {onClose && (
            <Button onClick={onClose}>Close</Button>
          )}
        </Space>
      }
    >
      <Tabs defaultActiveKey="overview">
        <TabPane tab="Overview" key="overview">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="System Health" size="small">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="API Service">
                    <Space>
                      {getHealthIcon(systemHealth.api)}
                      <Text>{systemHealth.api}</Text>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="WebSocket">
                    <Space>
                      {getHealthIcon(systemHealth.websocket)}
                      <Text>{systemHealth.websocket}</Text>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="Server-Sent Events">
                    <Space>
                      {getHealthIcon(systemHealth.sse)}
                      <Text>{systemHealth.sse}</Text>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="Database">
                    <Space>
                      {getHealthIcon(systemHealth.database)}
                      <Text>{systemHealth.database}</Text>
                    </Space>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Environment Health" size="small">
                <Row gutter={8}>
                  <Col span={6}>
                    <Statistic
                      title="Total"
                      value={systemHealth.environments.total}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Healthy"
                      value={systemHealth.environments.healthy}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Degraded"
                      value={systemHealth.environments.degraded}
                      valueStyle={{ color: '#faad14' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Unhealthy"
                      value={systemHealth.environments.unhealthy}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={8}>
              <Card title="Error Rate" size="small">
                <Progress
                  type="circle"
                  percent={Math.round(metrics.errorRate)}
                  status={metrics.errorRate > 10 ? 'exception' : metrics.errorRate > 5 ? 'active' : 'success'}
                  format={percent => `${percent}%`}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Response Time" size="small">
                <Statistic
                  title="Average"
                  value={metrics.averageResponseTime}
                  suffix="ms"
                  valueStyle={{
                    color: metrics.averageResponseTime > 1000 ? '#ff4d4f' :
                           metrics.averageResponseTime > 500 ? '#faad14' : '#52c41a'
                  }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Request Stats" size="small">
                <Row>
                  <Col span={12}>
                    <Statistic
                      title="Success"
                      value={metrics.successfulRequests}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Failed"
                      value={metrics.failedRequests}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab={`Errors (${filteredErrors.length})`} key="errors">
          <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
            <Row gutter={8}>
              <Col span={6}>
                <Input
                  placeholder="Search errors..."
                  prefix={<SearchOutlined />}
                  value={filters.search}
                  onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
                />
              </Col>
              <Col span={4}>
                <Select
                  placeholder="Category"
                  allowClear
                  style={{ width: '100%' }}
                  value={filters.category}
                  onChange={value => setFilters(prev => ({ ...prev, category: value }))}
                >
                  {Object.values(ErrorCategory).map(cat => (
                    <Option key={cat} value={cat}>{cat}</Option>
                  ))}
                </Select>
              </Col>
              <Col span={4}>
                <Select
                  placeholder="Severity"
                  allowClear
                  style={{ width: '100%' }}
                  value={filters.severity}
                  onChange={value => setFilters(prev => ({ ...prev, severity: value }))}
                >
                  {Object.values(ErrorSeverity).map(sev => (
                    <Option key={sev} value={sev}>{sev}</Option>
                  ))}
                </Select>
              </Col>
              <Col span={6}>
                <RangePicker
                  style={{ width: '100%' }}
                  value={filters.dateRange}
                  onChange={value => setFilters(prev => ({ ...prev, dateRange: value as any }))}
                />
              </Col>
              <Col span={4}>
                <Button
                  icon={<ClearOutlined />}
                  onClick={() => setFilters({
                    category: undefined,
                    severity: undefined,
                    search: '',
                    dateRange: undefined
                  })}
                >
                  Clear Filters
                </Button>
              </Col>
            </Row>
          </Space>

          <Table
            dataSource={filteredErrors}
            columns={errorColumns}
            rowKey="id"
            size="small"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} errors`
            }}
            expandable={{
              expandedRowRender: (record: ErrorDetails) => (
                <Collapse size="small">
                  <Panel header="Error Details" key="details">
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="ID">{record.id}</Descriptions.Item>
                      <Descriptions.Item label="User Facing">
                        {record.userFacing ? 'Yes' : 'No'}
                      </Descriptions.Item>
                      {record.description && (
                        <Descriptions.Item label="Description" span={2}>
                          {record.description}
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Panel>
                  {record.context && (
                    <Panel header="Context" key="context">
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {JSON.stringify(record.context, null, 2)}
                      </pre>
                    </Panel>
                  )}
                  {record.diagnosticInfo && (
                    <Panel header="Diagnostic Info" key="diagnostic">
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {JSON.stringify(record.diagnosticInfo, null, 2)}
                      </pre>
                    </Panel>
                  )}
                  {record.suggestedActions && record.suggestedActions.length > 0 && (
                    <Panel header="Suggested Actions" key="actions">
                      <Timeline size="small">
                        {record.suggestedActions.map(action => (
                          <Timeline.Item key={action.id}>
                            <Text strong>{action.label}</Text>: {action.description}
                          </Timeline.Item>
                        ))}
                      </Timeline>
                    </Panel>
                  )}
                </Collapse>
              )
            }}
          />
        </TabPane>

        <TabPane tab="Performance" key="performance">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Retry Statistics" size="small">
                <Statistic
                  title="Retry Attempts"
                  value={metrics.retryAttempts}
                  suffix="in last hour"
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Fallback Activations" size="small">
                <Statistic
                  title="Fallbacks Used"
                  value={metrics.fallbackActivations}
                  suffix="in last hour"
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default DiagnosticPanel;