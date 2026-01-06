import React, { useState, useEffect } from 'react'
import { Alert, Card, Button, Space, Typography, Collapse, Tag, Steps, Divider } from 'antd'
import { 
  ExclamationCircleOutlined,
  BugOutlined,
  ToolOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  BookOutlined,
  LinkOutlined
} from '@ant-design/icons'

const { Text, Title, Paragraph } = Typography
const { Panel } = Collapse
const { Step } = Steps

export interface DeploymentError {
  deployment_id: string
  stage: string
  error_type: string
  error_message: string
  timestamp: string
  environment_id: string
  plan_id: string
  retry_count: number
  validation_failures?: ValidationFailure[]
  step_failures?: StepFailure[]
  context?: Record<string, any>
}

export interface ValidationFailure {
  check_name: string
  error_message: string
  remediation_suggestions: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: 'network' | 'resource' | 'configuration' | 'security' | 'compatibility'
}

export interface StepFailure {
  step_name: string
  error_message: string
  duration_seconds?: number
  details?: Record<string, any>
}

interface DeploymentErrorDisplayProps {
  error: DeploymentError
  onRetry?: (deploymentId: string) => void
  onViewLogs?: (deploymentId: string) => void
  onContactSupport?: (error: DeploymentError) => void
  showDetailedDiagnostics?: boolean
}

