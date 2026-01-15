import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error boundary component to catch and handle React errors
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Log to error reporting service
    this.logErrorToService(error, errorInfo);
  }

  private logErrorToService(error: Error, errorInfo: ErrorInfo): void {
    // TODO: Integrate with error reporting service (e.g., Sentry)
    console.error('Error logged:', {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });
  }

  private handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div style={{ padding: '50px' }}>
          <Result
            status="error"
            title="Something went wrong"
            subTitle={this.state.error?.message || 'An unexpected error occurred'}
            extra={[
              <Button type="primary" key="home" onClick={() => window.location.href = '/'}>
                Go Home
              </Button>,
              <Button key="retry" onClick={this.handleReset}>
                Try Again
              </Button>
            ]}
          >
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details style={{ whiteSpace: 'pre-wrap', textAlign: 'left', marginTop: '20px' }}>
                <summary>Error Details (Development Only)</summary>
                <p><strong>Error:</strong> {this.state.error?.toString()}</p>
                <p><strong>Stack:</strong></p>
                <pre>{this.state.error?.stack}</pre>
                <p><strong>Component Stack:</strong></p>
                <pre>{this.state.errorInfo.componentStack}</pre>
              </details>
            )}
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

/**
 * Feature-specific error boundary with custom messaging
 */
interface FeatureErrorBoundaryProps {
  children: ReactNode;
  featureName: string;
}

export const FeatureErrorBoundary: React.FC<FeatureErrorBoundaryProps> = ({
  children,
  featureName
}) => {
  const fallback = (
    <div style={{ padding: '50px' }}>
      <Result
        status="error"
        title={`${featureName} Error`}
        subTitle={`There was an error loading the ${featureName} feature. Please try again or contact support if the problem persists.`}
        extra={[
          <Button type="primary" key="home" onClick={() => window.location.href = '/'}>
            Go Home
          </Button>,
          <Button key="retry" onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        ]}
      />
    </div>
  );

  return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>;
};
