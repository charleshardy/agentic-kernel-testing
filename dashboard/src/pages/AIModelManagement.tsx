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
  Slider,
  InputNumber,
  List,
  Avatar
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ApiOutlined,
  CodeOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { AIModel, ModelMetrics, ModelConfiguration, PromptTemplate } from '../types/ai-models';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;
const { Text, Title } = Typography;

// Mock data for demonstration
const mockAIModels: AIModel[] = [
  {
    id: 'model-001',
    name: 'GPT-4 Turbo',
    provider: 'openai',
    version: 'gpt-4-1106-preview',
    status: 'active',
    metrics: {
      responseTime: 1250,
      accuracy: 94.5,
      tokenUsage: 125000,
      costPerRequest: 0.045,
      requestCount: 2847,
      errorRate: 0.8
    },
    configuration: {
      endpoint: 'https://api.openai.com/v1/chat/completions',
      apiKey: 'sk-***',
      maxTokens: 4096,
      temperature: 0.7,
      rateLimit: 100,
      timeout: 30000
    },
    fallbackModel: 'model-002'
  },
  {
    id: 'model-002',
    name: 'Claude 3 Sonnet',
    provider: 'anthropic',
    version: 'claude-3-sonnet-20240229',
    status: 'active',
    metrics: {
      responseTime: 980,
      accuracy: 92.8,
      tokenUsage: 89000,
      costPerRequest: 0.038,
      requestCount: 1523,
      errorRate: 1.2
    },
    configuration: {
      endpoint: 'https://api.anthropic.com/v1/messages',
      apiKey: 'sk-ant-***',
      maxTokens: 4096,
      temperature: 0.5,
      rateLimit: 50,
      timeout: 25000
    }
  },
  {
    id: 'model-003',
    name: 'Local Llama 2',
    provider: 'local',
    version: 'llama-2-70b-chat',
    status: 'maintenance',
    metrics: {
      responseTime: 3200,
      accuracy: 88.2,
      tokenUsage: 45000,
      costPerRequest: 0.0,
      requestCount: 892,
      errorRate: 2.5
    },
    configuration: {
      endpoint: 'http://localhost:8080/v1/chat/completions',
      apiKey: '',
      maxTokens: 2048,
      temperature: 0.8,
      rateLimit: 10,
      timeout: 60000
    }
  }
];

const mockPromptTemplates: PromptTemplate[] = [
  {
    id: 'template-001',
    name: 'Test Case Analysis',
    category: 'analysis',
    template: 'Analyze the following test case and identify potential issues:\n\n{testCase}\n\nFocus on: {focusAreas}\n\nProvide detailed analysis including:\n1. Potential vulnerabilities\n2. Edge cases\n3. Performance implications',
    variables: [
      { name: 'testCase', type: 'string', required: true, description: 'The test case code to analyze' },
      { name: 'focusAreas', type: 'array', required: false, defaultValue: ['security', 'performance'], description: 'Areas to focus the analysis on' }
    ],
    version: '1.2.0',
    createdBy: 'system',
    createdAt: new Date('2024-01-01')
  },
  {
    id: 'template-002',
    name: 'Kernel Fuzzing Generation',
    category: 'generation',
    template: 'Generate fuzzing test cases for the following kernel component:\n\nComponent: {component}\nAPI Functions: {apiFunctions}\nTarget Architecture: {architecture}\n\nGenerate {count} test cases that cover:\n- Boundary conditions\n- Invalid inputs\n- Race conditions\n- Memory corruption scenarios',
    variables: [
      { name: 'component', type: 'string', required: true, description: 'Kernel component name' },
      { name: 'apiFunctions', type: 'array', required: true, description: 'List of API functions to test' },
      { name: 'architecture', type: 'string', required: false, defaultValue: 'x86_64', description: 'Target architecture' },
      { name: 'count', type: 'number', required: false, defaultValue: 10, description: 'Number of test cases to generate' }
    ],
    version: '2.1.0',
    createdBy: 'ai-team',
    createdAt: new Date('2024-01-05')
  }
];

