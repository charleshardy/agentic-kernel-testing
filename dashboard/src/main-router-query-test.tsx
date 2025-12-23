import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from 'react-query'
import { ConfigProvider, Button, Card, Alert, Space, Typography, Menu, Layout } from 'antd'
import { HomeOutlined, SettingOutlined } from '@ant-design/icons'

console.log('🚀 Starting Router + React Query test...')

const { Title, Text } = Typography
const { Header, Content, Sider } = Layout

// Simple QueryClient without complex retry logic
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false, // Disable retries
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
    mutations: {
      retry: false,
    },
  },
})

// Simple API call for testing
const fetchTestData = async () => {
  await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate delay
  return {
    message: 'React Query is working!',
    timestamp: new Date().toISOString(),
    data: [
      { id: 1, name: 'Test Item 1' },
      { id: 2, name: 'Test Item 2' },
      { id: 3, name: 'Test Item 3' },
    ]
  }
}

// Home page component
const HomePage: React.FC = () => {
  const { data, isLoading, error } = useQuery('testData', fetchTestData)
  
  return (
    <div>
      <Title level={2}>Home Page</Title>
      <Alert
        message="Router + React Query Test"
        description="Testing React Router navigation and React Query data fetching."
        type="success"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Card title="React Query Test" loading={isLoading}>
        {error ? (
          <Alert message="Error" description="Failed to fetch data" type="error" />
        ) : data ? (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>{data.message}</Text>
            <Text>Fetched at: {data.timestamp}</Text>
            <div>
              <Text>Data items:</Text>
              <ul>
                {data.data.map(item => (
                  <li key={item.id}>{item.name}</li>
                ))}
              </ul>
            </div>
          </Space>
        ) : null}
      </Card>
    </div>
  )
}

// Settings page component
const SettingsPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>Settings Page</Title>
      <Alert
        message="Settings"
        description="This is the settings page. Navigation is working correctly."
        type="info"
        showIcon
      />
    </div>
  )
}

// Main layout component
const AppLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Home',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ]
  
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200}>
        <div style={{ padding: '16px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong>Test App</Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <Title level={3} style={{ margin: 0, lineHeight: '64px' }}>
            Router + Query Test
          </Title>
        </Header>
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

// Main app component
const TestApp: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  )
}

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(<TestApp />)
  console.log('✅ Router + React Query test rendered successfully')
} catch (error) {
  console.error('❌ Error rendering Router + React Query test:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>Router + React Query Error</h1>
      <p>Failed to render components:</p>
      <pre>${error}</pre>
    </div>
  `
}