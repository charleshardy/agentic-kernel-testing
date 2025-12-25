import React, { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Space,
  Button,
  Input,
  Select,
  Table,
  Tag,
  message,
  Alert,
  Modal,
  Form,
  Spin,
  Tabs,
  Popconfirm,
} from 'antd'
import {
  ReloadOutlined,
  SearchOutlined,
  PlusOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  EditOutlined,
  EyeOutlined,
  CodeOutlined,
  FunctionOutlined,
  ExclamationCircleOutlined,
  SettingOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import apiService from '../services/api'
import TestCaseModal from '../components/TestCaseModal'
// import useAIGeneration from '../hooks/useAIGeneration'
// import KernelDriverInfo from '../components/KernelDriverInfo'

const { Text, Title } = Typography
const { TextArea } = Input
const { TabPane } = Tabs

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
  generation_info?: {
    method: 'manual' | 'ai_diff' | 'ai_function' | 'ai_kernel_driver'
    source_data: any
    generated_at: string
    ai_model?: string
    generation_params?: Record<string, any>
    driver_files?: Record<string, string>
  }
  execution_status?: 'never_run' | 'running' | 'completed' | 'failed'
  last_execution_at?: string
  tags?: string[]
  is_favorite?: boolean
  requires_root?: boolean
  kernel_module?: boolean
  driver_files?: Record<string, string>
}

