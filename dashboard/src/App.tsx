import React, { Suspense } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Layout, Alert } from 'antd'
import DashboardLayout from './components/Layout/DashboardLayout'
import ErrorBoundary, { FeatureErrorBoundary } from './components/ErrorBoundary'
import { RouteGuard } from './components/RouteGuard'
import { SuspenseFallback } from './components/LoadingState'
import Dashboard from './pages/Dashboard'
import TestCases from './pages/TestCases'
import TestPlans from './pages/TestPlans'
import TestPlanDetails from './pages/TestPlanDetails'
import TestExecution from './pages/TestExecution'
import TestExecutionSimple from './pages/TestExecutionSimple'
import TestExecutionDebug from './pages/TestExecutionDebug'
import ExecutionDebug from './pages/ExecutionDebug'
import ExecutionMonitor from './pages/ExecutionMonitor'
import TestEnvironment from './pages/TestEnvironment'
import TestResults from './pages/TestResults'
import Coverage from './pages/Coverage'
import Performance from './pages/Performance'
import Settings from './pages/Settings'
import WorkflowDiagram from './pages/WorkflowDiagram'
import WorkflowDiagramSimple from './pages/WorkflowDiagramSimple'
import WorkflowBasic from './pages/WorkflowBasic'
import WorkflowTest from './pages/WorkflowTest'
import WorkflowMinimal from './pages/WorkflowMinimal'
import WorkflowFlowchartPage from './pages/WorkflowFlowchartPage'
import SimpleTest from './pages/SimpleTest'
import WorkflowDiagnostic from './components/WorkflowDiagnostic'
import MenuDebugger from './components/MenuDebugger'
import SyntaxHighlightTest from './components/SyntaxHighlightTest'
import DeploymentWorkflow from './pages/DeploymentWorkflow'
import Infrastructure from './pages/Infrastructure'
import TestSpecifications from './pages/TestSpecifications'
import DefectManagement from './pages/DefectManagement'
import SecurityDashboard from './pages/SecurityDashboard'
import VulnerabilityManagement from './pages/VulnerabilityManagement'
import AIModelManagement from './pages/AIModelManagement'
import AnalyticsInsights from './pages/AnalyticsInsights'
import ResourceMonitoring from './pages/ResourceMonitoring'
import UserTeamManagement from './pages/UserTeamManagement'
import IntegrationHub from './pages/IntegrationHub'
import AuditCompliance from './pages/AuditCompliance'
import BackupRecovery from './pages/BackupRecovery'
import NotificationCenter from './pages/NotificationCenter'
import KnowledgeBase from './pages/KnowledgeBase'


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
    <ErrorBoundary>
      <Suspense fallback={<SuspenseFallback />}>
        <Routes>
          {/* Login route - redirect back to dashboard in demo mode */}
          <Route path="/login" element={<LoginPlaceholder />} />
          
          {/* Main dashboard routes - flattened structure */}
          <Route path="/" element={<DashboardLayout><Dashboard /></DashboardLayout>} />
          <Route path="/test-cases" element={<DashboardLayout><TestCases /></DashboardLayout>} />
          <Route path="/test-plans" element={<DashboardLayout><TestPlans /></DashboardLayout>} />
          <Route path="/test-plans/:planId" element={<DashboardLayout><TestPlanDetails /></DashboardLayout>} />
          <Route path="/test-execution" element={<DashboardLayout><TestExecution /></DashboardLayout>} />
          <Route path="/test-execution-debug" element={<DashboardLayout><TestExecutionDebug /></DashboardLayout>} />
          {/* Backward compatibility redirect */}
          <Route path="/tests" element={<Navigate to="/test-execution-debug" replace />} />
          <Route path="/execution-debug" element={<DashboardLayout><ExecutionDebug /></DashboardLayout>} />
          <Route path="/execution-monitor" element={<DashboardLayout><ExecutionMonitor /></DashboardLayout>} />
          <Route path="/test-environment" element={<DashboardLayout><TestEnvironment /></DashboardLayout>} />
          {/* Backward compatibility redirect */}
          <Route path="/environment-management" element={<Navigate to="/test-environment" replace />} />
          <Route path="/results" element={<DashboardLayout><TestResults /></DashboardLayout>} />
          <Route path="/defects" element={<DashboardLayout><DefectManagement /></DashboardLayout>} />
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
          <Route path="/workflow-flowchart" element={<DashboardLayout><WorkflowFlowchartPage /></DashboardLayout>} />
          <Route path="/workflow-diagram" element={<Navigate to="/workflow-flowchart" replace />} />
          <Route path="/workflow-diagnostic" element={<DashboardLayout><WorkflowDiagnostic /></DashboardLayout>} />
          <Route path="/test-deployment" element={<DashboardLayout><DeploymentWorkflow /></DashboardLayout>} />
          <Route path="/test-deployment-workflow" element={<DashboardLayout><DeploymentWorkflow /></DashboardLayout>} />
          {/* Backward compatibility redirects */}
          <Route path="/deployment" element={<Navigate to="/test-deployment" replace />} />
          <Route path="/deployment-workflow" element={<Navigate to="/test-deployment" replace />} />
          
          {/* Infrastructure Management */}
          <Route path="/test-infrastructure" element={<DashboardLayout><Infrastructure /></DashboardLayout>} />
          <Route path="/infrastructure" element={<Navigate to="/test-infrastructure" replace />} />
          
          {/* Test Specifications - Property-based Testing */}
          <Route path="/test-specifications" element={<DashboardLayout><TestSpecifications /></DashboardLayout>} />
          <Route path="/specifications" element={<Navigate to="/test-specifications" replace />} />
          
          <Route path="/menu-debug" element={<DashboardLayout><MenuDebugger /></DashboardLayout>} />
          <Route path="/settings" element={<DashboardLayout><Settings /></DashboardLayout>} />
          <Route path="/syntax-test" element={<DashboardLayout><SyntaxHighlightTest /></DashboardLayout>} />
          
          {/* New Enhanced Sidebar Routes with Error Boundaries */}
          <Route path="/security-dashboard" element={
            <FeatureErrorBoundary featureName="Security Dashboard">
              <RouteGuard requiredPermissions={['read', 'manage_security']}>
                <DashboardLayout><SecurityDashboard /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/vulnerability-management" element={
            <FeatureErrorBoundary featureName="Vulnerability Management">
              <RouteGuard requiredPermissions={['read', 'manage_security']}>
                <DashboardLayout><VulnerabilityManagement /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/ai-model-management" element={
            <FeatureErrorBoundary featureName="AI Model Management">
              <RouteGuard requiredPermissions={['read', 'admin']}>
                <DashboardLayout><AIModelManagement /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/analytics-insights" element={
            <FeatureErrorBoundary featureName="Analytics & Insights">
              <RouteGuard requiredPermissions={['read']}>
                <DashboardLayout><AnalyticsInsights /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/resource-monitoring" element={
            <FeatureErrorBoundary featureName="Resource Monitoring">
              <RouteGuard requiredPermissions={['read', 'admin']}>
                <DashboardLayout><ResourceMonitoring /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/user-team-management" element={
            <FeatureErrorBoundary featureName="User & Team Management">
              <RouteGuard requiredPermissions={['manage_users', 'admin']}>
                <DashboardLayout><UserTeamManagement /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/integration-hub" element={
            <FeatureErrorBoundary featureName="Integration Hub">
              <RouteGuard requiredPermissions={['read', 'admin']}>
                <DashboardLayout><IntegrationHub /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/audit-compliance" element={
            <FeatureErrorBoundary featureName="Audit & Compliance">
              <RouteGuard requiredPermissions={['read', 'admin']}>
                <DashboardLayout><AuditCompliance /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/backup-recovery" element={
            <FeatureErrorBoundary featureName="Backup & Recovery">
              <RouteGuard requiredPermissions={['admin']}>
                <DashboardLayout><BackupRecovery /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/notification-center" element={
            <FeatureErrorBoundary featureName="Notification Center">
              <RouteGuard requiredPermissions={['read']}>
                <DashboardLayout><NotificationCenter /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          <Route path="/knowledge-base" element={
            <FeatureErrorBoundary featureName="Knowledge Base">
              <RouteGuard requiredPermissions={['read']}>
                <DashboardLayout><KnowledgeBase /></DashboardLayout>
              </RouteGuard>
            </FeatureErrorBoundary>
          } />
          
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
      </Suspense>
    </ErrorBoundary>
  )
}

export default App