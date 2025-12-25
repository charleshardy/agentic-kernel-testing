import React, { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Space,
  Button,
  Table,
  Tag,
  message,
  Alert,
  Spin,
} from 'antd'
import {
  ReloadOutlined,
  PlusOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  EditOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import TestCaseModal from '../components/TestCaseModal-safe'

const { Text } = Typography

interface EnhancedTestCase {
  id: string
  name: string
  description: string
  test_type: string
  target_subsystem: string
  code_paths: string[]
  execution_time_estimate: number
  test_script: string
  created_at: string
  updated_at: string
  metadata: {
    execution_status?: string
    generation_method?: string
    [key: string]: any
  }
}

const TestCases: React.FC = (): React.ReactElement => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [testCases, setTestCases] = useState<EnhancedTestCase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fetchAttempts, setFetchAttempts] = useState(0)

  // Test Case Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

  // Direct fetch function
  const fetchTestCases = async () => {
    const attemptNumber = fetchAttempts + 1
    setFetchAttempts(attemptNumber)
    
    try {
      console.log(`🔄 Direct fetch attempt #${attemptNumber}...`)
      setIsLoading(true)
      setError(null)
      
      // Step 1: Get auth token
      console.log('🔑 Getting auth token...')
      const authResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'admin',
          password: 'admin123'
        })
      })
      
      if (!authResponse.ok) {
        throw new Error(`Auth failed: ${authResponse.status} ${authResponse.statusText}`)
      }
      
      const authData = await authResponse.json()
      console.log('✅ Auth successful:', authData.success)
      
      if (!authData.success || !authData.data?.access_token) {
        throw new Error('Invalid auth response')
      }
      
      const token = authData.data.access_token
      
      // Step 2: Fetch test cases
      console.log('📋 Fetching test cases...')
      const testsResponse = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!testsResponse.ok) {
        throw new Error(`Tests fetch failed: ${testsResponse.status} ${testsResponse.statusText}`)
      }
      
      const testsData = await testsResponse.json()
      console.log('✅ Tests fetch successful:', testsData)
      
      if (!testsData.success || !testsData.data?.tests) {
        throw new Error('Invalid tests response format')
      }
      
      console.log(`✅ Loaded ${testsData.data.tests.length} test cases`)
      setTestCases(testsData.data.tests)
      setError(null)
      
    } catch (err: any) {
      console.error(`❌ Fetch attempt #${attemptNumber} failed:`, err)
      setError(err.message)
      
      // Use mock data as fallback
      const mockTestCases: EnhancedTestCase[] = [
        {
          id: 'mock-001',
          name: 'Mock Kernel Boot Test',
          description: 'Tests kernel boot sequence and initialization (MOCK DATA)',
          test_type: 'integration',
          target_subsystem: 'kernel/core',
          code_paths: ['kernel/init/main.c', 'kernel/init/init_task.c'],
          execution_time_estimate: 45,
          test_script: '#!/bin/bash\necho "Mock kernel boot test"',
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
          metadata: {
            execution_status: 'completed',
            generation_method: 'manual',
          }
        },
        {
          id: 'mock-002',
          name: 'Mock Memory Allocation Test',
          description: 'Tests kmalloc and memory management functions (MOCK DATA)',
          test_type: 'unit',
          target_subsystem: 'kernel/mm',
          code_paths: ['mm/slab.c', 'mm/kmalloc.c'],
          execution_time_estimate: 30,
          test_script: '#!/bin/bash\necho "Mock memory allocation test"',
          created_at: '2024-01-15T11:00:00Z',
          updated_at: '2024-01-15T11:00:00Z',
          metadata: {
            execution_status: 'never_run',
            generation_method: 'ai_function',
          }
        },
      ]
      
      console.log('📋 Using mock data as fallback')
      setTestCases(mockTestCases)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch on component mount
  useEffect(() => {
    console.log('🚀 TestCases-direct-fetch component mounted')
    fetchTestCases()
  }, [])

  // Test Case Modal handlers
  const handleViewTest = async (testId: string) => {
    try {
      console.log('🔍 Attempting to view test:', testId)
      
      // Find the test in current data
      const currentTest = testCases.find(t => t.id === testId)
      if (currentTest) {
        console.log('✅ Found test in current data:', currentTest)
        setSelectedTestCase(currentTest)
        setModalMode('view')
        setModalVisible(true)
        return
      }
      
      // If not found, show error
      message.error(`Test case ${testId} not found`)
    } catch (error: any) {
      console.error('❌ Error loading test case:', error)
      message.error('Failed to load test case details')
    }
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedTestCase(null)
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      message.success(`Test case ${updatedTestCase.name} updated successfully`)
      fetchTestCases() // Refetch data
    } catch (error) {
      console.error('Error updating test case:', error)
      message.error('Failed to update test case')
    }
  }

  console.log('🔍 Direct fetch render state:', {
    isLoading,
    testCasesCount: testCases.length,
    error: !!error,
    errorMessage: error,
    fetchAttempts
  })

  // Calculate statistics
  const totalTests = testCases.length
  const aiGeneratedTests = testCases.filter(t => t.metadata?.generation_method !== 'manual').length
  const manualTests = totalTests - aiGeneratedTests

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green'
      case 'running': return 'blue'
      case 'failed': return 'red'
      case 'never_run': return 'default'
      default: return 'default'
    }
  }

  const getGenerationMethodColor = (method: string) => {
    switch (method) {
      case 'manual': return 'default'
      case 'ai_diff': return 'blue'
      case 'ai_function': return 'green'
      case 'ai_kernel_driver': return 'purple'
      default: return 'default'
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: EnhancedTestCase) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'test_type',
      key: 'test_type',
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      ),
    },
    {
      title: 'Subsystem',
      dataIndex: 'target_subsystem',
      key: 'target_subsystem',
      render: (subsystem: string) => (
        <Tag>{subsystem}</Tag>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: EnhancedTestCase) => {
        const status = record.metadata?.execution_status || 'never_run'
        return <Tag color={getStatusColor(status)}>{status.replace('_', ' ')}</Tag>
      },
    },
    {
      title: 'Generation',
      key: 'generation',
      render: (record: EnhancedTestCase) => {
        const method = record.metadata?.generation_method || 'manual'
        return <Tag color={getGenerationMethodColor(method)}>{method.replace('_', ' ')}</Tag>
      },
    },
    {
      title: 'Est. Time',
      dataIndex: 'execution_time_estimate',
      key: 'execution_time_estimate',
      render: (time: number) => `${time}s`,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: EnhancedTestCase) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewTest(record.id)}
          >
            View
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => message.info(`Editing test: ${record.name}`)}
          >
            Edit
          </Button>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            type="primary"
            onClick={() => message.success(`Starting execution of: ${record.name}`)}
            disabled={record.metadata?.execution_status === 'running'}
          >
            Run
          </Button>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedRowKeys: React.Key[]) => setSelectedRowKeys(selectedRowKeys as string[]),
    getCheckboxProps: (record: EnhancedTestCase) => ({
      disabled: record.metadata?.execution_status === 'running',
    }),
  }

  return (
    <div style={{ padding: '0 24px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 24 
      }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>
          Test Cases (Direct Fetch - Attempt #{fetchAttempts})
        </h2>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => message.info('AI Generation coming soon')}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => message.info('Create test functionality coming soon')}
          >
            Create Test
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchTestCases()
              message.info('Refreshing test case list...')
            }}
            loading={isLoading}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Connection Status */}
      {error && (
        <Alert
          message="Backend Connection Issue"
          description={`API Error: ${error}. Using mock data as fallback.`}
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Loading State */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, fontSize: '16px' }}>
            Loading test cases (attempt #{fetchAttempts})...
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      {!isLoading && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Total Test Cases"
                value={totalTests}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="AI Generated"
                value={aiGeneratedTests}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Manual Tests"
                value={manualTests}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Fetch Attempts"
                value={fetchAttempts}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Test Cases Table */}
      {!isLoading && (
        <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
          <Table
            columns={columns}
            dataSource={testCases}
            rowKey="id"
            loading={false}
            rowSelection={rowSelection}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} tests`,
            }}
          />
        </Card>
      )}

      {/* Test Case Detail Modal */}
      <TestCaseModal
        testCase={selectedTestCase}
        visible={modalVisible}
        mode={modalMode}
        onClose={handleCloseModal}
        onSave={handleSaveTest}
        onModeChange={setModalMode}
      />
    </div>
  )
}

export default TestCases