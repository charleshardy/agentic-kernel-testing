import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, InputNumber,
  Select, Typography, Row, Col, Statistic, Badge, Tooltip, Progress
} from 'antd'
import {
  DesktopOutlined, PlusOutlined, ReloadOutlined, SettingOutlined,
  PauseCircleOutlined, PlayCircleOutlined, CloudServerOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select

interface Host {
  id: string
  hostname: string
  ip_address: string
  status: 'online' | 'offline' | 'degraded' | 'maintenance'
  architecture: string
  total_cpu_cores: number
  total_memory_mb: number
  total_storage_gb: number
  kvm_enabled: boolean
  running_vm_count: number
  max_vms: number
  maintenance_mode: boolean
  created_at: string
}

/**
 * Host Management Panel
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 7.1**: Register hosts with hostname, IP, SSH credentials
 * **Requirement 9.1**: Display all hosts with status and utilization
 */
const HostManagementPanel: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedHost, setSelectedHost] = useState<Host | null>(null)
  const [form] = Form.useForm()

  const { data: hosts = [], isLoading, refetch } = useQuery<Host[]>(
    'hosts',
    async () => {
      const response = await fetch('/api/v1/infrastructure/hosts')
      if (!response.ok) throw new Error('Failed to fetch hosts')
      return response.json()
    },
    { refetchInterval: 10000 }
  )

  const registerMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/hosts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to register host')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('hosts')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  const maintenanceMutation = useMutation(
    async ({ hostId, enabled }: { hostId: string; enabled: boolean }) => {
      const response = await fetch(`/api/v1/infrastructure/hosts/${hostId}/maintenance?enabled=${enabled}`, { method: 'PUT' })
      if (!response.ok) throw new Error('Failed to set maintenance mode')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('hosts') }
  )

  const getStatusBadge = (status: string) => {
    const config: Record<string, { status: any; text: string }> = {
      online: { status: 'success', text: 'Online' },
      offline: { status: 'error', text: 'Offline' },
      degraded: { status: 'warning', text: 'Degraded' },
      maintenance: { status: 'default', text: 'Maintenance' }
    }
    const c = config[status] || { status: 'default', text: status }
    return <Badge status={c.status} text={c.text} />
  }

  const columns = [
    {
      title: 'Host',
      key: 'host',
      render: (_: any, record: Host) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedHost(record)}>{record.hostname}</a>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.ip_address}</Text>
        </Space>
      )
    },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => getStatusBadge(s) },
    { title: 'Architecture', dataIndex: 'architecture', key: 'arch', render: (a: string) => <Tag color="blue">{a}</Tag> },
    {
      title: 'CPU',
      key: 'cpu',
      render: (_: any, record: Host) => (
        <Tooltip title={`${record.total_cpu_cores} cores`}>
          <Progress percent={Math.round((record.running_vm_count / Math.max(record.max_vms, 1)) * 100)} size="small" />
        </Tooltip>
      )
    },
    {
      title: 'Memory',
      dataIndex: 'total_memory_mb',
      key: 'memory',
      render: (m: number) => <Tag>{Math.round(m / 1024)} GB</Tag>
    },
    {
      title: 'VMs',
      key: 'vms',
      render: (_: any, record: Host) => (
        <Space>
          <CloudServerOutlined />
          <Text>{record.running_vm_count} / {record.max_vms}</Text>
        </Space>
      )
    },
    {
      title: 'KVM',
      dataIndex: 'kvm_enabled',
      key: 'kvm',
      render: (enabled: boolean) => enabled ? <Tag color="green">Enabled</Tag> : <Tag color="red">Disabled</Tag>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Host) => (
        <Space>
          <Tooltip title={record.maintenance_mode ? 'Exit Maintenance' : 'Enter Maintenance'}>
            <Button size="small" 
              icon={record.maintenance_mode ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={() => maintenanceMutation.mutate({ hostId: record.id, enabled: !record.maintenance_mode })} />
          </Tooltip>
          <Button size="small" icon={<SettingOutlined />} onClick={() => setSelectedHost(record)} />
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><DesktopOutlined /> QEMU Hosts</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Register Host</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Hosts" value={hosts.length} prefix={<DesktopOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Online" value={hosts.filter(h => h.status === 'online').length} 
              valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Running VMs" value={hosts.reduce((sum, h) => sum + h.running_vm_count, 0)} 
              prefix={<CloudServerOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Capacity" value={hosts.reduce((sum, h) => sum + h.max_vms, 0)} suffix="VMs" />
          </Card>
        </Col>
      </Row>

      <Table columns={columns} dataSource={hosts} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} />

      {/* Registration Modal */}
      <Modal title="Register Host" open={isModalVisible} onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} confirmLoading={registerMutation.isLoading} width={600}>
        <Form form={form} layout="vertical" onFinish={(values) => registerMutation.mutate(values)}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="hostname" label="Hostname" rules={[{ required: true }]}>
                <Input placeholder="qemu-host-01" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ip_address" label="IP Address" rules={[{ required: true }]}>
                <Input placeholder="192.168.1.100" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="architecture" label="Architecture" rules={[{ required: true }]}>
                <Select placeholder="Select architecture">
                  <Option value="x86_64">x86_64</Option>
                  <Option value="arm64">ARM64</Option>
                  <Option value="riscv64">RISC-V 64</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ssh_port" label="SSH Port" initialValue={22}>
                <InputNumber min={1} max={65535} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="total_cpu_cores" label="CPU Cores" rules={[{ required: true }]}>
                <InputNumber min={1} max={256} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="total_memory_mb" label="Memory (MB)" rules={[{ required: true }]}>
                <InputNumber min={1024} step={1024} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="total_storage_gb" label="Storage (GB)" rules={[{ required: true }]}>
                <InputNumber min={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="max_vms" label="Max VMs" rules={[{ required: true }]}>
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ssh_username" label="SSH Username" initialValue="root">
                <Input />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Host Details Modal */}
      <Modal title={`Host: ${selectedHost?.hostname}`} open={!!selectedHost} onCancel={() => setSelectedHost(null)} footer={null} width={700}>
        {selectedHost && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={6}><Statistic title="Status" value={selectedHost.status} /></Col>
              <Col span={6}><Statistic title="Architecture" value={selectedHost.architecture} /></Col>
              <Col span={6}><Statistic title="Running VMs" value={selectedHost.running_vm_count} /></Col>
              <Col span={6}><Statistic title="Max VMs" value={selectedHost.max_vms} /></Col>
            </Row>
            <Card title="Resources" size="small" style={{ marginTop: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="CPU Cores" value={selectedHost.total_cpu_cores} />
                </Col>
                <Col span={8}>
                  <Statistic title="Memory" value={Math.round(selectedHost.total_memory_mb / 1024)} suffix="GB" />
                </Col>
                <Col span={8}>
                  <Statistic title="Storage" value={selectedHost.total_storage_gb} suffix="GB" />
                </Col>
              </Row>
            </Card>
            <Card title="Features" size="small" style={{ marginTop: 16 }}>
              <Space>
                {selectedHost.kvm_enabled && <Tag color="green">KVM Enabled</Tag>}
                {selectedHost.maintenance_mode && <Tag color="orange">Maintenance Mode</Tag>}
              </Space>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default HostManagementPanel
