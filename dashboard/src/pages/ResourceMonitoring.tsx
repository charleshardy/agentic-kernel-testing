import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Button,
  Table,
  Tag,
  Space,
  Tabs,
  Alert,
  Typography,
  Select,
  DatePicker,
  Tooltip,
  Divider,
  List,
  Avatar,
  Badge,
  Descriptions,
  Timeline,
  Slider,
  Switch,
  InputNumber,
  Form,
  Modal
} from 'antd';
import {
  MonitorOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  CloudOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  ThunderboltOutlined,
  HddOutlined,
  WifiOutlined,
  AlertOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ResourceMetrics, InfrastructureMetrics, CapacityMetrics, ResourceAlert, ResourceThreshold } from '../types/resources';

const { TabPane } = Tabs;
const { Option } = Select;
const { Text, Title } = Typography;
const { RangePicker } = DatePicker;

// Mock data for demonstration
const mockResourceMetrics: ResourceMetrics[] = [
  {
    id: 'resource-001',
    name: 'Test Environment 1',
    type: 'virtual_machine',
    status: 'healthy',
    location: 'us-east-1a',
    provider: 'aws',
    metrics: {
      cpu: {
        usage: 65.5,
        cores: 8,
        frequency: 2.4,
        temperature: 45.2,
        loadAverage: [1.2, 1.5, 1.8]
      },
      memory: {
        usage: 78.3,
        total: 16384,
        used: 12825,
        available: 3559,
        cached: 2048,
        buffers: 512
      },
      disk: {
        usage: 45.2,
        total: 500,
        used: 226,
        available: 274,
        readIops: 150,
        writeIops: 75,
        readThroughput: 25.5,
        writeThroughput: 12.3
      },
      network: {
        usage: 23.7,
        bandwidth: 1000,
        inbound: 125.5,
        outbound: 87.3,
        packets: 1250,
        errors: 0,
        drops: 0
      }
    },
    thresholds: {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 },
      disk: { warning: 75, critical: 85 },
      network: { warning: 80, critical: 90 }
    },
    alerts: [],
    lastUpdated: '2024-01-13T10:30:00Z',
    tags: ['testing', 'kernel', 'production']
  },
  {
    id: 'resource-002',
    name: 'Build Server 1',
    type: 'physical_server',
    status: 'warning',
    location: 'datacenter-1',
    provider: 'on_premise',
    metrics: {
      cpu: {
        usage: 88.2,
        cores: 16,
        frequency: 3.2,
        temperature: 72.1,
        loadAverage: [3.2, 3.8, 4.1]
      },
      memory: {
        usage: 92.1,
        total: 32768,
        used: 30165,
        available: 2603,
        cached: 4096,
        buffers: 1024
      },
      disk: {
        usage: 67.8,
        total: 2000,
        used: 1356,
        available: 644,
        readIops: 450,
        writeIops: 280,
        readThroughput: 85.2,
        writeThroughput: 45.7
      },
      network: {
        usage: 45.3,
        bandwidth: 10000,
        inbound: 2250.5,
        outbound: 2275.8,
        packets: 15750,
        errors: 2,
        drops: 0
      }
    },
    thresholds: {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 },
      disk: { warning: 75, critical: 85 },
      network: { warning: 80, critical: 90 }
    },
    alerts: [
      {
        id: 'alert-001',
        resourceId: 'resource-002',
        type: 'threshold_exceeded',
        severity: 'warning',
        metric: 'cpu',
        value: 88.2,
        threshold: 85,
        message: 'CPU usage exceeded warning threshold',
        timestamp: '2024-01-13T10:25:00Z',
        status: 'active',
        acknowledged: false
      }
    ],
    lastUpdated: '2024-01-13T10:30:00Z',
    tags: ['build', 'ci-cd', 'high-performance']
  },
  {
    id: 'resource-003',
    name: 'Database Server',
    type: 'database_server',
    status: 'critical',
    location: 'us-west-2b',
    provider: 'aws',
    metrics: {
      cpu: {
        usage: 45.8,
        cores: 4,
        frequency: 2.8,
        temperature: 38.5,
        loadAverage: [0.8, 1.1, 1.3]
      },
      memory: {
        usage: 95.7,
        total: 8192,
        used: 7840,
        available: 352,
        cached: 1024,
        buffers: 256
      },
      disk: {
        usage: 89.3,
        total: 1000,
        used: 893,
        available: 107,
        readIops: 850,
        writeIops: 420,
        readThroughput: 125.8,
        writeThroughput: 67.4
      },
      network: {
        usage: 67.2,
        bandwidth: 1000,
        inbound: 335.5,
        outbound: 336.7,
        packets: 8750,
        errors: 0,
        drops: 1
      }
    },
    thresholds: {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 },
      disk: { warning: 75, critical: 85 },
      network: { warning: 80, critical: 90 }
    },
    alerts: [
      {
        id: 'alert-002',
        resourceId: 'resource-003',
        type: 'threshold_exceeded',
        severity: 'critical',
        metric: 'memory',
        value: 95.7,
        threshold: 90,
        message: 'Memory usage exceeded critical threshold',
        timestamp: '2024-01-13T10:20:00Z',
        status: 'active',
        acknowledged: false
      },
      {
        id: 'alert-003',
        resourceId: 'resource-003',
        type: 'threshold_exceeded',
        severity: 'critical',
        metric: 'disk',
        value: 89.3,
        threshold: 85,
        message: 'Disk usage exceeded critical threshold',
        timestamp: '2024-01-13T10:18:00Z',
        status: 'active',
        acknowledged: false
      }
    ],
    lastUpdated: '2024-01-13T10:30:00Z',
    tags: ['database', 'postgresql', 'critical']
  }
];

