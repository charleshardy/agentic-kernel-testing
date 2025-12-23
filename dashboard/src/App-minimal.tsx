import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout, Typography, Alert } from 'antd'

const { Content } = Layout
const { Title } = Typography

// Minimal Dashboard component
const MinimalDashboard = () => (
  <div style={{ padding: '20px' }}>
    <Title level={2}>Dashboard</Title>
    <Alert
      message="Frontend Working!"
      description="The React frontend is now rendering successfully. This is a minimal version to test basic functionality."
      type="success"
      showIcon
      style={{ marginBottom: 16 }}
    />
    <p>Current time: {new Date().toLocaleString()}</p>
  </div>
)

// Minimal layout without complex dependencies
const MinimalLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Layout style={{ minHeight: '100vh' }}>
    <Layout.Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
      <Title level={3} style={{ margin: 0, lineHeight: '64px' }}>
        Agentic AI Testing System
      </Title>
    </Layout.Header>
    <Content style={{ padding: '24px', background: '#f0f2f5' }}>
      {children}
    </Content>
  </Layout>
)

function App() {
  return (
    <Routes>
      <Route path="/*" element={
        <MinimalLayout>
          <Routes>
            <Route path="/" element={<MinimalDashboard />} />
            <Route path="*" element={<MinimalDashboard />} />
          </Routes>
        </MinimalLayout>
      } />
    </Routes>
  )
}

export default App