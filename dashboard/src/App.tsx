import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Alert } from 'antd'
import DashboardLayout from './components/Layout/DashboardLayout'
import Dashboard from './pages/Dashboard'
import TestCases from './pages/TestCases'
import TestExecution from './pages/TestExecution'
import TestExecutionSimple from './pages/TestExecutionSimple'
import TestExecutionDebug from './pages/TestExecutionDebug'
import ExecutionDebug from './pages/ExecutionDebug'
import TestResults from './pages/TestResults'
import Coverage from './pages/Coverage'
import Performance from './pages/Performance'
import Settings from './pages/Settings'
import SyntaxHighlightTest from './components/SyntaxHighlightTest'


const { Content } = Layout

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
            <Route path="/test-execution" element={<TestExecution />} />
            <Route path="/tests" element={<TestExecutionDebug />} />
            <Route path="/execution-debug" element={<ExecutionDebug />} />
            <Route path="/results" element={<TestResults />} />
            <Route path="/coverage" element={<Coverage />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/syntax-test" element={<SyntaxHighlightTest />} />
            {/* Catch-all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </DashboardLayout>
      } />
    </Routes>
  )
}

export default App