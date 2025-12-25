import React, { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Progress,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Row,
  Col,
  Statistic,
  Tooltip,
  message,
  Tabs,
  Alert,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  PlusOutlined,
  EyeOutlined,
  RobotOutlined,
  CodeOutlined,
  FunctionOutlined,
  DownOutlined,
  RightOutlined,
  FileTextOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from 'react-query'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import apiService from '../services/api'
import ExecutionConsole from '../components/ExecutionConsole'

const { Title, Text } = Typography
const { TextArea } = Input
const { TabPane } = Tabs

const TestExecutionDebug: React.FC = () => {
  console.log('TestExecutionDebug: Starting component render')
  
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(false)
  const [isAutoGenModalVisible, setIsAutoGenModalVisible] = useState(false)
  const [autoGenType, setAutoGenType] = useState<'diff' | 'function'>('diff')
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([])
  const [executionDetails, setExecutionDetails] = useState<Record<string, any>>({})
  const [loadingActions, setLoadingActions] = useState<Record<string, string>>({}) // Track loading states
  const [activeTab, setActiveTab] = useState('executions')
  const [selectedExecutionForConsole, setSelectedExecutionForConsole] = useState<string | null>(null)
  const [sourceCodeModalVisible, setSourceCodeModalVisible] = useState(false)
  const [selectedTestCaseForSource, setSelectedTestCaseForSource] = useState<any>(null)
  const [form] = Form.useForm()
  const [autoGenForm] = Form.useForm()
  const queryClient = useQueryClient()

  console.log('TestExecutionDebug: State initialized')

  // Function to handle viewing test case source code
  const handleViewTestCaseSource = async (testCase: any) => {
    console.log('🔍 Viewing test case source for:', testCase)
    console.log('🔍 Test case test_script field:', testCase.test_script)
    console.log('🔍 Full test case object:', JSON.stringify(testCase, null, 2))
    
    // If the test case doesn't have full details (like test_script), fetch them
    if (!testCase.test_script && testCase.test_id) {
      try {
        console.log('🔄 Fetching full test case details for:', testCase.test_id)
        
        // Set loading state
        setLoadingActions(prev => ({ ...prev, [`source_${testCase.test_id}`]: 'loading' }))
        
        const fullTestCase = await apiService.getTestById(testCase.test_id)
        console.log('✅ Got full test case details:', fullTestCase)
        setSelectedTestCaseForSource(fullTestCase)
      } catch (error) {
        console.error('❌ Failed to fetch full test case details:', error)
        // Fall back to using the partial data we have
        setSelectedTestCaseForSource(testCase)
      } finally {
        // Clear loading state
        setLoadingActions(prev => {
          const newState = { ...prev }
          delete newState[`source_${testCase.test_id}`]
          return newState
        })
      }
    } else {
      setSelectedTestCaseForSource(testCase)
    }
    
    setSourceCodeModalVisible(true)
  }

  // Function to fetch execution details including test cases
  const fetchExecutionDetails = async (planId: string) => {
    try {
      console.log(`Fetching details for execution plan: ${planId}`)
      const response = await apiService.getExecutionStatus(planId)
      setExecutionDetails(prev => ({
        ...prev,
        [planId]: response
      }))
      return response
    } catch (error) {
      console.error(`Error fetching execution details for ${planId}:`, error)
      return null
    }
  }

  // Handle row expansion
  const handleExpand = async (expanded: boolean, record: any) => {
    const planId = record.plan_id
    
    if (expanded) {
      setExpandedRowKeys(prev => [...prev, planId])
      if (!executionDetails[planId]) {
        await fetchExecutionDetails(planId)
      }
    } else {
      setExpandedRowKeys(prev => prev.filter(key => key !== planId))
    }
  }

  // Execution control handlers
  const handleStartExecution = async (planId: string) => {
    try {
      console.log(`Starting execution for plan: ${planId}`)
      setLoadingActions(prev => ({ ...prev, [planId]: 'starting' }))
      
      const response = await apiService.startExecution(planId)
      
      message.success('Execution started successfully!')
      // Refresh the executions list
      queryClient.invalidateQueries('activeExecutions')
    } catch (error: any) {
      console.error('Error starting execution:', error)
      message.error(`Failed to start execution: ${error.message}`)
    } finally {
      setLoadingActions(prev => {
        const newState = { ...prev }
        delete newState[planId]
        return newState
      })
    }
  }

  const handlePauseExecution = async (planId: string) => {
    try {
      console.log(`Pausing execution for plan: ${planId}`)
      setLoadingActions(prev => ({ ...prev, [planId]: 'pausing' }))
      
      // Simulate pausing - in real implementation, call orchestrator
      await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate API call
      message.info('Pause functionality coming soon!')
    } catch (error: any) {
      console.error('Error pausing execution:', error)
      message.error(`Failed to pause execution: ${error.message}`)
    } finally {
      setLoadingActions(prev => {
        const newState = { ...prev }
        delete newState[planId]
        return newState
      })
    }
  }

  const handleCancelExecution = async (planId: string) => {
    try {
      console.log(`Cancelling execution for plan: ${planId}`)
      setLoadingActions(prev => ({ ...prev, [planId]: 'cancelling' }))
      
      const response = await apiService.cancelExecution(planId)
      
      message.success('Execution cancelled successfully!')
      // Refresh the executions list
      queryClient.invalidateQueries('activeExecutions')
    } catch (error: any) {
      console.error('Error cancelling execution:', error)
      message.error(`Failed to cancel execution: ${error.message}`)
    } finally {
      setLoadingActions(prev => {
        const newState = { ...prev }
        delete newState[planId]
        return newState
      })
    }
  }

  // Use real API data instead of mock data
  const { data: executionsData = [], isLoading, error } = useQuery(
    'activeExecutions',
    async () => {
      console.log('TestExecutionDebug: Fetching real execution data...')
      try {
        const result = await apiService.getActiveExecutions()
        console.log('TestExecutionDebug: Got execution data:', result)
        return result
      } catch (error: any) {
        console.error('TestExecutionDebug: API Error, using fallback data:', error)
        // Return mock data as fallback when API fails
        return [
          {
            plan_id: 'plan_demo_001',
            submission_id: 'sub_demo_001',
            overall_status: 'running',
            total_tests: 5,
            completed_tests: 2,
            failed_tests: 0,
            progress: 0.4,
            test_statuses: [],
            started_at: new Date().toISOString(),
            estimated_completion: new Date(Date.now() + 300000).toISOString(), // 5 minutes from now
          },
          {
            plan_id: 'plan_demo_002',
            submission_id: 'sub_demo_002',
            overall_status: 'queued',
            total_tests: 3,
            completed_tests: 0,
            failed_tests: 0,
            progress: 0,
            test_statuses: [],
          },
          {
            plan_id: 'plan_demo_003',
            submission_id: 'sub_demo_003',
            overall_status: 'completed',
            total_tests: 8,
            completed_tests: 7,
            failed_tests: 1,
            progress: 1.0,
            test_statuses: [],
            started_at: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago
            completed_at: new Date(Date.now() - 60000).toISOString(), // 1 minute ago
          }
        ]
      }
    },
    {
      refetchInterval: 5000,
      cacheTime: 0, // Don't cache the data
      staleTime: 0, // Always consider data stale
      retry: 1, // Only retry once to avoid long loading times
      retryDelay: 1000, // Wait 1 second before retry
      onError: (error) => {
        console.error('TestExecutionDebug: Error fetching executions:', error)
      },
      onSuccess: (data) => {
        console.log('TestExecutionDebug: Successfully fetched executions:', data)
      }
    }
  )

  const environments = [
    { id: 'env-1', config: { architecture: 'x86_64', cpu_model: 'Intel Core i7' } }
  ]

  console.log('TestExecutionDebug: Using real API data, executions count:', executionsData.length)

  const columns = [
    {
      title: 'Execution ID',
      dataIndex: 'plan_id',
      key: 'plan_id',
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code>{id.slice(0, 8)}...</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'overall_status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          running: 'blue',
          completed: 'green',
          failed: 'red',
          pending: 'orange',
          queued: 'orange',
          cancelled: 'default',
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Test Count',
      dataIndex: 'total_tests',
      key: 'total_tests',
      render: (count: number, record: any) => (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>{count} tests</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.completed_tests || 0} completed, {record.failed_tests || 0} failed
          </Text>
        </Space>
      ),
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number, record: any) => (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Progress
            percent={Math.round(progress * 100)}
            size="small"
            status={record.overall_status === 'failed' ? 'exception' : 'normal'}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.completed_tests}/{record.total_tests} tests
          </Text>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record: any) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              const isExpanded = expandedRowKeys.includes(record.plan_id)
              handleExpand(!isExpanded, record)
            }}
          >
            {expandedRowKeys.includes(record.plan_id) ? 'Hide' : 'View'} Details
          </Button>
          
          <Button
            size="small"
            type="primary"
            icon={<BarChartOutlined />}
            onClick={() => {
              // Navigate to monitor page with plan ID
              window.location.href = `/execution-monitor?planId=${record.plan_id}`
            }}
          >
            Monitor
          </Button>
          
          <Button
            size="small"
            icon={<CodeOutlined />}
            onClick={() => {
              setSelectedExecutionForConsole(record.plan_id)
              setActiveTab('console')
            }}
          >
            Console
          </Button>
          
          {/* Execution Control Actions */}
          {record.overall_status === 'queued' && (
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartExecution(record.plan_id)}
              loading={loadingActions[record.plan_id] === 'starting'}
            >
              Start
            </Button>
          )}
          
          {record.overall_status === 'running' && (
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={() => handlePauseExecution(record.plan_id)}
              loading={loadingActions[record.plan_id] === 'pausing'}
            >
              Pause
            </Button>
          )}
          
          {(record.overall_status === 'queued' || record.overall_status === 'running') && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancelExecution(record.plan_id)}
              loading={loadingActions[record.plan_id] === 'cancelling'}
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ]

  console.log('TestExecutionDebug: Columns defined')

  // Expandable row render function
  const expandedRowRender = (record: any) => {
    const planId = record.plan_id
    const details = executionDetails[planId]
    
    if (!details) {
      return (
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Text type="secondary">Loading execution details...</Text>
        </div>
      )
    }

    // Use real test case data from the API
    const testCases = details.test_cases || []

    const testColumns = [
      {
        title: 'Test Case ID',
        dataIndex: 'test_id',
        key: 'test_id',
        render: (id: string) => (
          <Tooltip title={id}>
            <Text code>{id.slice(0, 8)}...</Text>
          </Tooltip>
        )
      },
      {
        title: 'Test Name',
        dataIndex: 'name',
        key: 'name',
        render: (name: string) => (
          <Tooltip title={name}>
            <Text>{name.length > 50 ? `${name.slice(0, 50)}...` : name}</Text>
          </Tooltip>
        )
      },
      {
        title: 'Type',
        dataIndex: 'test_type',
        key: 'test_type',
        render: (type: string) => <Tag color="blue">{type}</Tag>
      },
      {
        title: 'Subsystem',
        dataIndex: 'target_subsystem',
        key: 'target_subsystem',
        render: (subsystem: string) => <Tag color="green">{subsystem}</Tag>
      },
      {
        title: 'Status',
        dataIndex: 'execution_status',
        key: 'execution_status',
        render: (status: string) => {
          const colors = {
            queued: 'orange',
            running: 'blue',
            completed: 'green',
            failed: 'red',
            never_run: 'default'
          }
          return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
        }
      },
      {
        title: 'Est. Time',
        dataIndex: 'execution_time_estimate',
        key: 'execution_time_estimate',
        render: (time: number) => <Text type="secondary">{time}s</Text>
      },
      {
        title: 'Actions',
        key: 'actions',
        width: 120,
        render: (_, testCase: any) => (
          <Space size="small">
            <Tooltip title="View test case source code">
              <Button
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => handleViewTestCaseSource(testCase)}
                loading={loadingActions[`source_${testCase.test_id}`]}
              >
                Source
              </Button>
            </Tooltip>
          </Space>
        )
      }
    ]

    return (
      <div style={{ margin: '16px 0', padding: '16px', backgroundColor: '#fafafa', borderRadius: '6px' }}>
        <Title level={5}>Test Cases in Execution Plan: {planId.slice(0, 8)}...</Title>
        <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
          This execution plan contains {testCases.length} test cases. Below are the individual tests that will be executed:
        </Text>
        
        {testCases.length > 0 ? (
          <Table
            columns={testColumns}
            dataSource={testCases}
            pagination={testCases.length > 10 ? { pageSize: 10, size: 'small' } : false}
            size="small"
            rowKey="test_id"
            scroll={{ x: 800 }}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Text type="secondary">No test case details available</Text>
          </div>
        )}
        
        <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#e6f7ff', borderRadius: '4px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Text type="secondary">
                <strong>Execution Plan Details:</strong><br/>
                • Plan ID: <Text code>{planId}</Text><br/>
                • Submission ID: <Text code>{details.submission_id}</Text><br/>
                • Status: <Tag color="orange">{details.overall_status}</Tag>
              </Text>
            </Col>
            <Col span={12}>
              <Text type="secondary">
                <strong>Progress Information:</strong><br/>
                • Total Tests: {details.total_tests}<br/>
                • Completed: {details.completed_tests}<br/>
                • Failed: {details.failed_tests}<br/>
                • Progress: {Math.round(details.progress * 100)}%
              </Text>
            </Col>
          </Row>
        </div>
      </div>
    )
  }

  const handleSubmitTest = (values: any) => {
    console.log('Submitting test with values:', values)
    message.success('Test submitted successfully (debug mode)')
    setIsSubmitModalVisible(false)
    form.resetFields()
  }

  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
    { label: 'Fuzz Test', value: 'fuzz' },
  ]

  const subsystems = [
    'kernel/core',
    'kernel/mm',
    'kernel/fs',
    'kernel/net',
    'drivers/block',
    'drivers/char',
    'drivers/net',
    'arch/x86',
    'arch/arm64',
  ]

  console.log('TestExecutionDebug: About to render JSX')

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Test Execution (Debug Mode)</Title>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => {
              console.log('AI Generate Tests clicked')
              setIsAutoGenModalVisible(true)
            }}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => {
              console.log('Manual Submit clicked')
              setIsSubmitModalVisible(true)
            }}
          >
            Manual Submit
          </Button>
          <Button
            icon={<BarChartOutlined />}
            onClick={() => {
              // Navigate to monitor page without specific plan ID for overview
              window.location.href = '/execution-monitor'
            }}
          >
            Execution Monitor
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              console.log('Refresh clicked - invalidating queries')
              queryClient.invalidateQueries('activeExecutions')
            }}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Summary Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Executions"
              value={executionsData.length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Running"
              value={executionsData.filter(e => e.overall_status === 'running').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Completed"
              value={executionsData.filter(e => e.overall_status === 'completed').length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Failed"
              value={executionsData.filter(e => e.overall_status === 'failed').length}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content Tabs */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Executions" key="executions">
          {/* Executions Table */}
          <Card title="Active Test Executions (Real-time Data)">
            {/* Connection Status Alert */}
            {error && (
              <Alert
                message="Backend Connection Issue"
                description={
                  <div>
                    <p>Unable to connect to the backend API. Showing demo data for testing.</p>
                    <p><strong>Error:</strong> {error instanceof Error ? error.message : 'Unknown error'}</p>
                    <p><strong>Endpoint:</strong> /execution/active</p>
                    <p>Please ensure the backend API server is running on port 8000.</p>
                  </div>
                }
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                action={
                  <Button
                    size="small"
                    onClick={() => {
                      console.log('Manual refresh clicked')
                      queryClient.invalidateQueries('activeExecutions')
                    }}
                  >
                    Retry Connection
                  </Button>
                }
              />
            )}
            
            <Table
              columns={columns}
              dataSource={executionsData}
              loading={isLoading}
              rowKey="plan_id"
              expandable={{
                expandedRowKeys,
                onExpand: handleExpand,
                expandedRowRender,
                expandIcon: ({ expanded, onExpand, record }) => (
                  <Button
                    type="text"
                    size="small"
                    icon={expanded ? <DownOutlined /> : <RightOutlined />}
                    onClick={e => onExpand(record, e)}
                  />
                ),
              }}
              rowSelection={{
                selectedRowKeys,
                onChange: (selectedRowKeys: React.Key[]) => setSelectedRowKeys(selectedRowKeys as string[]),
              }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) =>
                  `${range[0]}-${range[1]} of ${total} executions`,
              }}
              locale={{
                emptyText: error ? 
                  'No executions available (using demo data due to API connection issue)' : 
                  'No active executions'
              }}
            />
          </Card>
        </TabPane>
        
        <TabPane 
          tab={
            <Space>
              <CodeOutlined />
              Console
              {selectedExecutionForConsole && (
                <Tag size="small">{selectedExecutionForConsole.slice(0, 8)}...</Tag>
              )}
            </Space>
          } 
          key="console"
        >
          <ExecutionConsole 
            planId={selectedExecutionForConsole || undefined}
            height={500}
            autoScroll={true}
          />
          
          {!selectedExecutionForConsole && (
            <Card style={{ marginTop: 16 }}>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <CodeOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
                <Title level={4} type="secondary">No Execution Selected</Title>
                <Text type="secondary">
                  Click the "Console" button next to an execution to view its real-time logs
                </Text>
              </div>
            </Card>
          )}
        </TabPane>
      </Tabs>

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation (Debug Mode)"
        open={isAutoGenModalVisible}
        onCancel={() => setIsAutoGenModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={autoGenType === 'diff' ? 'primary' : 'default'}
              icon={<CodeOutlined />}
              onClick={() => setAutoGenType('diff')}
            >
              From Code Diff
            </Button>
            <Button
              type={autoGenType === 'function' ? 'primary' : 'default'}
              icon={<FunctionOutlined />}
              onClick={() => setAutoGenType('function')}
            >
              From Function
            </Button>
          </Space>
        </div>

        {autoGenType === 'function' && (
          <Form
            form={autoGenForm}
            layout="vertical"
            onFinish={async (values) => {
              console.log('AI Generation form values:', values)
              try {
                const result = await apiService.generateTestsFromFunction(
                  values.functionName,
                  values.filePath,
                  values.subsystem,
                  values.maxTests
                )
                message.success(`Generated ${result.data?.generated_count || 0} tests successfully!`)
                // Refresh the executions list
                queryClient.invalidateQueries('activeExecutions')
              } catch (error: any) {
                console.error('AI Generation error:', error)
                message.error(`Test generation failed: ${error.message}`)
              }
              setIsAutoGenModalVisible(false)
              autoGenForm.resetFields()
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
                  rules={[{ required: true, message: 'Please select a subsystem' }]}
                >
                  <Select
                    placeholder="Select subsystem"
                    options={subsystems.map(s => ({ label: s, value: s }))}
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
                <Button onClick={() => setIsAutoGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<RobotOutlined />}
                >
                  Generate Tests (Debug)
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Submit Test Modal */}
      <Modal
        title="Submit New Test (Debug Mode)"
        open={isSubmitModalVisible}
        onCancel={() => setIsSubmitModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitTest}
        >
          <Form.Item
            name="name"
            label="Test Name"
            rules={[{ required: true, message: 'Please enter test name' }]}
          >
            <Input placeholder="Enter test name" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={3} placeholder="Describe what this test does" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="test_type"
                label="Test Type"
                rules={[{ required: true, message: 'Please select test type' }]}
              >
                <Select placeholder="Select test type" options={testTypes} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="subsystem"
                label="Target Subsystem"
                rules={[{ required: true, message: 'Please select subsystem' }]}
              >
                <Select
                  placeholder="Select subsystem"
                  options={subsystems.map(s => ({ label: s, value: s }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsSubmitModalVisible(false)}>
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
              >
                Submit Test (Debug)
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Test Case Source Code Modal */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            Test Case Source Code
            {selectedTestCaseForSource && (
              <Tag color="blue">{selectedTestCaseForSource.name}</Tag>
            )}
          </Space>
        }
        open={sourceCodeModalVisible}
        onCancel={() => {
          setSourceCodeModalVisible(false)
          setSelectedTestCaseForSource(null)
        }}
        footer={[
          <Button key="close" onClick={() => {
            setSourceCodeModalVisible(false)
            setSelectedTestCaseForSource(null)
          }}>
            Close
          </Button>
        ]}
        width={900}
        style={{ top: 20 }}
      >
        {selectedTestCaseForSource && (
          <div>
            {/* Test Case Information */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>Test Case ID:</Text> <Text code>{selectedTestCaseForSource.test_id}</Text><br/>
                  <Text strong>Name:</Text> <Text>{selectedTestCaseForSource.name}</Text><br/>
                  <Text strong>Type:</Text> <Tag color="blue">{selectedTestCaseForSource.test_type}</Tag>
                </Col>
                <Col span={12}>
                  <Text strong>Subsystem:</Text> <Tag color="green">{selectedTestCaseForSource.target_subsystem}</Tag><br/>
                  <Text strong>Status:</Text> <Tag color="orange">{selectedTestCaseForSource.execution_status}</Tag><br/>
                  <Text strong>Est. Time:</Text> <Text type="secondary">{selectedTestCaseForSource.execution_time_estimate}s</Text>
                </Col>
              </Row>
              {selectedTestCaseForSource.description && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
                  <Text strong>Description:</Text><br/>
                  <Text type="secondary">{selectedTestCaseForSource.description}</Text>
                </div>
              )}
            </Card>

            {/* Source Code */}
            <Card 
              title={
                <Space>
                  <CodeOutlined />
                  Test Script Source Code
                  <Tag color="purple">
                    {(() => {
                      // Check multiple possible source code fields
                      const testScript = selectedTestCaseForSource.test_script
                      const driverFiles = selectedTestCaseForSource.driver_files
                      const generationInfo = selectedTestCaseForSource.generation_info
                      
                      if (testScript) {
                        if (testScript.includes('#!/bin/bash')) return 'bash'
                        if (testScript.includes('#include')) return 'c'
                        if (testScript.includes('import ')) return 'python'
                        return 'text'
                      } else if (driverFiles && Object.keys(driverFiles).length > 0) {
                        const firstFile = Object.keys(driverFiles)[0]
                        if (firstFile.endsWith('.c')) return 'c'
                        if (firstFile.endsWith('.sh')) return 'bash'
                        if (firstFile.endsWith('.py')) return 'python'
                        return 'text'
                      }
                      return 'text'
                    })()}
                  </Tag>
                </Space>
              }
              size="small"
            >
              {(() => {
                const testScript = selectedTestCaseForSource.test_script
                const driverFiles = selectedTestCaseForSource.driver_files
                const generationInfo = selectedTestCaseForSource.generation_info
                
                // Try to find source code in different fields
                let sourceCode = null
                let language = 'text'
                let sourceType = 'Unknown'
                
                if (testScript && testScript.trim()) {
                  sourceCode = testScript
                  sourceType = 'Test Script'
                  if (testScript.includes('#!/bin/bash')) language = 'bash'
                  else if (testScript.includes('#include')) language = 'c'
                  else if (testScript.includes('import ')) language = 'python'
                  else if (testScript.includes('function ')) language = 'javascript'
                } else if (driverFiles && Object.keys(driverFiles).length > 0) {
                  // Show the first driver file
                  const firstFileName = Object.keys(driverFiles)[0]
                  sourceCode = driverFiles[firstFileName]
                  sourceType = `Driver File: ${firstFileName}`
                  if (firstFileName.endsWith('.c')) language = 'c'
                  else if (firstFileName.endsWith('.sh')) language = 'bash'
                  else if (firstFileName.endsWith('.py')) language = 'python'
                  else if (firstFileName.endsWith('.js')) language = 'javascript'
                } else if (generationInfo?.source_data) {
                  // Try to extract source from generation info
                  const sourceData = generationInfo.source_data
                  if (typeof sourceData === 'string') {
                    sourceCode = sourceData
                    sourceType = 'Generation Source Data'
                  } else if (sourceData.diff_content) {
                    sourceCode = sourceData.diff_content
                    sourceType = 'Diff Content'
                    language = 'diff'
                  } else if (sourceData.function_code) {
                    sourceCode = sourceData.function_code
                    sourceType = 'Function Code'
                    language = 'c'
                  }
                }
                
                if (sourceCode && sourceCode.trim()) {
                  return (
                    <div>
                      <div style={{ marginBottom: 8 }}>
                        <Tag color="blue">{sourceType}</Tag>
                        {driverFiles && Object.keys(driverFiles).length > 1 && (
                          <Tag color="orange">+{Object.keys(driverFiles).length - 1} more files</Tag>
                        )}
                      </div>
                      <SyntaxHighlighter
                        language={language}
                        style={vscDarkPlus}
                        customStyle={{
                          backgroundColor: '#1e1e1e',
                          color: '#d4d4d4',
                          fontSize: '13px',
                          lineHeight: '1.4',
                          borderRadius: '6px',
                          maxHeight: '400px',
                          overflow: 'auto'
                        }}
                        showLineNumbers={true}
                        wrapLines={true}
                        lineNumberStyle={{
                          color: '#858585',
                          fontSize: '12px',
                          paddingRight: '10px'
                        }}
                      >
                        {sourceCode}
                      </SyntaxHighlighter>
                      
                      {/* Show additional driver files if they exist */}
                      {driverFiles && Object.keys(driverFiles).length > 1 && (
                        <div style={{ marginTop: 16 }}>
                          <Text strong>Additional Driver Files:</Text>
                          {Object.entries(driverFiles).slice(1).map(([fileName, fileContent]) => (
                            <Card key={fileName} size="small" style={{ marginTop: 8 }}>
                              <div style={{ marginBottom: 8 }}>
                                <Tag color="green">{fileName}</Tag>
                              </div>
                              <SyntaxHighlighter
                                language={
                                  fileName.endsWith('.c') ? 'c' :
                                  fileName.endsWith('.sh') ? 'bash' :
                                  fileName.endsWith('.py') ? 'python' :
                                  fileName.endsWith('.js') ? 'javascript' :
                                  'text'
                                }
                                style={vscDarkPlus}
                                customStyle={{
                                  backgroundColor: '#1e1e1e',
                                  color: '#d4d4d4',
                                  fontSize: '12px',
                                  lineHeight: '1.4',
                                  borderRadius: '6px',
                                  maxHeight: '300px',
                                  overflow: 'auto'
                                }}
                                showLineNumbers={true}
                                wrapLines={true}
                              >
                                {fileContent}
                              </SyntaxHighlighter>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                } else {
                  return (
                    <div style={{ 
                      padding: '20px', 
                      textAlign: 'center', 
                      backgroundColor: '#f5f5f5', 
                      borderRadius: '6px',
                      border: '1px dashed #d9d9d9'
                    }}>
                      <FileTextOutlined style={{ fontSize: '24px', color: '#ccc', marginBottom: '8px' }} />
                      <div>
                        <Text type="secondary">No source code available for this test case</Text>
                      </div>
                      <div style={{ marginTop: '8px' }}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          The test script may be generated dynamically or stored externally
                        </Text>
                      </div>
                      <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#fff2e8', borderRadius: '4px' }}>
                        <Text type="secondary" style={{ fontSize: '11px' }}>
                          <strong>Debug Info for Test Case: {selectedTestCaseForSource.test_id}</strong><br/>
                          • test_script: {selectedTestCaseForSource.test_script ? 
                            (selectedTestCaseForSource.test_script.trim() ? `present (${selectedTestCaseForSource.test_script.length} chars)` : 'present but empty') : 
                            'null/undefined'}<br/>
                          • driver_files: {selectedTestCaseForSource.driver_files ? 
                            `${Object.keys(selectedTestCaseForSource.driver_files).length} files: [${Object.keys(selectedTestCaseForSource.driver_files).join(', ')}]` : 
                            'none'}<br/>
                          • generation_info: {selectedTestCaseForSource.generation_info ? 
                            `present (method: ${selectedTestCaseForSource.generation_info.method || 'unknown'})` : 
                            'none'}<br/>
                          • All available fields: {Object.keys(selectedTestCaseForSource).join(', ')}
                        </Text>
                      </div>
                    </div>
                  )
                }
              })()}
            </Card>

            {/* Additional Metadata */}
            {selectedTestCaseForSource.metadata && (
              <Card 
                title={
                  <Space>
                    <CodeOutlined />
                    Test Metadata
                  </Space>
                }
                size="small"
                style={{ marginTop: 16 }}
              >
                <SyntaxHighlighter
                  language="json"
                  style={vscDarkPlus}
                  customStyle={{
                    backgroundColor: '#1e1e1e',
                    color: '#d4d4d4',
                    fontSize: '12px',
                    lineHeight: '1.4',
                    borderRadius: '6px',
                    maxHeight: '200px',
                    overflow: 'auto'
                  }}
                  showLineNumbers={false}
                >
                  {JSON.stringify(selectedTestCaseForSource.metadata, null, 2)}
                </SyntaxHighlighter>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TestExecutionDebug