import React from 'react'
import { Card, Typography, Space, Button, Alert, List, Tag } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import { RobotOutlined, BugOutlined, InfoCircleOutlined } from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

const MenuDebugger: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()

  const menuItems = [
    { key: '/', label: 'Dashboard', icon: '📊' },
    { key: '/workflow', label: 'Workflow Diagram', icon: '🤖' },
    { key: '/test-cases', label: 'Test Cases', icon: '🧪' },
    { key: '/tests', label: 'Test Execution', icon: '⚡' },
    { key: '/results', label: 'Test Results', icon: '📈' },
    { key: '/coverage', label: 'Coverage Analysis', icon: '📊' },
    { key: '/performance', label: 'Performance', icon: '🚀' },
    { key: '/settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={2}>
        <BugOutlined style={{ marginRight: '8px' }} />
        Menu & Navigation Debugger
      </Title>
      
      <Alert
        message="Menu Debugging Tool"
        description="This tool helps diagnose menu visibility and navigation issues."
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />

      <Card title="Current Navigation State" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text><strong>Current URL:</strong> {window.location.href}</Text>
          <Text><strong>Current Path:</strong> {location.pathname}</Text>
          <Text><strong>Browser:</strong> {navigator.userAgent}</Text>
          <Text><strong>Viewport:</strong> {window.innerWidth} x {window.innerHeight}</Text>
        </Space>
      </Card>

      <Card title="Menu Items Test" style={{ marginBottom: '16px' }}>
        <Paragraph>
          Click any menu item below to test navigation. If the sidebar menu is not visible, 
          you can use these buttons to navigate:
        </Paragraph>
        
        <List
          dataSource={menuItems}
          renderItem={(item) => (
            <List.Item>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <Space>
                  <span style={{ fontSize: '20px' }}>{item.icon}</span>
                  <Text strong>{item.label}</Text>
                  <Text type="secondary">({item.key})</Text>
                  {location.pathname === item.key && (
                    <Tag color="green">Current Page</Tag>
                  )}
                </Space>
                <Button 
                  type={item.key === '/workflow' ? 'primary' : 'default'}
                  onClick={() => {
                    console.log(`Navigating to: ${item.key}`)
                    navigate(item.key)
                  }}
                  style={item.key === '/workflow' ? {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  } : {}}
                >
                  Go to {item.label}
                </Button>
              </div>
            </List.Item>
          )}
        />
      </Card>

      <Card title="Workflow Diagram Quick Access" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="🤖 Workflow Diagram Access"
            description="Multiple ways to access the complete workflow diagram:"
            type="success"
            showIcon
          />
          
          <Space wrap>
            <Button 
              type="primary" 
              size="large"
              icon={<RobotOutlined />}
              onClick={() => navigate('/workflow')}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                height: '48px'
              }}
            >
              Open Workflow Diagram
            </Button>
            
            <Button 
              onClick={() => window.open('/workflow', '_blank')}
            >
              Open in New Tab
            </Button>
            
            <Button 
              onClick={() => {
                window.location.href = '/workflow'
              }}
            >
              Direct Navigation
            </Button>
          </Space>
        </Space>
      </Card>

      <Card title="Troubleshooting Steps">
        <List
          dataSource={[
            {
              title: 'Check Sidebar Visibility',
              description: 'Look for a collapsible sidebar on the left side of the screen. It should contain menu items.',
              action: 'Look for the hamburger menu icon (☰) to expand/collapse the sidebar'
            },
            {
              title: 'Browser Cache',
              description: 'Clear browser cache and hard refresh the page.',
              action: 'Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)'
            },
            {
              title: 'JavaScript Console',
              description: 'Check for JavaScript errors in the browser console.',
              action: 'Press F12 and look at the Console tab for any red error messages'
            },
            {
              title: 'Incognito Mode',
              description: 'Try opening the dashboard in an incognito/private browsing window.',
              action: 'This rules out browser extensions and cached data issues'
            },
            {
              title: 'Direct URL Access',
              description: 'Try accessing the workflow diagram directly via URL.',
              action: 'Navigate to: http://localhost:3000/workflow'
            }
          ]}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                avatar={<InfoCircleOutlined style={{ color: '#1890ff' }} />}
                title={item.title}
                description={
                  <div>
                    <Text>{item.description}</Text>
                    <br />
                    <Text strong style={{ color: '#722ed1' }}>Action: {item.action}</Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Card title="System Information">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text><strong>React Router:</strong> {typeof useNavigate !== 'undefined' ? '✅ Loaded' : '❌ Not loaded'}</Text>
          <Text><strong>Ant Design:</strong> {typeof Card !== 'undefined' ? '✅ Loaded' : '❌ Not loaded'}</Text>
          <Text><strong>Local Storage:</strong> {localStorage.getItem('auth_token') ? '✅ Has token' : '⚠️ No token'}</Text>
          <Text><strong>Session Storage:</strong> {Object.keys(sessionStorage).length} items</Text>
        </Space>
      </Card>
    </div>
  )
}

export default MenuDebugger