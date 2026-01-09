import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, InputNumber,
  Select, Typography, Row, Col, Statistic, Badge, Tooltip, Progress
} from 'antd'
import {
  CloudServerOutlined, PlusOutlined, ReloadOutlined, SettingOutlined,
  ThunderboltOutlined, UploadOutlined, ToolOutlined, CheckCircleOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select

interface Board {
  id: string
  name: string
  board_type: string
  serial_number?: string
  architecture: string
  status: 'available' | 'in_use' | 'flashing' | 'offline' | 'maintenance' | 'recovery'
  ip_address?: string
  power_control: { method: string; usb_hub_port?: number; pdu_outlet?: number }
  peripherals: string[]
  current_firmware_version?: string
  maintenance_mode: boolean
  created_at: string
}

interface BoardHealth {
  connectivity: string
  temperature_celsius?: number
  storage_percent?: number
  power_status: string
  last_response_time_ms?: number
}

/**
 * Board Management Panel
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 8.1**: Register boards with type, serial, connection method
 * **Requirement 10.1**: Display all boards with status and health
 * **Requirement 18.1-18.5**: Power control operations
 */
const BoardManagementPanel: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedBoard, setSelectedBoard] = useState<Board | null>(null)
  const [form] = Form.useForm()

  const { data: boards = [], isLoading, refetch } = useQuery<Board[]>(
    'boards',
    async () => {
      const response = await fetch('/api/v1/infrastructure/boards')
      if (!response.ok) throw new Error('Failed to fetch boards')
      return response.json()
    },
    { refetchInterval: 5000 }
  )

  const registerMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/boards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to register board')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('boards')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  const powerCycleMutation = useMutation(
    async (boardId: string) => {
      const response = await fetch(`/api/v1/infrastructure/boards/${boardId}/power-cycle`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to power cycle board')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('boards') }
  )

  const getStatusBadge = (status: string) => {
    const config: Record<string, { status: any; text: string }> = {
      available: { status: 'success', text: 'Available' },
      in_use: { status: 'processing', text: 'In Use' },
      flashing: { status: 'warning', text: 'Flashing' },
      offline: { status: 'error', text: 'Offline' },
      maintenance: { status: 'default', text: 'Maintenance' },
      recovery: { status: 'warning', text: 'Recovery' }
    }
    const c = config[status] || { status: 'default', text: status }
    return <Badge status={c.status} text={c.text} />
  }

  const columns = [
    {
      title: 'Board',
      key: 'board',
      render: (_: any, record: Board) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedBoard(record)}>{record.name}</a>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.board_type}</Text>
        </Space>
      )
    },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => getStatusBadge(s) },
    { title: 'Architecture', dataIndex: 'architecture', key: 'arch', render: (a: string) => <Tag color="blue">{a}</Tag> },
    {
      title: 'Peripherals',
      dataIndex: 'peripherals',
      key: 'peripherals',
      render: (p: string[]) => <Space wrap>{p.slice(0, 3).map(x => <Tag key={x}>{x}</Tag>)}{p.length > 3 && <Tag>+{p.length - 3}</Tag>}</Space>
    },
    {
      title: 'Power Control',
      key: 'power',
      render: (_: any, record: Board) => <Tag>{record.power_control.method}</Tag>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Board) => (
        <Space>
          <Tooltip title="Power Cycle">
            <Button size="small" icon={<ThunderboltOutlined />} onClick={() => powerCycleMutation.mutate(record.id)} 
              disabled={record.status === 'flashing'} />
          </Tooltip>
          <Button size="small" icon={<SettingOutlined />} onClick={() => setSelectedBoard(record)} />
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><CloudServerOutlined /> Physical Boards</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Register Board</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={boards} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} />

      {/* Registration Modal */}
      <Modal title="Register Board" open={isModalVisible} onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} confirmLoading={registerMutation.isLoading} width={600}>
        <Form form={form} layout="vertical" onFinish={(values) => registerMutation.mutate({
          ...values,
          power_control: { method: values.power_method, usb_hub_port: values.usb_hub_port }
        })}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="Board Name" rules={[{ required: true }]}>
                <Input placeholder="rpi4-board-01" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="board_type" label="Board Type" rules={[{ required: true }]}>
                <Select placeholder="Select type">
                  <Option value="raspberry_pi_4">Raspberry Pi 4</Option>
                  <Option value="raspberry_pi_5">Raspberry Pi 5</Option>
                  <Option value="beaglebone_black">BeagleBone Black</Option>
                  <Option value="nvidia_jetson">NVIDIA Jetson</Option>
                  <Option value="custom">Custom</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="architecture" label="Architecture" rules={[{ required: true }]}>
                <Select placeholder="Select architecture">
                  <Option value="arm64">ARM64</Option>
                  <Option value="arm">ARM</Option>
                  <Option value="x86_64">x86_64</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="serial_number" label="Serial Number">
                <Input placeholder="SN123456789" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="ip_address" label="IP Address">
                <Input placeholder="192.168.1.150" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="power_method" label="Power Control" rules={[{ required: true }]}>
                <Select placeholder="Select method">
                  <Option value="usb_hub">USB Hub</Option>
                  <Option value="network_pdu">Network PDU</Option>
                  <Option value="gpio_relay">GPIO Relay</Option>
                  <Option value="manual">Manual</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="peripherals" label="Peripherals">
            <Select mode="multiple" placeholder="Select peripherals">
              <Option value="gpio">GPIO</Option>
              <Option value="i2c">I2C</Option>
              <Option value="spi">SPI</Option>
              <Option value="uart">UART</Option>
              <Option value="usb">USB</Option>
              <Option value="ethernet">Ethernet</Option>
              <Option value="wifi">WiFi</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Board Details Modal */}
      <Modal title={`Board: ${selectedBoard?.name}`} open={!!selectedBoard} onCancel={() => setSelectedBoard(null)} footer={null} width={700}>
        {selectedBoard && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={8}><Statistic title="Status" value={selectedBoard.status} /></Col>
              <Col span={8}><Statistic title="Architecture" value={selectedBoard.architecture} /></Col>
              <Col span={8}><Statistic title="Firmware" value={selectedBoard.current_firmware_version || 'Unknown'} /></Col>
            </Row>
            <Card title="Peripherals" size="small" style={{ marginTop: 16 }}>
              <Space wrap>{selectedBoard.peripherals.map(p => <Tag key={p} color="green">{p}</Tag>)}</Space>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default BoardManagementPanel
