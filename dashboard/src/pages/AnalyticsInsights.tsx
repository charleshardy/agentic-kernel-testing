import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  Tabs,
  Typography
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  TrendingUpOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Title } = Typography;

const AnalyticsInsights: React.FC = () => {
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Analytics & Insights</Title>
        <Button type="primary" icon={<LineChartOutlined />}>
          Custom Report
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Tests"
              value={1250}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="overview">
        <TabPane tab="Overview" key="overview">
          <Card title="Key Metrics">
            <p>Analytics overview</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AnalyticsInsights;