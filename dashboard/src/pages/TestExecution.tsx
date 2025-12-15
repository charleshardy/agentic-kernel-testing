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
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useDashboardStore } from '../store'
import apiService from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

interface TestExecutionProps {}

const TestExecution: React.FC<TestExecutionProps> = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(false)
  const [isAutoGenModalVisible, setIsAutoGenModalVisible] = useState(false)
  const [autoGenType, setAutoGenType] = useState<'diff' | 'function'>('diff')
  const [form] = Form.useForm()
  const [autoGenForm] = Form.useForm()
  const queryClient = useQueryClient()
  const { activeExecutions } = useDashboardStore()

  // Fetch active test executions
  const { data: executionsData, isLoading: executionsLoading } = useQuery(
    'activeExecutions',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  )

  // Fetch available environments
  const { data: environments } = useQuery(
    'environments',
    () => apiService.getEnvironments()
  )

  // Submit new tests mutation
  const submitTestsMutation = useMutation(
    (testData: any) => apiService.submitTests([testData]),
    {
      onSuccess: () => {
        message.success('Tests submitted successfully')
        setIsSubmitModalVisible(false)
        form.resetFields()
        queryClient.invalidateQueries('activeExecutions')
      },
      onError: (error: any) => {
        message.error(`Failed to submit tests: ${error.message}`)
      },
    }
  )

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
          cancelled: 'default',
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
      },
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
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'Not started',
    },
    {
      title: 'ETA',
      dataIndex: 'estimated_completion',
      key: 'estimated_completion',
      render: (date: string) => {
        if (!date) return 'Unknown'
        const eta = new Date(date)
        const now = new Date()
        const diff = eta.getTime() - now.getTime()
        if (diff <= 0) return 'Overdue'
        const minutes = Math.floor(diff / 60000)
        return `${minutes}m`
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewExecution(record.plan_id)}
          >
            View
          </Button>
          {record.overall_status === 'running' && (
            <Button
              type="text"
              icon={<PauseCircleOutlined />}
              onClick={() => handlePauseExecution(record.plan_id)}
            >
              Pause
            </Button>
          )}
          {record.overall_status === 'pending' && (
            <Button
              type="text"
              icon={<StopOutlined />}
              onClick={() => handleCancelExecution(record.plan_id)}
              danger
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const handleViewExecution = (planId: string) => {
    // Navigate to detailed execution view
    console.log('View execution:', planId)
  }

  const handlePauseExecution = (planId: string) => {
    // Implement pause functionality
    console.log('Pause execution:', planId)
    message.info('Pause functionality not yet implemented')
  }

  const handleCancelExecution = (planId: string) => {
    // Implement cancel functionality
    console.log('Cancel execution:', planId)
    message.info('Cancel functionality not yet implemented')
  }

  const handleSubmitTest = (values: any) => {
    const testData = {
      name: values.name,
      description: values.description,
      test_type: values.test_type,
      target_subsystem: values.subsystem,
      test_script: values.test_script,
      execution_time_estimate: parseInt(values.execution_time) || 60,
      metadata: {
        priority: values.priority || 5,
        environment_preference: values.environment,
      },
    }

    submitTestsMutation.mutate(testData)
  }

  // Auto-generation mutations
  const generateFromDiffMutation = useMutation(
    (data: { diff: string; maxTests: number; testTypes: string[] }) =>
      apiService.generateTestsFromDiff(data.diff, data.maxTests, data.testTypes),
    {
      onSuccess: (response) => {
        message.success(`Generated ${response.data.generated_count} test cases from diff`)
        queryClient.invalidateQueries('activeExecutions')
        setIsAutoGenModalVisible(false)
        form.resetFields()
      },
      onError: (error: any) => {
        message.error(`Failed to generate tests: ${error.message}`)
      },
    }
  )

  const generateFromFunctionMutation = useMutation(
    (data: { functionName: string; filePath: string; subsystem: string; maxTests: number }) =>
      apiService.generateTestsFromFunction(data.functionName, data.filePath, data.subsystem, data.maxTests),
    {
      onSuccess: (response) => {
        message.success(`Generated ${response.data.generated_count} test cases for function`)
        queryClient.invalidateQueries('activeExecutions')
        setIsAutoGenModalVisible(false)
        autoGenForm.resetFields()
      },
      onError: (error: any) => {
        message.error(`Failed to generate tests: ${error.message}`)
      },
    }
  )

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

  // Calculate summary statistics
  const totalExecutions = executionsData?.length || 0
  const runningExecutions = executionsData?.filter(e => e.overall_status === 'running').length || 0
  const completedExecutions = executionsData?.filter(e => e.overall_status === 'completed').length || 0
  const failedExecutions = executionsData?.filter(e => e.overall_status === 'failed').length || 0

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Test Execution</Title>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => setIsAutoGenModalVisible(true)}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => setIsSubmitModalVisible(true)}
          >
            Manual Submit
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries('activeExecutions')}
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
              value={totalExecutions}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Running"
              value={runningExecutions}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Completed"
              value={completedExecutions}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Failed"
              value={failedExecutions}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Executions Table */}
      <Card title="Active Test Executions">
        <Table
          columns={columns}
          dataSource={executionsData}
          loading={executionsLoading}
          rowKey="plan_id"
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
        />
      </Card>

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation"
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

        {autoGenType === 'diff' ? (
          <Form
            form={autoGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateFromDiffMutation.mutate({
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
                <Button onClick={() => setIsAutoGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={generateFromDiffMutation.isLoading}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        ) : (
          <Form
            form={autoGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateFromFunctionMutation.mutate({
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
                  loading={generateFromFunctionMutation.isLoading}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Submit Test Modal */}
      <Modal
        title="Submit New Test"
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

          <Form.Item
            name="test_script"
            label="Test Script"
            rules={[{ required: true, message: 'Please enter test script' }]}
          >
            <TextArea
              rows={6}
              placeholder="#!/bin/bash&#10;# Enter your test script here"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="execution_time"
                label="Estimated Time (seconds)"
              >
                <Input type="number" placeholder="60" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="Priority"
              >
                <Select
                  placeholder="Select priority"
                  options={[
                    { label: 'Low (1)', value: 1 },
                    { label: 'Normal (5)', value: 5 },
                    { label: 'High (8)', value: 8 },
                    { label: 'Critical (10)', value: 10 },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="environment"
            label="Preferred Environment"
          >
            <Select
              placeholder="Any available environment"
              options={environments?.map(env => ({
                label: `${env.config?.architecture} - ${env.config?.cpu_model}`,
                value: env.id,
              }))}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsSubmitModalVisible(false)}>
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={submitTestsMutation.isLoading}
              >
                Submit Test
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TestExecution