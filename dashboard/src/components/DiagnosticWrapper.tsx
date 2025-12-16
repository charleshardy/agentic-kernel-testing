import React from 'react'
import { Alert, Card, Space, Typography } from 'antd'

const { Text, Title } = Typography

interface DiagnosticWrapperProps {
  children: React.ReactNode
  componentName: string
}

const DiagnosticWrapper: React.FC<DiagnosticWrapperProps> = ({ children, componentName }) => {
  const [error, setError] = React.useState<Error | null>(null)

  React.useEffect(() => {
    console.log(`${componentName} component mounted successfully`)
    
    // Check for common issues
    const diagnostics = {
      reactQuery: typeof window !== 'undefined' && (window as any).ReactQueryDevtools,
      antd: typeof window !== 'undefined' && (window as any).antd,
      router: typeof window !== 'undefined' && window.location,
    }
    
    console.log(`${componentName} diagnostics:`, diagnostics)
  }, [componentName])

  if (error) {
    return (
      <Card style={{ margin: '20px' }}>
        <Alert
          message={`Error in ${componentName}`}
          description={
            <div>
              <Text>Component failed to render properly.</Text>
              <details style={{ marginTop: '10px' }}>
                <summary>Error details</summary>
                <pre style={{ fontSize: '12px', marginTop: '10px' }}>
                  {error.message}
                  {'\n'}
                  {error.stack}
                </pre>
              </details>
            </div>
          }
          type="error"
          showIcon
        />
      </Card>
    )
  }

  try {
    return <>{children}</>
  } catch (err) {
    console.error(`Error rendering ${componentName}:`, err)
    setError(err as Error)
    return null
  }
}

export default DiagnosticWrapper