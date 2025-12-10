import React, { useEffect, useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Badge, Space, Typography, Button } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from '@ant-design/icons'
import { useDashboardStore } from '../../store'
import webSocketService from '../../services/websocket'

const { Header, Sider, Content } = Layout
const { Text } = Typography

interface DashboardLayoutProps {
  children: React.ReactNode
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const { isConnected, setConnectionStatus } = useDashboardStore()

  useEffect(() => {
    // Initialize WebSocket connection
    webSocketService.connect()
    
    // Monitor connection status
    const checkConnection = () => {
      setConnectionStatus(webSocketService.isConnected())
    }
    
    const interval = setInterval(checkConnection, 5000)
    checkConnection()
    
    return () => {
      clearInterval(interval)
      webSocketService.disconnect()
    }
  }, [setConnectionStatus])

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/tests',
      icon: <ExperimentOutlined />,
      label: 'Test Execution',
    },
    {
      key: '/results',
      icon: <BarChartOutlined />,
      label: 'Test Results',
    },
    {
      key: '/coverage',
      icon: <PieChartOutlined />,
      label: 'Coverage Analysis',
    },
    {
      key: '/performance',
      icon: <LineChartOutlined />,
      label: 'Performance',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      localStorage.removeItem('auth_token')
      navigate('/login')
    }
  }

  return (
    <Layout className="dashboard-layout">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        width={250}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          padding: '16px', 
          textAlign: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <div className="dashboard-logo">
            {collapsed ? 'ATS' : 'Agentic Testing System'}
          </div>
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 250 }}>
        <Header className="dashboard-header">
          <Space>
            <Text strong>Agentic AI Testing System</Text>
            <div className="real-time-indicator">
              {isConnected ? (
                <>
                  <WifiOutlined style={{ color: '#52c41a' }} />
                  <span>Connected</span>
                  <div className="real-time-dot" />
                </>
              ) : (
                <>
                  <DisconnectOutlined style={{ color: '#ff4d4f' }} />
                  <span>Disconnected</span>
                </>
              )}
            </div>
          </Space>

          <Space>
            <Button
              type="text"
              icon={<BellOutlined />}
              onClick={() => {/* Handle notifications */}}
            >
              <Badge count={0} />
            </Button>
            
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>Admin User</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content className="dashboard-content">
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default DashboardLayout