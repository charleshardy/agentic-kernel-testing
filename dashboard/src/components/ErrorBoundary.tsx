import React from 'react'
import { Alert, Button } from 'antd'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

interface ErrorBoundaryProps {
  children: React.ReactNode
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px' }}>
          <Alert
            message="Something went wrong"
            description={
              <div>
                <p>An error occurred while rendering this component.</p>
                <details style={{ marginTop: '10px' }}>
                  <summary>Error details</summary>
                  <pre style={{ marginTop: '10px', fontSize: '12px' }}>
                    {this.state.error?.message}
                    {'\n'}
                    {this.state.error?.stack}
                  </pre>
                </details>
              </div>
            }
            type="error"
            showIcon
            action={
              <Button
                size="small"
                onClick={() => {
                  this.setState({ hasError: false, error: undefined })
                  window.location.reload()
                }}
              >
                Reload Page
              </Button>
            }
          />
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary