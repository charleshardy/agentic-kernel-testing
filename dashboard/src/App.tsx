import React from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Layout, Alert } from 'antd'
import DashboardLayout from './components/Layout/DashboardLayout'
import Dashboard from './pages/Dashboard'
import TestCases from './pages/TestCases'
import TestPlans from './pages/TestPlans'
import TestPlanDetails from './pages/TestPlanDetails'
import TestExecution from './pages/TestExecution'
import TestExecutionSimple from './pages/TestExecutionSimple'
import TestExecutionDebug from './pages/TestExecutionDebug'
import ExecutionDebug from './pages/ExecutionDebug'
import ExecutionMonitor from './pages/ExecutionMonitor'
import EnvironmentManagement from './pages/EnvironmentManagement'
import TestResults from './pages/TestResults'
import Coverage from './pages/Coverage'
import Performance from './pages/Performance'
import Settings from './pages/Settings'
import WorkflowDiagram from './pages/WorkflowDiagram'
import WorkflowDiagramSimple from './pages/WorkflowDiagramSimple'
import WorkflowBasic from './pages/WorkflowBasic'
import WorkflowTest from './pages/WorkflowTest'
import WorkflowMinimal from './pages/WorkflowMinimal'
import SimpleTest from './pages/SimpleTest'
import WorkflowDiagnostic from './components/WorkflowDiagnostic'
import MenuDebugger from './components/MenuDebugger'
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
  const location = useLocation()
  
  return (
    <Routes>
      {/* Login route - redirect back to dashboard in demo mode */}
      <Route path="/login" element={<LoginPlaceholder />} />
      
      {/* Main dashboard routes - flattened structure */}
      <Route path="/" element={<DashboardLayout><Dashboard /></DashboardLayout>} />
      <Route path="/test-cases" element={<DashboardLayout><TestCases /></DashboardLayout>} />
      <Route path="/test-plans" element={<DashboardLayout><TestPlans /></DashboardLayout>} />
      <Route path="/test-plans/:planId" element={<DashboardLayout><TestPlanDetails /></DashboardLayout>} />
      <Route path="/test-execution" element={<DashboardLayout><TestExecution /></DashboardLayout>} />
      <Route path="/tests" element={<DashboardLayout><TestExecutionDebug /></DashboardLayout>} />
      <Route path="/execution-debug" element={<DashboardLayout><ExecutionDebug /></DashboardLayout>} />
      <Route path="/execution-monitor" element={<DashboardLayout><ExecutionMonitor /></DashboardLayout>} />
      <Route path="/environment-management" element={<DashboardLayout><EnvironmentManagement /></DashboardLayout>} />
      <Route path="/results" element={<DashboardLayout><TestResults /></DashboardLayout>} />
      <Route path="/coverage" element={<DashboardLayout><Coverage /></DashboardLayout>} />
      <Route path="/performance" element={<DashboardLayout><Performance /></DashboardLayout>} />
      <Route path="/workflow" element={
        <DashboardLayout>
          <SimpleTest />
        </DashboardLayout>
      } />
      <Route path="/workflow-minimal" element={<DashboardLayout><WorkflowMinimal /></DashboardLayout>} />
      <Route path="/workflow-test" element={<DashboardLayout><WorkflowTest /></DashboardLayout>} />
      <Route path="/workflow-simple" element={<DashboardLayout><WorkflowDiagramSimple /></DashboardLayout>} />
      <Route path="/workflow-basic" element={<DashboardLayout><WorkflowBasic /></DashboardLayout>} />
      <Route path="/workflow-full" element={<DashboardLayout><WorkflowBasic /></DashboardLayout>} />
      <Route path="/workflow-complex" element={<DashboardLayout><WorkflowDiagram /></DashboardLayout>} />
      <Route path="/workflow-diagnostic" element={<DashboardLayout><WorkflowDiagnostic /></DashboardLayout>} />
      <Route path="/menu-debug" element={<DashboardLayout><MenuDebugger /></DashboardLayout>} />
      <Route path="/settings" element={<DashboardLayout><Settings /></DashboardLayout>} />
      <Route path="/syntax-test" element={<DashboardLayout><SyntaxHighlightTest /></DashboardLayout>} />
      
      {/* Catch-all route */}
      <Route path="*" element={
        <DashboardLayout>
          <div style={{ padding: '24px' }}>
            <div style={{ background: '#fff2e8', padding: '16px', border: '1px solid #ffbb96', borderRadius: '6px' }}>
              <h2>🚨 Page Not Found</h2>
              <p><strong>Requested Path:</strong> {window.location.pathname}</p>
              <p><strong>Available Routes:</strong></p>
              <ul>
                <li>/workflow - Workflow overview</li>
                <li>/workflow-complex - Complete workflow diagram</li>
                <li>/workflow-minimal - Minimal workflow view</li>
                <li>/workflow-basic - Basic workflow view</li>
              </ul>
              <div style={{ marginTop: '16px' }}>
                <button onClick={() => window.location.href = '/workflow'}>
                  Go to Workflow Overview
                </button>
                <button onClick={() => window.location.href = '/'} style={{ marginLeft: '8px' }}>
                  Go to Dashboard
                </button>
              </div>
            </div>
          </div>
        </DashboardLayout>
      } />
    </Routes>
  )
}

export default App