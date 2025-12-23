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
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService from '../services/api'

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
  const [aiGenForm] = Form.useForm()

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
            onClick={() => message.info(`Viewing test: ${record.name}`)}
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

  const handleAIGenerate = async (values: any) => {
    try {
      message.loading('Generating tests with AI...', 2)
      
      // Simulate AI generation
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      message.success('AI test generation completed! New tests have been added.')
      setAiGenModalVisible(false)
      aiGenForm.resetFields()
      refetch()
    } catch (error) {
      message.error('AI test generation failed')
    }
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
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
        <Title level={2} style={{ margin: 0 }}>Test Cases</Title>
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

      {/* AI Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={aiGenModalVisible}
        onCancel={() => setAiGenModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={aiGenForm}
          layout="vertical"
          onFinish={handleAIGenerate}
        >
          <Form.Item
            name="type"
            label="Generation Type"
            initialValue="diff"
          >
            <Select>
              <Select.Option value="diff">From Code Diff</Select.Option>
              <Select.Option value="function">From Function</Select.Option>
              <Select.Option value="kernel">Kernel Test Driver</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="input"
            label="Input"
            rules={[{ required: true, message: 'Please provide input for AI generation' }]}
          >
            <TextArea
              rows={6}
              placeholder="Paste your git diff, function name, or kernel function details here..."
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="maxTests"
                label="Max Tests"
                initialValue={10}
              >
                <Input type="number" min={1} max={50} />
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
                icon={<RobotOutlined />}
              >
                Generate Tests
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TestCases