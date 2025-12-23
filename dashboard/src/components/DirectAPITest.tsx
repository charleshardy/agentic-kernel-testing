import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Alert, Typography } from 'antd'
import apiService from '../services/api'

const { Text, Paragraph } = Typography

interface DirectAPITestProps {}

const DirectAPITest: React.FC<DirectAPITestProps> = () => {
  const [testResults, setTestResults] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const addResult = (message: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`])
  }

  const clearResults = () => {
    setTestResults([])
  }

  const testDirectAPI = async () => {
    setIsLoading(true)
    addResult('🔍 Starting direct API test...')

    try {
      // Test 1: Health check
      addResult('1️⃣ Testing health endpoint...')
      const health = await fetch('http://localhost:8000/api/v1/health')
      const healthData = await health.json()
      if (health.ok) {
        addResult(`✅ Health check OK: ${healthData.message}`)
      } else {
        addResult(`❌ Health check failed: ${health.status}`)
      }

      // Test 2: Login
      addResult('2️⃣ Testing login...')
      const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      })
      const loginData = await loginResponse.json()
      
      if (loginResponse.ok && loginData.success) {
        const token = loginData.data.access_token
        addResult(`✅ Login successful, token: ${token.substring(0, 20)}...`)

        // Test 3: Generate AI test
        addResult('3️⃣ Generating AI test...')
        const genResponse = await fetch('http://localhost:8000/api/v1/tests/generate-from-function?function_name=direct_test&file_path=test.c&subsystem=test&max_tests=1', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const genData = await genResponse.json()
        
        if (genResponse.ok) {
          addResult(`✅ AI test generated: ${genData.data.execution_plan_id}`)

          // Test 4: Check active executions
          addResult('4️⃣ Checking active executions...')
          const execResponse = await fetch('http://localhost:8000/api/v1/execution/active', {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          const execData = await execResponse.json()
          
          if (execResponse.ok) {
            const executions = execData.data.executions
            addResult(`✅ Active executions: ${executions.length} found`)
            executions.forEach((exec: any, index: number) => {
              addResult(`   ${index + 1}. Plan: ${exec.plan_id}, Status: ${exec.overall_status}, Tests: ${exec.total_tests}`)
            })
          } else {
            addResult(`❌ Active executions failed: ${execResponse.status}`)
          }
        } else {
          addResult(`❌ AI test generation failed: ${genResponse.status}`)
        }
      } else {
        addResult(`❌ Login failed: ${loginData.message || loginResponse.status}`)
      }

      // Test 5: Test via API service
      addResult('5️⃣ Testing via API service...')
      try {
        const serviceExecutions = await apiService.getActiveExecutions()
        addResult(`✅ API service executions: ${serviceExecutions.length} found`)
        serviceExecutions.forEach((exec, index) => {
          addResult(`   ${index + 1}. Service Plan: ${exec.plan_id}, Status: ${exec.overall_status}`)
        })
      } catch (error: any) {
        addResult(`❌ API service error: ${error.message}`)
      }

    } catch (error: any) {
      addResult(`❌ Test error: ${error.message}`)
    }

    setIsLoading(false)
  }

  const testContinuousPolling = () => {
    addResult('🔄 Starting continuous polling (every 3 seconds)...')
    
    const interval = setInterval(async () => {
      try {
        const executions = await apiService.getActiveExecutions()
        addResult(`🔄 Poll result: ${executions.length} active executions`)
      } catch (error: any) {
        addResult(`❌ Poll error: ${error.message}`)
      }
    }, 3000)

    // Stop after 30 seconds
    setTimeout(() => {
      clearInterval(interval)
      addResult('⏹️ Continuous polling stopped')
    }, 30000)
  }

  return (
    <Card title="Direct API Test" style={{ margin: '20px 0' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="Direct API Testing"
          description="This component bypasses React Query and tests the API directly to isolate any issues."
          type="info"
          showIcon
        />
        
        <Space>
          <Button 
            type="primary" 
            onClick={testDirectAPI} 
            loading={isLoading}
          >
            Run Complete Test
          </Button>
          <Button onClick={testContinuousPolling}>
            Test Continuous Polling
          </Button>
          <Button onClick={clearResults}>
            Clear Results
          </Button>
        </Space>

        {testResults.length > 0 && (
          <Card title="Test Results" size="small">
            <div style={{ 
              maxHeight: '400px', 
              overflow: 'auto', 
              fontFamily: 'monospace', 
              fontSize: '12px',
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '4px'
            }}>
              {testResults.map((result, index) => (
                <div key={index} style={{ marginBottom: '4px' }}>
                  {result}
                </div>
              ))}
            </div>
          </Card>
        )}
      </Space>
    </Card>
  )
}

export default DirectAPITest