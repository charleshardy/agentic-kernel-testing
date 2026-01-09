import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, Select,
  Typography, Row, Col, Statistic, Badge, Tooltip, Progress, Tabs
} from 'antd'
import {
  BuildOutlined, PlusOutlined, ReloadOutlined, StopOutlined,
  ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input

interface BuildJob {
  id: string
  repository_url: string
  branch: string
  commit_hash?: string
  architecture: string
  build_server_id?: string
  status: 'queued' | 'building' | 'completed' | 'failed' | 'cancelled'
  progress_percent: number
  estimated_completion?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

/**
 * Build Job Dashboard
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 3.1**: Submit build jobs with repository, branch, architecture
 * **Requirement 3.5**: View build logs and progress
 */
const BuildJobDashboard: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedJob, setSelectedJob] = useState<BuildJob | null>(null)
  const [form] = Form.useForm()

  const { data: jobs = [], isLoading, refetch } = useQuery<BuildJob[]>(
    'build-jobs',
    async () => {
      const response = await fetch('/api/v1/infrastructure/build-jobs')
      if (!response.ok) throw new Error('Failed to fetch build jobs')
      return response.json()
    },
    { refetchInterval: 5000 }
  )

  const { data: buildServers = [] } = useQuery<any[]>('build-servers', async () => {
    const response = await fetch('/api/v1/infrastructure/build-servers')
    if (!response.ok) throw new Error('Failed to fetch build servers')
    return response.json()
  })

  const submitMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/build-jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to submit build job')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('build-jobs')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  const cancelMutation = useMutation(
    async (jobId: string) => {
      const response = await fetch(`/api/v1/infrastructure/build-jobs/${jobId}/cancel`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to cancel build job')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('build-jobs') }
  )

  const getStatusBadge = (status: string) => {
    const config: Record<string, { status: any; text: string; icon: React.ReactNode }> = {
      queued: { status: 'default', text: 'Queued', icon: <ClockCircleOutlined /> },
      building: { status: 'processing', text: 'Building', icon: <BuildOutlined spin /> },
      completed: { status: 'success', text: 'Completed', icon: <CheckCircleOutlined /> },
      failed: { status: 'error', text: 'Failed', icon: <CloseCircleOutlined /> },
      cancelled: { status: 'warning', text: 'Cancelled', icon: <StopOutlined /> }
    }
    const c = config[status] || { status: 'default', text: status, icon: null }
    return <Badge status={c.status} text={<Space>{c.icon}{c.text}</Space>} />
  }

  const activeJobs = jobs.filter(j => j.status === 'building')
  const queuedJobs = jobs.filter(j => j.status === 'queued')

  const columns = [
    {
      title: 'Job',
      key: 'job',
      render: (_: any, record: BuildJob) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedJob(record)}>{record.id.slice(0, 8)}</a>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.branch}</Text>
        </Space>
      )
    },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => getStatusBadge(s) },
    { title: 'Architecture', dataIndex: 'architecture', key: 'arch', render: (a: string) => <Tag color="blue">{a}</Tag> },
    {
      title: 'Progress',
      key: 'progress',
      render: (_: any, record: BuildJob) => (
        record.status === 'building' ? <Progress percent={record.progress_percent} size="small" /> : '-'
      )
    },
    {
      title: 'Repository',
      dataIndex: 'repository_url',
      key: 'repo',
      render: (url: string) => <Text ellipsis style={{ maxWidth: 200 }}>{url}</Text>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: BuildJob) => (
        <Space>
          {['queued', 'building'].includes(record.status) && (
            <Tooltip title="Cancel">
              <Button size="small" danger icon={<StopOutlined />} onClick={() => cancelMutation.mutate(record.id)} />
            </Tooltip>
          )}
          <Button size="small" onClick={() => setSelectedJob(record)}>View</Button>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><BuildOutlined /> Build Jobs</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Submit Build</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="Active Builds" value={activeJobs.length} prefix={<BuildOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Queued" value={queuedJobs.length} prefix={<ClockCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Completed Today" 
              value={jobs.filter(j => j.status === 'completed').length} 
              valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Failed Today" 
              value={jobs.filter(j => j.status === 'failed').length} 
              valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="all" items={[
        { key: 'all', label: 'All Jobs', children: <Table columns={columns} dataSource={jobs} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} /> },
        { key: 'active', label: `Active (${activeJobs.length})`, children: <Table columns={columns} dataSource={activeJobs} rowKey="id" loading={isLoading} /> },
        { key: 'queued', label: `Queued (${queuedJobs.length})`, children: <Table columns={columns} dataSource={queuedJobs} rowKey="id" loading={isLoading} /> }
      ]} />

      {/* Submit Build Modal */}
      <Modal title="Submit Build Job" open={isModalVisible} onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} confirmLoading={submitMutation.isLoading} width={600}>
        <Form form={form} layout="vertical" onFinish={(values) => submitMutation.mutate(values)}>
          <Form.Item name="repository_url" label="Repository URL" rules={[{ required: true }]}>
            <Input placeholder="https://github.com/org/kernel.git" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="branch" label="Branch" rules={[{ required: true }]}>
                <Input placeholder="main" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="commit_hash" label="Commit (optional)">
                <Input placeholder="abc123..." />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="architecture" label="Architecture" rules={[{ required: true }]}>
                <Select placeholder="Select architecture">
                  <Option value="x86_64">x86_64</Option>
                  <Option value="arm64">ARM64</Option>
                  <Option value="arm">ARM</Option>
                  <Option value="riscv64">RISC-V 64</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="build_server_id" label="Build Server">
                <Select placeholder="Auto (recommended)" allowClear>
                  {buildServers.filter(s => s.status === 'online').map(s => (
                    <Option key={s.id} value={s.id}>{s.hostname}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Job Details Modal */}
      <Modal title={`Build Job: ${selectedJob?.id.slice(0, 8)}`} open={!!selectedJob} 
        onCancel={() => setSelectedJob(null)} footer={null} width={800}>
        {selectedJob && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={6}><Statistic title="Status" value={selectedJob.status} /></Col>
              <Col span={6}><Statistic title="Architecture" value={selectedJob.architecture} /></Col>
              <Col span={6}><Statistic title="Progress" value={selectedJob.progress_percent} suffix="%" /></Col>
              <Col span={6}><Statistic title="Branch" value={selectedJob.branch} /></Col>
            </Row>
            <Card title="Build Logs" size="small" style={{ marginTop: 16 }}>
              <Paragraph code style={{ maxHeight: 300, overflow: 'auto', background: '#1e1e1e', color: '#d4d4d4', padding: 12 }}>
                Build logs will appear here when available...
              </Paragraph>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default BuildJobDashboard
