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
  DesktopOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from 'react-query'
import apiService from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input
const { TabPane } = Tabs

const TestExecutionDebugWorking: React.FC = () => {
  console.log('TestExecutionDebugWorking: Starting component render')
  
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(false)
  const [isAutoGenModalVisible, setIsAutoGenModalVisible] = useState(false)
  const [autoGenType, setAutoGenType] = useState<'diff' | 'function'>('diff')
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([])
  const [executionDetails, setExecutionDetails] = useState<Record<string, any>>({})
  const [loadingActions, setLoadingActions] = useState<Record<string, string>>({}) // Track loading states
  const [activeTab, setActiveTab] = useState('executions')
  const [selectedExecutionForConsole, setSelectedExecutionForConsole] = useState<string | null>(null)
  const [form] = Form.useForm()
  const [autoGenForm] = Form.useForm()
  const queryClient = useQueryClient()

  console.log('TestExecutionDebugWorking: State initialized')

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
      console.log('TestExecutionDebugWorking: Fetching real execution data...')
      const result = await apiService.getActiveExecutions()
      console.log('TestExecutionDebugWorking: Got execution data:', result)
      return result
    },
    {
      refetchInterval: 5000,
      cacheTime: 0, // Don't cache the data
      staleTime: 0, // Always consider data stale
      onError: (error) => {
        console.error('TestExecutionDebugWorking: Error fetching executions:', error)
      },
      onSuccess: (data) => {
        console.log('TestExecutionDebugWorking: Successfully fetched executions:', data)
      }
    }
  )

  console.log('TestExecutionDebugWorking: Using real API data, executions count:', executionsData.length)

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
      render: (_: any, record: any) => (
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
            icon={<DesktopOutlined />}
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

  console.log('TestExecutionDebugWorking: Columns defined')

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

  console.log('TestExecutionDebugWorking: About to render JSX')

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
                emptyText: error ? `Error loading data: ${(error as any)?.message}` : 'No active executions'
              }}
            />
          </Card>
        </TabPane>
        
        <TabPane 
          tab={
            <Space>
              <DesktopOutlined />
              Console
              {selectedExecutionForConsole && (
                <Tag>{selectedExecutionForConsole.slice(0, 8)}...</Tag>
              )}
            </Space>
          } 
          key="console"
        >
          {/* Simple Console Placeholder - without ExecutionConsole component */}
          <Card title="Execution Console">
            {selectedExecutionForConsole ? (
              <div style={{ 
                backgroundColor: '#001529', 
                color: '#fff', 
                padding: '16px', 
                borderRadius: '4px',
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontSize: '12px',
                height: '400px',
                overflow: 'auto'
              }}>
                <div>[{new Date().toLocaleTimeString()}] INFO ExecutionService: Starting execution plan {selectedExecutionForConsole.slice(0, 8)}...</div>
                <div>[{new Date().toLocaleTimeString()}] INFO EnvironmentManager: Provisioned environment env-001 (x86_64, 2048MB)</div>
                <div>[{new Date().toLocaleTimeString()}] INFO TestRunner: Executing test cases...</div>
                <div>[{new Date().toLocaleTimeString()}] DEBUG MockRunner: Mock test execution in progress</div>
                <div style={{ color: '#666', marginTop: '20px' }}>
                  Console logs for execution {selectedExecutionForConsole.slice(0, 8)}... would appear here in real-time.
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <DesktopOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
                <Title level={4} type="secondary">No Execution Selected</Title>
                <Text type="secondary">
                  Click the "Console" button next to an execution to view its real-time logs
                </Text>
              </div>
            )}
          </Card>
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
    </div>
  )
}

export default TestExecutionDebugWorking