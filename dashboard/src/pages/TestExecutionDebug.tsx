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

const { Title, Text } = Typography
const { TextArea } = Input

const TestExecutionDebug: React.FC = () => {
  console.log('TestExecutionDebug: Starting component render')
  
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(false)
  const [isAutoGenModalVisible, setIsAutoGenModalVisible] = useState(false)
  const [autoGenType, setAutoGenType] = useState<'diff' | 'function'>('diff')
  const [form] = Form.useForm()
  const [autoGenForm] = Form.useForm()

  console.log('TestExecutionDebug: State initialized')

  // Mock data for testing
  const executionsData = [
    {
      plan_id: 'test-123',
      overall_status: 'running',
      progress: 0.6,
      completed_tests: 6,
      total_tests: 10,
      started_at: new Date().toISOString(),
      estimated_completion: new Date(Date.now() + 300000).toISOString()
    }
  ]

  const environments = [
    { id: 'env-1', config: { architecture: 'x86_64', cpu_model: 'Intel Core i7' } }
  ]

  console.log('TestExecutionDebug: Mock data created')

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
  ]

  console.log('TestExecutionDebug: Columns defined')

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
            icon={<ReloadOutlined />}
            onClick={() => console.log('Refresh clicked')}
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
              value={1}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Running"
              value={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Completed"
              value={0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Failed"
              value={0}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Executions Table */}
      <Card title="Active Test Executions (Debug Mode)">
        <Table
          columns={columns}
          dataSource={executionsData}
          loading={false}
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
            onFinish={(values) => {
              console.log('AI Generation form values:', values)
              message.success('Test generation started (debug mode)')
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

export default TestExecutionDebug