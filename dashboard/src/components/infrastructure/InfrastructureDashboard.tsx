import React, { useState, useCallback } from 'react'
import { Card, Row, Col, Typography, Space, Button, Statistic, Alert, Spin, Tabs } from 'antd'
import {
  CloudServerOutlined,
  DesktopOutlined,
  HddOutlined,
  RocketOutlined,
  ReloadOutlined,
  SettingOutlined,
  AlertOutlined,
  PlusOutlined
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface InfrastructureOverview {
  build_servers: { total: number; online: number; offline: number; maintenance: number }
  hosts: { total: number; online: number; offline: number; maintenance: number }
  boards: { total: number; available: number; in_use: number; offline: number; maintenance: number }
  active_builds: number
  active_pipelines: number
  recent_alerts: Alert[]
}

interface Alert {
  id: string
  severity: 'critical' | 'warning' | 'info'
  resource_type: string
  resource_id: string
  message: string
  created_at: string
  acknowledged: boolean
}

/**
 * Infrastructure Dashboard Component
 * 
 * Main dashboard for test infrastructure management showing overview of
 * build servers, QEMU hosts, physical boards, and pipelines.
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 15.1-15.4**: Display resource counts and health summary
 */
const InfrastructureDashboard: React.FC = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch infrastructure overview
  const { data: overview, isLoading, error, refetch } = useQuery<InfrastructureOverview>(
    'infrastructureOverview',
    async () => {
      const response = await fetch('/api/v1/infrastructure/overview')
      if (!response.ok) throw new Error('Failed to fetch infrastructure overview')
      return response.json()
    },
    { refetchInterval: 10000 }
  )

  // Fetch alerts
  const { data: alerts = [] } = useQuery<Alert[]>(
    'infrastructureAlerts',
    async () => {
      const response = await fetch('/api/v1/infrastructure/alerts?limit=10')
      if (!response.ok) throw new Error('Failed to fetch alerts')
      return response.json()
    },
    { refetchInterval: 5000 }
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': case 'available': return '#52c41a'
      case 'offline': return '#ff4d4f'
      case 'maintenance': return '#faad14'
      case 'in_use': return '#1890ff'
      default: return '#d9d9d9'
    }
  }

  if (error) {
    return (
      <Alert
        message="Failed to Load Infrastructure Data"
        description="Unable to fetch infrastructure overview. Please try again."
        type="error"
        showIcon
        action={<Button onClick={() => refetch()}>Retry</Button>}
      />
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={2}>
            <CloudServerOutlined style={{ marginRight: 8 }} />
            Infrastructure Management
          </Title>
          <Text type="secondary">
            Manage build servers, QEMU hosts, physical boards, and pipelines
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>
            Refresh
          </Button>
          <Button icon={<SettingOutlined />} onClick={() => navigate('/infrastructure/settings')}>
            Settings
          </Button>
        </Space>
      </div>

      {isLoading && !overview ? (
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}><Text>Loading infrastructure data...</Text></div>
        </div>
      ) : (
        <>
          {/* Overview Statistics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card hoverable onClick={() => navigate('/infrastructure/build-servers')}>
                <Statistic
                  title="Build Servers"
                  value={overview?.build_servers.total || 0}
                  prefix={<HddOutlined />}
                  suffix={
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      ({overview?.build_servers.online || 0} online)
                    </Text>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card hoverable onClick={() => navigate('/infrastructure/hosts')}>
                <Statistic
                  title="QEMU Hosts"
                  value={overview?.hosts.total || 0}
                  prefix={<DesktopOutlined />}
                  suffix={
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      ({overview?.hosts.online || 0} online)
                    </Text>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card hoverable onClick={() => navigate('/infrastructure/boards')}>
                <Statistic
                  title="Physical Boards"
                  value={overview?.boards.total || 0}
                  prefix={<CloudServerOutlined />}
                  suffix={
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      ({overview?.boards.available || 0} available)
                    </Text>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card hoverable onClick={() => navigate('/infrastructure/pipelines')}>
                <Statistic
                  title="Active Pipelines"
                  value={overview?.active_pipelines || 0}
                  prefix={<RocketOutlined />}
                  suffix={
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      ({overview?.active_builds || 0} builds)
                    </Text>
                  }
                />
              </Card>
            </Col>
          </Row>

          {/* Quick Actions */}
          <Card title="Quick Actions" style={{ marginBottom: 24 }}>
            <Space wrap>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/infrastructure/build-servers/new')}>
                Register Build Server
              </Button>
              <Button icon={<PlusOutlined />} onClick={() => navigate('/infrastructure/hosts/new')}>
                Register Host
              </Button>
              <Button icon={<PlusOutlined />} onClick={() => navigate('/infrastructure/boards/new')}>
                Register Board
              </Button>
              <Button icon={<RocketOutlined />} onClick={() => navigate('/infrastructure/pipelines/new')}>
                Create Pipeline
              </Button>
            </Space>
          </Card>

          {/* Alerts Panel */}
          {alerts.length > 0 && (
            <Card
              title={<><AlertOutlined /> Recent Alerts ({alerts.length})</>}
              style={{ marginBottom: 24 }}
              extra={<Button size="small" onClick={() => navigate('/infrastructure/alerts')}>View All</Button>}
            >
              {alerts.slice(0, 5).map(alert => (
                <Alert
                  key={alert.id}
                  message={`[${alert.resource_type}] ${alert.message}`}
                  type={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
                  showIcon
                  style={{ marginBottom: 8 }}
                  closable={!alert.acknowledged}
                />
              ))}
            </Card>
          )}

          {/* Tabs for detailed views */}
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane tab="Build Servers" key="build-servers">
              <Card>
                <Text type="secondary">Build server list will be displayed here.</Text>
                <Button style={{ marginTop: 16 }} onClick={() => navigate('/infrastructure/build-servers')}>
                  Go to Build Servers
                </Button>
              </Card>
            </TabPane>
            <TabPane tab="QEMU Hosts" key="hosts">
              <Card>
                <Text type="secondary">QEMU host list will be displayed here.</Text>
                <Button style={{ marginTop: 16 }} onClick={() => navigate('/infrastructure/hosts')}>
                  Go to Hosts
                </Button>
              </Card>
            </TabPane>
            <TabPane tab="Physical Boards" key="boards">
              <Card>
                <Text type="secondary">Physical board list will be displayed here.</Text>
                <Button style={{ marginTop: 16 }} onClick={() => navigate('/infrastructure/boards')}>
                  Go to Boards
                </Button>
              </Card>
            </TabPane>
            <TabPane tab="Pipelines" key="pipelines">
              <Card>
                <Text type="secondary">Pipeline list will be displayed here.</Text>
                <Button style={{ marginTop: 16 }} onClick={() => navigate('/infrastructure/pipelines')}>
                  Go to Pipelines
                </Button>
              </Card>
            </TabPane>
          </Tabs>
        </>
      )}
    </div>
  )
}

export default InfrastructureDashboard
