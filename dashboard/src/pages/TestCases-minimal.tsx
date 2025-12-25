import React, { useState, useEffect } from 'react'
import { Card, Table, Button, message, Spin } from 'antd'

const TestCases: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])

  useEffect(() => {
    console.log('🔄 TestCases-minimal: Component mounted')
    
    // Simulate API call
    const fetchData = async () => {
      try {
        console.log('🔄 TestCases-minimal: Starting fetch...')
        setLoading(true)
        
        // Wait 2 seconds to simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        const mockData = [
          { id: '1', name: 'Test 1', type: 'unit' },
          { id: '2', name: 'Test 2', type: 'integration' }
        ]
        
        console.log('✅ TestCases-minimal: Data loaded:', mockData)
        setData(mockData)
        setLoading(false)
      } catch (error) {
        console.error('❌ TestCases-minimal: Error:', error)
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  console.log('🔍 TestCases-minimal: Render state:', { loading, dataLength: data.length })

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'type', key: 'type' },
  ]

  if (loading) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading minimal test cases...</div>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <h1>Test Cases - Minimal Version</h1>
      <Button 
        onClick={() => {
          console.log('🔄 TestCases-minimal: Refresh clicked')
          message.info('Refresh clicked!')
        }}
      >
        Test Button
      </Button>
      <Card title={`Test Cases (${data.length} tests)`} style={{ marginTop: 16 }}>
        <Table 
          columns={columns} 
          dataSource={data} 
          rowKey="id"
          loading={false}
        />
      </Card>
    </div>
  )
}

export default TestCases