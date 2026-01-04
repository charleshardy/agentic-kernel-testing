import React, { useState, useEffect } from 'react'
import { Alert, Button, Space, Typography, Collapse, Tag } from 'antd'
import { 
  ExclamationCircleOutlined,
  CloseOutlined,
  ReloadOutlined,
  BugOutlined,
  InfoCircleOutlined,
  WarningOutlined
} from '@ant-design/icons'

const { Text, Paragraph } = Typography
const { Panel } = Collapse

export interface ErrorDetails {
  id: string
  message: string
  type: 'network' | 'allocation' | 'environment' | 'user_input' | 'system'
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: Date
  context?: Record<string, any>
  stack?: string
  suggestedActions?: string[]
  retryable?: boolean
  diagnosticInfo?: {
    endpoint?: string
    statusCode?: number
    responseTime?: number
    userAgent?: string
    environmentId?: string
    testId?: string
  }
}

interface ErrorAlertProps {
  error: ErrorDetails
  onDismiss?: (errorId: string) => void
  onRetry?: (errorId: string) => void
  showDetails?: boolean
  autoHide?: boolean
  autoHideDelay?: number
  compact?: boolean
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({
  error,
  onDismiss,
  onRetry,
  showDetails = false,
  autoHide = false,
  autoHideDelay = 5000,
  compact = false
}) => {
  const [visible, setVisible] = useState(true)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  useEffect(() => {
    if (autoHide && error.severity !== 'critical') {
      const timer = setTimeout(() => {
        handleDismiss()
      }, autoHideDelay)

      return () => clearTimeout(timer)
    }
  }, [autoHide, autoHideDelay, error.severity])

  const handleDismiss = () => {
    setVisible(false)
    if (onDismiss) {
      onDismiss(error.id)
    }
  }

  const handleRetry = () => {
    if (onRetry) {
      onRetry(error.id)
    }
  }

  const getAlertType = () => {
    switch (error.severity) {
      case 'critical': return 'error'
      case 'high': return 'error'
      case 'medium': return 'warning'
      case 'low': return 'info'
      default: return 'warning'
    }
  }

  const getErrorTypeColor = () => {
    switch (error.type) {
      case 'network': return 'red'
      case 'allocation': return 'orange'
      case 'environment': return 'purple'
      case 'user_input': return 'blue'
      case 'system': return 'red'
      default: return 'default'
    }
  }

  const getErrorTypeLabel = () => {
    switch (error.type) {
      case 'network': return 'Network Error'
      case 'allocation': return 'Allocation Error'
      case 'environment': return 'Environment Error'
      case 'user_input': return 'Input Error'
      case 'system': return 'System Error'
      default: return 'Error'
    }
  }

  const getSeverityIcon = () => {
    switch (error.severity) {
      case 'critical': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'high': return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />
      case 'medium': return <WarningOutlined style={{ color: '#faad14' }} />
      case 'low': return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      default: return <WarningOutlined />
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleString()
  }

  if (!visible) {
    return null
  }

  const alertMessage = (
    <Space>
      {getSeverityIcon()}
      <Text strong>{getErrorTypeLabel()}</Text>
      <Tag color={getErrorTypeColor()}>{error.type.toUpperCase()}</Tag>
      <Tag color={error.severity === 'critical' ? 'red' : 'orange'}>
        {error.severity.toUpperCase()}
      </Tag>
    </Space>
  )

  const alertDescription = compact ? error.message : (
    <Space direction="vertical" size="small" style={{ width: '100%' }}>
      <Text>{error.message}</Text>
      
      {error.suggestedActions && error.suggestedActions.length > 0 && (
        <div>
          <Text strong>Suggested Actions:</Text>
          <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
            {error.suggestedActions.map((action, index) => (
              <li key={index}>
                <Text>{action}</Text>
              </li>
            ))}
          </ul>
        </div>
      )}

      {error.diagnosticInfo && (
        <div>
          <Text strong>Diagnostic Information:</Text>
          <Space wrap style={{ marginTop: '4px' }}>
            {error.diagnosticInfo.endpoint && (
              <Tag>Endpoint: {error.diagnosticInfo.endpoint}</Tag>
            )}
            {error.diagnosticInfo.statusCode && (
              <Tag color={error.diagnosticInfo.statusCode >= 400 ? 'red' : 'green'}>
                Status: {error.diagnosticInfo.statusCode}
              </Tag>
            )}
            {error.diagnosticInfo.responseTime && (
              <Tag>Response Time: {error.diagnosticInfo.responseTime}ms</Tag>
            )}
            {error.diagnosticInfo.environmentId && (
              <Tag>Environment: {error.diagnosticInfo.environmentId}</Tag>
            )}
            {error.diagnosticInfo.testId && (
              <Tag>Test: {error.diagnosticInfo.testId}</Tag>
            )}
          </Space>
        </div>
      )}

      <Text type="secondary" style={{ fontSize: '12px' }}>
        Error ID: {error.id} | Time: {formatTimestamp(error.timestamp)}
      </Text>

      {(showDetails || showTechnicalDetails) && (error.stack || error.context) && (
        <Collapse ghost size="small">
          <Panel 
            header="Technical Details" 
            key="1"
            extra={<BugOutlined />}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {error.context && Object.keys(error.context).length > 0 && (
                <div>
                  <Text strong>Context:</Text>
                  <Paragraph 
                    code 
                    copyable 
                    style={{ 
                      marginTop: '4px',
                      fontSize: '11px',
                      maxHeight: '150px',
                      overflow: 'auto'
                    }}
                  >
                    {JSON.stringify(error.context, null, 2)}
                  </Paragraph>
                </div>
              )}

              {error.stack && (
                <div>
                  <Text strong>Stack Trace:</Text>
                  <Paragraph 
                    code 
                    copyable 
                    style={{ 
                      marginTop: '4px',
                      fontSize: '11px',
                      maxHeight: '150px',
                      overflow: 'auto'
                    }}
                  >
                    {error.stack}
                  </Paragraph>
                </div>
              )}
            </Space>
          </Panel>
        </Collapse>
      )}
    </Space>
  )

  const alertActions = (
    <Space>
      {error.retryable && onRetry && (
        <Button 
          size="small" 
          type="primary" 
          icon={<ReloadOutlined />}
          onClick={handleRetry}
        >
          Retry
        </Button>
      )}
      {!compact && !showTechnicalDetails && (showDetails || error.stack || error.context) && (
        <Button 
          size="small" 
          icon={<BugOutlined />}
          onClick={() => setShowTechnicalDetails(true)}
        >
          Details
        </Button>
      )}
      <Button 
        size="small" 
        icon={<CloseOutlined />}
        onClick={handleDismiss}
      >
        Dismiss
      </Button>
    </Space>
  )

  return (
    <Alert
      message={alertMessage}
      description={alertDescription}
      type={getAlertType()}
      showIcon={false}
      action={alertActions}
      closable={false}
      style={{ 
        marginBottom: '8px',
        border: error.severity === 'critical' ? '2px solid #ff4d4f' : undefined
      }}
    />
  )
}

export default ErrorAlert