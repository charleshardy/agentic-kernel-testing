import React, { useState, useEffect } from 'react'
import { Card, Table, Button, message } from 'antd'

const TestCases: React.FC = () => {
  const [tests, setTests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    console.log('🚀 Ultra-simple TestCases mounted')
    
    // Immediate mock data - no API calls
    setTimeout(() => {
      console.log('✅ Ultra-simple: Setting mock data')
      setTests([
        { id: '1', name: 'Ultra Simple Test 1', test_type: 'unit' },
        { id: '2', name: 'Ultra Simple Test 2', test_type: 'integration' }
      ])
      setLoading(false)
    }, 1000)
  }, [])

  console.log('🔍 Ultra-simple render:', { loading, testsCount: tests.length })

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'test_type', key: 'test_type' },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <h1>Test Cases - Ultra Simple</h1>
      <Button onClick={() => message.success('Button works!')}>
        Test Button
      </Button>
      <Card title={`Test Cases (${tests.length} tests)`} style={{ marginTop: 16 }}>
        <Table 
          columns={columns}
          dataSource={tests}
          rowKey="id"
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default TestCases