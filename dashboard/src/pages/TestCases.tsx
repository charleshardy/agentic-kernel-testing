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
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import dayjs from 'dayjs'
import TestCaseTable from '../components/TestCaseTable'
import TestCaseModal from '../components/TestCaseModal'
import AIGenerationProgress from '../components/AIGenerationProgress'
import KernelDriverInfo from '../components/KernelDriverInfo'
import apiService, { TestCase, EnhancedTestCase } from '../services/api'
import useAIGeneration from '../hooks/useAIGeneration'

const { Title } = Typography
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
  const [sortConfig, setSortConfig] = useState<{
    field?: string
    order?: 'ascend' | 'descend'
  }>({
    field: searchParams.get('sortField') || undefined,
    order: (searchParams.get('sortOrder') as 'ascend' | 'descend') || undefined,
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
  
  // Bulk tagging modal state
  const [bulkTagModalVisible, setBulkTagModalVisible] = useState(false)
  const [bulkTagForm] = Form.useForm()

  // AI Generation hook that preserves current filters and pagination
  const { generateFromDiff, generateFromFunction, generateKernelDriver, isGenerating } = useAIGeneration({
    onSuccess: (response, type) => {
      setIsAIGenModalVisible(false)
      aiGenForm.resetFields()
      // Force immediate refresh of the test list
      setTimeout(() => {
        refetch()
      }, 1000) // Small delay to ensure backend has processed the new tests
    },
    preserveFilters: true,
    enableOptimisticUpdates: true, // Enable optimistic updates for better UX
  })

  // Update URL when state changes
  useEffect(() => {
    const params = new URLSearchParams()
    
    if (searchText) params.set('search', searchText)
    if (filters.testType) params.set('type', filters.testType)
    if (filters.subsystem) params.set('subsystem', filters.subsystem)
    if (filters.generationMethod) params.set('generation', filters.generationMethod)
    if (filters.status) params.set('status', filters.status)
    if (pagination.current !== 1) params.set('page', pagination.current.toString())
    if (pagination.pageSize !== 20) params.set('pageSize', pagination.pageSize.toString())
    if (sortConfig.field) params.set('sortField', sortConfig.field)
    if (sortConfig.order) params.set('sortOrder', sortConfig.order)
    
    setSearchParams(params, { replace: true })
  }, [searchText, filters, pagination, sortConfig, setSearchParams])

  // Fetch test cases with filters
  const { data: testCasesData, isLoading, error, refetch } = useQuery(
    ['testCases', searchText, filters, dateRange],
    () => apiService.getTests({
      page: 1,
      page_size: 50,
      // Add filter parameters when backend supports them
      test_type: filters.testType,
      status: filters.status,
    }),
    {
      refetchInterval: 5000, // Refresh every 5 seconds for more responsive updates
      refetchOnWindowFocus: true, // Refetch when window gains focus
      retry: 3, // Retry failed requests 3 times
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
      onError: (error) => {
        console.error('Failed to fetch test cases:', error)
      },
      onSuccess: (data) => {
        console.log('Successfully fetched test cases:', data)
      }
    }
  )

  // Client-side filtering for now (until backend supports all filters)
  const filteredTests = React.useMemo(() => {
    try {
      if (!testCasesData?.tests || !Array.isArray(testCasesData.tests)) {
        return []
      }
      
      let filtered = testCasesData.tests

      // Search text filter
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
            console.warn('Error filtering test by search text:', test, error)
            return false
          }
        })
      }

      // Subsystem filter
      if (filters.subsystem) {
        filtered = filtered.filter(test => {
          try {
            return test.target_subsystem === filters.subsystem
          } catch (error) {
            console.warn('Error filtering test by subsystem:', test, error)
            return false
          }
        })
      }

      // Generation method filter
      if (filters.generationMethod) {
        filtered = filtered.filter(test => {
          try {
            const method = test.metadata?.generation_method || test.generation_info?.method || 'manual'
            return method === filters.generationMethod
          } catch (error) {
            console.warn('Error filtering test by generation method:', test, error)
            return false
          }
        })
      }

      // Status filter (based on execution status)
      if (filters.status) {
        filtered = filtered.filter(test => {
          try {
            const status = test.metadata?.execution_status || 'never_run'
            return status === filters.status
          } catch (error) {
            console.warn('Error filtering test by status:', test, error)
            return false
          }
        })
      }

      // Date range filter
      if (dateRange && dateRange[0] && dateRange[1]) {
        const startDate = dateRange[0].startOf('day')
        const endDate = dateRange[1].endOf('day')
        filtered = filtered.filter(test => {
          try {
            const createdAt = dayjs(test.created_at)
            return createdAt.isAfter(startDate) && createdAt.isBefore(endDate)
          } catch (error) {
            console.warn('Error filtering test by date range:', test, error)
            return false
          }
        })
      }

      return filtered
    } catch (error) {
      console.error('Error in filteredTests calculation:', error)
      return []
    }
  }, [testCasesData?.tests, searchText, filters, dateRange])

  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
    { label: 'Fuzz Test', value: 'fuzz' },
  ]

  const subsystems = [
    { label: 'Kernel Core', value: 'kernel/core' },
    { label: 'Memory Management', value: 'kernel/mm' },
    { label: 'File System', value: 'kernel/fs' },
    { label: 'Networking', value: 'kernel/net' },
    { label: 'Block Drivers', value: 'drivers/block' },
    { label: 'Character Drivers', value: 'drivers/char' },
    { label: 'Network Drivers', value: 'drivers/net' },
    { label: 'x86 Architecture', value: 'arch/x86' },
    { label: 'ARM64 Architecture', value: 'arch/arm64' },
  ]

  const generationMethods = [
    { label: 'Manual', value: 'manual' },
    { label: 'AI from Diff', value: 'ai_diff' },
    { label: 'AI from Function', value: 'ai_function' },
    { label: 'AI Kernel Driver', value: 'ai_kernel_driver' },
  ]

  const statusOptions = [
    { label: 'Never Run', value: 'never_run' },
    { label: 'Running', value: 'running' },
    { label: 'Completed', value: 'completed' },
    { label: 'Failed', value: 'failed' },
  ]

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleClearFilters = () => {
    setSearchText('')
    setFilters({
      testType: undefined,
      subsystem: undefined,
      generationMethod: undefined,
      status: undefined,
    })
    setDateRange(null)
  }

  const handleBulkAction = async (action: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select at least one test case')
      return
    }

    setBulkOperationType(action)
    setBulkOperationInProgress(true)
    setBulkOperationProgress(0)

    try {
      const selectedTests = filteredTests.filter(test => selectedRowKeys.includes(test.id))
      
      switch (action) {
        case 'execute':
          await handleBulkExecute(selectedTests)
          break
        case 'delete':
          await handleBulkDelete(selectedTests)
          break
        case 'export':
          await handleBulkExport(selectedTests)
          break
        case 'tag':
          await handleBulkTag(selectedTests)
          break
        default:
          message.error(`Unknown action: ${action}`)
      }
    } catch (error) {
      console.error(`Bulk ${action} failed:`, error)
      message.error(`Bulk ${action} operation failed`)
    } finally {
      setBulkOperationInProgress(false)
      setBulkOperationType('')
      setBulkOperationProgress(0)
    }
  }

  const handleBulkExecute = async (tests: EnhancedTestCase[]) => {
    message.info(`Starting execution of ${tests.length} test cases...`)
    
    for (let i = 0; i < tests.length; i++) {
      const test = tests[i]
      setBulkOperationProgress(((i + 1) / tests.length) * 100)
      
      try {
        // Simulate API call - replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`Executing test: ${test.name}`)
        // TODO: Call actual API - apiService.executeTest(test.id)
      } catch (error) {
        console.error(`Failed to execute test ${test.name}:`, error)
      }
    }
    
    message.success(`Successfully started execution of ${tests.length} test cases`)
    setSelectedRowKeys([])
    refetch()
  }

  const handleBulkDelete = async (tests: EnhancedTestCase[]) => {
    message.info(`Deleting ${tests.length} test cases...`)
    
    let successCount = 0
    let failureCount = 0
    
    for (let i = 0; i < tests.length; i++) {
      const test = tests[i]
      setBulkOperationProgress(((i + 1) / tests.length) * 100)
      
      try {
        // Call actual API to delete the test
        await apiService.deleteTest(test.id)
        console.log(`Successfully deleted test: ${test.name}`)
        successCount++
      } catch (error) {
        console.error(`Failed to delete test ${test.name}:`, error)
        failureCount++
      }
    }
    
    // Clear selected rows immediately to prevent state issues
    setSelectedRowKeys([])
    
    // Show appropriate message based on results
    if (failureCount === 0) {
      message.success(`Successfully deleted ${successCount} test cases`)
    } else if (successCount === 0) {
      message.error(`Failed to delete all ${tests.length} test cases`)
    } else {
      message.warning(`Deleted ${successCount} test cases, ${failureCount} failed`)
    }
    
    // Refresh the data
    try {
      await refetch()
    } catch (error) {
      console.error('Failed to refresh test list after deletion:', error)
      // Force a page reload if refetch fails
      window.location.reload()
    }
  }

  const handleBulkExport = async (tests: EnhancedTestCase[]) => {
    message.info(`Exporting ${tests.length} test cases...`)
    
    try {
      // Simulate export processing
      setBulkOperationProgress(25)
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setBulkOperationProgress(50)
      const exportData = {
        exported_at: new Date().toISOString(),
        test_cases: tests.map(test => ({
          id: test.id,
          name: test.name,
          description: test.description,
          test_type: test.test_type,
          target_subsystem: test.target_subsystem,
          test_script: test.test_script,
          metadata: test.metadata,
          created_at: test.created_at,
        }))
      }
      
      setBulkOperationProgress(75)
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Create and download file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `test-cases-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      setBulkOperationProgress(100)
      message.success(`Successfully exported ${tests.length} test cases`)
      setSelectedRowKeys([])
    } catch (error) {
      console.error('Export failed:', error)
      message.error('Export operation failed')
    }
  }

  const handleBulkTag = async (tests: EnhancedTestCase[]) => {
    // This will be called from the modal form submission
    // The actual implementation is in handleBulkTagSubmit
  }

  const handleBulkTagSubmit = async (values: any) => {
    const { tags, action } = values
    const selectedTests = filteredTests.filter(test => selectedRowKeys.includes(test.id))
    
    setBulkOperationInProgress(true)
    setBulkOperationType('tag')
    setBulkOperationProgress(0)
    
    try {
      message.info(`${action === 'add' ? 'Adding' : 'Removing'} tags for ${selectedTests.length} test cases...`)
      
      for (let i = 0; i < selectedTests.length; i++) {
        const test = selectedTests[i]
        setBulkOperationProgress(((i + 1) / selectedTests.length) * 100)
        
        try {
          // Simulate API call - replace with actual API call
          await new Promise(resolve => setTimeout(resolve, 200))
          console.log(`${action === 'add' ? 'Adding' : 'Removing'} tags for test: ${test.name}`, tags)
          // TODO: Call actual API - apiService.updateTestTags(test.id, tags, action)
        } catch (error) {
          console.error(`Failed to update tags for test ${test.name}:`, error)
        }
      }
      
      message.success(`Successfully ${action === 'add' ? 'added' : 'removed'} tags for ${selectedTests.length} test cases`)
      setSelectedRowKeys([])
      setBulkTagModalVisible(false)
      bulkTagForm.resetFields()
      refetch()
    } catch (error) {
      console.error('Bulk tagging failed:', error)
      message.error('Bulk tagging operation failed')
    } finally {
      setBulkOperationInProgress(false)
      setBulkOperationType('')
      setBulkOperationProgress(0)
    }
  }

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
      refetch()
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

  const handleExecuteTests = (testIds: string[]) => {
    console.log('Execute tests:', testIds)
    // TODO: Implement execute functionality
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      // TODO: Implement API call to update test case
      console.log('Saving test case:', updatedTestCase)
      
      // For now, just update local state
      // In real implementation, this would call apiService.updateTest()
      
      // Refresh the test list
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

  const handleTableChange = (paginationConfig: any, filters: any, sorter: any) => {
    setPagination({
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
    })
    
    if (sorter.field) {
      setSortConfig({
        field: sorter.field,
        order: sorter.order,
      })
    } else {
      setSortConfig({})
    }
  }

  const handleSelectAll = () => {
    const selectableTests = filteredTests.filter(test => 
      test.metadata?.execution_status !== 'running'
    )
    setSelectedRowKeys(selectableTests.map(test => test.id))
  }

  const handleSelectNone = () => {
    setSelectedRowKeys([])
  }

  // Clear selected rows if they no longer exist in the filtered tests
  React.useEffect(() => {
    if (selectedRowKeys.length > 0 && filteredTests.length > 0) {
      const existingIds = new Set(filteredTests.map(test => test.id))
      const validSelectedKeys = selectedRowKeys.filter(key => existingIds.has(key))
      
      if (validSelectedKeys.length !== selectedRowKeys.length) {
        setSelectedRowKeys(validSelectedKeys)
      }
    } else if (selectedRowKeys.length > 0 && filteredTests.length === 0) {
      // Clear all selections if no tests remain
      setSelectedRowKeys([])
    }
  }, [filteredTests, selectedRowKeys])

  const handleSelectByType = (testType: string) => {
    const testsOfType = filteredTests.filter(test => 
      test.test_type === testType && test.metadata?.execution_status !== 'running'
    )
    setSelectedRowKeys(testsOfType.map(test => test.id))
  }

  const handleSelectByStatus = (status: string) => {
    const testsWithStatus = filteredTests.filter(test => {
      const testStatus = test.metadata?.execution_status || 'never_run'
      return testStatus === status && testStatus !== 'running'
    })
    setSelectedRowKeys(testsWithStatus.map(test => test.id))
  }

  // Calculate statistics based on filtered data with error handling
  const totalTests = filteredTests?.length || 0
  const neverRunTests = React.useMemo(() => {
    try {
      return filteredTests.filter(t => !t?.metadata?.last_execution).length
    } catch (error) {
      console.warn('Error calculating neverRunTests:', error)
      return 0
    }
  }, [filteredTests])
  
  const aiGeneratedTests = React.useMemo(() => {
    try {
      return filteredTests.filter(t => {
        const method = t?.metadata?.generation_method || t?.generation_info?.method
        return method && method !== 'manual'
      }).length
    } catch (error) {
      console.warn('Error calculating aiGeneratedTests:', error)
      return 0
    }
  }, [filteredTests])
  
  const manualTests = Math.max(0, totalTests - aiGeneratedTests)



  // Show error state if there's an actual error
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
        <Title level={2} style={{ margin: 0 }}>Test Cases</Title>
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
            onClick={() => {/* TODO: Navigate to test creation */}}
            disabled={bulkOperationInProgress}
          >
            Create Test
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={() => handleBulkAction('export')}
            disabled={selectedRowKeys.length === 0 || bulkOperationInProgress}
          >
            Export Selected
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

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="Search test cases..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Test Type"
              value={filters.testType}
              onChange={(value) => handleFilterChange('testType', value)}
              options={testTypes}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Subsystem"
              value={filters.subsystem}
              onChange={(value) => handleFilterChange('subsystem', value)}
              options={subsystems}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Generation Method"
              value={filters.generationMethod}
              onChange={(value) => handleFilterChange('generationMethod', value)}
              options={generationMethods}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Status"
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
              options={statusOptions}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={2}>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={handleClearFilters}
              >
                Clear
              </Button>
            </Space>
          </Col>
        </Row>
        
        <Divider style={{ margin: '16px 0' }} />
        
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              placeholder={['Start Date', 'End Date']}
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={16}>
            {selectedRowKeys.length > 0 ? (
              <Space wrap>
                <span style={{ fontWeight: 500 }}>
                  {selectedRowKeys.length} test case{selectedRowKeys.length !== 1 ? 's' : ''} selected
                </span>
                <Divider type="vertical" />
                <Popconfirm
                  title="Execute Selected Test Cases"
                  description={
                    <div>
                      <p>Execute {selectedRowKeys.length} test case{selectedRowKeys.length !== 1 ? 's' : ''}?</p>
                      <p style={{ margin: 0, fontSize: '12px', color: '#8c8c8c' }}>
                        This will create execution plans and start running the selected tests.
                      </p>
                    </div>
                  }
                  onConfirm={() => handleBulkAction('execute')}
                  okText="Yes, Execute"
                  cancelText="Cancel"
                  icon={<PlayCircleOutlined style={{ color: '#52c41a' }} />}
                  disabled={bulkOperationInProgress}
                >
                  <Button
                    size="small"
                    icon={<PlayCircleOutlined />}
                    loading={bulkOperationInProgress && bulkOperationType === 'execute'}
                    disabled={bulkOperationInProgress}
                  >
                    Execute
                  </Button>
                </Popconfirm>
                <Popconfirm
                  title="Export Selected Test Cases"
                  description={
                    <div>
                      <p>Export {selectedRowKeys.length} test case{selectedRowKeys.length !== 1 ? 's' : ''} to JSON file?</p>
                      <p style={{ margin: 0, fontSize: '12px', color: '#8c8c8c' }}>
                        This will download a JSON file containing all selected test case data.
                      </p>
                    </div>
                  }
                  onConfirm={() => handleBulkAction('export')}
                  okText="Yes, Export"
                  cancelText="Cancel"
                  icon={<DownloadOutlined style={{ color: '#1890ff' }} />}
                  disabled={bulkOperationInProgress}
                >
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    loading={bulkOperationInProgress && bulkOperationType === 'export'}
                    disabled={bulkOperationInProgress}
                  >
                    Export
                  </Button>
                </Popconfirm>
                <Button
                  size="small"
                  icon={<TagOutlined />}
                  onClick={() => setBulkTagModalVisible(true)}
                  disabled={bulkOperationInProgress}
                >
                  Tag
                </Button>
                <Popconfirm
                  title="Delete Selected Test Cases"
                  description={`Are you sure you want to delete ${selectedRowKeys.length} test case${selectedRowKeys.length !== 1 ? 's' : ''}? This action cannot be undone.`}
                  onConfirm={() => handleBulkAction('delete')}
                  okText="Yes, Delete"
                  cancelText="Cancel"
                  okType="danger"
                  icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
                  disabled={bulkOperationInProgress}
                >
                  <Button
                    size="small"
                    icon={<DeleteOutlined />}
                    danger
                    loading={bulkOperationInProgress && bulkOperationType === 'delete'}
                    disabled={bulkOperationInProgress}
                  >
                    Delete
                  </Button>
                </Popconfirm>
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={handleSelectNone}
                  disabled={bulkOperationInProgress}
                >
                  Clear Selection
                </Button>
              </Space>
            ) : (
              <Space wrap>
                <span style={{ color: '#8c8c8c' }}>Quick select:</span>
                <Button size="small" onClick={handleSelectAll}>
                  All
                </Button>
                <Button size="small" onClick={() => handleSelectByStatus('never_run')}>
                  Never Run
                </Button>
                <Button size="small" onClick={() => handleSelectByStatus('failed')}>
                  Failed
                </Button>
                <Button size="small" onClick={() => handleSelectByType('unit')}>
                  Unit Tests
                </Button>
                <Button size="small" onClick={() => handleSelectByType('integration')}>
                  Integration Tests
                </Button>
                <Divider type="vertical" />
                <span style={{ color: '#1890ff', fontSize: '12px' }}>
                  💡 Select test cases to see bulk actions (Execute, Export, Tag, Delete)
                </span>
              </Space>
            )}
          </Col>
        </Row>
      </Card>

      {/* AI Generation Progress */}
      <AIGenerationProgress 
        isGenerating={isGenerating}
        message="Generating test cases and updating the list..."
      />

      {/* Bulk Operation Progress */}
      {bulkOperationInProgress && (
        <Card style={{ marginBottom: 24, borderColor: '#1890ff' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>
                {bulkOperationType === 'execute' && 'Executing test cases...'}
                {bulkOperationType === 'delete' && 'Deleting test cases...'}
                {bulkOperationType === 'export' && 'Exporting test cases...'}
                {bulkOperationType === 'tag' && 'Tagging test cases...'}
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

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        {/* Bulk Actions Help */}
        {totalTests > 0 && selectedRowKeys.length === 0 && (
          <div style={{ 
            marginBottom: 16, 
            padding: 12, 
            backgroundColor: '#f6ffed', 
            border: '1px solid #b7eb8f', 
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <span style={{ fontSize: '16px' }}>💡</span>
            <div>
              <Text strong style={{ color: '#52c41a' }}>Bulk Actions Available:</Text>
              <Text style={{ marginLeft: 8, color: '#8c8c8c' }}>
                Select test cases using checkboxes to access bulk operations including 
                <Text strong style={{ color: '#ff4d4f' }}> Delete</Text>, Execute, Export, and Tag
              </Text>
            </div>
          </div>
        )}
        
        <TestCaseTable
          tests={filteredTests || []}
          loading={isLoading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: (filteredTests || []).length,
          }}
          sortConfig={sortConfig}
          onRefresh={refetch}
          onSelect={setSelectedRowKeys}
          selectedRowKeys={selectedRowKeys || []}
          onTableChange={handleTableChange}
          onView={handleViewTest}
          onEdit={handleEditTest}
          onDelete={handleDeleteTest}
          onExecute={handleExecuteTests}
        />
      </Card>

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={isAIGenModalVisible}
        onCancel={() => setIsAIGenModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={aiGenType === 'diff' ? 'primary' : 'default'}
              icon={<CodeOutlined />}
              onClick={() => setAIGenType('diff')}
            >
              From Code Diff
            </Button>
            <Button
              type={aiGenType === 'function' ? 'primary' : 'default'}
              icon={<FunctionOutlined />}
              onClick={() => setAIGenType('function')}
            >
              From Function
            </Button>
            <Button
              type={aiGenType === 'kernel' ? 'primary' : 'default'}
              icon={<RobotOutlined />}
              onClick={() => setAIGenType('kernel')}
            >
              Kernel Test Driver
            </Button>
          </Space>
        </div>

        <KernelDriverInfo visible={aiGenType === 'kernel'} />

        {aiGenType === 'diff' ? (
          <Form
            form={aiGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateFromDiff({
                diff: values.diff,
                maxTests: values.maxTests || 20,
                testTypes: values.testTypes || ['unit']
              })
            }}
          >
            <Form.Item
              name="diff"
              label="Code Diff"
              rules={[{ required: true, message: 'Please paste your git diff' }]}
            >
              <TextArea
                rows={8}
                placeholder="Paste your git diff here..."
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="maxTests"
                  label="Max Tests to Generate"
                  initialValue={20}
                >
                  <Input type="number" min={1} max={100} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="testTypes"
                  label="Test Types"
                  initialValue={['unit']}
                >
                  <Select
                    mode="multiple"
                    placeholder="Select test types"
                    options={testTypes}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setIsAIGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        ) : aiGenType === 'function' ? (
          <Form
            form={aiGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateFromFunction({
                functionName: values.functionName,
                filePath: values.filePath,
                subsystem: values.subsystem || 'unknown',
                maxTests: values.maxTests || 10
              })
            }}
          >
            <Form.Item
              name="functionName"
              label="Function Name"
              rules={[{ required: true, message: 'Please enter function name' }]}
            >
              <Input placeholder="e.g., schedule_task" />
            </Form.Item>

            <Form.Item
              name="filePath"
              label="File Path"
              rules={[{ required: true, message: 'Please enter file path' }]}
            >
              <Input placeholder="e.g., kernel/sched/core.c" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="subsystem"
                  label="Subsystem"
                  initialValue="unknown"
                >
                  <Select
                    placeholder="Select subsystem"
                    options={subsystems}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="maxTests"
                  label="Max Tests to Generate"
                  initialValue={10}
                >
                  <Input type="number" min={1} max={50} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setIsAIGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        ) : (
          <Form
            form={aiGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateKernelDriver({
                functionName: values.functionName,
                filePath: values.filePath,
                subsystem: values.subsystem || 'unknown',
                testTypes: values.testTypes || ['unit', 'integration']
              })
            }}
          >
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: 4 }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                <ExclamationCircleOutlined style={{ color: '#fa8c16', marginRight: 8 }} />
                <strong>Kernel Test Driver Generation</strong>
              </div>
              <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                This generates a complete kernel module (.ko) that tests kernel functions directly in kernel space.
                Requires root privileges and kernel headers for compilation and execution.
              </div>
            </div>

            <Form.Item
              name="functionName"
              label="Kernel Function Name"
              rules={[{ required: true, message: 'Please enter kernel function name' }]}
            >
              <Input placeholder="e.g., kmalloc, schedule, netif_rx" />
            </Form.Item>

            <Form.Item
              name="filePath"
              label="Source File Path"
              rules={[{ required: true, message: 'Please enter source file path' }]}
            >
              <Input placeholder="e.g., mm/slab.c, kernel/sched/core.c, net/core/dev.c" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="subsystem"
                  label="Kernel Subsystem"
                  initialValue="unknown"
                >
                  <Select
                    placeholder="Select kernel subsystem"
                    options={subsystems}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="testTypes"
                  label="Test Types"
                  initialValue={['unit', 'integration']}
                >
                  <Select
                    mode="multiple"
                    placeholder="Select test types"
                    options={[
                      { label: 'Unit Tests', value: 'unit' },
                      { label: 'Integration Tests', value: 'integration' },
                      { label: 'Performance Tests', value: 'performance' },
                      { label: 'Stress Tests', value: 'stress' },
                      { label: 'Error Injection', value: 'error_injection' },
                      { label: 'Concurrency Tests', value: 'concurrency' }
                    ]}
                  />
                </Form.Item>
              </Col>
            </Row>

            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4 }}>
              <div style={{ fontSize: '12px', color: '#52c41a', fontWeight: 500, marginBottom: 4 }}>
                Generated Kernel Driver Will Include:
              </div>
              <ul style={{ fontSize: '12px', color: '#8c8c8c', margin: 0, paddingLeft: 16 }}>
                <li>Complete kernel module source code (.c file)</li>
                <li>Makefile for compilation</li>
                <li>Installation and test execution scripts</li>
                <li>Comprehensive test functions for the target kernel function</li>
                <li>/proc interface for result collection</li>
                <li>Proper cleanup and error handling</li>
              </ul>
            </div>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setIsAIGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Kernel Driver
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
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

      {/* Bulk Tagging Modal */}
      <Modal
        title={`Manage Tags for ${selectedRowKeys.length} Test Case${selectedRowKeys.length !== 1 ? 's' : ''}`}
        open={bulkTagModalVisible}
        onCancel={() => {
          setBulkTagModalVisible(false)
          bulkTagForm.resetFields()
        }}
        footer={null}
        width={500}
      >
        <Form
          form={bulkTagForm}
          layout="vertical"
          onFinish={handleBulkTagSubmit}
          initialValues={{ action: 'add' }}
        >
          <Form.Item
            name="action"
            label="Action"
          >
            <Select>
              <Select.Option value="add">Add Tags</Select.Option>
              <Select.Option value="remove">Remove Tags</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="tags"
            label="Tags"
            rules={[{ required: true, message: 'Please enter at least one tag' }]}
          >
            <Select
              mode="tags"
              placeholder="Enter tags (press Enter to add)"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
              options={[
                { label: 'critical', value: 'critical' },
                { label: 'regression', value: 'regression' },
                { label: 'performance', value: 'performance' },
                { label: 'security', value: 'security' },
                { label: 'experimental', value: 'experimental' },
                { label: 'stable', value: 'stable' },
                { label: 'deprecated', value: 'deprecated' },
              ]}
            />
          </Form.Item>

          <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f6f6f6', borderRadius: 4 }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Selected test cases: {selectedRowKeys.length}
              <br />
              This operation will affect all selected test cases.
            </Text>
          </div>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button 
                onClick={() => {
                  setBulkTagModalVisible(false)
                  bulkTagForm.resetFields()
                }}
              >
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={bulkOperationInProgress && bulkOperationType === 'tag'}
                icon={<TagOutlined />}
              >
                Apply Tags
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TestCases