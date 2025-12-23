import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider, Button, Card, Alert, Space, Typography } from 'antd'
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons'

console.log('🚀 Starting Ant Design test...')

const { Title, Text } = Typography

// Test Ant Design components
const AntdTestApp: React.FC = () => {
  const [loading, setLoading] = React.useState(false)
  
  const handleClick = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 2000)
  }
  
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <div style={{ padding: '20px', background: '#f0f2f5', minHeight: '100vh' }}>
        <Title level={2}>Ant Design Test Working!</Title>
        
        <Alert
          message="Success"
          description="Ant Design components are loading correctly."
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Card title="Component Test" style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text>Current time: {new Date().toLocaleString()}</Text>
            
            <Space>
              <Button type="primary" onClick={handleClick} loading={loading}>
                {loading ? 'Loading...' : 'Test Button'}
              </Button>
              <Button icon={<CheckCircleOutlined />}>
                Icon Button
              </Button>
              <Button type="dashed" icon={<LoadingOutlined />}>
                Dashed Button
              </Button>
            </Space>
            
            <Alert
              message="Interactive Test"
              description={loading ? "Button is loading..." : "Click the button above to test loading state"}
              type={loading ? "warning" : "info"}
              showIcon
            />
          </Space>
        </Card>
        
        <Card title="Debug Info">
          <Text>React Version: {React.version}</Text><br />
          <Text>Location: {window.location.href}</Text><br />
          <Text>Timestamp: {Date.now()}</Text>
        </Card>
      </div>
    </ConfigProvider>
  )
}

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(<AntdTestApp />)
  console.log('✅ Ant Design test rendered successfully')
} catch (error) {
  console.error('❌ Error rendering Ant Design test:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>Ant Design Error</h1>
      <p>Failed to render Ant Design components:</p>
      <pre>${error}</pre>
    </div>
  `
}