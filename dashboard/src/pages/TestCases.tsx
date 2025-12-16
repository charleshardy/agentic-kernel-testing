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
} from 'antd'
import {
  ReloadOutlined,
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import dayjs from 'dayjs'
import TestCaseTable from '../components/TestCaseTable'
import TestCaseModal from '../components/TestCaseModal'
import apiService, { TestCase } from '../services/api'

const { Title } = Typography
const { RangePicker } = DatePicker

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
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

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
  const { data: testCasesData, isLoading, refetch } = useQuery(
    ['testCases', searchText, filters, dateRange],
    () => apiService.getTests({
      page: 1,
      page_size: 50,
      // Add filter parameters when backend supports them
      test_type: filters.testType,
      status: filters.status,
    }),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  // Client-side filtering for now (until backend supports all filters)
  const filteredTests = React.useMemo(() => {
    if (!testCasesData?.tests) return []
    
    let filtered = testCasesData.tests

    // Search text filter
    if (searchText) {
      const searchLower = searchText.toLowerCase()
      filtered = filtered.filter(test => 
        test.name.toLowerCase().includes(searchLower) ||
        test.description?.toLowerCase().includes(searchLower) ||
        test.target_subsystem?.toLowerCase().includes(searchLower)
      )
    }

    // Subsystem filter
    if (filters.subsystem) {
      filtered = filtered.filter(test => test.target_subsystem === filters.subsystem)
    }

    // Generation method filter
    if (filters.generationMethod) {
      filtered = filtered.filter(test => {
        const method = test.metadata?.generation_method || 'manual'
        return method === filters.generationMethod
      })
    }

    // Status filter (based on execution status)
    if (filters.status) {
      filtered = filtered.filter(test => {
        const status = test.metadata?.execution_status || 'never_run'
        return status === filters.status
      })
    }

    // Date range filter
    if (dateRange && dateRange[0] && dateRange[1]) {
      const startDate = dateRange[0].startOf('day')
      const endDate = dateRange[1].endOf('day')
      filtered = filtered.filter(test => {
        const createdAt = dayjs(test.created_at)
        return createdAt.isAfter(startDate) && createdAt.isBefore(endDate)
      })
    }

    return filtered
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

  const handleBulkAction = (action: string) => {
    console.log(`Bulk ${action} for tests:`, selectedRowKeys)
    // TODO: Implement bulk actions
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

  const handleDeleteTest = (testId: string) => {
    console.log('Delete test:', testId)
    // TODO: Implement delete functionality
  }

  const handleExecuteTests = (testIds: string[]) => {
    console.log('Execute tests:', testIds)
    // TODO: Implement execute functionality
  }

  const handleSaveTest = async (updatedTestCase: TestCase) => {
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

  // Calculate statistics based on filtered data
  const totalTests = filteredTests.length
  const neverRunTests = filteredTests.filter(t => !t.metadata?.last_execution).length
  const aiGeneratedTests = filteredTests.filter(t => 
    t.metadata?.generation_method && t.metadata.generation_method !== 'manual'
  ).length
  const manualTests = totalTests - aiGeneratedTests

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
            icon={<PlusOutlined />}
            onClick={() => {/* TODO: Navigate to test creation */}}
          >
            Create Test
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={() => handleBulkAction('export')}
            disabled={selectedRowKeys.length === 0}
          >
            Export Selected
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
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
            {selectedRowKeys.length > 0 && (
              <Space>
                <span>{selectedRowKeys.length} test(s) selected</span>
                <Button
                  size="small"
                  onClick={() => handleBulkAction('execute')}
                >
                  Execute Selected
                </Button>
                <Button
                  size="small"
                  onClick={() => handleBulkAction('delete')}
                  danger
                >
                  Delete Selected
                </Button>
              </Space>
            )}
          </Col>
        </Row>
      </Card>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        <TestCaseTable
          tests={filteredTests}
          loading={isLoading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: filteredTests.length,
          }}
          sortConfig={sortConfig}
          onRefresh={refetch}
          onSelect={setSelectedRowKeys}
          selectedRowKeys={selectedRowKeys}
          onTableChange={handleTableChange}
          onView={handleViewTest}
          onEdit={handleEditTest}
          onDelete={handleDeleteTest}
          onExecute={handleExecuteTests}
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