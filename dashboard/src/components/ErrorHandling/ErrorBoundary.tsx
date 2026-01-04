import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography, Card, Space, Alert, Collapse } from 'antd'
import { 
  ExclamationCircleOutlined, 
  ReloadOutlined, 
  BugOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons'

const { Text, Paragraph } = Typography
const { Panel } = Collapse

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    })

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // In production, you might want to send this to an error reporting service
    // Example: Sentry.captureException(error, { contexts: { react: errorInfo } })
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      const { error, errorInfo, errorId } = this.state
      const isDevelopment = process.env.NODE_ENV === 'development'

      return (
        <Card style={{ margin: '20px', maxWidth: '800px' }}>
          <Result
            status="error"
            icon={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
            title="Something went wrong"
            subTitle={
              <Space direction="vertical" size="small">
                <Text>
                  An unexpected error occurred while rendering this component.
                </Text>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Error ID: {errorId}
                </Text>
              </Space>
            }
            extra={
              <Space>
                <Button 
                  type="primary" 
                  icon={<ReloadOutlined />}
                  onClick={this.handleRetry}
                >
                  Try Again
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={this.handleReload}
                >
                  Reload Page
                </Button>
              </Space>
            }
          />

          {(isDevelopment || this.props.showDetails) && error && (
            <Alert
              message="Error Details"
              type="error"
              showIcon
              icon={<BugOutlined />}
              style={{ marginTop: '16px' }}
              description={
                <Collapse ghost>
                  <Panel 
                    header="Click to view technical details" 
                    key="1"
                    extra={<InfoCircleOutlined />}
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <Text strong>Error Message:</Text>
                        <Paragraph code copyable style={{ marginTop: '4px' }}>
                          {error.message}
                        </Paragraph>
                      </div>
                      
                      <div>
                        <Text strong>Stack Trace:</Text>
                        <Paragraph 
                          code 
                          copyable 
                          style={{ 
                            marginTop: '4px',
                            maxHeight: '200px',
                            overflow: 'auto',
                            fontSize: '11px'
                          }}
                        >
                          {error.stack}
                        </Paragraph>
                      </div>

                      {errorInfo && (
                        <div>
                          <Text strong>Component Stack:</Text>
                          <Paragraph 
                            code 
                            copyable 
                            style={{ 
                              marginTop: '4px',
                              maxHeight: '200px',
                              overflow: 'auto',
                              fontSize: '11px'
                            }}
                          >
                            {errorInfo.componentStack}
                          </Paragraph>
                        </div>
                      )}
                    </Space>
                  </Panel>
                </Collapse>
              }
            />
          )}
        </Card>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary