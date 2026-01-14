import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Tabs,
  Alert,
  Typography,
  Select,
  Modal,
  Form,
  Input,
  Switch,
  Badge,
  List,
  Avatar,
  Descriptions,
  Divider,
  Tooltip,
  Progress
} from 'antd';
import {
  ApiOutlined,
  GithubOutlined,
  GitlabOutlined,
  SlackOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  PlusOutlined,
  LinkOutlined,
  DisconnectOutlined,
  SyncOutlined,
  BellOutlined,
  CodeOutlined,
  CloudOutlined,
  DatabaseOutlined,
  ToolOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Integration, IntegrationConfig, WebhookConfig, IntegrationHealth } from '../types/integrations';

const { TabPane } = Tabs;
const { Option } = Select;
const { Text, Title } = Typography;
const { TextArea } = Input;

// Mock data
const mockIntegrations: Integration[] = [
  {
    id: 'int-001',
    name: 'GitHub Actions',
    type: 'ci_cd',
    provider: 'github',
    status: 'connected',
    health: 'healthy',
    config: {
      apiEndpoint: 'https://api.github.com',
      authType: 'oauth',
      credentials: { token: '***' },
      settings: { autoSync: true, webhookEnabled: true }
    },
    webhooks: [
      {
        id: 'wh-001',
        url: 'https://api.example.com/webhooks/github',
        events: ['push', 'pull_request', 'release'],
        active: true,
        secret: '***',
        lastTriggered: '2024-01-13T10:25:00Z'
      }
    ],
    lastSync: '2024-01-13T10:30:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-13T10:30:00Z',
    metadata: { repository: 'org/repo', branch: 'main' },
    tags: ['ci', 'github', 'production']
  }
];

const IntegrationHub: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>(mockIntegrations);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [form] = Form.useForm();

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Integration Hub</Title>
        <Space>
          <Button icon={<ReloadOutlined />} loading={loading}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            Add Integration
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Integrations"
              value={integrations.length}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="overview">
        <TabPane tab="Overview" key="overview">
          <Card title="Active Integrations">
            <List
              dataSource={integrations}
              renderItem={integration => (
                <List.Item
                  actions={[
                    <Button type="link" size="small">Configure</Button>,
                    <Button type="link" size="small">Test</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<ApiOutlined />} />}
                    title={integration.name}
                    description={`Type: ${integration.type} • Provider: ${integration.provider}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default IntegrationHub;