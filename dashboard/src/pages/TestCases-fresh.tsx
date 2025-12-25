import React, { useState, useEffect } from 'react'
import { Card, Table, Spin, Alert } from 'antd'

const TestCases: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [tests, setTests] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    
    const loadTests = async () => {
      try {
        console.log('🔄 Fresh: Loading tests...')
        setLoading(true)
        setError(null)
        
        // Direct fetch without any libraries
        const response = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50')
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        console.log('✅ Fresh: Raw response:', data)
        
        if (mounted) {
          if (data.success && data.data && data.data.tests) {
            setTests(data.data.tests)
            console.log('✅ Fresh: Tests loaded:', data.data.tests.length)
          } else {
            throw new Error('Invalid response format')
          }
          setLoading(false)
        }
      } catch (err: any) {
        console.error('❌ Fresh: Error loading tests:', err)
        if (mounted) {
          setError(err.message)
          // Use mock data
          setTests([
            { id: '1', name: 'Mock Test 1', test_type: 'unit', target_subsystem: 'kernel/core' },
            { id: '2', name: 'Mock Test 2', test_type: 'integration', target_subsystem: 'kernel/mm' }
          ])
          setLoading(false)
        }
      }
    }
    
    loadTests()
    
    return () => {
      mounted = false
    }
  }, [])

  console.log('🔍 Fresh: Current state:', { loading, testsCount: tests.length, error })

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'test_type', key: 'test_type' },
    { title: 'Subsystem', dataIndex: 'target_subsystem', key: 'target_subsystem' },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <h1>Test Cases - Fresh Version</h1>
      
      {error && (
        <Alert 
          message="API Error" 
          description={`Error: ${error}. Showing mock data.`}
          type="warning" 
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Card title={`Test Cases (${tests.length} tests)`}>
        <Table 
          columns={columns}
          dataSource={tests}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
      
      {loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <div>Loading...</div>
        </div>
      )}
    </div>
  )
}

export default TestCases