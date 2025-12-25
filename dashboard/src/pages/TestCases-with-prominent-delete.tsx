import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
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
  DatePicker,
  Divider,
  Modal,
  Form,
  Checkbox,
  Progress,
  message,
  Popconfirm,
  Table,
  Tag,
  Badge,
  Tooltip,
  Alert,
} from 'antd'
import {
  ReloadOutlined,
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  PlusOutlined,
  RobotOutlined,
  CodeOutlined,
  FunctionOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  TagOutlined,
  CheckOutlined,
  CloseOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  EditOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import dayjs from 'dayjs'
import TestCaseModal from '../components/TestCaseModal'
import AIGenerationProgress from '../components/AIGenerationProgress'
import KernelDriverInfo from '../components/KernelDriverInfo'
import apiService, { TestCase, EnhancedTestCase } from '../services/api'
import useAIGeneration from '../hooks/useAIGeneration'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { TextArea } = Input

interface TestCasesProps {}

const TestCases: React.FC<TestCasesProps> = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchText, setSearchText] = useState(searchParams.get('search') || '')
  const [filters, setFilters] = useState({
    testType: searchParams.get('type') || undefined,
    subsystem: searchParams.get('subsystem') || undefined,
    generationMethod: searchParams.get('generation') || undefined,
    status: searchParams.get('status') || undefined,
  })
  const [dateRange, setDateRange] = useState<[any, any] | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [pagination, setPagination] = useState({
    current: parseInt(searchParams.get('page') || '1'),
    pageSize: parseInt(searchParams.get('pageSize') || '20'),
  })
  
  // Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')
  
  // AI Generation modal state
  const [isAIGenModalVisible, setIsAIGenModalVisible] = useState(false)
  const [aiGenType, setAIGenType] = useState<'diff' | 'function' | 'kernel'>('diff')
  const [aiGenForm] = Form.useForm()

  // Bulk operations state
  const [bulkOperationInProgress, setBulkOperationInProgress] = useState(false)
  const [bulkOperationType, setBulkOperationType] = useState<string>('')
  const [bulkOperationProgress, setBulkOperationProgress] = useState(0)

  // AI Generation hook
  const { generateFromDiff, generateFromFunction, generateKernelDriver, isGenerating } = useAIGeneration({
    onSuccess: (response, type) => {
      setIsAIGenModalVisible(false)
      aiGenForm.resetFields()
      setTimeout(() => {
        refetch()
      }, 1000)
    },
    preserveFilters: true,
    enableOptimisticUpdates: true,
  })

  // Fetch test cases
  const { data: testCasesData, isLoading, error, refetch } = useQuery(
    ['testCases', searchText, filters, dateRange],
    () => apiService.getTests({
      page: 1,
      page_size: 50,
      test_type: filters.testType,
      status: filters.status,
    }),
    {
      refetchInterval: 5000,
      refetchOnWindowFocus: true,
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    }
  )

  // Client-side filtering
  const filteredTests = React.useMemo(() => {
    try {
      if (!testCasesData?.tests || !Array.isArray(testCasesData.tests)) {
        return []
      }
      
      let filtered = testCasesData.tests

      if (searchText) {
        const searchLower = searchText.toLowerCase()
        filtered = filtered.filter(test => {
          try {
            return (
              (test.name && test.name.toLowerCase().includes(searchLower)) ||
              (test.description && test.description.toLowerCase().includes(searchLower)) ||
              (test.target_subsystem && test.target_subsystem.toLowerCase().includes(searchLower))
            )
          } catch (error) {
            return false
          }
        })
      }

      if (filters.subsystem) {
        filtered = filtered.filter(test => test.target_subsystem === filters.subsystem)
      }

      if (filters.generationMethod) {
        filtered = filtered.filter(test => {
          const method = test.metadata?.generation_method || test.generation_info?.method || 'manual'
          return method === filters.generationMethod
        })
      }

      if (filters.status) {
        filtered = filtered.filter(test => {
          const status = test.metadata?.execution_status || 'never_run'
          return status === filters.status
        })
      }

      return filtered
    } catch (error) {
      console.error('Error in filteredTests calculation:', error)
      return []
    }
  }, [testCasesData?.tests, searchText, filters, dateRange])

  // Delete handlers
  const handleDeleteTest = async (testId: string) => {
    try {
      console.log('Deleting test:', testId)
      
      const test = filteredTests.find(t => t.id === testId)
      const testName = test?.name || testId
      
      await apiService.deleteTest(testId)
      
      message.success(`Successfully deleted test case: ${testName}`)
      
      if (selectedRowKeys.includes(testId)) {
        setSelectedRowKeys(prev => prev.filter(id => id !== testId))
      }
      
      refetch()
    } catch (error: any) {
      console.error('Failed to delete test:', error)
      
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
    if (selectedRowKeys.length === 0) {
      message.warning('Please select at least one test case to delete')
      return
    }

    setBulkOperationInProgress(true)
    setBulkOperationType('delete')
    setBulkOperationProgress(0)

    try {
      const selectedTests = filteredTests.filter(test => selectedRowKeys.includes(test.id))
      message.info(`Deleting ${selectedTests.length} test cases...`)
      
      let successCount = 0
      let failureCount = 0
      
      for (let i = 0; i < selectedTests.length; i++) {
        const test = selectedTests[i]
        setBulkOperationProgress(((i + 1) / selectedTests.length) * 100)
        
        try {
          await apiService.deleteTest(test.id)
          console.log(`Successfully deleted test: ${test.name}`)
          successCount++
        } catch (error) {
          console.error(`Failed to delete test ${test.name}:`, error)
          failureCount++
        }
      }
      
      setSelectedRowKeys([])
      
      if (failureCount === 0) {
        message.success(`Successfully deleted ${successCount} test cases`)
      } else if (successCount === 0) {
        message.error(`Failed to delete all ${selectedTests.length} test cases`)
      } else {
        message.warning(`Deleted ${successCount} test cases, ${failureCount} failed`)
      }
      
      refetch()
    } catch (error) {
      console.error('Bulk delete failed:', error)
      message.error('Bulk delete operation failed')
    } finally {
      setBulkOperationInProgress(false)
      setBulkOperationType('')
      setBulkOperationProgress(0)
    }
  }

  // Other handlers
  const handleViewTest = (testId: string) => {
    const test = filteredTests.find(t => t.id === testId)
    if (test) {
      setSelectedTestCase(test)
      setModalMode('view')
      setModalVisible(true)
    }
  }

  const handleEditTest = (testId: string) => {
    const test = filteredTests.find(t => t.id === testId)
    if (test) {
      setSelectedTestCase(test)
      setModalMode('edit')
      setModalVisible(true)
    }
  }

  const handleExecuteTests = (testIds: string[]) => {
    message.success(`Starting execution of ${testIds.length} test case${testIds.length !== 1 ? 's' : ''}`)
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      console.log('Saving test case:', updatedTestCase)
      refetch()
    } catch (error) {
      console.error('Failed to save test case:', error)
      throw error
    }
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedTestCase(null)
  }

  // Calculate statistics
  const totalTests = filteredTests?.length || 0
  const neverRunTests = filteredTests.filter(t => !t?.metadata?.last_execution).length
  const aiGeneratedTests = filteredTests.filter(t => {
    const method = t?.metadata?.generation_method || t?.generation_info?.method
    return method && method !== 'manual'
  }).length
  const manualTests = Math.max(0, totalTests - aiGeneratedTests)

  // Table columns with prominent delete buttons
  const columns = [
    {
      title: 'Select',
      width: 60,
      render: (record: EnhancedTestCase) => (
        <Checkbox
          checked={selectedRowKeys.includes(record.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedRowKeys(prev => [...prev, record.id])
            } else {
              setSelectedRowKeys(prev => prev.filter(id => id !== record.id))
            }
          }}
        />
      ),
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (name: string, record: EnhancedTestCase) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: '14px' }}>
            {name}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description?.substring(0, 60)}
            {record.description && record.description.length > 60 ? '...' : ''}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 120,
      render: (type: string) => {
        const colors = {
          unit: 'blue',
          integration: 'green',
          performance: 'orange',
          security: 'red',
          fuzz: 'purple',
        }
        return (
          <Tag color={colors[type as keyof typeof colors] || 'default'}>
            {type?.toUpperCase() || 'UNKNOWN'}
          </Tag>
        )
      },
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (record: EnhancedTestCase) => {
        const executionStatus = record.metadata?.execution_status || 'never_run'
        
        const statusConfig = {
          never_run: { color: 'default', text: 'Never Run' },
          running: { color: 'processing', text: 'Running' },
          completed: { color: 'success', text: 'Passed' },
          failed: { color: 'error', text: 'Failed' },
        }
        
        const config = statusConfig[executionStatus as keyof typeof statusConfig] || statusConfig.never_run
        
        return (
          <Badge 
            status={config.color as any} 
            text={config.text}
          />
        )
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 250,
      fixed: 'right' as const,
      render: (record: EnhancedTestCase) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewTest(record.id)}
            />
          </Tooltip>
          <Tooltip title="Edit Test">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditTest(record.id)}
            />
          </Tooltip>
          <Tooltip title="Execute Test">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleExecuteTests([record.id])}
              style={{ color: '#52c41a' }}
            />
          </Tooltip>
          <Tooltip title="Delete Test">
            <Popconfirm
              title="Delete Test Case"
              description={
                <div>
                  <p>Are you sure you want to delete "{record.name}"?</p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#8c8c8c' }}>
                    This action cannot be undone.
                  </p>
                </div>
              }
              onConfirm={() => handleDeleteTest(record.id)}
              okText="Yes, Delete"
              cancelText="Cancel"
              okType="danger"
              icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
            >
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                danger
                style={{ 
                  color: '#ff4d4f',
                  borderColor: '#ff4d4f',
                  backgroundColor: '#fff2f0'
                }}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  if (error && !isLoading) {
    return (
      <div style={{ padding: '0 24px' }}>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Title level={3}>Unable to load test cases</Title>
          <p>Error: {error instanceof Error ? error.message : 'Unknown error'}</p>
          <Space>
            <Button onClick={() => refetch()} type="primary">
              Retry
            </Button>
            <Button onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </Space>
        </div>
      </div>
    )
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
        <Title level={2} style={{ margin: 0 }}>Test Cases (With Prominent Delete)</Title>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => setIsAIGenModalVisible(true)}
            disabled={bulkOperationInProgress}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            disabled={bulkOperationInProgress}
          >
            Create Test
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              refetch()
              message.info('Refreshing test case list...')
            }}
            disabled={bulkOperationInProgress}
            type="default"
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Delete Functionality Alert */}
      <Alert
        message="Delete Functionality Available"
        description={
          <div>
            <p><strong>Individual Delete:</strong> Click the red trash icon (🗑️) in the Actions column of any test case</p>
            <p><strong>Bulk Delete:</strong> Select multiple test cases and use the "Delete Selected" button below</p>
          </div>
        }
        type="success"
        showIcon
        style={{ marginBottom: 16 }}
      />

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
              title="Never Run"
              value={neverRunTests}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Prominent Bulk Delete Section */}
      {selectedRowKeys.length > 0 && (
        <Card 
          style={{ 
            marginBottom: 24, 
            borderColor: '#ff4d4f',
            backgroundColor: '#fff2f0'
          }}
        >
          <Row align="middle" justify="space-between">
            <Col>
              <Space>
                <Text strong style={{ color: '#ff4d4f' }}>
                  {selectedRowKeys.length} test case{selectedRowKeys.length !== 1 ? 's' : ''} selected
                </Text>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={<PlayCircleOutlined />}
                  onClick={() => handleExecuteTests(selectedRowKeys)}
                  disabled={bulkOperationInProgress}
                >
                  Execute Selected
                </Button>
                <Popconfirm
                  title="Delete Selected Test Cases"
                  description={`Are you sure you want to delete ${selectedRowKeys.length} test case${selectedRowKeys.length !== 1 ? 's' : ''}? This action cannot be undone.`}
                  onConfirm={handleBulkDelete}
                  okText="Yes, Delete All"
                  cancelText="Cancel"
                  okType="danger"
                  icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
                  disabled={bulkOperationInProgress}
                >
                  <Button
                    icon={<DeleteOutlined />}
                    danger
                    loading={bulkOperationInProgress && bulkOperationType === 'delete'}
                    disabled={bulkOperationInProgress}
                    style={{ 
                      backgroundColor: '#ff4d4f',
                      borderColor: '#ff4d4f',
                      color: 'white'
                    }}
                  >
                    Delete Selected ({selectedRowKeys.length})
                  </Button>
                </Popconfirm>
                <Button
                  icon={<CloseOutlined />}
                  onClick={() => setSelectedRowKeys([])}
                  disabled={bulkOperationInProgress}
                >
                  Clear Selection
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Bulk Operation Progress */}
      {bulkOperationInProgress && (
        <Card style={{ marginBottom: 24, borderColor: '#1890ff' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>
                {bulkOperationType === 'delete' && 'Deleting test cases...'}
              </Text>
              <Text type="secondary">
                {Math.round(bulkOperationProgress)}% complete
              </Text>
            </div>
            <Progress 
              percent={bulkOperationProgress} 
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </Space>
        </Card>
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
              allowClear
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
            </Select>
          </Col>
          <Col span={4}>
            <Button
              onClick={() => {
                setSearchText('')
                setFilters({
                  testType: undefined,
                  subsystem: undefined,
                  generationMethod: undefined,
                  status: undefined,
                })
              }}
            >
              Clear Filters
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        <Table
          columns={columns}
          dataSource={filteredTests}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: filteredTests.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} test cases`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          size="middle"
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