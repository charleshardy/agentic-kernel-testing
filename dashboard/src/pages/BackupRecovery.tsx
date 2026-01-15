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
  Typography,
  Progress
} from 'antd';
import {
  CloudUploadOutlined,
  CloudDownloadOutlined,
  SafetyCertificateOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Title } = Typography;

const BackupRecovery: React.FC = () => {
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Backup & Recovery</Title>
        <Space>
          <Button type="primary" icon={<CloudUploadOutlined />}>
            Create Backup
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Backups"
              value={45}
              prefix={<CloudUploadOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Last Backup"
              value="2h ago"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="backups">
        <TabPane tab="Backups" key="backups">
          <Card title="Backup History">
            <p>Backup list</p>
          </Card>
        </TabPane>
        <TabPane tab="Policies" key="policies">
          <Card title="Backup Policies">
            <p>Policy configuration</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default BackupRecovery;