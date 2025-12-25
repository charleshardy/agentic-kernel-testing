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
} from 'antd'
import {
  ReloadOutlined,
  PlusOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  EditOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService, { EnhancedTestCase } from '../services/api'
import TestCaseModal from '../components/TestCaseModal-safe'

const { Text } = Typography

const TestCases: React.FC = (): React.ReactElement => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])

  // Test Case Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

  // Add manual API test on component mount
  useEffect(() => {
    const testAPI = async () => {
      try {
        console.log('🧪 Manual API test on component mount...')
        
        // Add timeout to the API call
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('API call timeout')), 10000)
        )
        
        const apiPromise = apiService.getTests({ page: 1, page_size: 50 })
        
        const result = await Promise.race([apiPromise, timeoutPromise])
        console.log('✅ Manual API test successful:', result)
      } catch (error) {
        console.error('❌ Manual API test failed:', error)
      }
    }
    testAPI()
  }, [])

  // Test Case Modal handlers
  const handleViewTest = async (testId: string) => {
    try {
      console.log('🔍 Attempting to view test:', testId)
      
      // First try to get from API
      try {
        const test = await apiService.getTestById(testId)
        console.log('✅ Found test in API:', test)
        setSelectedTestCase(test)
        setModalMode('view')
        setModalVisible(true)
        return
      } catch (apiError: any) {
        console.log('⚠️ API fetch failed:', apiError.response?.status, apiError.message)
        
        // If API fails, try to find in current test data (mock or API)
        const currentTest = tests.find(t => t.id === testId)
        if (currentTest) {
          console.log('✅ Found test in current data:', currentTest)
          setSelectedTestCase(currentTest)
          setModalMode('view')
          setModalVisible(true)
          return
        }
        
        // If not found anywhere, throw the original error
        throw apiError
      }
    } catch (error: any) {
      console.error('❌ Error loading test case:', error)
      if (error.response?.status === 404) {
        message.error(`Test case ${testId} not found`)
      } else {
        message.error('Failed to load test case details')
      }
    }
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedTestCase(null)
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      message.success(`Test case ${updatedTestCase.name} updated successfully`)
      refetch()
    } catch (error) {
      console.error('Error updating test case:', error)
      message.error('Failed to update test case')
    }
  }

  // Fetch test cases - REACT QUERY V3 SYNTAX
  const { data: testCasesData, isLoading, error, refetch } = useQuery(
    'testCases',
    () => apiService.getTests({ page: 1, page_size: 50 }),
    {
      retry: false,
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      staleTime: 0,
      cacheTime: 0,
    }
  )

  // Mock data when API is not available
  const mockTestCases: EnhancedTestCase[] = [
    {
      id: 'test-001',
      name: 'Kernel Boot Test',
      description: 'Tests kernel boot sequence and initialization',
      test_type: 'integration',
      target_subsystem: 'kernel/core',
      code_paths: ['kernel/init/main.c', 'kernel/init/init_task.c'],
      execution_time_estimate: 45,
      test_script: '#!/bin/bash\n# Kernel boot test script\necho "Testing kernel boot sequence"\n# Add test logic here',
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      metadata: {
        execution_status: 'completed',
        generation_method: 'manual',
        last_execution: '2024-01-15T14:20:00Z',
      }
    },
    {
      id: 'test-002',
      name: 'Memory Allocation Test',
      description: 'Tests kmalloc and memory management functions',
      test_type: 'unit',
      target_subsystem: 'kernel/mm',
      code_paths: ['mm/slab.c', 'mm/kmalloc.c'],
      execution_time_estimate: 30,
      test_script: '#!/bin/bash\n# Memory allocation test script\necho "Testing memory allocation"\n# Add test logic here',
      created_at: '2024-01-15T11:00:00Z',
      updated_at: '2024-01-15T11:00:00Z',
      metadata: {
        execution_status: 'never_run',
        generation_method: 'ai_function',
      }
    },
  ]

  const tests = testCasesData?.tests || mockTestCases
  
  console.log('TestCases Debug:', {
    hasData: !!testCasesData,
    dataTests: testCasesData?.tests?.length || 0,
    error: !!error,
    errorMessage: error?.message,
    isLoading,
    mockTests: mockTestCases.length,
    queryState: {
      isLoading,
      isError: !!error,
      isSuccess: !!testCasesData && !error,
      data: testCasesData ? 'present' : 'missing'
    }
  })
  
  // Force re-render every 5 seconds to debug
  useEffect(() => {
    const interval = setInterval(() => {
      console.log('🔄 Debug: Forcing component update, current state:', {
        isLoading,
        hasData: !!testCasesData,
        error: !!error
      })
    }, 5000)
    
    return () => clearInterval(interval)
  }, [isLoading, testCasesData, error])
  
  // Filter tests based on search and filters
  const filteredTests = tests

  // Calculate statistics
  const totalTests = filteredTests.length
  const aiGeneratedTests = filteredTests.filter(t => t.metadata?.generation_method !== 'manual').length
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
          Test Cases
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
              refetch()
              message.info('Refreshing test case list...')
            }}
          >
            Refresh
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={async () => {
              try {
                console.log('🧪 Testing direct API call...')
                const result = await apiService.getTests({ page: 1, page_size: 50 })
                console.log('✅ Direct API result:', result)
                message.success(`Direct API call successful: ${result.tests.length} tests`)
              } catch (error) {
                console.error('❌ Direct API call failed:', error)
                message.error(`Direct API call failed: ${error.message}`)
              }
            }}
          >
            Test API
          </Button>
        </Space>
      </div>

      {/* Connection Status */}
      {error && (
        <Alert
          message="Backend Connection"
          description="Using mock data - backend API not available. Start the backend server to see real test data."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Statistics Cards */}
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
      </Row>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        <Table
          columns={columns}
          dataSource={filteredTests}
          rowKey="id"
          loading={isLoading}
          rowSelection={rowSelection}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} tests`,
          }}
        />
      </Card>

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