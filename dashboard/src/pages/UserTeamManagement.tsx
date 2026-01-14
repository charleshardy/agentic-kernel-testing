import React from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Avatar, Space, Button, Tabs } from 'antd'
import { 
  TeamOutlined, 
  UserOutlined, 
  CrownOutlined,
  SafetyCertificateOutlined,
  PlusOutlined,
  EditOutlined
} from '@ant-design/icons'

const { TabPane } = Tabs

const UserTeamManagement: React.FC = () => {
  // Mock user and team data
  const stats = {
    totalUsers: 47,
    activeUsers: 42,
    totalTeams: 8,
    activeTeams: 7
  }

  const users = [
    {
      key: '1',
      name: 'Alice Johnson',
      email: 'alice.johnson@company.com',
      role: 'Admin',
      team: 'Security Team',
      status: 'Active',
      lastLogin: '2024-01-13 09:30',
      permissions: ['security.read', 'security.write', 'admin.all']
    },
    {
      key: '2',
      name: 'Bob Smith',
      email: 'bob.smith@company.com',
      role: 'Developer',
      team: 'Kernel Team',
      status: 'Active',
      lastLogin: '2024-01-13 08:15',
      permissions: ['test.read', 'test.write', 'execution.read']
    },
    {
      key: '3',
      name: 'Carol Davis',
      email: 'carol.davis@company.com',
      role: 'Tester',
      team: 'QA Team',
      status: 'Inactive',
      lastLogin: '2024-01-10 16:45',
      permissions: ['test.read', 'results.read']
    }
  ]

  const teams = [
    {
      key: '1',
      name: 'Security Team',
      description: 'Responsible for security testing and vulnerability management',
      members: 8,
      lead: 'Alice Johnson',
      status: 'Active',
      created: '2023-06-15',
      permissions: ['security.*', 'vulnerability.*']
    },
    {
      key: '2',
      name: 'Kernel Team',
      description: 'Core kernel development and testing',
      members: 12,
      lead: 'Bob Smith',
      status: 'Active',
      created: '2023-05-20',
      permissions: ['kernel.*', 'test.*']
    },
    {
      key: '3',
      name: 'QA Team',
      description: 'Quality assurance and test execution',
      members: 15,
      lead: 'Carol Davis',
      status: 'Active',
      created: '2023-04-10',
      permissions: ['test.read', 'results.*', 'coverage.*']
    }
  ]

  const userColumns = [
    {
      title: 'User',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 'bold' }}>{name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{record.email}</div>
          </div>
        </Space>
      )
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const colors = {
          'Admin': 'red',
          'Developer': 'blue',
          'Tester': 'green',
          'Viewer': 'gray'
        }
        return <Tag color={colors[role as keyof typeof colors]} icon={role === 'Admin' ? <CrownOutlined /> : undefined}>{role}</Tag>
      }
    },
    {
      title: 'Team',
      dataIndex: 'team',
      key: 'team'
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
      title: 'Last Login',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
      render: (text: string) => <span style={{ fontSize: '12px' }}>{text}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <Space>
          <Button size="small" icon={<EditOutlined />}>Edit</Button>
        </Space>
      )
    }
  ]

  const teamColumns = [
    {
      title: 'Team',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div>
          <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TeamOutlined />
            {name}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: 'Members',
      dataIndex: 'members',
      key: 'members',
      render: (count: number) => (
        <Space>
          <UserOutlined />
          <span>{count}</span>
        </Space>
      )
    },
    {
      title: 'Team Lead',
      dataIndex: 'lead',
      key: 'lead',
      render: (lead: string) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          {lead}
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
      title: 'Created',
      dataIndex: 'created',
      key: 'created',
      render: (text: string) => <span style={{ fontSize: '12px' }}>{text}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <Space>
          <Button size="small" icon={<EditOutlined />}>Edit</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <TeamOutlined />
          User & Team Management
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Manage users, teams, roles, and permissions for the testing platform
        </p>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Users"
              value={stats.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Users"
              value={stats.activeUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Teams"
              value={stats.totalTeams}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Teams"
              value={stats.activeTeams}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Tabs defaultActiveKey="users">
          <TabPane 
            tab={
              <span>
                <UserOutlined />
                Users
              </span>
            } 
            key="users"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>User Management</h3>
              <Button type="primary" icon={<PlusOutlined />}>
                Add User
              </Button>
            </div>
            <Table
              columns={userColumns}
              dataSource={users}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <TeamOutlined />
                Teams
              </span>
            } 
            key="teams"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>Team Management</h3>
              <Button type="primary" icon={<PlusOutlined />}>
                Create Team
              </Button>
            </div>
            <Table
              columns={teamColumns}
              dataSource={teams}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <SafetyCertificateOutlined />
                Permissions
              </span>
            } 
            key="permissions"
          >
            <div style={{ marginBottom: '16px' }}>
              <h3>Permission Management</h3>
              <p style={{ color: '#666' }}>
                Configure role-based access control and permissions for users and teams.
              </p>
            </div>
            
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="Role Definitions" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ padding: '8px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                      <div style={{ fontWeight: 'bold', color: '#ff4d4f' }}>
                        <CrownOutlined /> Admin
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        Full system access, user management, security configuration
                      </div>
                    </div>
                    <div style={{ padding: '8px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                      <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        <UserOutlined /> Developer
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        Test creation, execution, code analysis, performance monitoring
                      </div>
                    </div>
                    <div style={{ padding: '8px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                      <div style={{ fontWeight: 'bold', color: '#52c41a' }}>
                        <UserOutlined /> Tester
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        Test execution, result viewing, basic reporting
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="Permission Matrix" size="small">
                  <div style={{ fontSize: '12px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <th style={{ textAlign: 'left', padding: '8px' }}>Permission</th>
                          <th style={{ textAlign: 'center', padding: '8px' }}>Admin</th>
                          <th style={{ textAlign: 'center', padding: '8px' }}>Dev</th>
                          <th style={{ textAlign: 'center', padding: '8px' }}>Tester</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td style={{ padding: '4px 8px' }}>User Management</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#ff4d4f' }}>✗</td>
                          <td style={{ textAlign: 'center', color: '#ff4d4f' }}>✗</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px' }}>Test Creation</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#ff4d4f' }}>✗</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px' }}>Test Execution</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px' }}>Security Config</td>
                          <td style={{ textAlign: 'center', color: '#52c41a' }}>✓</td>
                          <td style={{ textAlign: 'center', color: '#faad14' }}>R</td>
                          <td style={{ textAlign: 'center', color: '#ff4d4f' }}>✗</td>
                        </tr>
                      </tbody>
                    </table>
                    <div style={{ marginTop: '8px', color: '#666' }}>
                      ✓ = Full Access, R = Read Only, ✗ = No Access
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default UserTeamManagement