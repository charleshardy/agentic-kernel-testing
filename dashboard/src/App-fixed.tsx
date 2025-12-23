import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Alert } from 'antd'
import DashboardLayout from './components/Layout/DashboardLayout-simple'
import Dashboard from './pages/Dashboard-fixed'
import TestCases from './pages/TestCases-working'
import TestExecutionDebugWorking from './pages/TestExecutionDebug-working'
import ExecutionDebug from './pages/ExecutionDebug'
// Import other pages as needed - we'll add them back gradually
// import TestExecution from './pages/TestExecution'
// import TestExecutionSimple from './pages/TestExecutionSimple'
import TestResults from './pages/TestResults'
import Coverage from './pages/Coverage'
import Performance from './pages/Performance'
import Settings from './pages/Settings'

// Simple placeholder components for now
const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <div style={{ padding: '20px' }}>
    <Alert
      message={`${title} Page`}
      description={`This is the ${title} page. Full functionality will be restored soon.`}
      type="info"
      showIcon
    />
  </div>
)

// Simple login placeholder component
const LoginPlaceholder = () => (
  <div style={{ padding: '50px', textAlign: 'center' }}>
    <Alert
      message="Demo Mode - No Authentication Required"
      description="This is a demo dashboard. Authentication is not implemented yet. Click below to return to the dashboard."
      type="info"
      showIcon
      action={
        <a href="/" style={{ textDecoration: 'none' }}>
          Return to Dashboard
        </a>
      }
    />
  </div>
)

function App() {
  return (
    <Routes>
      {/* Login route - redirect back to dashboard in demo mode */}
      <Route path="/login" element={<LoginPlaceholder />} />
      
      {/* Main dashboard routes */}
      <Route path="/*" element={
        <DashboardLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/test-cases" element={<TestCases />} />
            <Route path="/test-execution" element={<PlaceholderPage title="Test Execution" />} />
            <Route path="/tests" element={<TestExecutionDebugWorking />} />
            <Route path="/execution-debug" element={<ExecutionDebug />} />
            <Route path="/results" element={<TestResults />} />
            <Route path="/coverage" element={<Coverage />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/settings" element={<Settings />} />
            {/* Catch-all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </DashboardLayout>
      } />
    </Routes>
  )
}

export default App