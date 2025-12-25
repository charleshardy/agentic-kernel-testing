import React, { useState, useEffect } from 'react'
import { Card, Button, Alert, Spin } from 'antd'

const TestCases: React.FC = () => {
  const [step, setStep] = useState(0)
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    const logMessage = `[${timestamp}] ${message}`
    console.log(logMessage)
    setLogs(prev => [...prev, logMessage])
  }

  useEffect(() => {
    addLog('🚀 TestCases-debug component mounted')
    setStep(1)
  }, [])

  const testStep1 = () => {
    addLog('🧪 Step 1: Testing basic functionality')
    setStep(2)
  }

  const testStep2 = async () => {
    addLog('🧪 Step 2: Testing API health check')
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/health')
      const result = await response.json()
      addLog(`✅ Health check successful: ${result.data.status}`)
      setData(result)
      setStep(3)
    } catch (err: any) {
      addLog(`❌ Health check failed: ${err.message}`)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const testStep3 = async () => {
    addLog('🧪 Step 3: Testing authentication')
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      })
      const result = await response.json()
      addLog(`✅ Auth successful: ${result.success}`)
      setStep(4)
    } catch (err: any) {
      addLog(`❌ Auth failed: ${err.message}`)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const testStep4 = async () => {
    addLog('🧪 Step 4: Testing test cases fetch')
    setLoading(true)
    setError(null)
    
    try {
      // Get token first
      const authResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      })
      const authResult = await authResponse.json()
      const token = authResult.data.access_token
      
      // Fetch tests
      const testsResponse = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      const testsResult = await testsResponse.json()
      addLog(`✅ Tests fetch successful: ${testsResult.data.tests.length} tests`)
      setData(testsResult.data.tests)
      setStep(5)
    } catch (err: any) {
      addLog(`❌ Tests fetch failed: ${err.message}`)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <h1>Test Cases - Debug Mode</h1>
      
      <div style={{ marginBottom: 16 }}>
        <Button 
          onClick={testStep1} 
          disabled={step < 1}
          type={step >= 2 ? 'default' : 'primary'}
        >
          Step 1: Basic Test
        </Button>
        <Button 
          onClick={testStep2} 
          disabled={step < 2}
          loading={loading && step === 2}
          type={step >= 3 ? 'default' : step === 2 ? 'primary' : 'default'}
          style={{ marginLeft: 8 }}
        >
          Step 2: Health Check
        </Button>
        <Button 
          onClick={testStep3} 
          disabled={step < 3}
          loading={loading && step === 3}
          type={step >= 4 ? 'default' : step === 3 ? 'primary' : 'default'}
          style={{ marginLeft: 8 }}
        >
          Step 3: Auth Test
        </Button>
        <Button 
          onClick={testStep4} 
          disabled={step < 4}
          loading={loading && step === 4}
          type={step >= 5 ? 'default' : step === 4 ? 'primary' : 'default'}
          style={{ marginLeft: 8 }}
        >
          Step 4: Fetch Tests
        </Button>
      </div>

      {error && (
        <Alert 
          message="Error" 
          description={error}
          type="error" 
          style={{ marginBottom: 16 }}
        />
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <div>Loading step {step}...</div>
        </div>
      )}

      <Card title="Debug Logs" style={{ marginBottom: 16 }}>
        <div style={{ 
          backgroundColor: '#f5f5f5', 
          padding: '12px', 
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '12px',
          maxHeight: '300px',
          overflow: 'auto'
        }}>
          {logs.map((log, index) => (
            <div key={index}>{log}</div>
          ))}
        </div>
      </Card>

      {data && (
        <Card title="Data">
          <pre style={{ fontSize: '12px', overflow: 'auto' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  )
}

export default TestCases