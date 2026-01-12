import React, { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Progress,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  Tabs,
  List,
  Collapse,
  Empty,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  ExportOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  BulbOutlined,
  CodeOutlined,
  LinkOutlined,
  BarChartOutlined,
  SyncOutlined,
  TableOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import apiService from '../services/api'
import RequirementEditor from '../components/RequirementEditor'
import PropertyViewer from '../components/PropertyViewer'
import TestExecutionDashboard from '../components/TestExecutionDashboard'
import TraceabilityMatrix from '../components/TraceabilityMatrix'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { TabPane } = Tabs
const { Panel } = Collapse

interface Requirement {
  id: string
  text: string
  pattern: string
  trigger?: string
  state?: string
  system: string
  response: string
}

interface Property {
  id: string
  name: string
  description: string
  pattern: string
  universal_quantifier: string
  property_statement: string
  requirement_ids: string[]
}

interface GeneratedTest {
  id: string
  name: string
  property_id: string
  requirement_ids: string[]
  iterations: number
  test_code?: string
}

interface TestSpecification {
  id: string
  name: string
  description: string
  version: string
  requirements: Requirement[]
  properties: Property[]
  tests: GeneratedTest[]
  glossary: Record<string, string>
  created_at: string
  updated_at: string
}

const TestSpecifications: React.FC = () => {
  const queryClient = useQueryClient()
  const [selectedSpec, setSelectedSpec] = useState<TestSpecification | null>(null)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [requirementModalVisible, setRequirementModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [reqForm] = Form.useForm()

  // Fetch specifications
  const { data: specsData, isLoading, refetch } = useQuery(
    'specifications',
    async () => {
      try {
        const result = await apiService.getSpecifications()
        return result
      } catch (error) {
        console.warn('Specifications API not available, using mock data')
        return { specifications: mockSpecifications }
      }
    },
    { refetchInterval: 30000 }
  )

  const specifications = specsData?.specifications || []

  // Create specification mutation
  const createMutation = useMutation(
    async (data: any) => {
      return await apiService.createSpecification(data)
    },
    {
      onSuccess: () => {
        message.success('Specification created successfully')
        setCreateModalVisible(false)
        form.resetFields()
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to create specification: ${error.message}`)
      },
    }
  )

  // Delete specification mutation
  const deleteMutation = useMutation(
    async (specId: string) => {
      await apiService.deleteSpecification(specId)
    },
    {
      onSuccess: () => {
        message.success('Specification deleted')
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to delete: ${error.message}`)
      },
    }
  )

  // Generate properties mutation
  const generatePropertiesMutation = useMutation(
    async (specId: string) => {
      return await apiService.generateSpecificationProperties(specId)
    },
    {
      onSuccess: (data) => {
        const count = data?.properties?.length || 0
        message.success(`Generated ${count} properties`)
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to generate properties: ${error.message}`)
      },
    }
  )

  // Generate tests mutation
  const generateTestsMutation = useMutation(
    async (specId: string) => {
      return await apiService.generateSpecificationTests(specId)
    },
    {
      onSuccess: (data) => {
        const count = data?.tests?.length || 0
        message.success(`Generated ${count} tests`)
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to generate tests: ${error.message}`)
      },
    }
  )

  // Execute tests mutation
  const executeTestsMutation = useMutation(
    async (specId: string) => {
      return await apiService.executeSpecificationTests(specId, {
        iterations: 100,
        parallel: true,
      })
    },
    {
      onSuccess: (data) => {
        const summary = data?.summary || {}
        message.success(`Executed ${summary.total || 0} tests: ${summary.passed || 0} passed`)
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to execute tests: ${error.message}`)
      },
    }
  )

  // Add requirement mutation
  const addRequirementMutation = useMutation(
    async ({ specId, text }: { specId: string; text: string }) => {
      return await apiService.addSpecificationRequirement(specId, text)
    },
    {
      onSuccess: () => {
        message.success('Requirement added')
        setRequirementModalVisible(false)
        reqForm.resetFields()
        refetch()
      },
      onError: (error: any) => {
        message.error(`Failed to add requirement: ${error.message}`)
      },
    }
  )

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      createMutation.mutate({
        name: values.name,
        description: values.description || '',
        glossary: {},
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleAddRequirement = async () => {
    if (!selectedSpec) return
    try {
      const values = await reqForm.validateFields()
      addRequirementMutation.mutate({
        specId: selectedSpec.id,
        text: values.text,
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const getPatternColor = (pattern: string) => {
    const colors: Record<string, string> = {
      event_driven: 'blue',
      state_driven: 'green',
      unwanted: 'red',
      ubiquitous: 'purple',
      optional: 'orange',
      complex: 'cyan',
    }
    return colors[pattern] || 'default'
  }

  const getPropertyPatternIcon = (pattern: string) => {
    switch (pattern) {
      case 'round_trip':
        return <SyncOutlined />
      case 'invariant':
        return <CheckCircleOutlined />
      case 'idempotence':
        return <CodeOutlined />
      default:
        return <BulbOutlined />
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: TestSpecification) => (
        <Space direction="vertical" size="small">
          <Space>
            <FileTextOutlined />
            <Text strong>{name}</Text>
            <Tag>v{record.version}</Tag>
          </Space>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description || 'No description'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Requirements',
      key: 'requirements',
      width: 120,
      render: (_: any, record: TestSpecification) => (
        <Statistic
          value={record.requirements?.length || 0}
          prefix={<FileTextOutlined />}
          valueStyle={{ fontSize: '16px' }}
        />
      ),
    },
    {
      title: 'Properties',
      key: 'properties',
      width: 120,
      render: (_: any, record: TestSpecification) => (
        <Statistic
          value={record.properties?.length || 0}
          prefix={<BulbOutlined />}
          valueStyle={{ fontSize: '16px', color: '#1890ff' }}
        />
      ),
    },
    {
      title: 'Tests',
      key: 'tests',
      width: 120,
      render: (_: any, record: TestSpecification) => (
        <Statistic
          value={record.tests?.length || 0}
          prefix={<CodeOutlined />}
          valueStyle={{ fontSize: '16px', color: '#52c41a' }}
        />
      ),
    },
    {
      title: 'Coverage',
      key: 'coverage',
      width: 150,
      render: (_: any, record: TestSpecification) => {
        const reqCount = record.requirements?.length || 0
        const testedCount = record.tests?.length || 0
        const coverage = reqCount > 0 ? Math.round((testedCount / reqCount) * 100) : 0
        return (
          <Progress
            percent={Math.min(coverage, 100)}
            size="small"
            status={coverage >= 80 ? 'success' : coverage >= 50 ? 'normal' : 'exception'}
          />
        )
      },
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
      render: (date: string) => (
        <Text style={{ fontSize: '12px' }}>
          {date ? new Date(date).toLocaleDateString() : 'N/A'}
        </Text>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 280,
      render: (_: any, record: TestSpecification) => (
        <Space wrap>
          <Tooltip title="View Details">
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => {
                setSelectedSpec(record)
                setDetailModalVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title="Generate Properties">
            <Button
              icon={<BulbOutlined />}
              size="small"
              loading={generatePropertiesMutation.isLoading}
              onClick={() => generatePropertiesMutation.mutate(record.id)}
            />
          </Tooltip>
          <Tooltip title="Generate Tests">
            <Button
              icon={<CodeOutlined />}
              size="small"
              loading={generateTestsMutation.isLoading}
              onClick={() => generateTestsMutation.mutate(record.id)}
            />
          </Tooltip>
          <Tooltip title="Run Tests">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              size="small"
              loading={executeTestsMutation.isLoading}
              onClick={() => executeTestsMutation.mutate(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this specification?"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Tooltip title="Delete">
              <Button danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Mock data
  const mockSpecifications: TestSpecification[] = [
    {
      id: 'spec_001',
      name: 'Memory Management Tests',
      description: 'Property-based tests for memory allocation and deallocation',
      version: '1.0.0',
      requirements: [
        {
          id: 'req_001',
          text: 'WHEN memory is allocated, THE System SHALL return a valid pointer',
          pattern: 'event_driven',
          trigger: 'memory is allocated',
          system: 'System',
          response: 'return a valid pointer',
        },
        {
          id: 'req_002',
          text: 'WHEN memory is freed, THE System SHALL mark the memory as available',
          pattern: 'event_driven',
          trigger: 'memory is freed',
          system: 'System',
          response: 'mark the memory as available',
        },
      ],
      properties: [
        {
          id: 'prop_001',
          name: 'Allocation Round-Trip',
          description: 'Allocating and freeing memory should be reversible',
          pattern: 'round_trip',
          universal_quantifier: 'For any valid allocation size',
          property_statement: 'allocate(size) followed by free() should return memory to pool',
          requirement_ids: ['req_001', 'req_002'],
        },
      ],
      tests: [
        {
          id: 'test_001',
          name: 'test_allocation_round_trip',
          property_id: 'prop_001',
          requirement_ids: ['req_001', 'req_002'],
          iterations: 100,
        },
      ],
      glossary: {
        System: 'The memory management subsystem',
        Memory: 'Heap memory managed by the allocator',
      },
      created_at: '2024-12-20T10:00:00Z',
      updated_at: '2024-12-24T15:30:00Z',
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={2}>Test Specifications</Title>
          <Text type="secondary">
            Manage EARS requirements, correctness properties, and property-based tests
          </Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          Create Specification
        </Button>
      </div>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Specifications"
              value={specifications.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Requirements"
              value={specifications.reduce((acc: number, s: TestSpecification) => 
                acc + (s.requirements?.length || 0), 0)}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Properties"
              value={specifications.reduce((acc: number, s: TestSpecification) => 
                acc + (s.properties?.length || 0), 0)}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Tests"
              value={specifications.reduce((acc: number, s: TestSpecification) => 
                acc + (s.tests?.length || 0), 0)}
              prefix={<CodeOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Specifications Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={specifications}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Create Modal */}
      <Modal
        title="Create Test Specification"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => setCreateModalVisible(false)}
        confirmLoading={createMutation.isLoading}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Specification Name"
            rules={[{ required: true, message: 'Please enter a name' }]}
          >
            <Input placeholder="e.g., Memory Management Tests" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Describe the purpose of this specification" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Modal */}
      <Modal
        title={selectedSpec?.name || 'Specification Details'}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={1100}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="addReq"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setRequirementModalVisible(true)}
          >
            Add Requirement
          </Button>,
        ]}
      >
        {selectedSpec && (
          <Tabs defaultActiveKey="requirements">
            <TabPane tab={`Requirements (${selectedSpec.requirements?.length || 0})`} key="requirements">
              {selectedSpec.requirements?.length > 0 ? (
                <List
                  dataSource={selectedSpec.requirements}
                  renderItem={(req: Requirement) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Tag color={getPatternColor(req.pattern)}>{req.pattern}</Tag>}
                        title={<Text code>{req.id}</Text>}
                        description={
                          <div>
                            <Paragraph>{req.text}</Paragraph>
                            <Space>
                              {req.trigger && <Tag>Trigger: {req.trigger}</Tag>}
                              <Tag color="blue">System: {req.system}</Tag>
                            </Space>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="No requirements yet" />
              )}
            </TabPane>

            <TabPane tab={`Properties (${selectedSpec.properties?.length || 0})`} key="properties">
              <PropertyViewer
                properties={selectedSpec.properties || []}
                requirements={selectedSpec.requirements}
                editable={true}
                onGenerateTest={(propId) => {
                  message.info(`Generating test for property ${propId}`)
                  generateTestsMutation.mutate(selectedSpec.id)
                }}
                onDelete={(propId) => {
                  message.info(`Delete property ${propId} - not implemented yet`)
                }}
              />
              {(!selectedSpec.properties || selectedSpec.properties.length === 0) && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Button
                    type="primary"
                    icon={<BulbOutlined />}
                    onClick={() => generatePropertiesMutation.mutate(selectedSpec.id)}
                    loading={generatePropertiesMutation.isLoading}
                  >
                    Generate Properties
                  </Button>
                </div>
              )}
            </TabPane>

            <TabPane tab={`Tests (${selectedSpec.tests?.length || 0})`} key="tests">
              <TestExecutionDashboard
                results={(selectedSpec.tests || []).map(test => ({
                  id: test.id,
                  test_name: test.name,
                  property_id: test.property_id,
                  requirement_ids: test.requirement_ids,
                  status: 'pending' as const,
                  iterations_completed: 0,
                  iterations_total: test.iterations,
                }))}
                onStart={() => executeTestsMutation.mutate(selectedSpec.id)}
                isRunning={executeTestsMutation.isLoading}
              />
              {(!selectedSpec.tests || selectedSpec.tests.length === 0) && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Button
                    type="primary"
                    icon={<CodeOutlined />}
                    onClick={() => generateTestsMutation.mutate(selectedSpec.id)}
                    loading={generateTestsMutation.isLoading}
                    disabled={!selectedSpec.properties?.length}
                  >
                    Generate Tests
                  </Button>
                </div>
              )}
            </TabPane>

            <TabPane 
              tab={
                <Space>
                  <TableOutlined />
                  Traceability
                </Space>
              } 
              key="traceability"
            >
              <TraceabilityMatrix
                requirements={selectedSpec.requirements || []}
                properties={selectedSpec.properties || []}
                tests={(selectedSpec.tests || []).map(t => ({
                  id: t.id,
                  name: t.name,
                  property_id: t.property_id,
                  requirement_ids: t.requirement_ids,
                  status: 'not_run' as const,
                }))}
                onExport={(format) => {
                  message.info(`Exporting traceability matrix as ${format}`)
                }}
              />
            </TabPane>

            <TabPane tab="Glossary" key="glossary">
              {Object.keys(selectedSpec.glossary || {}).length > 0 ? (
                <List
                  dataSource={Object.entries(selectedSpec.glossary)}
                  renderItem={([term, definition]) => (
                    <List.Item>
                      <List.Item.Meta
                        title={<Text strong>{term}</Text>}
                        description={definition}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="No glossary terms defined" />
              )}
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* Add Requirement Modal */}
      <Modal
        title="Add Requirement"
        open={requirementModalVisible}
        onOk={handleAddRequirement}
        onCancel={() => setRequirementModalVisible(false)}
        confirmLoading={addRequirementMutation.isLoading}
        width={700}
      >
        <Form form={reqForm} layout="vertical">
          <Form.Item
            name="text"
            label="Requirement Text"
            rules={[{ required: true, message: 'Please enter the requirement' }]}
          >
            <RequirementEditor
              glossary={selectedSpec?.glossary || {}}
              showTemplates={true}
              showValidation={true}
              onChange={(value) => reqForm.setFieldsValue({ text: value })}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TestSpecifications