const DeploymentErrorDisplay: React.FC<DeploymentErrorDisplayProps> = ({
  error,
  onRetry,
  onViewLogs,
  onContactSupport,
  showDetailedDiagnostics = true
}) => {
  const [expandedSections, setExpandedSections] = useState<string[]>([])
  const [remediationProgress, setRemediationProgress] = useState<Record<string, boolean>>({})

  // Get error severity based on type and stage
  const getErrorSeverity = (): 'low' | 'medium' | 'high' | 'critical' => {
    if (error.stage === 'readiness_validation' && error.validation_failures) {
      const maxSeverity = error.validation_failures.reduce((max, failure) => {
        const severityLevels = { low: 1, medium: 2, high: 3, critical: 4 }
        return severityLevels[failure.severity] > severityLevels[max] ? failure.severity : max
      }, 'low' as 'low' | 'medium' | 'high' | 'critical')
      return maxSeverity
    }
    
    if (error.error_type === 'connection_error' || error.error_type === 'timeout_error') {
      return 'high'
    }
    
    if (error.error_type === 'permission_error' || error.error_type === 'security_error') {
      return 'critical'
    }
    
    return 'medium'
  }

  // Get comprehensive remediation suggestions based on error type and context
  const getRemediationSuggestions = (): Array<{
    title: string
    description: string
    actions: string[]
    priority: 'immediate' | 'high' | 'medium' | 'low'
    category: string
    automated?: boolean
  }> => {
    const suggestions = []
    
    // Stage-specific suggestions
    if (error.stage === 'environment_connection') {
      suggestions.push({
        title: 'Environment Connection Issues',
        description: 'Failed to establish connection to the target environment',
        actions: [
          'Verify environment is running and accessible',
          'Check network connectivity and firewall rules',
          'Validate SSH keys or authentication credentials',
          'Ensure environment has sufficient resources available'
        ],
        priority: 'immediate' as const,
        category: 'connectivity'
      })
    }
    
    if (error.stage === 'artifact_preparation') {
      suggestions.push({
        title: 'Artifact Preparation Failures',
        description: 'Issues with test artifact validation or preparation',
        actions: [
          'Verify artifact checksums and integrity',
          'Check artifact dependencies are available',
          'Ensure artifacts have proper permissions and format',
          'Validate artifact content is not corrupted'
        ],
        priority: 'high' as const,
        category: 'artifacts'
      })
    }
    
    if (error.stage === 'dependency_installation') {
      suggestions.push({
        title: 'Dependency Installation Problems',
        description: 'Failed to install required dependencies or tools',
        actions: [
          'Check package repository availability',
          'Verify sufficient disk space for installations',
          'Ensure proper package manager configuration',
          'Check for conflicting package versions'
        ],
        priority: 'high' as const,
        category: 'dependencies'
      })
    }
    
    if (error.stage === 'instrumentation_setup') {
      suggestions.push({
        title: 'Instrumentation Configuration Issues',
        description: 'Problems setting up debugging or monitoring tools',
        actions: [
          'Verify kernel debugging features are available',
          'Check if KASAN/KTSAN modules are loaded',
          'Ensure sufficient memory for instrumentation overhead',
          'Validate kernel configuration supports requested features'
        ],
        priority: 'medium' as const,
        category: 'instrumentation'
      })
    }
    
    if (error.stage === 'readiness_validation' && error.validation_failures) {
      error.validation_failures.forEach(failure => {
        suggestions.push({
          title: `${failure.check_name} Validation Failure`,
          description: failure.error_message,
          actions: failure.remediation_suggestions,
          priority: failure.severity === 'critical' ? 'immediate' : 
                   failure.severity === 'high' ? 'high' : 'medium',
          category: failure.category
        })
      })
    }
    
    // Error type specific suggestions
    if (error.error_type === 'timeout_error') {
      suggestions.push({
        title: 'Timeout Resolution',
        description: 'Operation exceeded maximum allowed time',
        actions: [
          'Increase deployment timeout settings',
          'Check for resource constraints on target environment',
          'Verify network latency is within acceptable limits',
          'Consider breaking large deployments into smaller chunks'
        ],
        priority: 'high' as const,
        category: 'performance',
        automated: true
      })
    }
    
    if (error.error_type === 'permission_error') {
      suggestions.push({
        title: 'Permission and Access Issues',
        description: 'Insufficient permissions for deployment operations',
        actions: [
          'Verify deployment user has necessary privileges',
          'Check file and directory permissions',
          'Ensure SSH key has proper access rights',
          'Validate user is in required groups (sudo, docker, etc.)'
        ],
        priority: 'immediate' as const,
        category: 'security'
      })
    }
    
    // General suggestions based on retry count
    if (error.retry_count >= 2) {
      suggestions.push({
        title: 'Persistent Failure Resolution',
        description: 'Multiple retry attempts have failed',
        actions: [
          'Review deployment logs for patterns',
          'Check environment health and stability',
          'Consider manual intervention or environment reset',
          'Contact system administrator for assistance'
        ],
        priority: 'immediate' as const,
        category: 'escalation'
      })
    }
    
    return suggestions
  }

  // Get error category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'connectivity': return <LinkOutlined />
      case 'artifacts': return <BookOutlined />
      case 'dependencies': return <ToolOutlined />
      case 'instrumentation': return <BugOutlined />
      case 'security': return <ExclamationCircleOutlined />
      case 'performance': return <ClockCircleOutlined />
      case 'escalation': return <WarningOutlined />
      default: return <InfoCircleOutlined />
    }
  }

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'immediate': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'blue'
      case 'low': return 'green'
      default: return 'default'
    }
  }

  // Handle remediation action completion
  const markActionCompleted = (suggestionIndex: number, actionIndex: number) => {
    const key = `${suggestionIndex}-${actionIndex}`
    setRemediationProgress(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const suggestions = getRemediationSuggestions()
  const severity = getErrorSeverity()

  return (
    <div className="deployment-error-display">
      {/* Main Error Alert */}
      <Alert
        message={
          <Space>
            <ExclamationCircleOutlined />
            <Text strong>Deployment Failed: {error.stage.replace('_', ' ').toUpperCase()}</Text>
            <Tag color={getPriorityColor(severity)}>{severity.toUpperCase()}</Tag>
          </Space>
        }
        description={
          <div>
            <Paragraph>{error.error_message}</Paragraph>
            <Space>
              <Text type="secondary">Deployment ID: {error.deployment_id}</Text>
              <Text type="secondary">Environment: {error.environment_id}</Text>
              <Text type="secondary">Retry Count: {error.retry_count}</Text>
              <Text type="secondary">Time: {new Date(error.timestamp).toLocaleString()}</Text>
            </Space>
          </div>
        }
        type="error"
        showIcon={false}
        style={{ marginBottom: '16px' }}
      />

      {/* Quick Actions */}
      <Card title="Quick Actions" size="small" style={{ marginBottom: '16px' }}>
        <Space wrap>
          {onRetry && error.retry_count < 3 && (
            <Button 
              type="primary" 
              icon={<ReloadOutlined />}
              onClick={() => onRetry(error.deployment_id)}
            >
              Retry Deployment
            </Button>
          )}
          {onViewLogs && (
            <Button 
              icon={<BookOutlined />}
              onClick={() => onViewLogs(error.deployment_id)}
            >
              View Logs
            </Button>
          )}
          {onContactSupport && (
            <Button 
              icon={<ExclamationCircleOutlined />}
              onClick={() => onContactSupport(error)}
            >
              Contact Support
            </Button>
          )}
        </Space>
      </Card>

      {/* Remediation Suggestions */}
      <Card title="Remediation Guide" style={{ marginBottom: '16px' }}>
        <Collapse 
          activeKey={expandedSections}
          onChange={setExpandedSections}
          ghost
        >
          {suggestions.map((suggestion, suggestionIndex) => (
            <Panel
              header={
                <Space>
                  {getCategoryIcon(suggestion.category)}
                  <Text strong>{suggestion.title}</Text>
                  <Tag color={getPriorityColor(suggestion.priority)}>
                    {suggestion.priority.toUpperCase()}
                  </Tag>
                  {suggestion.automated && <Tag color="green">AUTO-FIXABLE</Tag>}
                </Space>
              }
              key={suggestionIndex.toString()}
            >
              <div style={{ marginBottom: '12px' }}>
                <Text>{suggestion.description}</Text>
              </div>
              
              <Title level={5}>Recommended Actions:</Title>
              <div>
                {suggestion.actions.map((action, actionIndex) => {
                  const actionKey = `${suggestionIndex}-${actionIndex}`
                  const isCompleted = remediationProgress[actionKey]
                  
                  return (
                    <div key={actionIndex} style={{ marginBottom: '8px' }}>
                      <Space>
                        <Button
                          size="small"
                          type={isCompleted ? "primary" : "default"}
                          icon={isCompleted ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                          onClick={() => markActionCompleted(suggestionIndex, actionIndex)}
                        />
                        <Text 
                          style={{ 
                            textDecoration: isCompleted ? 'line-through' : 'none',
                            color: isCompleted ? '#999' : 'inherit'
                          }}
                        >
                          {action}
                        </Text>
                      </Space>
                    </div>
                  )
                })}
              </div>
            </Panel>
          ))}
        </Collapse>
      </Card>
      {/* Detailed Diagnostics */}
      {showDetailedDiagnostics && (
        <Card title="Detailed Diagnostics" style={{ marginBottom: '16px' }}>
          <Collapse ghost>
            {/* Step Failures */}
            {error.step_failures && error.step_failures.length > 0 && (
              <Panel header="Step-by-Step Failure Analysis" key="steps">
                <Steps
                  direction="vertical"
                  size="small"
                  current={-1}
                >
                  {error.step_failures.map((step, index) => (
                    <Step
                      key={index}
                      title={step.step_name.replace('_', ' ').toUpperCase()}
                      description={
                        <div>
                          <Text type="danger">{step.error_message}</Text>
                          {step.duration_seconds && (
                            <div>
                              <Text type="secondary">
                                Duration: {step.duration_seconds}s
                              </Text>
                            </div>
                          )}
                          {step.details && Object.keys(step.details).length > 0 && (
                            <details style={{ marginTop: '8px' }}>
                              <summary>Step Details</summary>
                              <pre style={{ fontSize: '11px', marginTop: '4px' }}>
                                {JSON.stringify(step.details, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      }
                      status="error"
                      icon={<CloseCircleOutlined />}
                    />
                  ))}
                </Steps>
              </Panel>
            )}

            {/* Validation Failures */}
            {error.validation_failures && error.validation_failures.length > 0 && (
              <Panel header="Validation Failure Details" key="validation">
                <div>
                  {error.validation_failures.map((failure, index) => (
                    <Card 
                      key={index}
                      size="small" 
                      style={{ marginBottom: '12px' }}
                      title={
                        <Space>
                          <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                          <Text strong>{failure.check_name}</Text>
                          <Tag color={getPriorityColor(failure.severity)}>
                            {failure.severity.toUpperCase()}
                          </Tag>
                          <Tag>{failure.category.toUpperCase()}</Tag>
                        </Space>
                      }
                    >
                      <Text>{failure.error_message}</Text>
                      
                      {failure.remediation_suggestions.length > 0 && (
                        <div style={{ marginTop: '8px' }}>
                          <Text strong>Specific Remediation:</Text>
                          <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                            {failure.remediation_suggestions.map((suggestion, suggestionIndex) => (
                              <li key={suggestionIndex}>
                                <Text>{suggestion}</Text>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </Panel>
            )}

            {/* Technical Context */}
            {error.context && Object.keys(error.context).length > 0 && (
              <Panel header="Technical Context" key="context">
                <Paragraph 
                  code 
                  copyable 
                  style={{ 
                    fontSize: '11px',
                    maxHeight: '200px',
                    overflow: 'auto'
                  }}
                >
                  {JSON.stringify(error.context, null, 2)}
                </Paragraph>
              </Panel>
            )}
          </Collapse>
        </Card>
      )}

      {/* Error Pattern Recognition */}
      <Card title="Error Pattern Analysis" size="small">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Error Classification:</Text>
            <div style={{ marginTop: '4px' }}>
              <Tag color="blue">Stage: {error.stage}</Tag>
              <Tag color="orange">Type: {error.error_type}</Tag>
              <Tag color={getPriorityColor(severity)}>Severity: {severity}</Tag>
            </div>
          </div>
          
          <div>
            <Text strong>Recovery Recommendations:</Text>
            <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
              {error.retry_count === 0 && (
                <li><Text>This is the first failure - automatic retry is recommended</Text></li>
              )}
              {error.retry_count >= 1 && error.retry_count < 3 && (
                <li><Text>Multiple failures detected - review remediation steps before retry</Text></li>
              )}
              {error.retry_count >= 3 && (
                <li><Text type="danger">Maximum retries exceeded - manual intervention required</Text></li>
              )}
              {severity === 'critical' && (
                <li><Text type="danger">Critical error - immediate attention required</Text></li>
              )}
            </ul>
          </div>
          
          <Divider />
          
          <div style={{ fontSize: '12px', color: '#666' }}>
            <Text type="secondary">
              This error analysis is generated based on deployment stage, error type, and historical patterns. 
              For additional assistance, contact your system administrator or review the deployment documentation.
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default DeploymentErrorDisplay