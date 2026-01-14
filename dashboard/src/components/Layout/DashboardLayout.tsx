import React, { useEffect, useState } from 'react'
import { Layout, Avatar, Dropdown, Badge, Space, Typography, Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  WifiOutlined,
  DisconnectOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useDashboardStore } from '../../store'
import EnhancedSidebar from './EnhancedSidebar'
import { SidebarProvider } from '../../contexts/SidebarContext'
import { NotificationCounts, PERMISSIONS } from '../../types/sidebar'

const { Header, Content } = Layout
const { Text } = Typography

interface DashboardLayoutProps {
  children: React.ReactNode
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const { isConnected, setConnectionStatus } = useDashboardStore()

  // Mock user permissions - in a real app, this would come from authentication
  const userPermissions = [
    PERMISSIONS.DASHBOARD.READ,
    PERMISSIONS.SECURITY.READ,
    PERMISSIONS.AI_MODELS.READ,
    PERMISSIONS.USERS.READ,
    PERMISSIONS.TEAMS.READ,
    PERMISSIONS.AUDIT.READ,
    PERMISSIONS.COMPLIANCE.READ,
    PERMISSIONS.NOTIFICATIONS.READ,
    PERMISSIONS.KNOWLEDGE.READ,
    PERMISSIONS.SETTINGS.READ,
    // Add more permissions as needed
    'specifications.read',
    'test-cases.read',
    'test-plans.read',
    'test-execution.read',
    'test-results.read',
    'defects.read',
    'coverage.read',
    'performance.read',
    'environment.read',
    'infrastructure.read',
    'deployment.read',
    'resources.read',
    'integrations.read',
    'backup.read'
  ]

  // Mock notification counts - in a real app, this would come from API
  const [notificationCounts, setNotificationCounts] = useState<NotificationCounts>({
    security: 3,
    vulnerabilities: 7,
    defects: 12,
    aiModels: 1,
    resources: 2,
    integrations: 0,
    notifications: 5,
    total: 30
  })

  // Analytics event handler
  const handleAnalyticsEvent = (event: string, data: any) => {
    console.log('Analytics Event:', event, data)
    // In a real app, this would send data to analytics service
  }

  useEffect(() => {
    // Check API connection status (HTTP-based, not WebSocket)
    const checkConnection = async () => {
      try {
        // Try proxy first, then direct connection
        let response = await fetch('/api/v1/health').catch(() => null)
        if (!response || !response.ok) {
          // Fallback to direct backend connection
          response = await fetch('http://localhost:8000/api/v1/health')
        }
        setConnectionStatus(response.ok)
      } catch (error) {
        console.log('API connection check failed:', error)
        setConnectionStatus(false)
      }
    }
    
    // Initial check
    checkConnection()
    
    // Check connection every 10 seconds
    const interval = setInterval(checkConnection, 10000)
    
    return () => {
      clearInterval(interval)
    }
  }, [setConnectionStatus])

  // Simulate notification updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Randomly update notification counts to demonstrate real-time updates
      if (Math.random() > 0.8) {
        setNotificationCounts(prev => ({
          ...prev,
          notifications: (prev.notifications || 0) + 1,
          total: (prev.total || 0) + 1
        }))
      }
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

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

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      localStorage.removeItem('auth_token')
      // In demo mode, just stay on the dashboard
      console.log('Logout clicked - staying in demo mode')
    }
  }

  return (
    <SidebarProvider userId="demo-user">
      <Layout className="dashboard-layout">
        <EnhancedSidebar
          collapsed={collapsed}
          onCollapse={setCollapsed}
          userPermissions={userPermissions}
          notificationCounts={notificationCounts}
        />

        <Layout style={{ marginLeft: collapsed ? 64 : 280 }}>
          <Header className="dashboard-header" style={{
            background: '#fff',
            padding: '0 24px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <Space>
              <Text strong style={{ fontSize: '16px' }}>Agentic AI Testing System</Text>
              <div className="real-time-indicator" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginLeft: '24px'
              }}>
                {isConnected ? (
                  <>
                    <WifiOutlined style={{ color: '#52c41a' }} />
                    <span style={{ color: '#52c41a', fontSize: '12px' }}>Connected</span>
                    <div className="real-time-dot" style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: '#52c41a',
                      animation: 'pulse 2s infinite'
                    }} />
                  </>
                ) : (
                  <>
                    <DisconnectOutlined style={{ color: '#ff4d4f' }} />
                    <span style={{ color: '#ff4d4f', fontSize: '12px' }}>Disconnected</span>
                  </>
                )}
              </div>
            </Space>

            <Space>
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => navigate('/notification-center')}
                style={{ position: 'relative' }}
              >
                <Badge 
                  count={notificationCounts.total} 
                  size="small"
                  style={{ 
                    position: 'absolute',
                    top: '8px',
                    right: '8px'
                  }}
                />
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

          <Content className="dashboard-content" style={{
            margin: '24px',
            padding: '24px',
            background: '#fff',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)',
            overflow: 'auto'
          }}>
            {children}
            
            {/* Floating Workflow Button - Always Visible */}
            <div style={{
              position: 'fixed',
              bottom: '24px',
              right: '24px',
              zIndex: 1000
            }}>
              <Button
                type="primary"
                size="large"
                shape="round"
                icon={<RobotOutlined />}
                onClick={() => {
                  console.log('🤖 Floating button clicked - navigating to workflow!')
                  navigate('/workflow')
                }}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  boxShadow: '0 4px 16px rgba(102, 126, 234, 0.4)',
                  height: '56px',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                Workflow Diagram
              </Button>
            </div>
          </Content>
        </Layout>

        {/* Global Styles */}
        <style jsx global>{`
          .dashboard-layout {
            min-height: 100vh;
          }
          
          .dashboard-header {
            position: sticky;
            top: 0;
            z-index: 100;
          }
          
          @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
          }
          
          .ant-layout-content {
            transition: margin-left 0.2s ease;
          }
          
          /* Responsive adjustments */
          @media (max-width: 768px) {
            .dashboard-content {
              margin: 16px !important;
              padding: 16px !important;
            }
          }
        `}</style>
      </Layout>
    </SidebarProvider>
  )
}
}

export default DashboardLayout