const mockInfrastructureMetrics: InfrastructureMetrics = {
  totalResources: 15,
  healthyResources: 10,
  warningResources: 3,
  criticalResources: 2,
  totalCapacity: {
    cpu: { total: 240, used: 156, available: 84 },
    memory: { total: 245760, used: 178432, available: 67328 },
    disk: { total: 15000, used: 8750, available: 6250 },
    network: { total: 50000, used: 12500, available: 37500 }
  },
  utilizationTrends: {
    cpu: [45, 52, 48, 65, 58, 62, 67],
    memory: [68, 72, 75, 78, 82, 79, 76],
    disk: [35, 38, 42, 45, 48, 52, 55],
    network: [25, 28, 32, 35, 38, 42, 45]
  },
  costMetrics: {
    totalCost: 15750.50,
    costPerResource: 1050.03,
    costTrend: [14200, 14850, 15200, 15750],
    costByProvider: {
      aws: 8500.25,
      azure: 3250.75,
      on_premise: 4000.00
    }
  },
  performanceBaselines: {
    cpu: { baseline: 45, current: 65, variance: 20 },
    memory: { baseline: 60, current: 73, variance: 13 },
    disk: { baseline: 40, current: 58, variance: 18 },
    network: { baseline: 30, current: 35, variance: 5 }
  }
};

const mockCapacityMetrics: CapacityMetrics = {
  currentUtilization: {
    cpu: 65.0,
    memory: 72.6,
    disk: 58.3,
    network: 25.0
  },
  projectedUtilization: {
    cpu: { '30d': 72, '60d': 78, '90d': 85 },
    memory: { '30d': 78, '60d': 82, '90d': 88 },
    disk: { '30d': 65, '60d': 72, '90d': 78 },
    network: { '30d': 32, '60d': 38, '90d': 45 }
  },
  capacityRecommendations: [
    {
      type: 'scale_up',
      resource: 'memory',
      reason: 'Projected to exceed 85% in 90 days',
      recommendation: 'Add 64GB memory to cluster',
      priority: 'high',
      estimatedCost: 2500.00,
      timeline: '30 days'
    },
    {
      type: 'scale_out',
      resource: 'cpu',
      reason: 'CPU utilization trending upward',
      recommendation: 'Add 2 additional compute nodes',
      priority: 'medium',
      estimatedCost: 5000.00,
      timeline: '60 days'
    }
  ],
  growthRate: {
    cpu: 2.5,
    memory: 3.2,
    disk: 1.8,
    network: 1.2
  }
};

