import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, InputNumber,
  Select, Typography, Row, Col, Statistic, Progress, Tabs
} from 'antd'
import {
  GroupOutlined, PlusOutlined, ReloadOutlined, SettingOutlined,
  DesktopOutlined, CloudServerOutlined, BuildOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select

interface ResourceGroup {
  id: string
  name: string
  resource_type: 'build_server' | 'host' | 'board'
  labels: Record<string, string>
  member_count: number
  total_capacity: number
  used_capacity: number
  allocation_policy?: {
    max_concurrent: number
    allowed_teams: string[]
    priority: number
  }
  created_at: string
}

/**
 * Resource Group Management Panel
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 14.1**: Create resource groups with labels
 * **Requirement 14.2**: Configure allocation policies
 * **Requirement 14.5**: View group statistics
 */
const ResourceGroupPanel: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<ResourceGroup | null>(null)
  const [form] = Form.useForm()

  const { data: groups = [], isLoading, refetch } = useQuery<ResourceGroup[]>(
    'resource-groups',
    async () => {
      const response = await fetch('/api/v1/infrastructure/resource-groups')
      if (!response.ok) throw new Error('Failed to fetch resource groups')
      return response.json()
    },
    { refetchInterval: 15000 }
  )

  const createMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/resource-groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to create resource group')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('resource-groups')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  const getTypeIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      build_server: <BuildOutlined />,
      host: <DesktopOutlined />,
      board: <CloudServerOutlined />
    }
    return icons[type] || <GroupOutlined />
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { build_server: 'blue', host: 'green', board: 'orange' }
    return colors[type] || 'default'
  }

  const columns = [
    {
      title: 'Group',
      key: 'group',
      render: (_: any, record: ResourceGroup) => (
        <Space>
          {getTypeIcon(record.resource_type)}
          <a onClick={() => setSelectedGroup(record)}>{record.name}</a>
        </Space>
      )
    },
    { title: 'Type', dataIndex: 'resource_type', key: 'type', render: (t: string) => <Tag color={getTypeColor(t)}>{t.replace('_', ' ')}</Tag> },
    { title: 'Members', dataIndex: 'member_count', key: 'members' },
    {
      title: 'Utilization',
      key: 'utilization',
      render: (_: any, record: ResourceGroup) => (
        <Progress percent={Math.round((record.used_capacity / Math.max(record.total_capacity, 1)) * 100)} size="small" />
      )
    },
    {
      title: 'Labels',
      dataIndex: 'labels',
      key: 'labels',
      render: (labels: Record<string, string>) => (
        <Space wrap>
          {Object.entries(labels || {}).slice(0, 2).map(([k, v]) => <Tag key={k}>{k}: {v}</Tag>)}
          {Object.keys(labels || {}).length > 2 && <Tag>+{Object.keys(labels).length - 2}</Tag>}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ResourceGroup) => (
        <Button size="small" icon={<SettingOutlined />} onClick={() => setSelectedGroup(record)} />
      )
    }
  ]

  const buildServerGroups = groups.filter(g => g.resource_type === 'build_server')
  const hostGroups = groups.filter(g => g.resource_type === 'host')
  const boardGroups = groups.filter(g => g.resource_type === 'board')

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><GroupOutlined /> Resource Groups</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Create Group</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={8}><Card><Statistic title="Build Server Groups" value={buildServerGroups.length} prefix={<BuildOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Host Groups" value={hostGroups.length} prefix={<DesktopOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Board Groups" value={boardGroups.length} prefix={<CloudServerOutlined />} /></Card></Col>
      </Row>

      <Tabs defaultActiveKey="all" items={[
        { key: 'all', label: 'All Groups', children: <Table columns={columns} dataSource={groups} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} /> },
        { key: 'build_server', label: 'Build Servers', children: <Table columns={columns} dataSource={buildServerGroups} rowKey="id" loading={isLoading} /> },
        { key: 'host', label: 'Hosts', children: <Table columns={columns} dataSource={hostGroups} rowKey="id" loading={isLoading} /> },
        { key: 'board', label: 'Boards', children: <Table columns={columns} dataSource={boardGroups} rowKey="id" loading={isLoading} /> }
      ]} />

      {/* Create Group Modal */}
      <Modal title="Create Resource Group" open={isModalVisible} onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} confirmLoading={createMutation.isLoading} width={600}>
        <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate({
          ...values,
          labels: values.labels ? JSON.parse(values.labels) : {},
          allocation_policy: values.max_concurrent ? {
            max_concurrent: values.max_concurrent,
            allowed_teams: values.allowed_teams || [],
            priority: values.priority || 5
          } : undefined
        })}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="Group Name" rules={[{ required: true }]}>
                <Input placeholder="production-x86" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="resource_type" label="Resource Type" rules={[{ required: true }]}>
                <Select placeholder="Select type">
                  <Option value="build_server">Build Server</Option>
                  <Option value="host">QEMU Host</Option>
                  <Option value="board">Physical Board</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="labels" label="Labels (JSON)">
            <Input.TextArea placeholder='{"environment": "production", "region": "us-west"}' rows={2} />
          </Form.Item>
          <Title level={5}>Allocation Policy (Optional)</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_concurrent" label="Max Concurrent">
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="priority" label="Priority" initialValue={5}>
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="allowed_teams" label="Allowed Teams">
                <Select mode="tags" placeholder="Add teams" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Group Details Modal */}
      <Modal title={`Group: ${selectedGroup?.name}`} open={!!selectedGroup} onCancel={() => setSelectedGroup(null)} footer={null} width={700}>
        {selectedGroup && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={6}><Statistic title="Members" value={selectedGroup.member_count} /></Col>
              <Col span={6}><Statistic title="Total Capacity" value={selectedGroup.total_capacity} /></Col>
              <Col span={6}><Statistic title="Used" value={selectedGroup.used_capacity} /></Col>
              <Col span={6}><Statistic title="Utilization" value={Math.round((selectedGroup.used_capacity / Math.max(selectedGroup.total_capacity, 1)) * 100)} suffix="%" /></Col>
            </Row>
            <Card title="Labels" size="small" style={{ marginTop: 16 }}>
              <Space wrap>
                {Object.entries(selectedGroup.labels || {}).map(([k, v]) => <Tag key={k} color="blue">{k}: {v}</Tag>)}
                {Object.keys(selectedGroup.labels || {}).length === 0 && <Text type="secondary">No labels</Text>}
              </Space>
            </Card>
            {selectedGroup.allocation_policy && (
              <Card title="Allocation Policy" size="small" style={{ marginTop: 16 }}>
                <Row gutter={16}>
                  <Col span={8}><Statistic title="Max Concurrent" value={selectedGroup.allocation_policy.max_concurrent} /></Col>
                  <Col span={8}><Statistic title="Priority" value={selectedGroup.allocation_policy.priority} /></Col>
                  <Col span={8}>
                    <Text strong>Allowed Teams</Text>
                    <div>{selectedGroup.allocation_policy.allowed_teams.length > 0 
                      ? selectedGroup.allocation_policy.allowed_teams.map(t => <Tag key={t}>{t}</Tag>)
                      : <Text type="secondary">All teams</Text>}</div>
                  </Col>
                </Row>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ResourceGroupPanel
