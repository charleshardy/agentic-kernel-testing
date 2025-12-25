import React from 'react'
import { Card, Alert, Space, Typography, Button } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const WorkflowDiagnostic: React.FC = () => {
  const [diagnostics, setDiagnostics] = React.useState<string[]>([])

  const runDiagnostics = () => {
    const results: string[] = []
    
    try {
      // Check if React is loaded
      if (typeof React !== 'undefined') {
        results.push('✅ React is loaded')
      } else {
        results.push('❌ React is not loaded')
      }
      
      // Check if Ant Design is loaded
      if (typeof Card !== 'undefined') {
        results.push('✅ Ant Design components are loaded')
      } else {
        results.push('❌ Ant Design components are not loaded')
      }
      
      // Check if we can import workflow components
      try {
        const InteractiveWorkflowNode = require('../components/WorkflowComponents/InteractiveWorkflowNode')
        results.push('✅ InteractiveWorkflowNode component can be imported')
      } catch (error) {
        results.push(`❌ InteractiveWorkflowNode import failed: ${error}`)
      }
      
      try {
        const RealTimeWorkflowExecution = require('../components/WorkflowComponents/RealTimeWorkflowExecution')
        results.push('✅ RealTimeWorkflowExecution component can be imported')
      } catch (error) {
        results.push(`❌ RealTimeWorkflowExecution import failed: ${error}`)
      }
      
      try {
        const WorkflowSystemStatus = require('../components/WorkflowComponents/WorkflowSystemStatus')
        results.push('✅ WorkflowSystemStatus component can be imported')
      } catch (error) {
        results.push(`❌ WorkflowSystemStatus import failed: ${error}`)
      }
      
      // Check API connectivity
      fetch('/api/v1/health')
        .then(response => {
          if (response.ok) {
            results.push('✅ Backend API is accessible')
          } else {
            results.push(`⚠️ Backend API returned status: ${response.status}`)
          }
          setDiagnostics([...results])
        })
        .catch(error => {
          results.push(`❌ Backend API connection failed: ${error.message}`)
          setDiagnostics([...results])
        })
      
      setDiagnostics(results)
      
    } catch (error) {
      results.push(`❌ Diagnostic error: ${error}`)
      setDiagnostics(results)
    }
  }

  React.useEffect(() => {
    runDiagnostics()
  }, [])

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Workflow Diagram Diagnostics</Title>
      
      <Alert
        message="Diagnostic Information"
        description="This page helps diagnose issues with the Workflow Diagram components."
        type="info"
        showIcon
        style={{ marginBottom: '16px' }}
      />
      
      <Card title="Component Status" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {diagnostics.map((diagnostic, index) => (
            <Text key={index} style={{ 
              color: diagnostic.startsWith('✅') ? '#52c41a' : 
                     diagnostic.startsWith('⚠️') ? '#faad14' : '#ff4d4f'
            }}>
              {diagnostic}
            </Text>
          ))}
        </Space>
        
        <Button 
          onClick={runDiagnostics} 
          style={{ marginTop: '16px' }}
        >
          Run Diagnostics Again
        </Button>
      </Card>
      
      <Card title="Navigation Test">
        <Space direction="vertical">
          <Text>Current URL: {window.location.href}</Text>
          <Text>Expected workflow URL: {window.location.origin}/workflow</Text>
          <Button 
            type="primary" 
            onClick={() => window.location.href = '/workflow'}
          >
            Navigate to Workflow Diagram
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default WorkflowDiagnostic