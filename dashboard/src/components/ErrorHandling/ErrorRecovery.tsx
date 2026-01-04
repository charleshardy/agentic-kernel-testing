import React, { useState, useEffect, useCallback } from 'react'
import { Card, Button, Space, Typography, Alert, Progress, Spin, Tag } from 'antd'
import { 
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

export interface RetryPolicy {
  maxAttempts: number
  backoffStrategy: 'linear' | 'exponential'
  baseDelay: number
  maxDelay: number
}

export interface RecoveryAction {
  id: string
  label: string
  description: string
  action: () => Promise<void>
  icon?: React.ReactNode
  type?: 'primary' | 'default' | 'danger'
  requiresConfirmation?: boolean
}

interface ErrorRecoveryProps {
  error: Error
  retryPolicy?: RetryPolicy
  recoveryActions?: RecoveryAction[]
  onRetry?: () => Promise<void>
  onRecovered?: () => void
  autoRetry?: boolean
  showProgress?: boolean
}

const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxAttempts: 3,
  backoffStrategy: 'exponential',
  baseDelay: 1000,
  maxDelay: 10000
}

const ErrorRecovery: React.FC<ErrorRecoveryProps> = ({
  error,
  retryPolicy = DEFAULT_RETRY_POLICY,
  recoveryActions = [],
  onRetry,
  onRecovered,
  autoRetry = false,
  showProgress = true
}) => {
  const [isRetrying, setIsRetrying] = useState(false)
  const [retryAttempt, setRetryAttempt] = useState(0)
  const [retryProgress, setRetryProgress] = useState(0)
  const [lastRetryTime, setLastRetryTime] = useState<Date | null>(null)
  const [recoveryStatus, setRecoveryStatus] = useState<'idle' | 'retrying' | 'recovered' | 'failed'>('idle')

  const calculateDelay = useCallback((attempt: number): number => {
    if (retryPolicy.backoffStrategy === 'exponential') {
      return Math.min(
        retryPolicy.baseDelay * Math.pow(2, attempt),
        retryPolicy.maxDelay
      )
    } else {
      return Math.min(
        retryPolicy.baseDelay * (attempt + 1),
        retryPolicy.maxDelay
      )
    }
  }, [retryPolicy])

  const performRetry = useCallback(async () => {
    if (retryAttempt >= retryPolicy.maxAttempts) {
      setRecoveryStatus('failed')
      return
    }

    setIsRetrying(true)
    setRecoveryStatus('retrying')
    setRetryAttempt(prev => prev + 1)
    setLastRetryTime(new Date())

    try {
      if (onRetry) {
        await onRetry()
      }
      
      setRecoveryStatus('recovered')
      setIsRetrying(false)
      
      if (onRecovered) {
        onRecovered()
      }
    } catch (retryError) {
      console.error('Retry failed:', retryError)
      
      if (retryAttempt + 1 < retryPolicy.maxAttempts) {
        const delay = calculateDelay(retryAttempt)
        
        // Show countdown progress
        if (showProgress) {
          let progress = 0
          const progressInterval = setInterval(() => {
            progress += (100 / (delay / 100))
            setRetryProgress(Math.min(progress, 100))
            
            if (progress >= 100) {
              clearInterval(progressInterval)
              setRetryProgress(0)
            }
          }, 100)
        }
        
        setTimeout(() => {
          setIsRetrying(false)
          performRetry()
        }, delay)
      } else {
        setIsRetrying(false)
        setRecoveryStatus('failed')
      }
    }
  }, [retryAttempt, retryPolicy, onRetry, onRecovered, calculateDelay, showProgress])

  const handleManualRetry = () => {
    setRetryAttempt(0)
    setRecoveryStatus('idle')
    performRetry()
  }

  const handleRecoveryAction = async (action: RecoveryAction) => {
    try {
      setIsRetrying(true)
      await action.action()
      setRecoveryStatus('recovered')
      
      if (onRecovered) {
        onRecovered()
      }
    } catch (actionError) {
      console.error('Recovery action failed:', actionError)
      setRecoveryStatus('failed')
    } finally {
      setIsRetrying(false)
    }
  }

  // Auto-retry on mount if enabled
  useEffect(() => {
    if (autoRetry && recoveryStatus === 'idle') {
      performRetry()
    }
  }, [autoRetry, recoveryStatus, performRetry])

  const getStatusIcon = () => {
    switch (recoveryStatus) {
      case 'retrying': return <ClockCircleOutlined spin style={{ color: '#1890ff' }} />
      case 'recovered': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <WarningOutlined style={{ color: '#faad14' }} />
    }
  }

  const getStatusText = () => {
    switch (recoveryStatus) {
      case 'retrying': return 'Attempting recovery...'
      case 'recovered': return 'Successfully recovered'
      case 'failed': return 'Recovery failed'
      default: return 'Error detected'
    }
  }

  const getStatusColor = () => {
    switch (recoveryStatus) {
      case 'retrying': return 'processing'
      case 'recovered': return 'success'
      case 'failed': return 'error'
      default: return 'warning'
    }
  }

  if (recoveryStatus === 'recovered') {
    return (
      <Alert
        message="Recovery Successful"
        description="The error has been resolved and normal operation has resumed."
        type="success"
        showIcon
        icon={<CheckCircleOutlined />}
        style={{ marginBottom: '16px' }}
      />
    )
  }

  return (
    <Card 
      title={
        <Space>
          {getStatusIcon()}
          <Text strong>Error Recovery</Text>
          <Tag color={getStatusColor()}>{getStatusText()}</Tag>
        </Space>
      }
      style={{ marginBottom: '16px' }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Error Information */}
        <Alert
          message="Error Details"
          description={error.message}
          type="error"
          showIcon
        />

        {/* Retry Status */}
        {retryAttempt > 0 && (
          <div>
            <Text strong>Retry Status:</Text>
            <div style={{ marginTop: '8px' }}>
              <Space>
                <Text>Attempt {retryAttempt} of {retryPolicy.maxAttempts}</Text>
                {lastRetryTime && (
                  <Text type="secondary">
                    Last attempt: {lastRetryTime.toLocaleTimeString()}
                  </Text>
                )}
              </Space>
              
              {isRetrying && showProgress && retryProgress > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <Text style={{ fontSize: '12px' }}>
                    Next retry in {Math.ceil((100 - retryProgress) / 10)} seconds
                  </Text>
                  <Progress 
                    percent={retryProgress} 
                    size="small" 
                    showInfo={false}
                    style={{ marginTop: '4px' }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Manual Actions */}
        <div>
          <Text strong>Recovery Options:</Text>
          <div style={{ marginTop: '8px' }}>
            <Space wrap>
              {/* Manual Retry */}
              {onRetry && retryAttempt < retryPolicy.maxAttempts && (
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  loading={isRetrying}
                  onClick={handleManualRetry}
                  disabled={recoveryStatus === 'recovered'}
                >
                  {isRetrying ? 'Retrying...' : 'Retry Now'}
                </Button>
              )}

              {/* Custom Recovery Actions */}
              {recoveryActions.map(action => (
                <Button
                  key={action.id}
                  type={action.type || 'default'}
                  icon={action.icon}
                  loading={isRetrying}
                  onClick={() => handleRecoveryAction(action)}
                  disabled={recoveryStatus === 'recovered'}
                  title={action.description}
                >
                  {action.label}
                </Button>
              ))}

              {/* Reload Page as last resort */}
              <Button
                icon={<ReloadOutlined />}
                onClick={() => window.location.reload()}
                disabled={isRetrying}
              >
                Reload Page
              </Button>
            </Space>
          </div>
        </div>

        {/* Recovery Policy Information */}
        <div style={{ fontSize: '12px', color: '#666' }}>
          <Text type="secondary">
            Recovery Policy: {retryPolicy.maxAttempts} max attempts, 
            {retryPolicy.backoffStrategy} backoff strategy, 
            {retryPolicy.baseDelay}ms base delay
          </Text>
        </div>

        {/* Loading Spinner */}
        {isRetrying && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '8px' }}>
              <Text>Attempting to recover from error...</Text>
            </div>
          </div>
        )}
      </Space>
    </Card>
  )
}

export default ErrorRecovery