import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Badge,
  Tabs,
  Alert,
  Tooltip,
  Divider,
  Typography,
  DatePicker,
  Timeline,
  List,
  Avatar,
  Descriptions,
  Steps
} from 'antd';
import {
  AuditOutlined,
  SafetyCertificateOutlined,
  FileTextOutlined,
  SearchOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  DownloadOutlined,
  FilterOutlined,
  ReloadOutlined,
  SettingOutlined,
  UserOutlined,
  CalendarOutlined,
  FlagOutlined,
  ShieldCheckOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { AuditEvent, ComplianceFramework, ComplianceReport, AuditTrail } from '../types/audit';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;
const { Text, Title } = Typography;
const { RangePicker } = DatePicker;
const { Step } = Steps;

// Mock data for demonstration
const mockAuditEvents: AuditEvent[] = [
  {
    id: 'audit-001',
    timestamp: '2024-01-13T10:30:00Z',
    userId: 'user-123',
    username: 'John Doe',
    userEmail: 'john.doe@example.com',
    action: 'execute',
    resource: 'test-plan-456',
    resourceType: 'test',
    details: {
      description: 'Executed kernel security test plan',
      context: {
        testPlanName: 'Kernel Security Tests',
        executionId: 'exec-789',
        environment: 'production'
      },
      changes: []
    },
    outcome: 'success',
    severity: 'medium',
    category: 'operational',
    source: 'user',
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    metadata: {},
    tags: ['security', 'kernel']
  },
  {
    id: 'audit-002',
    timestamp: '2024-01-13T09:15:00Z',
    userId: 'user-456',
    username: 'Jane Smith',
    userEmail: 'jane.smith@example.com',
    action: 'execute',
    resource: 'security-scan-123',
    resourceType: 'system',
    details: {
      description: 'Executed vulnerability scan',
      context: {
        scanType: 'full_system',
        findings: 5,
        severity: 'high'
      },
      changes: []
    },
    outcome: 'success',
    severity: 'high',
    category: 'security',
    source: 'user',
    ipAddress: '192.168.1.101',
    userAgent: 'Mozilla/5.0 (macOS; Intel Mac OS X 10_15_7)',
    metadata: {},
    tags: ['vulnerability', 'scan']
  },
  {
    id: 'audit-003',
    timestamp: '2024-01-13T08:45:00Z',
    userId: 'user-789',
    username: 'Bob Wilson',
    userEmail: 'bob.wilson@example.com',
    action: 'access',
    resource: 'security-policy-001',
    resourceType: 'policy',
    details: {
      description: 'Attempted unauthorized access to sensitive data',
      context: {
        violationType: 'unauthorized_access',
        policyName: 'Data Access Policy',
        attemptedResource: 'sensitive-data-store'
      },
      changes: []
    },
    outcome: 'denied',
    severity: 'critical',
    category: 'security',
    source: 'system',
    ipAddress: '192.168.1.102',
    userAgent: 'Mozilla/5.0 (Linux; Ubuntu)',
    metadata: {},
    tags: ['policy', 'violation']
  }
];

const mockComplianceFrameworks: ComplianceFramework[] = [
  {
    id: 'soc2',
    name: 'SOC 2 Type II',
    displayName: 'SOC 2 Type II',
    version: '2017',
    description: 'Service Organization Control 2 Type II compliance framework',
    type: 'certification',
    status: 'active',
    controls: [],
    requirements: [
      {
        id: 'soc2-cc1.1',
        frameworkId: 'soc2',
        requirementId: 'CC1.1',
        title: 'Control Environment',
        description: 'The entity demonstrates a commitment to integrity and ethical values',
        category: 'technical',
        mandatory: true,
        controls: ['ctrl-001'],
        status: 'compliant',
        compliance: 'full',
        evidence: [],
        lastVerified: '2024-01-01T00:00:00Z',
        nextVerification: '2024-07-01T00:00:00Z',
        owner: 'compliance-team',
        metadata: {}
      },
      {
        id: 'soc2-cc2.1',
        frameworkId: 'soc2',
        requirementId: 'CC2.1',
        title: 'Communication and Information',
        description: 'The entity obtains or generates and uses relevant, quality information',
        category: 'technical',
        mandatory: true,
        controls: ['ctrl-002'],
        status: 'partial',
        compliance: 'partial',
        evidence: [],
        lastVerified: '2024-01-05T00:00:00Z',
        nextVerification: '2024-07-05T00:00:00Z',
        owner: 'compliance-team',
        metadata: { notes: 'Additional documentation required' }
      }
    ],
    assessments: [],
    certifications: [],
    lastUpdated: '2024-01-01T00:00:00Z',
    nextReview: '2024-07-01T00:00:00Z',
    owner: 'compliance-team',
    tags: ['soc2', 'certification'],
    metadata: { certificationLevel: 'Type II', validUntil: '2024-12-31' }
  },
  {
    id: 'iso27001',
    name: 'ISO 27001',
    displayName: 'ISO 27001',
    version: '2013',
    description: 'Information Security Management System standard',
    type: 'certification',
    status: 'active',
    controls: [],
    requirements: [
      {
        id: 'iso27001-a5.1',
        frameworkId: 'iso27001',
        requirementId: 'A.5.1',
        title: 'Information Security Policies',
        description: 'Management direction for information security',
        category: 'administrative',
        mandatory: true,
        controls: ['ctrl-003'],
        status: 'compliant',
        compliance: 'full',
        evidence: [],
        lastVerified: '2024-01-10T00:00:00Z',
        nextVerification: '2024-07-10T00:00:00Z',
        owner: 'external-auditor',
        metadata: {}
      }
    ],
    assessments: [],
    certifications: [],
    lastUpdated: '2024-01-10T00:00:00Z',
    nextReview: '2025-01-10T00:00:00Z',
    owner: 'security-team',
    tags: ['iso27001', 'security'],
    metadata: { certificationLevel: 'Certified', validUntil: '2025-06-30' }
  }
];

const mockComplianceReports: ComplianceReport[] = [
  {
    id: 'report-001',
    title: 'Q4 2023 SOC 2 Compliance Report',
    framework: 'SOC 2 Type II',
    generatedAt: '2024-01-01T00:00:00Z',
    generatedBy: 'compliance-team',
    period: {
      start: '2023-10-01T00:00:00Z',
      end: '2023-12-31T23:59:59Z'
    },
    overallScore: 87,
    status: 'completed',
    summary: {
      totalRequirements: 64,
      compliantRequirements: 56,
      partialRequirements: 6,
      nonCompliantRequirements: 2,
      findings: 8,
      recommendations: 12
    },
    findings: [
      'Incomplete access logging for administrative accounts',
      'Missing encryption for data in transit in test environment'
    ],
    recommendations: [
      'Implement comprehensive access logging',
      'Enable TLS encryption for all environments'
    ]
  }
];

const AuditCompliance: React.FC = () => {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditEvents);
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>(mockComplianceFrameworks);
  const [reports, setReports] = useState<ComplianceReport[]>(mockComplianceReports);
  const [loading, setLoading] = useState(false);
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [form] = Form.useForm();

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'gold';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'blocked': return 'red';
      case 'failed': return 'red';
      case 'warning': return 'orange';
      default: return 'default';
    }
  };

  const getComplianceStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'partial': return 'warning';
      case 'non_compliant': return 'error';
      case 'not_applicable': return 'default';
      default: return 'default';
    }
  };

  const auditColumns: ColumnsType<AuditEvent> = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => {
        const date = new Date(timestamp);
        return (
          <div>
            <div>{date.toLocaleDateString()}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {date.toLocaleTimeString()}
            </Text>
          </div>
        );
      }
    },
    {
      title: 'User',
      key: 'user',
      width: 150,
      render: (_, record) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{record.userName}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.userId}</Text>
          </div>
        </Space>
      )
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => (
        <Tag color="blue">{action.replace('_', ' ').toUpperCase()}</Tag>
      )
    },
    {
      title: 'Resource',
      key: 'resource',
      width: 200,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.resource}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.resourceType}</Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'outcome',
      key: 'outcome',
      width: 100,
      render: (outcome: string) => (
        <Badge status={getStatusColor(outcome) as any} text={outcome} />
      )
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button 
          type="link" 
          size="small"
          onClick={() => setSelectedEvent(record)}
        >
          View Details
        </Button>
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

  const generateReport = async (values: any) => {
    console.log('Generating report:', values);
    setReportModalVisible(false);
    form.resetFields();
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Audit & Compliance</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refreshData} loading={loading}>
            Refresh
          </Button>
          <Button icon={<SettingOutlined />}>
            Settings
          </Button>
          <Button type="primary" icon={<FileTextOutlined />} onClick={() => setReportModalVisible(true)}>
            Generate Report
          </Button>
        </Space>
      </div>

      {/* Compliance Overview Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Compliance Score"
              value={89}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
              prefix={<SafetyCertificateOutlined />}
            />
            <Progress percent={89} strokeColor="#52c41a" showInfo={false} size="small" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Frameworks"
              value={frameworks.length}
              prefix={<ShieldCheckOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              SOC2, ISO27001, NIST
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Audit Events (24h)"
              value={auditEvents.length}
              prefix={<AuditOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {auditEvents.filter(e => e.severity === 'critical').length} critical
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Policy Violations"
              value={auditEvents.filter(e => e.action === 'policy_violation').length}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Requires attention
            </div>
          </Card>
        </Col>
      </Row>

      {/* Critical Alerts */}
      {auditEvents.some(e => e.severity === 'critical') && (
        <Alert
          message="Critical Compliance Issues Detected"
          description={`${auditEvents.filter(e => e.severity === 'critical').length} critical audit events require immediate attention.`}
          type="error"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary" ghost>
              Review Issues
            </Button>
          }
        />
      )}

      {/* Main Content Tabs */}
      <Tabs defaultActiveKey="audit-trail">
        <TabPane tab="Audit Trail" key="audit-trail">
          <Card title="Audit Events" extra={
            <Space>
              <Button icon={<FilterOutlined />}>
                Filter
              </Button>
              <Button icon={<DownloadOutlined />}>
                Export
              </Button>
            </Space>
          }>
            <Table
              columns={auditColumns}
              dataSource={auditEvents}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              scroll={{ x: 1200 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Compliance Frameworks" key="frameworks">
          <Row gutter={[16, 16]}>
            {frameworks.map(framework => (
              <Col xs={24} lg={12} key={framework.id}>
                <Card 
                  title={framework.name}
                  extra={
                    <Tag color={new Date(framework.metadata.validUntil) > new Date() ? 'green' : 'red'}>
                      {framework.metadata.certificationLevel}
                    </Tag>
                  }
                >
                  <Descriptions size="small" column={1}>
                    <Descriptions.Item label="Version">{framework.version}</Descriptions.Item>
                    <Descriptions.Item label="Valid Until">
                      {framework.metadata.validUntil}
                    </Descriptions.Item>
                    <Descriptions.Item label="Requirements">
                      {framework.requirements.length} total
                    </Descriptions.Item>
                  </Descriptions>
                  
                  <Divider />
                  
                  <div style={{ marginBottom: '16px' }}>
                    <Text strong>Compliance Status:</Text>
                  </div>
                  
                  <Steps direction="vertical" size="small">
                    {framework.requirements.slice(0, 3).map(req => (
                      <Step
                        key={req.id}
                        title={req.title}
                        description={req.description}
                        status={req.status === 'compliant' ? 'finish' : req.status === 'partial' ? 'process' : 'error'}
                        icon={
                          req.status === 'compliant' ? <CheckCircleOutlined /> :
                          req.status === 'partial' ? <ClockCircleOutlined /> :
                          <ExclamationCircleOutlined />
                        }
                      />
                    ))}
                  </Steps>
                  
                  {framework.requirements.length > 3 && (
                    <Button type="link" size="small">
                      View All {framework.requirements.length} Requirements
                    </Button>
                  )}
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        <TabPane tab="Compliance Reports" key="reports">
          <Card title="Generated Reports">
            <List
              itemLayout="horizontal"
              dataSource={reports}
              renderItem={report => (
                <List.Item
                  actions={[
                    <Button type="link" icon={<DownloadOutlined />}>Download</Button>,
                    <Button type="link">View</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<FileTextOutlined />} />}
                    title={report.title}
                    description={
                      <Space direction="vertical" size="small">
                        <Text type="secondary">
                          {report.framework} • Generated {new Date(report.generatedAt).toLocaleDateString()}
                        </Text>
                        <Space>
                          <Tag color="blue">Score: {report.overallScore}%</Tag>
                          <Tag color="green">{report.summary.compliantRequirements} Compliant</Tag>
                          <Tag color="orange">{report.summary.partialRequirements} Partial</Tag>
                          <Tag color="red">{report.summary.nonCompliantRequirements} Non-compliant</Tag>
                        </Space>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane tab="Audit Search" key="search">
          <Card title="Advanced Audit Search">
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="User">
                    <Select placeholder="Select user" allowClear>
                      <Option value="user-123">John Doe</Option>
                      <Option value="user-456">Jane Smith</Option>
                      <Option value="user-789">Bob Wilson</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Action">
                    <Select placeholder="Select action" allowClear>
                      <Option value="test_execution">Test Execution</Option>
                      <Option value="vulnerability_scan">Vulnerability Scan</Option>
                      <Option value="policy_violation">Policy Violation</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Date Range">
                    <RangePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="Resource Type">
                    <Select placeholder="Select resource type" allowClear>
                      <Option value="test_plan">Test Plan</Option>
                      <Option value="security_scan">Security Scan</Option>
                      <Option value="security_policy">Security Policy</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Severity">
                    <Select placeholder="Select severity" allowClear>
                      <Option value="critical">Critical</Option>
                      <Option value="high">High</Option>
                      <Option value="medium">Medium</Option>
                      <Option value="low">Low</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Status">
                    <Select placeholder="Select status" allowClear>
                      <Option value="success">Success</Option>
                      <Option value="blocked">Blocked</Option>
                      <Option value="failed">Failed</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Space>
                  <Button type="primary" icon={<SearchOutlined />}>
                    Search
                  </Button>
                  <Button>
                    Clear
                  </Button>
                  <Button icon={<DownloadOutlined />}>
                    Export Results
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab="Compliance Timeline" key="timeline">
          <Card title="Compliance Events Timeline">
            <Timeline>
              <Timeline.Item color="green">
                <p><strong>SOC 2 Audit Completed</strong></p>
                <p>Annual SOC 2 Type II audit completed successfully with 89% compliance score</p>
                <p style={{ color: '#666', fontSize: '12px' }}>January 1, 2024</p>
              </Timeline.Item>
              <Timeline.Item color="blue">
                <p><strong>ISO 27001 Certification Renewed</strong></p>
                <p>ISO 27001 certification renewed for another 3 years</p>
                <p style={{ color: '#666', fontSize: '12px' }}>December 15, 2023</p>
              </Timeline.Item>
              <Timeline.Item color="orange">
                <p><strong>Policy Violation Detected</strong></p>
                <p>Unauthorized access attempt to sensitive data store</p>
                <p style={{ color: '#666', fontSize: '12px' }}>December 10, 2023</p>
              </Timeline.Item>
              <Timeline.Item color="red">
                <p><strong>Compliance Gap Identified</strong></p>
                <p>Missing encryption for data in transit in test environment</p>
                <p style={{ color: '#666', fontSize: '12px' }}>December 5, 2023</p>
              </Timeline.Item>
            </Timeline>
          </Card>
        </TabPane>
      </Tabs>

      {/* Report Generation Modal */}
      <Modal
        title="Generate Compliance Report"
        visible={reportModalVisible}
        onCancel={() => {
          setReportModalVisible(false);
          form.resetFields();
        }}
        width={600}
        footer={[
          <Button key="cancel" onClick={() => setReportModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="generate" type="primary" onClick={() => form.submit()}>
            Generate Report
          </Button>
        ]}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={generateReport}
        >
          <Form.Item label="Report Title" name="title" rules={[{ required: true }]}>
            <Input placeholder="Enter report title" />
          </Form.Item>
          
          <Form.Item label="Compliance Framework" name="framework" rules={[{ required: true }]}>
            <Select placeholder="Select framework">
              <Option value="soc2">SOC 2 Type II</Option>
              <Option value="iso27001">ISO 27001</Option>
              <Option value="nist">NIST Cybersecurity Framework</Option>
              <Option value="custom">Custom Framework</Option>
            </Select>
          </Form.Item>
          
          <Form.Item label="Report Period" name="period" rules={[{ required: true }]}>
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item label="Include Sections">
            <Select mode="multiple" placeholder="Select sections to include">
              <Option value="executive_summary">Executive Summary</Option>
              <Option value="compliance_status">Compliance Status</Option>
              <Option value="audit_findings">Audit Findings</Option>
              <Option value="recommendations">Recommendations</Option>
              <Option value="evidence">Evidence</Option>
              <Option value="appendix">Appendix</Option>
            </Select>
          </Form.Item>
          
          <Form.Item label="Report Format" name="format">
            <Select defaultValue="pdf">
              <Option value="pdf">PDF</Option>
              <Option value="html">HTML</Option>
              <Option value="docx">Word Document</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Audit Event Detail Modal */}
      <Modal
        title="Audit Event Details"
        visible={!!selectedEvent}
        onCancel={() => setSelectedEvent(null)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setSelectedEvent(null)}>
            Close
          </Button>
        ]}
      >
        {selectedEvent && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="Event ID">{selectedEvent.id}</Descriptions.Item>
            <Descriptions.Item label="Timestamp">
              {new Date(selectedEvent.timestamp).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="User">{selectedEvent.userName}</Descriptions.Item>
            <Descriptions.Item label="User ID">{selectedEvent.userId}</Descriptions.Item>
            <Descriptions.Item label="Action">
              <Tag color="blue">{selectedEvent.action}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Badge status={getStatusColor(selectedEvent.status) as any} text={selectedEvent.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Resource">{selectedEvent.resource}</Descriptions.Item>
            <Descriptions.Item label="Resource Type">{selectedEvent.resourceType}</Descriptions.Item>
            <Descriptions.Item label="Severity">
              <Tag color={getSeverityColor(selectedEvent.severity)}>{selectedEvent.severity}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="IP Address">{selectedEvent.ipAddress}</Descriptions.Item>
            <Descriptions.Item label="User Agent" span={2}>
              {selectedEvent.userAgent}
            </Descriptions.Item>
            <Descriptions.Item label="Details" span={2}>
              <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(selectedEvent.details, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default AuditCompliance;