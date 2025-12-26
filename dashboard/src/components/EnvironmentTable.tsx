import React, { useState } from 'react'
import { 
  Table, 
  Tag, 
  Progress, 
  Space, 
  Button, 
  Dropdown, 
  Tooltip, 
  Badge,
  Typography,
  Popover,
  Descriptions,
  MenuProps
} from 'antd'
import { 
  MoreOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  ToolOutlined,
  StopOutlined,
  InfoCircleOutlined,
  CloudServerOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { 
  Environment, 
  EnvironmentTableProps, 
  EnvironmentStatus, 
  EnvironmentType, 
  EnvironmentHealth,
  EnvironmentAction
} from '../types/environment'

const { Text } = Typography

/**
 * Table component displaying real-time environment status with interactive controls
 * Shows environment information, resource usage, and provides management actions
 */
const EnvironmentTable: React.FC<EnvironmentTableProps> = ({
  environments,
  onEnvironmentSelect,
  onEnvironmentAction,
  showResourceUsage,
  filterOptions
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])

  // Get status badge configuration
  const getStatusBadge = (status: EnvironmentStatus) => {
    switch (status) {
      case EnvironmentStatus.READY:
        return { status: 'success' as const, text: 'READY' }
      case EnvironmentStatus.RUNNING:
        return { status: 'processing' as const, text: 'RUNNING' }
      case EnvironmentStatus.ALLOCATING:
        return { status: 'warning' as const, text: 'ALLOCATING' }
      case EnvironmentStatus.CLEANUP:
        return { status: 'processing' as const, text: 'CLEANUP' }
      case EnvironmentStatus.MAINTENANCE:
        return { status: 'default' as const, text: 'MAINTENANCE' }
      case EnvironmentStatus.ERROR:
        return { status: 'error' as const, text: 'ERROR' }
      case EnvironmentStatus.OFFLINE:
        return { status: 'default' as const, text: 'OFFLINE' }
      default:
        return { status: 'default' as const, text: status.toUpperCase() }
    }
  }

  // Get health indicator color
  const getHealthColor = (health: EnvironmentHealth) => {
    switch (health) {
      case EnvironmentHealth.HEALTHY:
        return 'green'
      case EnvironmentHealth.DEGRADED:
        return 'orange'
      case EnvironmentHealth.UNHEALTHY:
        return 'red'
      case EnvironmentHealth.UNKNOWN:
      default:
        return 'default'
    }
  }

  // Get environment type color
  const getTypeColor = (type: EnvironmentType) => {
    switch (type) {
      case EnvironmentType.QEMU_X86:
        return 'blue'
      case EnvironmentType.QEMU_ARM:
        return 'cyan'
      case EnvironmentType.DOCKER:
        return 'green'
      case EnvironmentType.PHYSICAL:
        return 'purple'
      case EnvironmentType.CONTAINER:
        return 'orange'
      default:
        return 'default'
    }
  }

  // Create action menu for each environment
  const getActionMenu = (environment: Environment): MenuProps => ({
    items: [
      {
        key: 'reset',
        label: 'Reset Environment',
        icon: <PlayCircleOutlined />,
        disabled: environment.status === EnvironmentStatus.RUNNING,
        onClick: () => onEnvironmentAction(environment.id, { type: 'reset' })
      },
      {
        key: 'maintenance',
        label: 'Enter Maintenance',
        icon: <ToolOutlined />,
        disabled: environment.status === EnvironmentStatus.MAINTENANCE,
        onClick: () => onEnvironmentAction(environment.id, { type: 'maintenance' })
      },
      {
        key: 'offline',
        label: 'Take Offline',
        icon: <StopOutlined />,
        disabled: environment.status === EnvironmentStatus.OFFLINE,
        onClick: () => onEnvironmentAction(environment.id, { type: 'offline' })
      },
      {
        key: 'cleanup',
        label: 'Force Cleanup',
        icon: <PauseCircleOutlined />,
        disabled: environment.status === EnvironmentStatus.CLEANUP,
        onClick: () => onEnvironmentAction(environment.id, { type: 'cleanup' })
      }
    ]
  })

  // Environment details popover content
  const getEnvironmentDetails = (environment: Environment) => (
    <Descriptions size="small" column={1} style={{ width: 300 }}>
      <Descriptions.Item label="Environment ID">
        <Text code>{environment.id}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Architecture">
        {environment.architecture}
      </Descriptions.Item>
      <Descriptions.Item label="Created">
        {new Date(environment.createdAt).toLocaleString()}
      </Descriptions.Item>
      <Descriptions.Item label="Last Updated">
        {new Date(environment.updatedAt).toLocaleString()}
      </Descriptions.Item>
      {environment.metadata.kernelVersion && (
        <Descriptions.Item label="Kernel Version">
          {environment.metadata.kernelVersion}
        </Descriptions.Item>
      )}
      {environment.metadata.ipAddress && (
        <Descriptions.Item label="IP Address">
          <Text code>{environment.metadata.ipAddress}</Text>
        </Descriptions.Item>
      )}
      {environment.metadata.lastHealthCheck && (
        <Descriptions.Item label="Last Health Check">
          {new Date(environment.metadata.lastHealthCheck).toLocaleString()}
        </Descriptions.Item>
      )}
    </Descriptions>
  )

  // Table columns configuration
  const columns: ColumnsType<Environment> = [
    {
      title: 'Environment',
      key: 'environment',
      width: 200,
      render: (_, environment) => (
        <Space direction="vertical" size="small">
          <Space>
            <CloudServerOutlined />
            <Text strong>{environment.id.slice(0, 12)}...</Text>
            <Popover 
              content={getEnvironmentDetails(environment)}
              title="Environment Details"
              trigger="hover"
            >
              <InfoCircleOutlined style={{ color: '#1890ff', cursor: 'pointer' }} />
            </Popover>
          </Space>
          <Tag color={getTypeColor(environment.type)}>
            {environment.type}
          </Tag>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: EnvironmentStatus) => {
        const badge = getStatusBadge(status)
        return <Badge status={badge.status} text={badge.text} />
      }
    },
    {
      title: 'Health',
      dataIndex: 'health',
      key: 'health',
      width: 100,
      render: (health: EnvironmentHealth) => (
        <Tag color={getHealthColor(health)}>
          {health.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Architecture',
      dataIndex: 'architecture',
      key: 'architecture',
      width: 100,
      render: (arch: string) => <Tag>{arch}</Tag>
    },
    {
      title: 'Assigned Tests',
      dataIndex: 'assignedTests',
      key: 'assignedTests',
      width: 200,
      render: (tests: string[]) => (
        <Space wrap>
          {tests.length === 0 ? (
            <Text type="secondary">None</Text>
          ) : (
            tests.slice(0, 2).map(test => (
              <Tag key={test} size="small">
                {test.slice(0, 8)}...
              </Tag>
            ))
          )}
          {tests.length > 2 && (
            <Tag size="small">+{tests.length - 2} more</Tag>
          )}
        </Space>
      )
    }
  ]

  // Add resource usage columns if enabled
  if (showResourceUsage) {
    columns.push({
      title: 'Resource Usage',
      key: 'resources',
      width: 200,
      render: (_, environment) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <div>
            <Text style={{ fontSize: '12px' }}>CPU:</Text>
            <Progress 
              percent={environment.resources.cpu} 
              size="small" 
              status={environment.resources.cpu > 80 ? 'exception' : 'normal'}
              format={(percent) => `${percent}%`}
            />
          </div>
          <div>
            <Text style={{ fontSize: '12px' }}>Memory:</Text>
            <Progress 
              percent={environment.resources.memory} 
              size="small"
              status={environment.resources.memory > 80 ? 'exception' : 'normal'}
              format={(percent) => `${percent}%`}
            />
          </div>
          <div>
            <Text style={{ fontSize: '12px' }}>Disk:</Text>
            <Progress 
              percent={environment.resources.disk} 
              size="small"
              status={environment.resources.disk > 80 ? 'exception' : 'normal'}
              format={(percent) => `${percent}%`}
            />
          </div>
        </Space>
      )
    })
  }

  // Actions column
  columns.push({
    title: 'Actions',
    key: 'actions',
    width: 80,
    render: (_, environment) => (
      <Dropdown menu={getActionMenu(environment)} trigger={['click']}>
        <Button 
          type="text" 
          icon={<MoreOutlined />} 
          size="small"
        />
      </Dropdown>
    )
  })

  // Row selection configuration
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys as string[])
    },
    onSelect: (record: Environment, selected: boolean) => {
      if (selected) {
        onEnvironmentSelect(record.id)
      }
    }
  }

  return (
    <div>
      <Table<Environment>
        columns={columns}
        dataSource={environments}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} environments`
        }}
        rowSelection={rowSelection}
        onRow={(record) => ({
          onClick: () => onEnvironmentSelect(record.id),
          style: { cursor: 'pointer' }
        })}
        scroll={{ x: 800 }}
        loading={environments.length === 0}
      />
      
      {selectedRowKeys.length > 0 && (
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          background: '#f0f2f5', 
          borderRadius: 6 
        }}>
          <Space>
            <Text strong>{selectedRowKeys.length} environment(s) selected</Text>
            <Button size="small" type="primary">
              Bulk Actions
            </Button>
            <Button 
              size="small" 
              onClick={() => setSelectedRowKeys([])}
            >
              Clear Selection
            </Button>
          </Space>
        </div>
      )}
    </div>
  )
}

export default EnvironmentTable