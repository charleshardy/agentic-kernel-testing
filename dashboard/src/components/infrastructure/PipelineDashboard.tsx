import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, Select,
  Steps, Progress, Typography, Row, Col, Tooltip, Badge
} from 'antd'
import {
  RocketOutlined, PlusOutlined, ReloadOutlined, StopOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined,
  ClockCircleOutlined, PlayCircleOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select
const { Step } = Steps

interface PipelineStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
}

interface Pipeline {
  id: string
  name?: string
  source_repository: string
  branch: string
  target_architecture: string
  environment_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current_stage?: string
  stages: PipelineStage[]
  started_at?: string
  completed_at?: string
  error_message?: string
  created_at: string
}

interface PipelineCreation {
  name?: string
  source_repository: string
  branch: string
  commit_hash?: string
  target_architecture: string
  environment_type: string
  environment_config: Record<string, any>
  auto_retry: boolean
}

/**
 * Pipeline Dashboard Component
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 17.1-17.5**: Pipeline creation, stage progress, and monitoring
 */
const PipelineDashboard: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [form] = Form.useForm()

  // Fetch pipelines
  const { data: pipelines = [], isLoading, refetch } = useQuery<Pipeline[]>(
    'pipelines',
    async () => {
      const response = await fetch('/api/v1/infrastructure/pipelines')
      if (!response.ok) throw new Error('Failed to fetch pipelines')
      return response.json()
    },
    { refetchInterval: 5000 }
  )

  // Create pipeline mutation
  const createMutation = useMutation(
    async (data: PipelineCreation) => {
      const response = await fetch('/api/v1/infrastructure/pipelines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to create pipeline')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('pipelines')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  // Cancel pipeline mutation
  const cancelMutation = useMutation(
    async (pipelineId: string) => {
      const response = await fetch(`/api/v1/infrastructure/pipelines/${pipelineId}/cancel`, {
        method: 'PUT'
      })
      if (!response.ok) throw new Error('Failed to cancel pipeline')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('pipelines') }
  )

  const getStageIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'running': return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'failed': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'pending': return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
      default: return <ClockCircleOutlined />
    }
  }

  const getStatusTag = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'default', running: 'processing', completed: 'success',
      failed: 'error', cancelled: 'warning'
    }
    return <Tag color={colors[status] || 'default'}>{status.toUpperCase()}</Tag>
  }

  const columns = [
    {
      title: 'Pipeline',
      key: 'pipeline',
      render: (_: any, record: Pipeline) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedPipeline(record)}>
            {record.name || `Pipeline ${record.id.slice(0, 8)}`}
          </a>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.source_repository}</Text>
        </Space>
      )
    },
    {
      title: 'Branch',
      dataIndex: 'branch',
      key: 'branch',
      render: (branch: string) => <Tag>{branch}</Tag>
    },
    {
      title: 'Architecture',
      dataIndex: 'target_architecture',
      key: 'architecture',
      render: (arch: string) => <Tag color="blue">{arch}</Tag>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status)
    },
    {
      title: 'Stages',
      key: 'stages',
      render: (_: any, record: Pipeline) => (
        <Space>
          {record.stages.map((stage, idx) => (
            <Tooltip key={idx} title={`${stage.name}: ${stage.status}`}>
              {getStageIcon(stage.status)}
            </Tooltip>
          ))}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Pipeline) => (
        <Space>
          {record.status === 'running' && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => cancelMutation.mutate(record.id)}
            >
              Cancel
            </Button>
          )}
          <Button size="small" onClick={() => setSelectedPipeline(record)}>Details</Button>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><RocketOutlined /> Pipelines</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
            Create Pipeline
          </Button>
        </Space>
      </div>

      <Table columns={columns} dataSource={pipelines} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} />

      {/* Create Pipeline Modal */}
      <Modal
        title="Create Pipeline"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isLoading}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate({
          ...values,
          environment_config: {},
          auto_retry: true
        })}>
          <Form.Item name="name" label="Pipeline Name">
            <Input placeholder="kernel-test-pipeline" />
          </Form.Item>
          <Form.Item name="source_repository" label="Source Repository" rules={[{ required: true }]}>
            <Input placeholder="https://github.com/example/linux-kernel" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="branch" label="Branch" rules={[{ required: true }]}>
                <Input placeholder="main" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="commit_hash" label="Commit Hash">
                <Input placeholder="abc123 (optional)" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="target_architecture" label="Architecture" rules={[{ required: true }]}>
                <Select placeholder="Select architecture">
                  <Option value="x86_64">x86_64</Option>
                  <Option value="arm64">ARM64</Option>
                  <Option value="arm">ARM</Option>
                  <Option value="riscv64">RISC-V 64</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="environment_type" label="Environment Type" rules={[{ required: true }]}>
                <Select placeholder="Select environment">
                  <Option value="qemu">QEMU (Virtual)</Option>
                  <Option value="physical_board">Physical Board</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Pipeline Details Modal */}
      <Modal
        title={`Pipeline: ${selectedPipeline?.name || selectedPipeline?.id}`}
        open={!!selectedPipeline}
        onCancel={() => setSelectedPipeline(null)}
        footer={null}
        width={800}
      >
        {selectedPipeline && (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={8}><Text strong>Repository:</Text> {selectedPipeline.source_repository}</Col>
              <Col span={8}><Text strong>Branch:</Text> {selectedPipeline.branch}</Col>
              <Col span={8}><Text strong>Status:</Text> {getStatusTag(selectedPipeline.status)}</Col>
            </Row>
            <Card title="Pipeline Stages" size="small">
              <Steps current={selectedPipeline.stages.findIndex(s => s.status === 'running')} status={
                selectedPipeline.status === 'failed' ? 'error' : undefined
              }>
                {selectedPipeline.stages.map((stage, idx) => (
                  <Step
                    key={idx}
                    title={stage.name.charAt(0).toUpperCase() + stage.name.slice(1)}
                    status={stage.status === 'completed' ? 'finish' : stage.status === 'running' ? 'process' : 
                            stage.status === 'failed' ? 'error' : 'wait'}
                    description={stage.duration_seconds ? `${stage.duration_seconds}s` : undefined}
                  />
                ))}
              </Steps>
            </Card>
            {selectedPipeline.error_message && (
              <Card title="Error" size="small" style={{ marginTop: 16 }}>
                <Text type="danger">{selectedPipeline.error_message}</Text>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default PipelineDashboard
