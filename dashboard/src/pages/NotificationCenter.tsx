import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Button,
  Space,
  Tabs,
  Badge,
  Avatar,
  Typography
} from 'antd';
import {
  BellOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  SettingOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Title, Text } = Typography;

const NotificationCenter: React.FC = () => {
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Notification Center</Title>
        <Space>
          <Button icon={<SettingOutlined />}>
            Preferences
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Unread Notifications"
              value={12}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="all">
        <TabPane tab="All Notifications" key="all">
          <Card>
            <List
              dataSource={[]}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<BellOutlined />} />}
                    title="Notification"
                    description="Description"
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

export default NotificationCenter;