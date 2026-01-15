import React from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, List, Badge } from 'antd';
import { 
  SecurityScanOutlined, 
  RobotOutlined, 
  TeamOutlined, 
  BellOutlined,
  BarChartOutlined,
  CloudServerOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

interface WidgetData {
  security: {
    critical: number;
    high: number;
    complianceScore: number;
  };
  aiModels: {
    active: number;
    total: number;
    avgResponseTime: number;
  };
  resources: {
    cpuUsage: number;
    memoryUsage: number;
    activeTests: number;
  };
  notifications: {
    unread: number;
    urgent: number;
  };
  analytics: {
    testsPassed: number;
    testsTotal: number;
    coverage: number;
  };
}

interface DashboardWidgetsProps {
  data: WidgetData;
}

const DashboardWidgets: React.FC<DashboardWidgetsProps> = ({ data }) => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        {/* Security Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => navigate('/security')}
            style={{ height: '100%' }}
          >
            <Statistic
              title="Security Status"
              value={data.security.complianceScore}
              suffix="%"
              prefix={<SecurityScanOutlined />}
              valueStyle={{ color: data.security.critical > 0 ? '#cf1322' : '#3f8600' }}
            />
            <div style={{ marginTop: 16 }}>
              <Tag color="red">Critical: {data.security.critical}</Tag>
              <Tag color="orange">High: {data.security.high}</Tag>
            </div>
          </Card>
        </Col>

        {/* AI Models Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => navigate('/ai-models')}
            style={{ height: '100%' }}
          >
            <Statistic
              title="AI Models"
              value={data.aiModels.active}
              suffix={`/ ${data.aiModels.total}`}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 16 }}>
              <span>Avg Response: {data.aiModels.avgResponseTime}ms</span>
            </div>
          </Card>
        </Col>

        {/* Resource Monitoring Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => navigate('/resource-monitoring')}
            style={{ height: '100%' }}
          >
            <Statistic
              title="Active Tests"
              value={data.resources.activeTests}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 16 }}>
              <div>CPU: <Progress percent={data.resources.cpuUsage} size="small" /></div>
              <div>Memory: <Progress percent={data.resources.memoryUsage} size="small" /></div>
            </div>
          </Card>
        </Col>

        {/* Notifications Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => navigate('/notifications')}
            style={{ height: '100%' }}
          >
            <Badge count={data.notifications.unread} offset={[10, 0]}>
              <Statistic
                title="Notifications"
                value={data.notifications.unread}
                prefix={<BellOutlined />}
                valueStyle={{ color: data.notifications.urgent > 0 ? '#fa8c16' : '#52c41a' }}
              />
            </Badge>
            <div style={{ marginTop: 16 }}>
              {data.notifications.urgent > 0 && (
                <Tag color="red" icon={<WarningOutlined />}>
                  {data.notifications.urgent} Urgent
                </Tag>
              )}
            </div>
          </Card>
        </Col>

        {/* Analytics Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => navigate('/analytics')}
            style={{ height: '100%' }}
          >
            <Statistic
              title="Test Success Rate"
              value={((data.analytics.testsPassed / data.analytics.testsTotal) * 100).toFixed(1)}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 16 }}>
              <div>Coverage: <Progress percent={data.analytics.coverage} size="small" /></div>
            </div>
          </Card>
        </Col>

        {/* Quick Actions Widget */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="Quick Actions" style={{ height: '100%' }}>
            <List
              size="small"
              dataSource={[
                { label: 'View Security Findings', path: '/security', icon: <SecurityScanOutlined /> },
                { label: 'Manage Teams', path: '/users', icon: <TeamOutlined /> },
                { label: 'Check Resources', path: '/resource-monitoring', icon: <CloudServerOutlined /> },
                { label: 'View Analytics', path: '/analytics', icon: <BarChartOutlined /> }
              ]}
              renderItem={(item) => (
                <List.Item
                  onClick={() => navigate(item.path)}
                  style={{ cursor: 'pointer', padding: '8px 0' }}
                >
                  {item.icon} <span style={{ marginLeft: 8 }}>{item.label}</span>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Mock data generator for testing
export const generateMockWidgetData = (): WidgetData => ({
  security: {
    critical: 2,
    high: 5,
    complianceScore: 87
  },
  aiModels: {
    active: 3,
    total: 5,
    avgResponseTime: 245
  },
  resources: {
    cpuUsage: 65,
    memoryUsage: 72,
    activeTests: 12
  },
  notifications: {
    unread: 8,
    urgent: 2
  },
  analytics: {
    testsPassed: 145,
    testsTotal: 160,
    coverage: 78
  }
});

export default DashboardWidgets;
