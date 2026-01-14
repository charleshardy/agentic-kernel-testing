import React from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, Tabs, Switch, Badge, Avatar } from 'antd'
import { 
  BellOutlined, 
  MailOutlined, 
  SlackOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  DeleteOutlined,
  SettingOutlined,
  UserOutlined
} from '@ant-design/icons'

const { TabPane } = Tabs

const NotificationCenter: React.FC = () => {
  // Mock notification data
  const stats = {
    totalNotifications: 47,
    unreadNotifications: 12,
    criticalAlerts: 3,
    activeChannels: 5
  }

  const notifications = [
    {
      key: '1',
      type: 'Security',
      title: 'Critical Vulnerability Detected',
      message: 'CVE-2024-0001: Buffer overflow vulnerability found in network driver',
      timestamp: '2024-01-13 14:30:00',
      priority: 'Critical',
      status: 'Unread',
      source: 'Security Scanner',
      channel: 'Email + Slack'
    },
    {
      key: '2',
      type: 'Test',
      title: 'Test Execution Completed',
      message: 'Kernel test suite completed with 94.2% pass rate (45/48 tests passed)',
      timestamp: '2024-01-13 14:25:00',
      priority: 'Info',
      status: 'Read',
      source: 'Test Engine',
      channel: 'In-App'
    },
    {
      key: '3',
      type: 'System',
      title: 'High Memory Usage Alert',
      message: 'Node-03 memory utilization exceeded 95% threshold',
      timestamp: '2024-01-13 14:20:00',
      priority: 'Warning',
      status: 'Unread',
      source: 'Resource Monitor',
      channel: 'Email'
    },
    {
      key: '4',
      type: 'Integration',
      title: 'Jenkins Integration Failed',
      message: 'Connection to Jenkins server failed - check credentials and network connectivity',
      timestamp: '2024-01-13 14:15:00',
      priority: 'High',
      status: 'Read',
      source: 'Integration Hub',
      channel: 'Slack'
    }
  ]

  const channels = [
    {
      key: '1',
      name: 'Email Notifications',
      type: 'Email',
      status: 'Active',
      recipients: 15,
      lastSent: '2024-01-13 14:30:00',
      config: 'smtp.company.com'
    },
    {
      key: '2',
      name: 'Slack Integration',
      type: 'Slack',
      status: 'Active',
      recipients: 8,
      lastSent: '2024-01-13 14:25:00',
      config: '#testing-alerts'
    },
    {
      key: '3',
      name: 'In-App Notifications',
      type: 'In-App',
      status: 'Active',
      recipients: 25,
      lastSent: '2024-01-13 14:32:00',
      config: 'Real-time'
    },
    {
      key: '4',
      name: 'SMS Alerts',
      type: 'SMS',
      status: 'Inactive',
      recipients: 5,
      lastSent: '2024-01-12 18:45:00',
      config: 'Twilio'
    }
  ]

  const notificationColumns = [
    {
      title: 'Notification',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: any) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {record.status === 'Unread' && <Badge status="processing" />}
            <span style={{ fontWeight: record.status === 'Unread' ? 'bold' : 'normal' }}>
              {title}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
            {record.message}
          </div>
          <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
            {record.source} • {record.timestamp}
          </div>
        </div>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colors = {
          'Security': 'red',
          'Test': 'blue',
          'System': 'orange',
          'Integration': 'purple'
        }
        return <Tag color={colors[type as keyof typeof colors]}>{type}</Tag>
      }
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => {
        const colors = {
          'Critical': 'red',
          'High': 'orange',
          'Warning': 'yellow',
          'Info': 'blue'
        }
        const icons = {
          'Critical': <ExclamationCircleOutlined />,
          'High': <WarningOutlined />,
          'Warning': <WarningOutlined />,
          'Info': <InfoCircleOutlined />
        }
        return (
          <Tag color={colors[priority as keyof typeof colors]} icon={icons[priority as keyof typeof icons]}>
            {priority}
          </Tag>
        )
      }
    },
    {
      title: 'Channel',
      dataIndex: 'channel',
      key: 'channel',
      render: (channel: string) => <span style={{ fontSize: '12px' }}>{channel}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          {record.status === 'Unread' && (
            <Button size="small" icon={<CheckCircleOutlined />}>Mark Read</Button>
          )}
          <Button size="small" icon={<DeleteOutlined />} danger>Delete</Button>
        </Space>
      )
    }
  ]

  const channelColumns = [
    {
      title: 'Channel',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <Space>
          {record.type === 'Email' && <MailOutlined />}
          {record.type === 'Slack' && <SlackOutlined />}
          {record.type === 'In-App' && <BellOutlined />}
          {!['Email', 'Slack', 'In-App'].includes(record.type) && <BellOutlined />}
          <div>
            <div style={{ fontWeight: 'bold' }}>{name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{record.config}</div>
          </div>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'Active' ? 'green' : 'gray'}>{status}</Tag>
      )
    },
    {
      title: 'Recipients',
      dataIndex: 'recipients',
      key: 'recipients',
      render: (count: number) => (
        <Space>
          <UserOutlined />
          <span>{count}</span>
        </Space>
      )
    },
    {
      title: 'Last Sent',
      dataIndex: 'lastSent',
      key: 'lastSent',
      render: (text: string) => <span style={{ fontSize: '12px', fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Switch 
            checked={record.status === 'Active'} 
            size="small"
          />
          <Button size="small" icon={<SettingOutlined />}>Configure</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BellOutlined />
          Notification Center
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Manage notifications, alerts, and communication channels
        </p>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Notifications"
              value={stats.totalNotifications}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Unread"
              value={stats.unreadNotifications}
              prefix={<Badge status="processing" />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Critical Alerts"
              value={stats.criticalAlerts}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Channels"
              value={stats.activeChannels}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Tabs defaultActiveKey="notifications">
          <TabPane 
            tab={
              <span>
                <BellOutlined />
                Notifications
                {stats.unreadNotifications > 0 && (
                  <Badge count={stats.unreadNotifications} size="small" style={{ marginLeft: '8px' }} />
                )}
              </span>
            } 
            key="notifications"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>Recent Notifications</h3>
              <Space>
                <Button size="small">Mark All Read</Button>
                <Button size="small" danger>Clear All</Button>
              </Space>
            </div>
            <Table
              columns={notificationColumns}
              dataSource={notifications}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <MailOutlined />
                Channels
              </span>
            } 
            key="channels"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>Notification Channels</h3>
              <Button type="primary" icon={<SettingOutlined />}>
                Add Channel
              </Button>
            </div>
            <Table
              columns={channelColumns}
              dataSource={channels}
              pagination={false}
              size="small"
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                Preferences
              </span>
            } 
            key="preferences"
          >
            <div style={{ marginBottom: '16px' }}>
              <h3>Notification Preferences</h3>
            </div>
            
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="Alert Policies" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>Critical Security Alerts</div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          Immediate notification for critical vulnerabilities
                        </div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>Test Failure Notifications</div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          Notify when test pass rate drops below threshold
                        </div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>Resource Alerts</div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          System resource utilization warnings
                        </div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>Integration Status</div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          External integration connection issues
                        </div>
                      </div>
                      <Switch />
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="Delivery Settings" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Quiet Hours</div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                        Suppress non-critical notifications during specified hours
                      </div>
                      <Space>
                        <span style={{ fontSize: '12px' }}>22:00 - 08:00</span>
                        <Switch />
                      </Space>
                    </div>
                    <div>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Digest Mode</div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                        Group non-urgent notifications into daily digest
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Mobile Push</div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                        Send push notifications to mobile devices
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default NotificationCenter