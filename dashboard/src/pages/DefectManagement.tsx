import React, { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Tabs,
  Descriptions,
  Upload,
  message,
} from 'antd'
import {
  PlusOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UploadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

interface Defect {
  id: string
  title: string
  description: string
  severity: 'Critical' | 'High' | 'Medium' | 'Low'
  priority: 'P1' | 'P2' | 'P3' | 'P4'
  status: 'Open' | 'In Progress' | 'Resolved' | 'Closed' | 'Reopened'
  assignee: string
  reporter: string
  testCase?: string
  testExecution?: string
  environment: string
  createdDate: string
  updatedDate: string
  resolvedDate?: string
  tags: string[]
  attachments?: string[]
}

const DefectManagement: React.FC = () => {
  const [defects, setDefects] = useState<Defect[]>([
    {
      id: 'DEF-001',
      title: 'Memory leak in kernel module test',
      description: 'Test execution shows increasing memory usage that is not released after test completion.',
      severity: 'High',
      priority: 'P1',
      status: 'Open',
      assignee: 'John Doe',
      reporter: 'Test System',
      testCase: 'TC-001',
      testExecution: 'EXE-12345',
      environment: 'QEMU x86_64',
      createdDate: '2024-01-10',
      updatedDate: '2024-01-10',
      tags: ['memory', 'kernel', 'performance'],
    },
    {
      id: 'DEF-002',
      title: 'Race condition in network driver',
      description: 'Intermittent failures in network stress tests, likely due to race condition in driver initialization.',
      severity: 'Critical',
      priority: 'P1',
      status: 'In Progress',
      assignee: 'Jane Smith',
      reporter: 'AI Analyzer',
      testCase: 'TC-045',
      testExecution: 'EXE-12346',
      environment: 'Physical ARM Board',
      createdDate: '2024-01-09',
      updatedDate: '2024-01-11',
      tags: ['network', 'race-condition', 'driver'],
    },
    {
      id: 'DEF-003',
      title: 'Test timeout in filesystem operations',
      description: 'Large file operations consistently timeout after 30 seconds.',
      severity: 'Medium',
      priority: 'P2',
      status: 'Resolved',
      assignee: 'Bob Wilson',
      reporter: 'Test Orchestrator',
      testCase: 'TC-078',
      testExecution: 'EXE-12340',
      environment: 'QEMU RISC-V',
      createdDate: '2024-01-08',
      updatedDate: '2024-01-11',
      resolvedDate: '2024-01-11',
      tags: ['filesystem', 'timeout', 'performance'],
    },
  ])

  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedDefect, setSelectedDefect] = useState<Defect | null>(null)
  const [form] = Form.useForm()

  const severityColors = {
    Critical: 'red',
    High: 'orange',
    Medium: 'yellow',
    Low: 'green',
  }

  const statusColors = {
    Open: 'red',
    'In Progress': 'blue',
    Resolved: 'green',
    Closed: 'gray',
    Reopened: 'orange',
  }

  const columns: ColumnsType<Defect> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (text) => <Text code>{text}</Text>,
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity) => (
        <Tag color={severityColors[severity as keyof typeof severityColors]}>
          {severity}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => (
        <Tag color={statusColors[status as keyof typeof statusColors]}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Assignee',
      dataIndex: 'assignee',
      key: 'assignee',
      width: 120,
    },
    {
      title: 'Test Case',
      dataIndex: 'testCase',
      key: 'testCase',
      width: 100,
      render: (text) => text ? <Text code>{text}</Text> : '-',
    },
    {
      title: 'Environment',
      dataIndex: 'environment',
      key: 'environment',
      width: 150,
    },
    {
      title: 'Created',
      dataIndex: 'createdDate',
      key: 'createdDate',
      width: 100,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => viewDefect(record)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => editDefect(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteDefect(record.id)}
          />
        </Space>
      ),
    },
  ]

  const viewDefect = (defect: Defect) => {
    setSelectedDefect(defect)
    setIsModalVisible(true)
  }

  const editDefect = (defect: Defect) => {
    setSelectedDefect(defect)
    form.setFieldsValue(defect)
    setIsModalVisible(true)
  }

  const deleteDefect = (id: string) => {
    Modal.confirm({
      title: 'Delete Defect',
      content: 'Are you sure you want to delete this defect?',
      onOk: () => {
        setDefects(defects.filter(d => d.id !== id))
        message.success('Defect deleted successfully')
      },
    })
  }

  const createNewDefect = () => {
    setSelectedDefect(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  const handleModalOk = () => {
    form.validateFields().then(values => {
      if (selectedDefect) {
        // Update existing defect
        setDefects(defects.map(d => 
          d.id === selectedDefect.id 
            ? { ...d, ...values, updatedDate: new Date().toISOString().split('T')[0] }
            : d
        ))
        message.success('Defect updated successfully')
      } else {
        // Create new defect
        const newDefect: Defect = {
          ...values,
          id: `DEF-${String(defects.length + 1).padStart(3, '0')}`,
          createdDate: new Date().toISOString().split('T')[0],
          updatedDate: new Date().toISOString().split('T')[0],
          reporter: 'Current User',
          tags: values.tags || [],
        }
        setDefects([...defects, newDefect])
        message.success('Defect created successfully')
      }
      setIsModalVisible(false)
    })
  }

  const getDefectStats = () => {
    const total = defects.length
    const open = defects.filter(d => d.status === 'Open').length
    const inProgress = defects.filter(d => d.status === 'In Progress').length
    const resolved = defects.filter(d => d.status === 'Resolved').length
    const critical = defects.filter(d => d.severity === 'Critical').length

    return { total, open, inProgress, resolved, critical }
  }

  const stats = getDefectStats()

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BugOutlined /> Defect Management
        </Title>
        <Text type="secondary">
          Track and manage defects, bugs, and issues discovered during testing
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Defects"
              value={stats.total}
              prefix={<BugOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Open"
              value={stats.open}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="In Progress"
              value={stats.inProgress}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Resolved"
              value={stats.resolved}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={createNewDefect}>
              Create Defect
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={defects}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} defects`,
          }}
        />
      </Card>

      {/* Defect Modal */}
      <Modal
        title={selectedDefect ? `Defect ${selectedDefect.id}` : 'Create New Defect'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        width={800}
        okText={selectedDefect ? 'Update' : 'Create'}
      >
        {selectedDefect && !form.getFieldsValue().title ? (
          // View mode
          <Tabs defaultActiveKey="details">
            <TabPane tab="Details" key="details">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="ID">{selectedDefect.id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Tag color={statusColors[selectedDefect.status as keyof typeof statusColors]}>
                    {selectedDefect.status}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Severity">
                  <Tag color={severityColors[selectedDefect.severity as keyof typeof severityColors]}>
                    {selectedDefect.severity}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Priority">{selectedDefect.priority}</Descriptions.Item>
                <Descriptions.Item label="Assignee">{selectedDefect.assignee}</Descriptions.Item>
                <Descriptions.Item label="Reporter">{selectedDefect.reporter}</Descriptions.Item>
                <Descriptions.Item label="Test Case">{selectedDefect.testCase || 'N/A'}</Descriptions.Item>
                <Descriptions.Item label="Environment">{selectedDefect.environment}</Descriptions.Item>
                <Descriptions.Item label="Created">{selectedDefect.createdDate}</Descriptions.Item>
                <Descriptions.Item label="Updated">{selectedDefect.updatedDate}</Descriptions.Item>
                <Descriptions.Item label="Title" span={2}>{selectedDefect.title}</Descriptions.Item>
                <Descriptions.Item label="Description" span={2}>
                  {selectedDefect.description}
                </Descriptions.Item>
                <Descriptions.Item label="Tags" span={2}>
                  {selectedDefect.tags.map(tag => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="History" key="history">
              <Alert
                message="Activity History"
                description="Defect history and comments would be displayed here."
                type="info"
              />
            </TabPane>
          </Tabs>
        ) : (
          // Edit/Create mode
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="title"
                  label="Title"
                  rules={[{ required: true, message: 'Please enter defect title' }]}
                >
                  <Input placeholder="Brief description of the defect" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="severity"
                  label="Severity"
                  rules={[{ required: true, message: 'Please select severity' }]}
                >
                  <Select placeholder="Select severity">
                    <Option value="Critical">Critical</Option>
                    <Option value="High">High</Option>
                    <Option value="Medium">Medium</Option>
                    <Option value="Low">Low</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="priority"
                  label="Priority"
                  rules={[{ required: true, message: 'Please select priority' }]}
                >
                  <Select placeholder="Select priority">
                    <Option value="P1">P1 - Critical</Option>
                    <Option value="P2">P2 - High</Option>
                    <Option value="P3">P3 - Medium</Option>
                    <Option value="P4">P4 - Low</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="status"
                  label="Status"
                  rules={[{ required: true, message: 'Please select status' }]}
                >
                  <Select placeholder="Select status">
                    <Option value="Open">Open</Option>
                    <Option value="In Progress">In Progress</Option>
                    <Option value="Resolved">Resolved</Option>
                    <Option value="Closed">Closed</Option>
                    <Option value="Reopened">Reopened</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="assignee" label="Assignee">
                  <Select placeholder="Select assignee">
                    <Option value="John Doe">John Doe</Option>
                    <Option value="Jane Smith">Jane Smith</Option>
                    <Option value="Bob Wilson">Bob Wilson</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="environment" label="Environment">
                  <Select placeholder="Select environment">
                    <Option value="QEMU x86_64">QEMU x86_64</Option>
                    <Option value="QEMU ARM">QEMU ARM</Option>
                    <Option value="QEMU RISC-V">QEMU RISC-V</Option>
                    <Option value="Physical ARM Board">Physical ARM Board</Option>
                    <Option value="Physical x86 Board">Physical x86 Board</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="testCase" label="Related Test Case">
                  <Input placeholder="e.g., TC-001" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="testExecution" label="Test Execution ID">
                  <Input placeholder="e.g., EXE-12345" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="description" label="Description">
              <TextArea
                rows={4}
                placeholder="Detailed description of the defect, steps to reproduce, expected vs actual behavior"
              />
            </Form.Item>

            <Form.Item name="tags" label="Tags">
              <Select
                mode="tags"
                placeholder="Add tags (e.g., memory, network, performance)"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default DefectManagement