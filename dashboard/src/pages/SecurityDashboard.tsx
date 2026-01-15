import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Alert,
  Tabs,
  Button,
  Modal,
  Form,
  Select,
  Input,
  Switch,
  Space,
  Badge,
  Timeline,
  Tooltip,
  Divider
} from 'antd';
import {
  BugOutlined,
  ExclamationCircleOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  ExportOutlined,
  EyeOutlined,
  AlertOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { SecurityMetrics, SecurityFinding, Vulnerability, SecurityPolicy, FuzzingResult } from '../types/security';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

// Mock data for demonstration
const mockSecurityMetrics: SecurityMetrics = {
  vulnerabilityCount: {
    critical: 2,
    high: 8,
    medium: 15,
    low: 23
  },
  complianceScore: 87,
  activeFuzzingCampaigns: 3,
  recentFindings: [
    {
      id: 'SEC-001',
      severity: 'critical',
      type: 'vulnerability',
      title: 'Buffer Overflow in Network Driver',
      description: 'Potential buffer overflow vulnerability detected in network driver code',
      affectedComponents: ['network-driver', 'kernel-core'],
      discoveredAt: new Date('2024-01-10'),
      status: 'open',
      cveId: 'CVE-2024-0001',
      remediation: 'Apply bounds checking in network packet processing'
    },
    {
      id: 'SEC-002',
      severity: 'high',
      type: 'fuzzing',
      title: 'Race Condition in Memory Management',
      description: 'Race condition discovered during fuzzing of memory allocation routines',
      affectedComponents: ['memory-manager'],
      discoveredAt: new Date('2024-01-09'),
      status: 'investigating'
    }
  ],
  securityTrends: [
    { date: '2024-01-01', vulnerabilities: 45, resolved: 38 },
    { date: '2024-01-08', vulnerabilities: 48, resolved: 42 }
  ]
};

const mockVulnerabilities: Vulnerability[] = [
  {
    id: 'VULN-001',
    cveId: 'CVE-2024-0001',
    title: 'Buffer Overflow in Network Driver',
    description: 'A buffer overflow vulnerability exists in the network driver that could allow remote code execution',
    severity: 'critical',
    cvssScore: 9.8,
    affectedComponents: ['network-driver', 'kernel-core'],
    discoveryMethod: 'scan',
    status: 'open',
    assignee: 'security-team',
    remediation: 'Apply bounds checking and input validation',
    discoveredAt: new Date('2024-01-10')
  },
  {
    id: 'VULN-002',
    title: 'Race Condition in Memory Manager',
    description: 'Race condition in memory allocation could lead to use-after-free vulnerabilities',
    severity: 'high',
    cvssScore: 7.5,
    affectedComponents: ['memory-manager'],
    discoveryMethod: 'fuzzing',
    status: 'investigating',
    assignee: 'kernel-team',
    discoveredAt: new Date('2024-01-09')
  }
];

const mockFuzzingResults: FuzzingResult[] = [
  {
    id: 'FUZZ-001',
    campaign: 'Network Driver Fuzzing',
    status: 'running',
    startTime: new Date('2024-01-08'),
    duration: 72,
    crashCount: 5,
    coverage: 78.5,
    findings: ['Buffer overflow', 'Null pointer dereference'],
    testCases: 150000,
    uniqueCrashes: 3
  },
  {
    id: 'FUZZ-002',
    campaign: 'System Call Fuzzing',
    status: 'completed',
    startTime: new Date('2024-01-05'),
    duration: 168,
    crashCount: 12,
    coverage: 85.2,
    findings: ['Race condition', 'Memory leak', 'Integer overflow'],
    testCases: 500000,
    uniqueCrashes: 8
  }
];

const SecurityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SecurityMetrics>(mockSecurityMetrics);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>(mockVulnerabilities);
  const [fuzzingResults, setFuzzingResults] = useState<FuzzingResult[]>(mockFuzzingResults);
  const [loading, setLoading] = useState(false);
  const [policyModalVisible, setPolicyModalVisible] = useState(false);
  const [selectedVulnerability, setSelectedVulnerability] = useState<Vulnerability | null>(null);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#ff4d4f';
      case 'high': return '#ff7a45';
      case 'medium': return '#ffa940';
      case 'low': return '#52c41a';
      default: return '#d9d9d9';
    }
  };

  const getSeverityTag = (severity: string) => {
    const colors = {
      critical: 'red',
      high: 'orange',
      medium: 'gold',
      low: 'green'
    };
    return <Tag color={colors[severity as keyof typeof colors]}>{severity.toUpperCase()}</Tag>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'investigating': return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      case 'resolved': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'false_positive': return <CheckCircleOutlined style={{ color: '#d9d9d9' }} />;
      default: return <ClockCircleOutlined />;
    }
  };

  const vulnerabilityColumns: ColumnsType<Vulnerability> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => <Button type="link" size="small">{id}</Button>
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => getSeverityTag(severity)
    },
    {
      title: 'CVSS',
      dataIndex: 'cvssScore',
      key: 'cvssScore',
      width: 80,
      render: (score?: number) => score ? score.toFixed(1) : 'N/A'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          {status.replace('_', ' ')}
        </Space>
      )
    },
    {
      title: 'Discovered',
      dataIndex: 'discoveredAt',
      key: 'discoveredAt',
      width: 120,
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => setSelectedVulnerability(record)}
          >
            View
          </Button>
        </Space>
      )
    }
  ];

  const fuzzingColumns: ColumnsType<FuzzingResult> = [
    {
      title: 'Campaign',
      dataIndex: 'campaign',
      key: 'campaign'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge 
          status={status === 'running' ? 'processing' : status === 'completed' ? 'success' : 'default'} 
          text={status}
        />
      )
    },
    {
      title: 'Duration (hrs)',
      dataIndex: 'duration',
      key: 'duration'
    },
    {
      title: 'Test Cases',
      dataIndex: 'testCases',
      key: 'testCases',
      render: (count: number) => count.toLocaleString()
    },
    {
      title: 'Coverage',
      dataIndex: 'coverage',
      key: 'coverage',
      render: (coverage: number) => `${coverage.toFixed(1)}%`
    },
    {
      title: 'Crashes',
      dataIndex: 'crashCount',
      key: 'crashCount',
      render: (count: number, record) => (
        <Tooltip title={`${record.uniqueCrashes} unique crashes`}>
          <Badge count={count} style={{ backgroundColor: count > 0 ? '#ff4d4f' : '#52c41a' }} />
        </Tooltip>
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

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Security Dashboard</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refreshData} loading={loading}>
            Refresh
          </Button>
          <Button icon={<SettingOutlined />} onClick={() => setPolicyModalVisible(true)}>
            Security Policies
          </Button>
          <Button icon={<ExportOutlined />}>
            Export Report
          </Button>
        </Space>
      </div>

      {/* Security Overview Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Compliance Score"
              value={metrics.complianceScore}
              suffix="%"
              valueStyle={{ color: metrics.complianceScore >= 90 ? '#3f8600' : metrics.complianceScore >= 70 ? '#cf1322' : '#ff4d4f' }}
              prefix={<SafetyCertificateOutlined />}
            />
            <Progress 
              percent={metrics.complianceScore} 
              strokeColor={metrics.complianceScore >= 90 ? '#52c41a' : metrics.complianceScore >= 70 ? '#faad14' : '#ff4d4f'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Critical Vulnerabilities"
              value={metrics.vulnerabilityCount.critical}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<ExclamationCircleOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              High: {metrics.vulnerabilityCount.high} | Medium: {metrics.vulnerabilityCount.medium} | Low: {metrics.vulnerabilityCount.low}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Fuzzing"
              value={metrics.activeFuzzingCampaigns}
              valueStyle={{ color: '#1890ff' }}
              prefix={<BugOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Campaigns running
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Security Score"
              value={85}
              suffix="/100"
              valueStyle={{ color: '#52c41a' }}
              prefix={<SafetyCertificateOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Overall security rating
            </div>
          </Card>
        </Col>
      </Row>

      {/* Recent Security Alerts */}
      {metrics.recentFindings.length > 0 && (
        <Alert
          message="Recent Security Findings"
          description={
            <div>
              {metrics.recentFindings.slice(0, 2).map(finding => (
                <div key={finding.id} style={{ marginBottom: '8px' }}>
                  <Space>
                    {getSeverityTag(finding.severity)}
                    <strong>{finding.title}</strong>
                    <span style={{ color: '#666' }}>- {finding.affectedComponents.join(', ')}</span>
                  </Space>
                </div>
              ))}
            </div>
          }
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary" ghost>
              View All
            </Button>
          }
        />
      )}

      {/* Main Content Tabs */}
      <Tabs defaultActiveKey="vulnerabilities">
        <TabPane tab="Vulnerabilities" key="vulnerabilities">
          <Card title="Vulnerability Management" extra={
            <Space>
              <Button type="primary" icon={<AlertOutlined />}>
                New Scan
              </Button>
            </Space>
          }>
            <Table
              columns={vulnerabilityColumns}
              dataSource={vulnerabilities}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Fuzzing Results" key="fuzzing">
          <Card title="Fuzzing Campaigns" extra={
            <Space>
              <Button type="primary">
                Start Campaign
              </Button>
            </Space>
          }>
            <Table
              columns={fuzzingColumns}
              dataSource={fuzzingResults}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Security Policies" key="policies">
          <Card title="Security Policy Configuration">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" title="Vulnerability Thresholds">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>Critical: Block deployment</div>
                    <div>High: Require approval</div>
                    <div>Medium: Generate warning</div>
                    <div>Low: Log only</div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Compliance Frameworks">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>✓ SOC2 Type II</div>
                    <div>✓ ISO 27001</div>
                    <div>✓ NIST Cybersecurity Framework</div>
                    <div>○ Custom Framework</div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="Security Timeline" key="timeline">
          <Card title="Security Events Timeline">
            <Timeline>
              <Timeline.Item color="red">
                <p>Critical vulnerability discovered in network driver</p>
                <p style={{ color: '#666', fontSize: '12px' }}>2 hours ago</p>
              </Timeline.Item>
              <Timeline.Item color="orange">
                <p>High severity finding from fuzzing campaign</p>
                <p style={{ color: '#666', fontSize: '12px' }}>1 day ago</p>
              </Timeline.Item>
              <Timeline.Item color="green">
                <p>Security scan completed successfully</p>
                <p style={{ color: '#666', fontSize: '12px' }}>2 days ago</p>
              </Timeline.Item>
              <Timeline.Item color="blue">
                <p>New security policy activated</p>
                <p style={{ color: '#666', fontSize: '12px' }}>3 days ago</p>
              </Timeline.Item>
            </Timeline>
          </Card>
        </TabPane>
      </Tabs>

      {/* Security Policy Configuration Modal */}
      <Modal
        title="Security Policy Configuration"
        visible={policyModalVisible}
        onCancel={() => setPolicyModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setPolicyModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="save" type="primary">
            Save Policy
          </Button>
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="Policy Name">
            <Input placeholder="Enter policy name" />
          </Form.Item>
          <Form.Item label="Compliance Framework">
            <Select placeholder="Select framework" mode="multiple">
              <Option value="soc2">SOC2 Type II</Option>
              <Option value="iso27001">ISO 27001</Option>
              <Option value="nist">NIST Cybersecurity Framework</Option>
              <Option value="custom">Custom Framework</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Vulnerability Response">
            <Row gutter={16}>
              <Col span={6}>Critical:</Col>
              <Col span={18}>
                <Select defaultValue="block" style={{ width: '100%' }}>
                  <Option value="block">Block Deployment</Option>
                  <Option value="alert">Alert Only</Option>
                </Select>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item label="Enable Automatic Scanning">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item label="Policy Description">
            <TextArea rows={4} placeholder="Describe the security policy..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Vulnerability Detail Modal */}
      <Modal
        title="Vulnerability Details"
        visible={!!selectedVulnerability}
        onCancel={() => setSelectedVulnerability(null)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setSelectedVulnerability(null)}>
            Close
          </Button>,
          <Button key="assign" type="primary">
            Assign to Team
          </Button>
        ]}
      >
        {selectedVulnerability && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <strong>Vulnerability ID:</strong> {selectedVulnerability.id}
              </Col>
              <Col span={12}>
                <strong>CVE ID:</strong> {selectedVulnerability.cveId || 'N/A'}
              </Col>
              <Col span={12}>
                <strong>Severity:</strong> {getSeverityTag(selectedVulnerability.severity)}
              </Col>
              <Col span={12}>
                <strong>CVSS Score:</strong> {selectedVulnerability.cvssScore || 'N/A'}
              </Col>
              <Col span={24}>
                <strong>Description:</strong>
                <p style={{ marginTop: '8px' }}>{selectedVulnerability.description}</p>
              </Col>
              <Col span={24}>
                <strong>Affected Components:</strong>
                <div style={{ marginTop: '8px' }}>
                  {selectedVulnerability.affectedComponents.map(component => (
                    <Tag key={component}>{component}</Tag>
                  ))}
                </div>
              </Col>
              {selectedVulnerability.remediation && (
                <Col span={24}>
                  <strong>Remediation:</strong>
                  <p style={{ marginTop: '8px' }}>{selectedVulnerability.remediation}</p>
                </Col>
              )}
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SecurityDashboard;