const ResourceMonitoring: React.FC = () => {
  const [resources, setResources] = useState<ResourceMetrics[]>(mockResourceMetrics);
  const [infrastructure, setInfrastructure] = useState<InfrastructureMetrics>(mockInfrastructureMetrics);
  const [capacity, setCapacity] = useState<CapacityMetrics>(mockCapacityMetrics);
  const [loading, setLoading] = useState(false);
  const [alertModalVisible, setAlertModalVisible] = useState(false);
  const [thresholdModalVisible, setThresholdModalVisible] = useState(false);
  const [selectedResource, setSelectedResource] = useState<ResourceMetrics | null>(null);
  const [form] = Form.useForm();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'warning': return 'orange';
      case 'critical': return 'red';
      case 'offline': return 'gray';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'critical': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'offline': return <ExclamationCircleOutlined style={{ color: '#8c8c8c' }} />;
      default: return <MonitorOutlined />;
    }
  };

  const getUsageColor = (usage: number, thresholds: { warning: number; critical: number }) => {
    if (usage >= thresholds.critical) return '#ff4d4f';
    if (usage >= thresholds.warning) return '#faad14';
    return '#52c41a';
  };

  const resourceColumns: ColumnsType<ResourceMetrics> = [
    {
      title: 'Resource',
      key: 'resource',
      width: 200,
      render: (_, record) => (
        <Space>
          {getStatusIcon(record.status)}
          <div>
            <div style={{ fontWeight: 500 }}>{record.name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.type.replace('_', ' ')} • {record.location}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: 'CPU',
      key: 'cpu',
      width: 120,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.metrics.cpu.usage}
            size="small"
            strokeColor={getUsageColor(record.metrics.cpu.usage, record.thresholds.cpu)}
            showInfo={false}
          />
          <Text style={{ fontSize: '12px' }}>{record.metrics.cpu.usage.toFixed(1)}%</Text>
        </div>
      )
    },
    {
      title: 'Memory',
      key: 'memory',
      width: 120,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.metrics.memory.usage}
            size="small"
            strokeColor={getUsageColor(record.metrics.memory.usage, record.thresholds.memory)}
            showInfo={false}
          />
          <Text style={{ fontSize: '12px' }}>{record.metrics.memory.usage.toFixed(1)}%</Text>
        </div>
      )
    },
    {
      title: 'Disk',
      key: 'disk',
      width: 120,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.metrics.disk.usage}
            size="small"
            strokeColor={getUsageColor(record.metrics.disk.usage, record.thresholds.disk)}
            showInfo={false}
          />
          <Text style={{ fontSize: '12px' }}>{record.metrics.disk.usage.toFixed(1)}%</Text>
        </div>
      )
    },
    {
      title: 'Network',
      key: 'network',
      width: 120,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.metrics.network.usage}
            size="small"
            strokeColor={getUsageColor(record.metrics.network.usage, record.thresholds.network)}
            showInfo={false}
          />
          <Text style={{ fontSize: '12px' }}>{record.metrics.network.usage.toFixed(1)}%</Text>
        </div>
      )
    },
    {
      title: 'Alerts',
      key: 'alerts',
      width: 80,
      render: (_, record) => (
        <Badge count={record.alerts.length} size="small">
          <AlertOutlined style={{ fontSize: '16px' }} />
        </Badge>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => setSelectedResource(record)}>
            Details
          </Button>
          <Button type="link" size="small" onClick={() => {
            setSelectedResource(record);
            setThresholdModalVisible(true);
          }}>
            Thresholds
          </Button>
        </Space>
      )
    }
  ];

  const refreshData = async () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const acknowledgeAlert = (alertId: string) => {
    setResources(prev => prev.map(resource => ({
      ...resource,
      alerts: resource.alerts.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    })));
  };

  const updateThresholds = (values: any) => {
    if (selectedResource) {
      setResources(prev => prev.map(resource => 
        resource.id === selectedResource.id 
          ? { ...resource, thresholds: values }
          : resource
      ));
    }
    setThresholdModalVisible(false);
    form.resetFields();
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Resource Monitoring</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refreshData} loading={loading}>
            Refresh
          </Button>
          <Button icon={<SettingOutlined />}>
            Settings
          </Button>
          <Button type="primary" icon={<AlertOutlined />} onClick={() => setAlertModalVisible(true)}>
            Alert Policies
          </Button>
        </Space>
      </div>

      {/* Infrastructure Overview Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Resources"
              value={infrastructure.totalResources}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {infrastructure.healthyResources} healthy, {infrastructure.warningResources} warning, {infrastructure.criticalResources} critical
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="CPU Utilization"
              value={capacity.currentUtilization.cpu}
              suffix="%"
              valueStyle={{ color: capacity.currentUtilization.cpu > 70 ? '#ff4d4f' : '#3f8600' }}
              prefix={<ThunderboltOutlined />}
            />
            <Progress 
              percent={capacity.currentUtilization.cpu} 
              strokeColor={capacity.currentUtilization.cpu > 70 ? '#ff4d4f' : '#52c41a'} 
              showInfo={false} 
              size="small" 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Memory Utilization"
              value={capacity.currentUtilization.memory}
              suffix="%"
              valueStyle={{ color: capacity.currentUtilization.memory > 80 ? '#ff4d4f' : '#3f8600' }}
              prefix={<DatabaseOutlined />}
            />
            <Progress 
              percent={capacity.currentUtilization.memory} 
              strokeColor={capacity.currentUtilization.memory > 80 ? '#ff4d4f' : '#52c41a'} 
              showInfo={false} 
              size="small" 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Cost"
              value={infrastructure.costMetrics.totalCost}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              ${infrastructure.costMetrics.costPerResource.toFixed(2)} per resource
            </div>
          </Card>
        </Col>
      </Row>

      {/* Critical Alerts */}
      {resources.some(r => r.alerts.some(a => a.severity === 'critical' && !a.acknowledged)) && (
        <Alert
          message="Critical Resource Alerts"
          description={`${resources.reduce((count, r) => count + r.alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length, 0)} critical alerts require immediate attention.`}
          type="error"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary" ghost onClick={() => setAlertModalVisible(true)}>
              View Alerts
            </Button>
          }
        />
      )}

      {/* Main Content Tabs */}
      <Tabs defaultActiveKey="resources">
        <TabPane tab="Resource Overview" key="resources">
          <Card title="Resource Status" extra={
            <Space>
              <Select defaultValue="all" style={{ width: 120 }}>
                <Option value="all">All Resources</Option>
                <Option value="healthy">Healthy</Option>
                <Option value="warning">Warning</Option>
                <Option value="critical">Critical</Option>
              </Select>
              <Select defaultValue="all" style={{ width: 150 }}>
                <Option value="all">All Types</Option>
                <Option value="virtual_machine">Virtual Machines</Option>
                <Option value="physical_server">Physical Servers</Option>
                <Option value="database_server">Database Servers</Option>
              </Select>
            </Space>
          }>
            <Table
              columns={resourceColumns}
              dataSource={resources}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              scroll={{ x: 1000 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Capacity Planning" key="capacity">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Current vs Projected Utilization">
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>CPU Utilization</Text>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>Current:</div>
                    <Progress percent={capacity.currentUtilization.cpu} style={{ flex: 1 }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '4px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>90d proj:</div>
                    <Progress percent={capacity.projectedUtilization.cpu['90d']} style={{ flex: 1 }} strokeColor="#faad14" />
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Memory Utilization</Text>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>Current:</div>
                    <Progress percent={capacity.currentUtilization.memory} style={{ flex: 1 }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '4px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>90d proj:</div>
                    <Progress percent={capacity.projectedUtilization.memory['90d']} style={{ flex: 1 }} strokeColor="#faad14" />
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Disk Utilization</Text>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>Current:</div>
                    <Progress percent={capacity.currentUtilization.disk} style={{ flex: 1 }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '4px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>90d proj:</div>
                    <Progress percent={capacity.projectedUtilization.disk['90d']} style={{ flex: 1 }} strokeColor="#faad14" />
                  </div>
                </div>

                <div>
                  <Text strong>Network Utilization</Text>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>Current:</div>
                    <Progress percent={capacity.currentUtilization.network} style={{ flex: 1 }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', marginTop: '4px' }}>
                    <div style={{ width: '60px', fontSize: '12px' }}>90d proj:</div>
                    <Progress percent={capacity.projectedUtilization.network['90d']} style={{ flex: 1 }} strokeColor="#faad14" />
                  </div>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Capacity Recommendations">
                <List
                  itemLayout="horizontal"
                  dataSource={capacity.capacityRecommendations}
                  renderItem={recommendation => (
                    <List.Item
                      actions={[
                        <Button type="link" size="small">View Details</Button>,
                        <Button type="primary" size="small">Implement</Button>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={
                          <Avatar 
                            icon={recommendation.type === 'scale_up' ? <ArrowUpOutlined /> : <CloudServerOutlined />}
                            style={{ 
                              backgroundColor: recommendation.priority === 'high' ? '#ff4d4f' : 
                                              recommendation.priority === 'medium' ? '#faad14' : '#52c41a'
                            }}
                          />
                        }
                        title={
                          <Space>
                            <span>{recommendation.recommendation}</span>
                            <Tag color={recommendation.priority === 'high' ? 'red' : 
                                      recommendation.priority === 'medium' ? 'orange' : 'green'}>
                              {recommendation.priority}
                            </Tag>
                          </Space>
                        }
                        description={
                          <div>
                            <div>{recommendation.reason}</div>
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                              Cost: ${recommendation.estimatedCost.toFixed(2)} • Timeline: {recommendation.timeline}
                            </div>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Performance Baselines" key="baselines">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Performance Baseline Tracking">
                <div style={{ marginBottom: '24px' }}>
                  <Text strong>CPU Performance</Text>
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <Text type="secondary">Baseline: {infrastructure.performanceBaselines.cpu.baseline}%</Text>
                      <Text type="secondary">Current: {infrastructure.performanceBaselines.cpu.current}%</Text>
                    </div>
                    <Progress 
                      percent={infrastructure.performanceBaselines.cpu.current} 
                      strokeColor={infrastructure.performanceBaselines.cpu.variance > 15 ? '#ff4d4f' : '#52c41a'}
                    />
                    <Text style={{ fontSize: '12px', color: infrastructure.performanceBaselines.cpu.variance > 15 ? '#ff4d4f' : '#52c41a' }}>
                      Variance: {infrastructure.performanceBaselines.cpu.variance > 0 ? '+' : ''}{infrastructure.performanceBaselines.cpu.variance}%
                    </Text>
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <Text strong>Memory Performance</Text>
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <Text type="secondary">Baseline: {infrastructure.performanceBaselines.memory.baseline}%</Text>
                      <Text type="secondary">Current: {infrastructure.performanceBaselines.memory.current}%</Text>
                    </div>
                    <Progress 
                      percent={infrastructure.performanceBaselines.memory.current} 
                      strokeColor={infrastructure.performanceBaselines.memory.variance > 15 ? '#ff4d4f' : '#52c41a'}
                    />
                    <Text style={{ fontSize: '12px', color: infrastructure.performanceBaselines.memory.variance > 15 ? '#ff4d4f' : '#52c41a' }}>
                      Variance: {infrastructure.performanceBaselines.memory.variance > 0 ? '+' : ''}{infrastructure.performanceBaselines.memory.variance}%
                    </Text>
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <Text strong>Disk Performance</Text>
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <Text type="secondary">Baseline: {infrastructure.performanceBaselines.disk.baseline}%</Text>
                      <Text type="secondary">Current: {infrastructure.performanceBaselines.disk.current}%</Text>
                    </div>
                    <Progress 
                      percent={infrastructure.performanceBaselines.disk.current} 
                      strokeColor={infrastructure.performanceBaselines.disk.variance > 15 ? '#ff4d4f' : '#52c41a'}
                    />
                    <Text style={{ fontSize: '12px', color: infrastructure.performanceBaselines.disk.variance > 15 ? '#ff4d4f' : '#52c41a' }}>
                      Variance: {infrastructure.performanceBaselines.disk.variance > 0 ? '+' : ''}{infrastructure.performanceBaselines.disk.variance}%
                    </Text>
                  </div>
                </div>

                <div>
                  <Text strong>Network Performance</Text>
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <Text type="secondary">Baseline: {infrastructure.performanceBaselines.network.baseline}%</Text>
                      <Text type="secondary">Current: {infrastructure.performanceBaselines.network.current}%</Text>
                    </div>
                    <Progress 
                      percent={infrastructure.performanceBaselines.network.current} 
                      strokeColor={infrastructure.performanceBaselines.network.variance > 15 ? '#ff4d4f' : '#52c41a'}
                    />
                    <Text style={{ fontSize: '12px', color: infrastructure.performanceBaselines.network.variance > 15 ? '#ff4d4f' : '#52c41a' }}>
                      Variance: {infrastructure.performanceBaselines.network.variance > 0 ? '+' : ''}{infrastructure.performanceBaselines.network.variance}%
                    </Text>
                  </div>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Growth Rate Analysis">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>CPU Growth Rate</Text>
                    <Tag color={capacity.growthRate.cpu > 3 ? 'red' : capacity.growthRate.cpu > 2 ? 'orange' : 'green'}>
                      {capacity.growthRate.cpu}% per month
                    </Tag>
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>Memory Growth Rate</Text>
                    <Tag color={capacity.growthRate.memory > 3 ? 'red' : capacity.growthRate.memory > 2 ? 'orange' : 'green'}>
                      {capacity.growthRate.memory}% per month
                    </Tag>
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>Disk Growth Rate</Text>
                    <Tag color={capacity.growthRate.disk > 3 ? 'red' : capacity.growthRate.disk > 2 ? 'orange' : 'green'}>
                      {capacity.growthRate.disk}% per month
                    </Tag>
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>Network Growth Rate</Text>
                    <Tag color={capacity.growthRate.network > 3 ? 'red' : capacity.growthRate.network > 2 ? 'orange' : 'green'}>
                      {capacity.growthRate.network}% per month
                    </Tag>
                  </div>
                </div>

                <Divider />

                <Alert
                  message="Growth Rate Analysis"
                  description="Memory usage is growing at 3.2% per month, which may require capacity expansion within 90 days."
                  type="warning"
                  showIcon
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Cost Analysis" key="costs">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Cost Breakdown by Provider">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <Text strong>AWS</Text>
                    <Text>${infrastructure.costMetrics.costByProvider.aws.toFixed(2)}</Text>
                  </div>
                  <Progress 
                    percent={(infrastructure.costMetrics.costByProvider.aws / infrastructure.costMetrics.totalCost) * 100} 
                    strokeColor="#ff9500"
                    showInfo={false}
                  />
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <Text strong>Azure</Text>
                    <Text>${infrastructure.costMetrics.costByProvider.azure.toFixed(2)}</Text>
                  </div>
                  <Progress 
                    percent={(infrastructure.costMetrics.costByProvider.azure / infrastructure.costMetrics.totalCost) * 100} 
                    strokeColor="#0078d4"
                    showInfo={false}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <Text strong>On-Premise</Text>
                    <Text>${infrastructure.costMetrics.costByProvider.on_premise.toFixed(2)}</Text>
                  </div>
                  <Progress 
                    percent={(infrastructure.costMetrics.costByProvider.on_premise / infrastructure.costMetrics.totalCost) * 100} 
                    strokeColor="#52c41a"
                    showInfo={false}
                  />
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Cost Optimization Opportunities">
                <List
                  size="small"
                  dataSource={[
                    {
                      title: 'Right-size underutilized instances',
                      description: 'Potential savings: $2,500/month',
                      type: 'optimization'
                    },
                    {
                      title: 'Use reserved instances for stable workloads',
                      description: 'Potential savings: $1,800/month',
                      type: 'reservation'
                    },
                    {
                      title: 'Implement auto-scaling policies',
                      description: 'Potential savings: $1,200/month',
                      type: 'automation'
                    },
                    {
                      title: 'Archive unused storage volumes',
                      description: 'Potential savings: $800/month',
                      type: 'cleanup'
                    }
                  ]}
                  renderItem={item => (
                    <List.Item
                      actions={[<Button type="link" size="small">Implement</Button>]}
                    >
                      <List.Item.Meta
                        avatar={
                          <Avatar 
                            icon={<ThunderboltOutlined />}
                            style={{ backgroundColor: '#1890ff' }}
                          />
                        }
                        title={item.title}
                        description={item.description}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Alert Management Modal */}
      <Modal
        title="Active Alerts"
        visible={alertModalVisible}
        onCancel={() => setAlertModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setAlertModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        <List
          dataSource={resources.flatMap(r => r.alerts.map(a => ({ ...a, resourceName: r.name })))}
          renderItem={alert => (
            <List.Item
              actions={[
                !alert.acknowledged && (
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    Acknowledge
                  </Button>
                ),
                <Button type="link" size="small">
                  View Details
                </Button>
              ].filter(Boolean)}
            >
              <List.Item.Meta
                avatar={
                  <Avatar 
                    icon={<AlertOutlined />}
                    style={{ 
                      backgroundColor: alert.severity === 'critical' ? '#ff4d4f' : 
                                      alert.severity === 'warning' ? '#faad14' : '#52c41a'
                    }}
                  />
                }
                title={
                  <Space>
                    <span>{alert.message}</span>
                    <Tag color={alert.severity === 'critical' ? 'red' : 
                              alert.severity === 'warning' ? 'orange' : 'green'}>
                      {alert.severity}
                    </Tag>
                    {alert.acknowledged && <Tag color="blue">Acknowledged</Tag>}
                  </Space>
                }
                description={
                  <div>
                    <div>Resource: {alert.resourceName} • Metric: {alert.metric}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Value: {alert.value}% • Threshold: {alert.threshold}% • {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Modal>

      {/* Threshold Configuration Modal */}
      <Modal
        title="Configure Resource Thresholds"
        visible={thresholdModalVisible}
        onCancel={() => {
          setThresholdModalVisible(false);
          form.resetFields();
        }}
        width={600}
        footer={[
          <Button key="cancel" onClick={() => setThresholdModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="save" type="primary" onClick={() => form.submit()}>
            Save Thresholds
          </Button>
        ]}
      >
        {selectedResource && (
          <Form
            form={form}
            layout="vertical"
            onFinish={updateThresholds}
            initialValues={selectedResource.thresholds}
          >
            <Text strong>Resource: {selectedResource.name}</Text>
            <Divider />
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="CPU Warning Threshold (%)" name={['cpu', 'warning']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="CPU Critical Threshold (%)" name={['cpu', 'critical']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Memory Warning Threshold (%)" name={['memory', 'warning']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Memory Critical Threshold (%)" name={['memory', 'critical']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Disk Warning Threshold (%)" name={['disk', 'warning']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Disk Critical Threshold (%)" name={['disk', 'critical']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Network Warning Threshold (%)" name={['network', 'warning']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Network Critical Threshold (%)" name={['network', 'critical']}>
                  <InputNumber min={0} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default ResourceMonitoring;