const TestCases: React.FC = (): React.ReactElement => {
  const [searchText, setSearchText] = useState('')
  const [filters, setFilters] = useState({
    testType: undefined,
    subsystem: undefined,
    status: undefined,
  })
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [aiGenModalVisible, setAiGenModalVisible] = useState(false)
  const [aiGenType, setAiGenType] = useState<'diff' | 'function' | 'kernel'>('diff')
  const [aiGenForm] = Form.useForm()

  // Direct fetch state (replacing React Query)
  const [testCases, setTestCases] = useState<EnhancedTestCase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Test Case Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

  // AI Generation hook - temporarily disabled
  // const {
  //   generateFromDiff,
  //   generateFromFunction,
  //   generateKernelDriver,
  //   isGenerating,
  //   error: aiError
  // } = useAIGeneration()
  
  const isGenerating = false
  // AI generation functions using the API service
  const generateFromDiff = async (diff: string, maxTests: number, testTypes: string[]) => {
    return await apiService.generateTestsFromDiff(diff, maxTests, testTypes)
  }
  
  const generateFromFunction = async (functionName: string, filePath: string, subsystem: string, maxTests: number) => {
    return await apiService.generateTestsFromFunction(functionName, filePath, subsystem, maxTests)
  }
  
  const generateKernelDriver = async (functionName: string, filePath: string, subsystem: string, testTypes: string[]) => {
    return await apiService.generateKernelTestDriver(functionName, filePath, subsystem, testTypes)
  }

  // Direct fetch function
  const fetchTestCases = async () => {
    try {
      console.log('🔄 Fetching test cases...')
      setIsLoading(true)
      setError(null)
      
      // Get auth token
      const authResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      })
      
      if (!authResponse.ok) {
        throw new Error(`Auth failed: ${authResponse.status}`)
      }
      
      const authData = await authResponse.json()
      const token = authData.data.access_token
      
      // Fetch test cases
      const testsResponse = await fetch('http://localhost:8000/api/v1/tests?page=1&page_size=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!testsResponse.ok) {
        throw new Error(`Tests fetch failed: ${testsResponse.status}`)
      }
      
      const testsData = await testsResponse.json()
      
      if (!testsData.success || !testsData.data?.tests) {
        throw new Error('Invalid tests response format')
      }
      
      console.log(`✅ Loaded ${testsData.data.tests.length} test cases`)
      setTestCases(testsData.data.tests)
      setError(null)
      
    } catch (err: any) {
      console.error('❌ Fetch failed:', err)
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
      
      setTestCases(mockTestCases)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch on component mount
  useEffect(() => {
    fetchTestCases()
  }, [])

  // Test Case Modal handlers
  const handleViewTest = async (testId: string) => {
    try {
      console.log('🔍 Attempting to view test:', testId)
      
      const currentTest = testCases.find(t => t.id === testId)
      if (currentTest) {
        console.log('✅ Found test in current data:', currentTest)
        setSelectedTestCase(currentTest)
        setModalMode('view')
        setModalVisible(true)
        return
      }
      
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

  const handleDeleteTest = async (testId: string) => {
    try {
      console.log('Deleting test:', testId)
      
      // Find the test to get its name for the message
      const test = filteredTests.find(t => t.id === testId)
      const testName = test?.name || testId
      
      // Call the API to delete the test
      await apiService.deleteTest(testId)
      
      // Show success message
      message.success(`Successfully deleted test case: ${testName}`)
      
      // Clear selection if this test was selected
      if (selectedRowKeys.includes(testId)) {
        setSelectedRowKeys(prev => prev.filter(id => id !== testId))
      }
      
      // Refresh the test list
      fetchTestCases()
    } catch (error: any) {
      console.error('Failed to delete test:', error)
      
      // Show appropriate error message
      if (error.response?.status === 404) {
        message.error('Test case not found')
      } else if (error.response?.status === 403) {
        message.error('Permission denied - cannot delete this test case')
      } else {
        message.error(`Failed to delete test case: ${error.message || 'Unknown error'}`)
      }
    }
  }

  const handleBulkDelete = async () => {
    try {
      const selectedTests = filteredTests.filter(test => selectedRowKeys.includes(test.id))
      message.info(`Deleting ${selectedTests.length} test cases...`)
      
      let successCount = 0
      let failureCount = 0
      
      for (const test of selectedTests) {
        try {
          await apiService.deleteTest(test.id)
          console.log(`Successfully deleted test: ${test.name}`)
          successCount++
        } catch (error) {
          console.error(`Failed to delete test ${test.name}:`, error)
          failureCount++
        }
      }
      
      // Clear selected rows
      setSelectedRowKeys([])
      
      // Show results
      if (failureCount === 0) {
        message.success(`Successfully deleted ${successCount} test cases`)
      } else if (successCount === 0) {
        message.error(`Failed to delete all ${selectedTests.length} test cases`)
      } else {
        message.warning(`Deleted ${successCount} test cases, ${failureCount} failed`)
      }
      
      // Refresh the test list
      fetchTestCases()
    } catch (error: any) {
      console.error('Bulk delete failed:', error)
      message.error('Bulk delete operation failed')
    }
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      message.success(`Test case ${updatedTestCase.name} updated successfully`)
      fetchTestCases()
    } catch (error) {
      console.error('Error updating test case:', error)
      message.error('Failed to update test case')
    }
  }

  // AI Generation handlers
  const handleAIGeneration = async () => {
    try {
      // Validate only the fields for the current tab
      let fieldsToValidate: string[] = []
      
      switch (aiGenType) {
        case 'diff':
          fieldsToValidate = ['diffContent', 'diffMaxTests', 'diffTestTypes']
          break
        case 'function':
          fieldsToValidate = ['functionName', 'filePath', 'subsystem', 'funcMaxTests']
          break
        case 'kernel':
          fieldsToValidate = ['kernelFunctionName', 'kernelFilePath', 'kernelSubsystem', 'kernelTestTypes']
          break
      }
      
      console.log('🔍 Validating fields for tab:', aiGenType, 'Fields:', fieldsToValidate)
      
      // Validate only the fields for the current tab
      const values = await aiGenForm.validateFields(fieldsToValidate)
      console.log('✅ Form validation passed. Values:', values)
      let result

      try {
        // Make API call
        console.log('🚀 Making API call for type:', aiGenType, 'with values:', values)
        
        switch (aiGenType) {
          case 'diff':
            result = await generateFromDiff(
              values.diffContent,
              values.diffMaxTests || 20,
              values.diffTestTypes || ['unit']
            )
            break
          case 'function':
            result = await generateFromFunction(
              values.functionName,
              values.filePath,
              values.subsystem || 'unknown',
              values.funcMaxTests || 10
            )
            break
          case 'kernel':
            result = await generateKernelDriver(
              values.kernelFunctionName,
              values.kernelFilePath,
              values.kernelSubsystem || 'unknown',
              values.kernelTestTypes || ['unit', 'integration']
            )
            break
        }

        console.log('API call result:', result)
        
        if (result.success) {
          message.success(`Generated ${result.data?.test_cases?.length || 0} test cases`)
          setAiGenModalVisible(false)
          aiGenForm.resetFields()
          fetchTestCases() // Refresh the list
        } else {
          const errorMsg = result.message || 'Unknown error occurred'
          console.error('API call failed:', result)
          message.error(`Generation failed: ${errorMsg}`)
        }
      } catch (apiError: any) {
        // Handle API call errors
        console.error('API Generation error:', apiError)
        console.error('Error type:', typeof apiError)
        console.error('Error constructor:', apiError?.constructor?.name)
        console.error('Error details:', {
          message: apiError?.message,
          response: apiError?.response,
          status: apiError?.response?.status,
          data: apiError?.response?.data,
          stack: apiError?.stack
        })
        
        let errorMessage = 'Generation failed'
        if (apiError?.message && apiError.message !== 'undefined') {
          errorMessage += `: ${apiError.message}`
        } else if (apiError?.response?.data?.message) {
          errorMessage += `: ${apiError.response.data.message}`
        } else if (apiError?.response?.status) {
          errorMessage += `: HTTP ${apiError.response.status}`
        } else {
          errorMessage += ': Network or server error occurred'
        }
        
        message.error(errorMessage)
      }
    } catch (validationError: any) {
      // Handle form validation errors
      console.error('Form validation error:', validationError)
      console.error('Error fields:', validationError.errorFields)
      console.error('Values:', validationError.values)
      
      // Log specific field errors
      if (validationError.errorFields && validationError.errorFields.length > 0) {
        validationError.errorFields.forEach((field: any) => {
          console.error(`Field "${field.name}" error:`, field.errors)
        })
      }
      
      message.error('Please fill in all required fields correctly')
    }
  }

  // Filter and search logic
  const filteredTests = testCases.filter(test => {
    const matchesSearch = !searchText || 
      test.name.toLowerCase().includes(searchText.toLowerCase()) ||
      test.description.toLowerCase().includes(searchText.toLowerCase())
    
    const matchesType = !filters.testType || test.test_type === filters.testType
    const matchesSubsystem = !filters.subsystem || test.target_subsystem === filters.subsystem
    const matchesStatus = !filters.status || test.metadata?.execution_status === filters.status

    return matchesSearch && matchesType && matchesSubsystem && matchesStatus
  })

  // Calculate statistics
  const totalTests = filteredTests.length
  const aiGeneratedTests = filteredTests.filter(t => t.metadata?.generation_method !== 'manual').length
  const manualTests = totalTests - aiGeneratedTests
  const runningTests = filteredTests.filter(t => t.metadata?.execution_status === 'running').length

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
          <Popconfirm
            title="Delete Test Case"
            description={`Are you sure you want to delete "${record.name}"? This action cannot be undone.`}
            onConfirm={() => handleDeleteTest(record.id)}
            okText="Yes, Delete"
            cancelText="Cancel"
            okType="danger"
            icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
          >
            <Button
              size="small"
              icon={<DeleteOutlined />}
              danger
            >
              Delete
            </Button>
          </Popconfirm>
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
          Test Cases (Complete Version)
        </h2>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => setAiGenModalVisible(true)}
            loading={isGenerating}
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

      {/* Search and Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="Search test cases..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Test Type"
              style={{ width: '100%' }}
              value={filters.testType}
              onChange={(value) => setFilters({ ...filters, testType: value })}
              allowClear
            >
              <Select.Option value="unit">Unit</Select.Option>
              <Select.Option value="integration">Integration</Select.Option>
              <Select.Option value="performance">Performance</Select.Option>
              <Select.Option value="security">Security</Select.Option>
              <Select.Option value="kernel_driver">Kernel Driver</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Subsystem"
              style={{ width: '100%' }}
              value={filters.subsystem}
              onChange={(value) => setFilters({ ...filters, subsystem: value })}
              allowClear
            >
              <Select.Option value="kernel/core">Kernel Core</Select.Option>
              <Select.Option value="kernel/mm">Memory Management</Select.Option>
              <Select.Option value="kernel/fs">File System</Select.Option>
              <Select.Option value="kernel/net">Networking</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Status"
              style={{ width: '100%' }}
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
            >
              <Select.Option value="never_run">Never Run</Select.Option>
              <Select.Option value="running">Running</Select.Option>
              <Select.Option value="completed">Completed</Select.Option>
              <Select.Option value="failed">Failed</Select.Option>
            </Select>
          </Col>
        </Row>
      </Card>

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
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Running"
              value={runningTests}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        {/* Bulk Actions */}
        {selectedRowKeys.length > 0 && (
          <div style={{ 
            marginBottom: 16, 
            padding: 12, 
            backgroundColor: '#f6ffed', 
            border: '1px solid #b7eb8f', 
            borderRadius: 6 
          }}>
            <Space>
              <span style={{ fontWeight: 500 }}>
                {selectedRowKeys.length} test case{selectedRowKeys.length !== 1 ? 's' : ''} selected
              </span>
              <Button
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => {
                  message.success(`Starting execution of ${selectedRowKeys.length} test cases`)
                  setSelectedRowKeys([])
                }}
              >
                Execute Selected
              </Button>
              <Popconfirm
                title="Delete Selected Test Cases"
                description={`Are you sure you want to delete ${selectedRowKeys.length} test case${selectedRowKeys.length !== 1 ? 's' : ''}? This action cannot be undone.`}
                onConfirm={handleBulkDelete}
                okText="Yes, Delete"
                cancelText="Cancel"
                okType="danger"
                icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
              >
                <Button
                  size="small"
                  icon={<DeleteOutlined />}
                  danger
                >
                  Delete Selected
                </Button>
              </Popconfirm>
              <Button
                size="small"
                onClick={() => setSelectedRowKeys([])}
              >
                Clear Selection
              </Button>
            </Space>
          </div>
        )}
        
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

      {/* AI Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={aiGenModalVisible}
        onCancel={() => {
          setAiGenModalVisible(false)
          aiGenForm.resetFields()
        }}
        onOk={handleAIGeneration}
        confirmLoading={isGenerating}
        width={800}
      >
        <Tabs activeKey={aiGenType} onChange={(key) => setAiGenType(key as any)}>
          <TabPane tab={<span><CodeOutlined />From Diff</span>} key="diff">
            <Form form={aiGenForm} layout="vertical">
              <Form.Item
                name="diffContent"
                label="Code Diff"
                rules={[{ required: true, message: 'Please enter code diff' }]}
              >
                <TextArea
                  rows={8}
                  placeholder="Paste your git diff or code changes here..."
                />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="diffMaxTests" label="Max Tests" initialValue={20}>
                    <Input type="number" min={1} max={50} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="diffTestTypes" label="Test Types" initialValue={['unit']}>
                    <Select mode="multiple">
                      <Select.Option value="unit">Unit</Select.Option>
                      <Select.Option value="integration">Integration</Select.Option>
                      <Select.Option value="performance">Performance</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>
          
          <TabPane tab={<span><FunctionOutlined />From Function</span>} key="function">
            <Form form={aiGenForm} layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="functionName"
                    label="Function Name"
                    rules={[{ required: true, message: 'Please enter function name' }]}
                  >
                    <Input placeholder="e.g., kmalloc" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="filePath"
                    label="File Path"
                    rules={[{ required: true, message: 'Please enter file path' }]}
                  >
                    <Input placeholder="e.g., mm/slab.c" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="subsystem" label="Subsystem" initialValue="kernel/core">
                    <Select>
                      <Select.Option value="kernel/core">Kernel Core</Select.Option>
                      <Select.Option value="kernel/mm">Memory Management</Select.Option>
                      <Select.Option value="kernel/fs">File System</Select.Option>
                      <Select.Option value="kernel/net">Networking</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="funcMaxTests" label="Max Tests" initialValue={10}>
                    <Input type="number" min={1} max={30} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>
          
          <TabPane tab={<span><SettingOutlined />Kernel Driver</span>} key="kernel">
            <Alert
              message="Advanced Kernel Test Driver Generation"
              description="This will generate a complete kernel module with test drivers, build system, and execution scripts."
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Form form={aiGenForm} layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="kernelFunctionName"
                    label="Function Name"
                    rules={[{ required: true, message: 'Please enter function name' }]}
                  >
                    <Input placeholder="e.g., test_function" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="kernelFilePath"
                    label="File Path"
                    rules={[{ required: true, message: 'Please enter file path' }]}
                  >
                    <Input placeholder="e.g., drivers/test.c" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="kernelSubsystem" label="Subsystem" initialValue="kernel/core">
                    <Select>
                      <Select.Option value="kernel/core">Kernel Core</Select.Option>
                      <Select.Option value="drivers/block">Block Drivers</Select.Option>
                      <Select.Option value="drivers/char">Character Drivers</Select.Option>
                      <Select.Option value="drivers/net">Network Drivers</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="kernelTestTypes" label="Test Types" initialValue={['unit', 'integration']}>
                    <Select mode="multiple">
                      <Select.Option value="unit">Unit</Select.Option>
                      <Select.Option value="integration">Integration</Select.Option>
                      <Select.Option value="performance">Performance</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
            {/* <KernelDriverInfo /> */}
          </TabPane>
        </Tabs>
      </Modal>

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