import React, { useState } from 'react'
import { Card, Table, Button, message, Alert } from 'antd'
import { useQuery } from 'react-query'

const TestCases: React.FC = () => {
  const [manualData, setManualData] = useState<any[]>([])

  // Very simple React Query usage
  const { data, isLoading, error } = useQuery(
    'simple-tests',
    async () => {
      console.log('🔄 Simple query: Starting...')
      
      // Direct fetch with timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      try {
        const response = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50', {
          signal: controller.signal
        })
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        console.log('✅ Simple query: Success:', result)
        return result.data.tests || []
      } catch (error) {
        clearTimeout(timeoutId)
        console.error('❌ Simple query: Failed:', error)
        throw error
      }
    },
    {
      retry: false,
      staleTime: 0,
      cacheTime: 0,
    }
  )

  console.log('🔍 Query Simple render:', { 
    isLoading, 
    hasData: !!data, 
    dataLength: data?.length || 0, 
    hasError: !!error,
    manualDataLength: manualData.length 
  })

  const tests = data || [
    { id: '1', name: 'Fallback Test 1', test_type: 'unit' },
    { id: '2', name: 'Fallback Test 2', test_type: 'integration' }
  ]

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'test_type', key: 'test_type' },
  ]

  const testManualFetch = async () => {
    try {
      console.log('🧪 Manual fetch test...')
      const response = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50')
      const result = await response.json()
      console.log('✅ Manual fetch success:', result)
      setManualData(result.data.tests || [])
      message.success(`Manual fetch: ${result.data.tests.length} tests`)
    } catch (error) {
      console.error('❌ Manual fetch failed:', error)
      message.error('Manual fetch failed')
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <h1>Test Cases - Query Simple</h1>
      
      <div style={{ marginBottom: 16 }}>
        <Button onClick={testManualFetch} style={{ marginRight: 8 }}>
          Test Manual Fetch
        </Button>
        <Button onClick={() => window.location.reload()}>
          Reload Page
        </Button>
      </div>

      {error && (
        <Alert 
          message="Query Error" 
          description={`Error: ${error.message}`}
          type="error" 
          style={{ marginBottom: 16 }}
        />
      )}

      <Card title={`Test Cases (Query: ${tests.length}, Manual: ${manualData.length})`}>
        <Table 
          columns={columns}
          dataSource={tests}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {manualData.length > 0 && (
        <Card title="Manual Fetch Results" style={{ marginTop: 16 }}>
          <Table 
            columns={columns}
            dataSource={manualData}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </Card>
      )}
    </div>
  )
}

export default TestCases