const AIModelManagement: React.FC = () => {
  const [models, setModels] = useState<AIModel[]>(mockAIModels);
  const [templates, setTemplates] = useState<PromptTemplate[]>(mockPromptTemplates);
  const [loading, setLoading] = useState(false);
  const [modelModalVisible, setModelModalVisible] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [selectedModel, setSelectedModel] = useState<AIModel | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [form] = Form.useForm();
  const [templateForm] = Form.useForm();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'default';
      case 'error': return 'red';
      case 'maintenance': return 'orange';
      default: return 'default';
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'local': return '💻';
      case 'custom': return '⚙️';
      default: return '🔧';
    }
  };

  const modelColumns: ColumnsType<AIModel> = [
    {
      title: 'Model',
      key: 'model',
      render: (_, record) => (
        <Space>
          <Avatar size="small" style={{ backgroundColor: '#1890ff' }}>
            {getProviderIcon(record.provider)}
          </Avatar>
          <div>
            <div style={{ fontWeight: 500 }}>{record.name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.version}</Text>
          </div>
        </Space>
      )
    },
    {
      title: 'Provider',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => (
        <Tag color={provider === 'openai' ? 'blue' : provider === 'anthropic' ? 'purple' : 'green'}>
          {provider.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'active' ? 'success' : status === 'error' ? 'error' : 'default'} text={status} />
      )
    },
    {
      title: 'Response Time',
      key: 'responseTime',
      render: (_, record) => (
        <Tooltip title="Average response time">
          <Space>
            <ClockCircleOutlined />
            {record.metrics.responseTime}ms
          </Space>
        </Tooltip>
      )
    },
    {
      title: 'Accuracy',
      key: 'accuracy',
      render: (_, record) => (
        <Progress 
          percent={record.metrics.accuracy} 
          size="small" 
          strokeColor={record.metrics.accuracy >= 90 ? '#52c41a' : record.metrics.accuracy >= 80 ? '#faad14' : '#ff4d4f'}
        />
      )
    },
    {
      title: 'Requests',
      key: 'requests',
      render: (_, record) => (
        <Statistic 
          value={record.metrics.requestCount} 
          valueStyle={{ fontSize: '14px' }}
        />
      )
    },
    {
      title: 'Cost/Req',
      key: 'cost',
      render: (_, record) => (
        <Space>
          <DollarOutlined />
          ${record.metrics.costPerRequest.toFixed(3)}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedModel(record);
              form.setFieldsValue(record);
              setModelModalVisible(true);
            }}
          >
            Edit
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={record.status === 'active' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => toggleModelStatus(record.id)}
          >
            {record.status === 'active' ? 'Pause' : 'Activate'}
          </Button>
        </Space>
      )
    }
  ];

  const templateColumns: ColumnsType<PromptTemplate> = [
    {
      title: 'Template',
      key: 'template',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.name}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>v{record.version}</Text>
        </div>
      )
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === 'analysis' ? 'blue' : category === 'generation' ? 'green' : 'orange'}>
          {category}
        </Tag>
      )
    },
    {
      title: 'Variables',
      key: 'variables',
      render: (_, record) => (
        <Space>
          <CodeOutlined />
          {record.variables.length} vars
        </Space>
      )
    },
    {
      title: 'Created By',
      dataIndex: 'createdBy',
      key: 'createdBy'
    },
    {
      title: 'Created',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedTemplate(record);
              templateForm.setFieldsValue(record);
              setTemplateModalVisible(true);
            }}
          >
            Edit
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={<DeleteOutlined />}
            danger
          >
            Delete
          </Button>
        </Space>
      )
    }
  ];

  const toggleModelStatus = (modelId: string) => {
    setModels(prev => prev.map(model => 
      model.id === modelId 
        ? { ...model, status: model.status === 'active' ? 'inactive' : 'active' }
        : model
    ));
  };

  const refreshData = async () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const handleModelSave = async (values: any) => {
    console.log('Saving model:', values);
    setModelModalVisible(false);
    form.resetFields();
    setSelectedModel(null);
  };

  const handleTemplateSave = async (values: any) => {
    console.log('Saving template:', values);
    setTemplateModalVisible(false);
    templateForm.resetFields();
    setSelectedTemplate(null);
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>AI Model Management</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refreshData} loading={loading}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModelModalVisible(true)}>
            Add Model
          </Button>
        </Space>
      </div>

      {/* Model Performance Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Models"
              value={models.filter(m => m.status === 'active').length}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={Math.round(models.reduce((acc, m) => acc + m.metrics.responseTime, 0) / models.length)}
              suffix="ms"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Requests"
              value={models.reduce((acc, m) => acc + m.metrics.requestCount, 0)}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Cost"
              value={models.reduce((acc, m) => acc + (m.metrics.requestCount * m.metrics.costPerRequest), 0)}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Model Health Alerts */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        {models.some(m => m.status === 'error') && (
          <Col span={24}>
            <Alert
              message="Model Health Issues Detected"
              description={`${models.filter(m => m.status === 'error').length} model(s) are experiencing errors. Check configuration and connectivity.`}
              type="error"
              showIcon
              action={
                <Button size="small" type="primary" ghost>
                  View Details
                </Button>
              }
            />
          </Col>
        )}
        {models.some(m => m.metrics.errorRate > 5) && (
          <Col span={24}>
            <Alert
              message="High Error Rate Warning"
              description="Some models are experiencing high error rates. Consider switching to fallback models."
              type="warning"
              showIcon
            />
          </Col>
        )}
      </Row>

      {/* Main Content Tabs */}
      <Tabs defaultActiveKey="models">
        <TabPane tab="AI Models" key="models">
          <Card title="Model Registry" extra={
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setModelModalVisible(true)}>
                Add Model
              </Button>
            </Space>
          }>
            <Table
              columns={modelColumns}
              dataSource={models}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Prompt Templates" key="templates">
          <Card title="Template Library" extra={
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setTemplateModalVisible(true)}>
                New Template
              </Button>
            </Space>
          }>
            <Table
              columns={templateColumns}
              dataSource={templates}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Performance Metrics" key="metrics">
          <Row gutter={[16, 16]}>
            {models.map(model => (
              <Col xs={24} lg={12} key={model.id}>
                <Card title={model.name} size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic 
                        title="Response Time" 
                        value={model.metrics.responseTime} 
                        suffix="ms"
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic 
                        title="Accuracy" 
                        value={model.metrics.accuracy} 
                        suffix="%"
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic 
                        title="Error Rate" 
                        value={model.metrics.errorRate} 
                        suffix="%"
                        valueStyle={{ fontSize: '16px', color: model.metrics.errorRate > 5 ? '#ff4d4f' : '#52c41a' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic 
                        title="Requests" 
                        value={model.metrics.requestCount}
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        <TabPane tab="Fallback Configuration" key="fallback">
          <Card title="Model Fallback Chain">
            <List
              itemLayout="horizontal"
              dataSource={models.filter(m => m.status === 'active')}
              renderItem={(model, index) => (
                <List.Item
                  actions={[
                    <Button type="link" size="small">Configure</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: '#1890ff' }}>{index + 1}</Avatar>}
                    title={model.name}
                    description={`Fallback: ${model.fallbackModel ? models.find(m => m.id === model.fallbackModel)?.name || 'None' : 'None'}`}
                  />
                  <div>
                    <Tag color={getStatusColor(model.status)}>{model.status}</Tag>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Model Configuration Modal */}
      <Modal
        title={selectedModel ? 'Edit AI Model' : 'Add AI Model'}
        visible={modelModalVisible}
        onCancel={() => {
          setModelModalVisible(false);
          form.resetFields();
          setSelectedModel(null);
        }}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setModelModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="test" type="default">
            Test Connection
          </Button>,
          <Button key="save" type="primary" onClick={() => form.submit()}>
            Save Model
          </Button>
        ]}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleModelSave}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Model Name" name="name" rules={[{ required: true }]}>
                <Input placeholder="Enter model name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Provider" name="provider" rules={[{ required: true }]}>
                <Select placeholder="Select provider">
                  <Option value="openai">OpenAI</Option>
                  <Option value="anthropic">Anthropic</Option>
                  <Option value="local">Local</Option>
                  <Option value="custom">Custom</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item label="API Endpoint" name={['configuration', 'endpoint']} rules={[{ required: true }]}>
            <Input placeholder="https://api.example.com/v1/chat/completions" />
          </Form.Item>
          
          <Form.Item label="API Key" name={['configuration', 'apiKey']}>
            <Input.Password placeholder="Enter API key" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Max Tokens" name={['configuration', 'maxTokens']}>
                <InputNumber min={1} max={32000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Temperature" name={['configuration', 'temperature']}>
                <Slider min={0} max={2} step={0.1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Rate Limit" name={['configuration', 'rateLimit']}>
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item label="Fallback Model" name="fallbackModel">
            <Select placeholder="Select fallback model" allowClear>
              {models.filter(m => m.id !== selectedModel?.id).map(model => (
                <Option key={model.id} value={model.id}>{model.name}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Template Configuration Modal */}
      <Modal
        title={selectedTemplate ? 'Edit Prompt Template' : 'New Prompt Template'}
        visible={templateModalVisible}
        onCancel={() => {
          setTemplateModalVisible(false);
          templateForm.resetFields();
          setSelectedTemplate(null);
        }}
        width={900}
        footer={[
          <Button key="cancel" onClick={() => setTemplateModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="test" type="default">
            Test Template
          </Button>,
          <Button key="save" type="primary" onClick={() => templateForm.submit()}>
            Save Template
          </Button>
        ]}
      >
        <Form
          form={templateForm}
          layout="vertical"
          onFinish={handleTemplateSave}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Template Name" name="name" rules={[{ required: true }]}>
                <Input placeholder="Enter template name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Category" name="category" rules={[{ required: true }]}>
                <Select placeholder="Select category">
                  <Option value="analysis">Analysis</Option>
                  <Option value="generation">Generation</Option>
                  <Option value="classification">Classification</Option>
                  <Option value="custom">Custom</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item label="Template Content" name="template" rules={[{ required: true }]}>
            <TextArea 
              rows={8} 
              placeholder="Enter your prompt template with variables like {variableName}..."
            />
          </Form.Item>
          
          <Form.Item label="Template Variables">
            <Text type="secondary">
              Define variables used in your template. Variables should be enclosed in curly braces {'{}'} in the template.
            </Text>
            {/* Variable configuration would go here - simplified for demo */}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIModelManagement;