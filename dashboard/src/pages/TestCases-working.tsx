import React, { useState } from 'react'
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
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService, { EnhancedTestCase } from '../services/api'
import useAIGeneration from '../hooks/useAIGeneration'
import KernelDriverInfo from '../components/KernelDriverInfo'
import TestCaseModal from '../components/TestCaseModal-safe'

const { Title, Text } = Typography
const { TextArea } = Input

const TestCases: React.FC = () => {
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

  // Test Case Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

  // AI Generation hook
  const { generateFromDiff, generateFromFunction, generateKernelDriver, isGenerating } = useAIGeneration({
    onSuccess: () => {
      setAiGenModalVisible(false)
      aiGenForm.resetFields()
      // Force immediate refresh of the test list
      setTimeout(() => {
        refetch()
      }, 1000)
    },
    preserveFilters: true,
    enableOptimisticUpdates: true,
  })

  // Test Case Modal handlers
  const handleViewTest = async (testId: string) => {
    try {
      // Fetch the test details from the API
      const test = await apiService.getTestById(testId)
      setSelectedTestCase(test)
      setModalMode('view')
      setModalVisible(true)
    } catch (error: any) {
      console.error('Error loading test case:', error)
      if (error.response?.status === 404) {
        message.error('Test case not found')
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
      // In a real implementation, call the API to update the test
      // await apiService.updateTest(updatedTestCase.id, updatedTestCase)
      
      // For now, just show success message
      message.success(`Test case ${updatedTestCase.name} updated successfully`)
      
      // Refresh the test list
      refetch()
    } catch (error) {
      console.error('Error updating test case:', error)
      message.error('Failed to update test case')
    }
  }

  // Fetch test cases
  const { data: testCasesData, isLoading, error, refetch } = useQuery(
    ['testCases', searchText, filters],
    () => apiService.getTests({
      page: 1,
      page_size: 50,
      test_type: filters.testType,
      status: filters.status,
    }),
    {
      refetchInterval: 10000,
      retry: false,
      onError: (error) => {
        console.log('Failed to fetch test cases (using mock data):', error)
      },
    }
  )

  // Mock data when API is not available
  const mockTestCases = [
    {
      id: 'test-001',
      name: 'Kernel Boot Test',
      description: 'Tests kernel boot sequence and initialization',
      test_type: 'integration',
      target_subsystem: 'kernel/core',
      execution_time_estimate: 45,
      created_at: '2024-01-15T10:30:00Z',
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
      execution_time_estimate: 30,
      created_at: '2024-01-15T11:00:00Z',
      metadata: {
        execution_status: 'never_run',
        generation_method: 'ai_function',
      }
    },
    {
      id: 'test-003',
      name: 'Network Driver Test',
      description: 'Tests network interface driver functionality',
      test_type: 'integration',
      target_subsystem: 'drivers/net',
      execution_time_estimate: 60,
      created_at: '2024-01-15T12:00:00Z',
      metadata: {
        execution_status: 'failed',
        generation_method: 'ai_diff',
        last_execution: '2024-01-15T15:45:00Z',
      }
    },
    {
      id: 'test-004',
      name: 'File System Stress Test',
      description: 'Stress tests file system operations',
      test_type: 'performance',
      target_subsystem: 'kernel/fs',
      execution_time_estimate: 120,
      created_at: '2024-01-15T13:00:00Z',
      metadata: {
        execution_status: 'running',
        generation_method: 'ai_kernel_driver',
        last_execution: '2024-01-15T16:00:00Z',
      }
    },
  ]

  const tests = testCasesData?.tests || mockTestCases

  // Filter tests based on search and filters
  const filteredTests = tests.filter(test => {
    const matchesSearch = !searchText || 
      test.name.toLowerCase().includes(searchText.toLowerCase()) ||
      test.description.toLowerCase().includes(searchText.toLowerCase()) ||
      test.target_subsystem.toLowerCase().includes(searchText.toLowerCase())
    
    const matchesType = !filters.testType || test.test_type === filters.testType
    const matchesSubsystem = !filters.subsystem || test.target_subsystem === filters.subsystem
    const matchesStatus = !filters.status || test.metadata?.execution_status === filters.status
    
    return matchesSearch && matchesType && matchesSubsystem && matchesStatus
  })

  // Calculate statistics
  const totalTests = filteredTests.length
  const neverRunTests = filteredTests.filter(t => t.metadata?.execution_status === 'never_run').length
  const aiGeneratedTests = filteredTests.filter(t => t.metadata?.generation_method !== 'manual').length
  const manualTests = totalTests - aiGeneratedTests

  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
  ]

  const subsystems = [
    { label: 'Kernel Core', value: 'kernel/core' },
    { label: 'Memory Management', value: 'kernel/mm' },
    { label: 'File System', value: 'kernel/fs' },
    { label: 'Networking', value: 'kernel/net' },
    { label: 'Block Drivers', value: 'drivers/block' },
    { label: 'Network Drivers', value: 'drivers/net' },
  ]

  const statusOptions = [
    { label: 'Never Run', value: 'never_run' },
    { label: 'Running', value: 'running' },
    { label: 'Completed', value: 'completed' },
    { label: 'Failed', value: 'failed' },
  ]

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
      render: (text: string, record: any) => (
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
      render: (record: any) => {
        const status = record.metadata?.execution_status || 'never_run'
        return <Tag color={getStatusColor(status)}>{status.replace('_', ' ')}</Tag>
      },
    },
    {
      title: 'Generation',
      key: 'generation',
      render: (record: any) => {
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
      render: (record: any) => (
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
    getCheckboxProps: (record: any) => ({
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
        <Typography.Title level={2 as const} style={{ margin: 0 }}>Test Cases</Typography.Title>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => setAiGenModalVisible(true)}
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
              onChange={(value) => setFilters(prev => ({ ...prev, testType: value }))}
              options={testTypes}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Subsystem"
              value={filters.subsystem}
              onChange={(value) => setFilters(prev => ({ ...prev, subsystem: value }))}
              options={subsystems}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Status"
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              options={statusOptions}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Space>
              <Button
                onClick={() => {
                  setSearchText('')
                  setFilters({ testType: undefined, subsystem: undefined, status: undefined })
                }}
              >
                Clear Filters
              </Button>
              {selectedRowKeys.length > 0 && (
                <Button
                  type="primary"
                  onClick={() => {
                    message.success(`Starting execution of ${selectedRowKeys.length} test cases`)
                    setSelectedRowKeys([])
                  }}
                >
                  Run Selected ({selectedRowKeys.length})
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

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

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={aiGenModalVisible}
        onCancel={() => setAiGenModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={aiGenType === 'diff' ? 'primary' : 'default'}
              icon={<CodeOutlined />}
              onClick={() => setAiGenType('diff')}
            >
              From Code Diff
            </Button>
            <Button
              type={aiGenType === 'function' ? 'primary' : 'default'}
              icon={<FunctionOutlined />}
              onClick={() => setAiGenType('function')}
            >
              From Function
            </Button>
            <Button
              type={aiGenType === 'kernel' ? 'primary' : 'default'}
              icon={<RobotOutlined />}
              onClick={() => setAiGenType('kernel')}
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
                <Button onClick={() => setAiGenModalVisible(false)}>
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
                    options={[
                      { label: 'Kernel Core', value: 'kernel/core' },
                      { label: 'Memory Management', value: 'kernel/mm' },
                      { label: 'File System', value: 'kernel/fs' },
                      { label: 'Networking', value: 'kernel/net' },
                      { label: 'Block Drivers', value: 'drivers/block' },
                      { label: 'Character Drivers', value: 'drivers/char' },
                      { label: 'Network Drivers', value: 'drivers/net' },
                      { label: 'x86 Architecture', value: 'arch/x86' },
                      { label: 'ARM64 Architecture', value: 'arch/arm64' },
                    ]}
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
                <Button onClick={() => setAiGenModalVisible(false)}>
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
                    options={[
                      { label: 'Kernel Core', value: 'kernel/core' },
                      { label: 'Memory Management', value: 'kernel/mm' },
                      { label: 'File System', value: 'kernel/fs' },
                      { label: 'Networking', value: 'kernel/net' },
                      { label: 'Block Drivers', value: 'drivers/block' },
                      { label: 'Character Drivers', value: 'drivers/char' },
                      { label: 'Network Drivers', value: 'drivers/net' },
                      { label: 'x86 Architecture', value: 'arch/x86' },
                      { label: 'ARM64 Architecture', value: 'arch/arm64' },
                    ]}
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
                <Button onClick={() => setAiGenModalVisible(false)}>
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
    </div>
  )
}

export default TestCases