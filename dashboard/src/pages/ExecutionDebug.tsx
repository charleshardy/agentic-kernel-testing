import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, Alert, Divider } from 'antd'
import { useQuery, useQueryClient } from 'react-query'
import apiService from '../services/api'

const { Title, Text, Paragraph } = Typography

const ExecutionDebug: React.FC = () => {
  const [debugLogs, setDebugLogs] = useState<string[]>([])
  const [manualResult, setManualResult] = useState<any>(null)
  const queryClient = useQueryClient()

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setDebugLogs(prev => [...prev, `[${timestamp}] ${message}`])
  }

  // React Query for active executions (same as RealTimeExecutionMonitor)
  const { data: executions, isLoading, error, refetch } = useQuery(
    'activeExecutions',
    async () => {
      addLog('🔍 React Query: Fetching active executions...')
      const result = await apiService.getActiveExecutions()
      addLog(`📊 React Query: Got ${result.length} executions`)
      return result
    },
    {
      refetchInterval: 5000,
      cacheTime: 0, // Don't cache the data
      staleTime: 0, // Always consider data stale
      onError: (error: any) => {
        addLog(`❌ React Query Error: ${error.message}`)
      },
      onSuccess: (data) => {
        addLog(`✅ React Query Success: ${data.length} executions`)
      }
    }
  )

  const testManualAPI = async () => {
    addLog('🧪 Manual API Test: Starting...')
    try {
      const result = await apiService.getActiveExecutions()
      setManualResult(result)
      addLog(`✅ Manual API Test: Success - ${result.length} executions`)
    } catch (error: any) {
      addLog(`❌ Manual API Test: Error - ${error.message}`)
      setManualResult({ error: error.message })
    }
  }

  const testDirectFetch = async () => {
    addLog('🌐 Direct Fetch Test: Starting...')
    try {
      // Get token from localStorage (same as API service)
      const token = localStorage.getItem('auth_token')
      if (!token) {
        addLog('❌ No auth token found in localStorage')
        return
      }

      const response = await fetch('http://localhost:8000/api/v1/execution/active', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()
      addLog(`🌐 Direct Fetch: Status ${response.status}`)
      addLog(`🌐 Direct Fetch: ${data.success ? 'Success' : 'Failed'} - ${data.data?.executions?.length || 0} executions`)
      
      if (!response.ok) {
        addLog(`❌ Direct Fetch Error: ${data.message || 'Unknown error'}`)
      }
    } catch (error: any) {
      addLog(`❌ Direct Fetch Error: ${error.message}`)
    }
  }

  const clearLogs = () => {
    setDebugLogs([])
    setManualResult(null)
  }

  const forceRefresh = () => {
    addLog('🔄 Force refreshing React Query...')
    queryClient.invalidateQueries('activeExecutions')
    queryClient.removeQueries('activeExecutions') // Also remove cached data
    refetch()
  }

  const forceClearCache = () => {
    addLog('🗑️ Force clearing all React Query cache...')
    queryClient.clear() // Clear all cached data
    setTimeout(() => {
      refetch()
    }, 100)
  }

  useEffect(() => {
    addLog('🚀 ExecutionDebug component mounted')
    addLog(`📱 Current executions from React Query: ${executions?.length || 0}`)
  }, [executions])

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2}>Execution Debug Page</Title>
      
      <Alert
        message="Debug Information"
        description="This page helps debug why executions might not be showing in the Web GUI."
        type="info"
        showIcon
        style={{ marginBottom: '20px' }}
      />

      <Space direction="vertical" style={{ width: '100%' }}>
        {/* Control Buttons */}
        <Card title="Debug Controls">
          <Space wrap>
            <Button type="primary" onClick={testManualAPI}>
              Test Manual API Call
            </Button>
            <Button onClick={testDirectFetch}>
              Test Direct Fetch
            </Button>
            <Button onClick={forceRefresh}>
              Force React Query Refresh
            </Button>
            <Button onClick={forceClearCache}>
              Clear All Cache
            </Button>
            <Button onClick={clearLogs}>
              Clear Logs
            </Button>
          </Space>
        </Card>

        {/* React Query Status */}
        <Card title="React Query Status">
          <Space direction="vertical">
            <Text>Loading: {isLoading ? '✅ Yes' : '❌ No'}</Text>
            <Text>Error: {error ? `❌ ${(error as any).message}` : '✅ None'}</Text>
            <Text>Data: {executions ? `✅ ${executions.length} executions` : '❌ No data'}</Text>
            <Text>Last Fetch: {executions ? '✅ Recent' : '❌ Never or failed'}</Text>
          </Space>
        </Card>

        {/* Current Executions */}
        <Card title="Current Executions (React Query)">
          {executions && executions.length > 0 ? (
            <div>
              <Text strong>Found {executions.length} execution(s):</Text>
              {executions.map((exec, index) => (
                <div key={exec.plan_id} style={{ marginLeft: '20px', marginTop: '8px' }}>
                  <Text code>{index + 1}. {exec.plan_id}</Text>
                  <br />
                  <Text type="secondary">Status: {exec.overall_status}, Tests: {exec.total_tests}</Text>
                </div>
              ))}
            </div>
          ) : (
            <Text type="secondary">No executions found via React Query</Text>
          )}
        </Card>

        {/* Manual Test Result */}
        {manualResult && (
          <Card title="Manual API Test Result">
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '10px', 
              borderRadius: '4px',
              overflow: 'auto'
            }}>
              {JSON.stringify(manualResult, null, 2)}
            </pre>
          </Card>
        )}

        {/* Debug Logs */}
        <Card title="Debug Logs">
          <div style={{ 
            maxHeight: '300px', 
            overflow: 'auto',
            backgroundColor: '#f5f5f5',
            padding: '10px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '12px'
          }}>
            {debugLogs.length === 0 ? (
              <Text type="secondary">No logs yet...</Text>
            ) : (
              debugLogs.map((log, index) => (
                <div key={index} style={{ marginBottom: '2px' }}>
                  {log}
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Browser Info */}
        <Card title="Browser Environment">
          <Space direction="vertical">
            <Text>User Agent: {navigator.userAgent}</Text>
            <Text>Current URL: {window.location.href}</Text>
            <Text>Local Storage Auth Token: {localStorage.getItem('auth_token') ? '✅ Present' : '❌ Missing'}</Text>
            <Text>API Base URL: http://localhost:8000/api/v1</Text>
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default ExecutionDebug