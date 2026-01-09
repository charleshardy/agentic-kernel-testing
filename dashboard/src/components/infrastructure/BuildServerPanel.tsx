import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, InputNumber,
  Select, Switch, Progress, Tooltip, Badge, Typography, Row, Col, Statistic
} from 'antd'
import {
  HddOutlined, PlusOutlined, ReloadOutlined, SettingOutlined,
  PlayCircleOutlined, PauseCircleOutlined, DeleteOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ToolOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select

interface BuildServer {
  id: string
  hostname: string
  ip_address: string
  status: 'online' | 'offline' | 'degraded' | 'maintenance'
  supported_architectures: string[]
  toolchains: Toolchain[]
  total_cpu_cores: number
  total_memory_mb: number
  total_storage_gb: number
  active_build_count: number
  queue_depth: number
  maintenance_mode: boolean
  created_at: string
  updated_at: string
}

interface Toolchain {
  name: string
  version: string
  target_architecture: string
  path: string
  available: boolean
}

interface BuildServerRegistration {
  hostname: string
  ip_address: string
  ssh_port: number
  ssh_username: string
  ssh_key_path?: string
  supported_architectures: string[]
  max_concurrent_builds: number
  labels: Record<string, string>
}

/**
 * Build Server Management Panel
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 1.1**: Register build servers with hostname, IP, SSH credentials
 * **Requirement 2.1**: Display all registered build servers with status
 * **Requirement 2.5**: Display detailed information including toolchains and history
 */
const BuildServerPanel: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedServer, setSelectedServer] = useState<BuildServer | null>(null)
  const [form] = Form.useForm()

  // Fetch build servers
  const { data: servers = [], isLoading, refetch } = useQuery<BuildServer[]>(
    'buildServers',
    async () => {
      const response = await fetch('/api/v1/infrastructure/build-servers')
      if (!response.ok) throw new Error('Failed to fetch build servers')
      return response.json()
    },
    { refetchInterval: 10000 }
  )

  // Register build server mutation
  const registerMutation = useMutation(
    async (data: BuildServerRegistration) => {
      const response = await fetch('/api/v1/infrastructure/build-servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to register build server')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('buildServers')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  // Set maintenance mode mutation
  const maintenanceMutation = useMutation(
    async ({ serverId, enabled }: { serverId: string; enabled: boolean }) => {
      const response = await fetch(
        `/api/v1/infrastructure/build-servers/${serverId}/maintenance?enabled=${enabled}`,
        { method: 'PUT' }
      )
      if (!response.ok) throw new Error('Failed to set maintenance mode')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('buildServers') }
  )

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      online: { color: 'green', text: 'Online' },
      offline: { color: 'red', text: 'Offline' },
      degraded: { color: 'orange', text: 'Degraded' },
      maintenance: { color: 'blue', text: 'Maintenance' }
    }
    const config = statusConfig[status] || { color: 'default', text: status }
    return <Badge status={config.color as any} text={config.text} />
  }

  const columns = [
    {
      title: 'Hostname',
      dataIndex: 'hostname',
      key: 'hostname',
      render: (text: string, record: BuildServer) => (
        <Space>
          <HddOutlined />
          <a onClick={() => setSelectedServer(record)}>{text}</a>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusBadge(status)
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address'
    },
    {
      title: 'Architectures',
      dataIndex: 'supported_architectures',
      key: 'architectures',
      render: (archs: string[]) => (
        <Space wrap>
          {archs.map(arch => <Tag key={arch} color="blue">{arch}</Tag>)}
        </Space>
      )
    },
    {
      title: 'Active Builds',
      dataIndex: 'active_build_count',
      key: 'active_builds',
      render: (count: number, record: BuildServer) => (
        <Tooltip title={`Queue depth: ${record.queue_depth}`}>
          <Badge count={count} showZero style={{ backgroundColor: count > 0 ? '#1890ff' : '#d9d9d9' }} />
        </Tooltip>
      )
    },
    {
      title: 'Resources',
      key: 'resources',
      render: (_: any, record: BuildServer) => (
        <Space direction="vertical" size="small">
          <Text type="secondary" style={{ fontSize: 12 }}>
            CPU: {record.total_cpu_cores} cores
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            RAM: {Math.round(record.total_memory_mb / 1024)}GB
          </Text>
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: BuildServer) => (
        <Space>
          <Tooltip title={record.maintenance_mode ? 'Exit Maintenance' : 'Enter Maintenance'}>
            <Button
              size="small"
              icon={record.maintenance_mode ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={() => maintenanceMutation.mutate({
                serverId: record.id,
                enabled: !record.maintenance_mode
              })}
            />
          </Tooltip>
          <Tooltip title="View Details">
            <Button size="small" icon={<SettingOutlined />} onClick={() => setSelectedServer(record)} />
          </Tooltip>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><HddOutlined /> Build Servers</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
            Register Server
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={servers}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />

      {/* Registration Modal */}
      <Modal
        title="Register Build Server"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={registerMutation.isLoading}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={(values) => registerMutation.mutate(values)}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="hostname" label="Hostname" rules={[{ required: true }]}>
                <Input placeholder="build-server-01" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ip_address" label="IP Address" rules={[{ required: true }]}>
                <Input placeholder="192.168.1.100" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="ssh_port" label="SSH Port" initialValue={22}>
                <InputNumber min={1} max={65535} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="ssh_username" label="SSH Username" rules={[{ required: true }]}>
                <Input placeholder="builder" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_concurrent_builds" label="Max Builds" initialValue={4}>
                <InputNumber min={1} max={32} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="ssh_key_path" label="SSH Key Path">
            <Input placeholder="/home/builder/.ssh/id_rsa" />
          </Form.Item>
          <Form.Item name="supported_architectures" label="Supported Architectures" rules={[{ required: true }]}>
            <Select mode="multiple" placeholder="Select architectures">
              <Option value="x86_64">x86_64</Option>
              <Option value="arm64">ARM64</Option>
              <Option value="arm">ARM</Option>
              <Option value="riscv64">RISC-V 64</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Server Details Modal */}
      <Modal
        title={`Build Server: ${selectedServer?.hostname}`}
        open={!!selectedServer}
        onCancel={() => setSelectedServer(null)}
        footer={null}
        width={700}
      >
        {selectedServer && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={8}><Statistic title="Status" value={selectedServer.status} /></Col>
              <Col span={8}><Statistic title="Active Builds" value={selectedServer.active_build_count} /></Col>
              <Col span={8}><Statistic title="Queue Depth" value={selectedServer.queue_depth} /></Col>
            </Row>
            <Card title="Toolchains" size="small" style={{ marginTop: 16 }}>
              {selectedServer.toolchains.length > 0 ? (
                selectedServer.toolchains.map(tc => (
                  <Tag key={tc.name} color={tc.available ? 'green' : 'red'} style={{ marginBottom: 4 }}>
                    {tc.name} ({tc.version}) - {tc.target_architecture}
                  </Tag>
                ))
              ) : (
                <Text type="secondary">No toolchains detected</Text>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default BuildServerPanel
