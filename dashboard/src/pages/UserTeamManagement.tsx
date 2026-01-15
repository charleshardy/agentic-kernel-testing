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
  Modal,
  Form,
  Input,
  Select,
  Avatar,
  Typography,
  Badge,
  Descriptions
} from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;
const { Title } = Typography;

const UserTeamManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>User & Team Management</Title>
        <Space>
          <Button type="primary" icon={<PlusOutlined />}>
            Add User
          </Button>
          <Button type="primary" icon={<TeamOutlined />}>
            Create Team
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Users"
              value={45}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Teams"
              value={8}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="users">
        <TabPane tab="Users" key="users">
          <Card title="User Directory">
            <p>User management interface</p>
          </Card>
        </TabPane>
        <TabPane tab="Teams" key="teams">
          <Card title="Teams">
            <p>Team management interface</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default UserTeamManagement;