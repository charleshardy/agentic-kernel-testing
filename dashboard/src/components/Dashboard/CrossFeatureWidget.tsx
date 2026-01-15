import React from 'react';
import { Card, Row, Col, Statistic, List, Tag, Space, Button } from 'antd';
import {
  SafetyOutlined,
  BugOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ArrowRightOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

interface CrossFeatureWidgetProps {
  type: 'security-overview' | 'test-summary' | 'user-activity' | 'system-health';
  data?: any;
}

const CrossFeatureWidget: React.FC<CrossFeatureWidgetProps> = ({ type, data }) => {
  const navigate = useNavigate();

  const renderSecurityOverview = () => (
    <Card 
      title="Security Overview" 
      extra={<Button type="link" onClick={() => navigate('/security')}>View All</Button>}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Statistic
            title="Critical Vulnerabilities"
            value={data?.criticalVulnerabilities || 3}
            valueStyle={{ color: '#cf1322' }}
            prefix={<WarningOutlined />}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Security Score"
            value={data?.securityScore || 87}
            suffix="%"
            valueStyle={{ color: '#3f8600' }}
            prefix={<SafetyOutlined />}
          />
        </Col>
      </Row>
      <List
        size="small"
        style={{ marginTop: '16px' }}
        dataSource={data?.recentFindings || [
          { id: '1', title: 'Buffer overflow in network stack', severity: 'critical' },
          { id: '2', title: 'Weak encryption algorithm', severity: 'high' }
        ]}
        renderItem={(item: any) => (
          <List.Item
            onClick={() => navigate(`/security/${item.id}`)}
            style={{ cursor: 'pointer' }}
          >
            <Space>
              <Tag color={item.severity === 'critical' ? 'red' : 'orange'}>
                {item.severity.toUpperCase()}
              </Tag>
              <span>{item.title}</span>
            </Space>
            <ArrowRightOutlined />
          </List.Item>
        )}
      />
    </Card>
  );

  const renderTestSummary = () => (
    <Card 
      title="Test Summary" 
      extra={<Button type="link" onClick={() => navigate('/test-results')}>View All</Button>}
    >
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="Passed"
            value={data?.passed || 245}
            valueStyle={{ color: '#3f8600' }}
            prefix={<CheckCircleOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Failed"
            value={data?.failed || 12}
            valueStyle={{ color: '#cf1322' }}
            prefix={<BugOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Running"
            value={data?.running || 5}
            valueStyle={{ color: '#1890ff' }}
            prefix={<ClockCircleOutlined />}
          />
        </Col>
      </Row>
      <div style={{ marginTop: '16px', textAlign: 'center' }}>
        <Button type="primary" onClick={() => navigate('/test-execution/new')}>
          Run New Tests
        </Button>
      </div>
    </Card>
  );

  const renderUserActivity = () => (
    <Card 
      title="Recent Activity" 
      extra={<Button type="link" onClick={() => navigate('/audit')}>View All</Button>}
    >
      <List
        size="small"
        dataSource={data?.recentActivity || [
          { id: '1', user: 'John Doe', action: 'Executed test plan', time: '5 min ago' },
          { id: '2', user: 'Jane Smith', action: 'Created security scan', time: '15 min ago' },
          { id: '3', user: 'Bob Wilson', action: 'Updated integration', time: '1 hour ago' }
        ]}
        renderItem={(item: any) => (
          <List.Item>
            <List.Item.Meta
              title={item.user}
              description={
                <Space direction="vertical" size={0}>
                  <span>{item.action}</span>
                  <span style={{ fontSize: '12px', color: '#999' }}>{item.time}</span>
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );

  const renderSystemHealth = () => (
    <Card 
      title="System Health" 
      extra={<Button type="link" onClick={() => navigate('/resources')}>View All</Button>}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Statistic
            title="CPU Usage"
            value={data?.cpuUsage || 45}
            suffix="%"
            valueStyle={{ color: data?.cpuUsage > 80 ? '#cf1322' : '#3f8600' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Memory Usage"
            value={data?.memoryUsage || 62}
            suffix="%"
            valueStyle={{ color: data?.memoryUsage > 80 ? '#cf1322' : '#3f8600' }}
          />
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: '16px' }}>
        <Col span={12}>
          <Statistic
            title="Active Tests"
            value={data?.activeTests || 8}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Environments"
            value={data?.environments || 12}
            valueStyle={{ color: '#722ed1' }}
          />
        </Col>
      </Row>
    </Card>
  );

  switch (type) {
    case 'security-overview':
      return renderSecurityOverview();
    case 'test-summary':
      return renderTestSummary();
    case 'user-activity':
      return renderUserActivity();
    case 'system-health':
      return renderSystemHealth();
    default:
      return null;
  }
};

export default CrossFeatureWidget;
