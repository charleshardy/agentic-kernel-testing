import React from 'react'
import {
  Table,
  Tag,
  Space,
  Button,
  Tooltip,
  Typography,
  Badge,
} from 'antd'
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  RobotOutlined,
  UserOutlined,
  CodeOutlined,
  FunctionOutlined,
} from '@ant-design/icons'
import { TestCase } from '../services/api'

const { Text } = Typography

interface TestCaseTableProps {
  tests: TestCase[]
  loading: boolean
  selectedRowKeys: string[]
  pagination?: {
    current: number
    pageSize: number
    total?: number
  }
  sortConfig?: {
    field?: string
    order?: 'ascend' | 'descend'
  }
  onRefresh: () => void
  onSelect: (selectedRowKeys: string[]) => void
  onView: (testId: string) => void
  onEdit: (testId: string) => void
  onDelete: (testId: string) => void
  onExecute: (testIds: string[]) => void
  onTableChange?: (pagination: any, filters: any, sorter: any) => void
}

const TestCaseTable: React.FC<TestCaseTableProps> = ({
  tests,
  loading,
  selectedRowKeys,
  pagination,
  sortConfig,
  onRefresh,
  onSelect,
  onView,
  onEdit,
  onDelete,
  onExecute,
  onTableChange,
}) => {
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      sorter: true,
      sortOrder: sortConfig?.field === 'name' ? sortConfig.order : null,
      render: (name: string, record: TestCase) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: '14px' }}>
            {name}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description?.substring(0, 60)}
            {record.description && record.description.length > 60 ? '...' : ''}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 120,
      sorter: true,
      sortOrder: sortConfig?.field === 'test_type' ? sortConfig.order : null,
      render: (type: string) => {
        const colors = {
          unit: 'blue',
          integration: 'green',
          performance: 'orange',
          security: 'red',
          fuzz: 'purple',
        }
        return (
          <Tag color={colors[type as keyof typeof colors] || 'default'}>
            {type?.toUpperCase() || 'UNKNOWN'}
          </Tag>
        )
      },
    },
    {
      title: 'Subsystem',
      dataIndex: 'target_subsystem',
      key: 'target_subsystem',
      width: 150,
      sorter: true,
      sortOrder: sortConfig?.field === 'target_subsystem' ? sortConfig.order : null,
      render: (subsystem: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {subsystem || 'unknown'}
        </Text>
      ),
    },
    {
      title: 'Generation',
      key: 'generation',
      width: 120,
      render: (record: TestCase) => {
        const generationMethod = record.metadata?.generation_method || 'manual'
        const icons = {
          manual: <UserOutlined />,
          ai_diff: <CodeOutlined />,
          ai_function: <FunctionOutlined />,
        }
        const colors = {
          manual: 'default',
          ai_diff: 'blue',
          ai_function: 'green',
        }
        
        return (
          <Tooltip title={`Generated via ${generationMethod.replace('_', ' ')}`}>
            <Tag 
              icon={icons[generationMethod as keyof typeof icons] || <UserOutlined />}
              color={colors[generationMethod as keyof typeof colors] || 'default'}
            >
              {generationMethod === 'manual' ? 'Manual' : 'AI'}
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (record: TestCase) => {
        const lastExecution = record.metadata?.last_execution
        const executionStatus = record.metadata?.execution_status || 'never_run'
        const isOptimistic = record.metadata?.optimistic === true
        
        const statusConfig = {
          never_run: { color: 'default', text: 'Never Run' },
          running: { color: 'processing', text: 'Running' },
          completed: { color: 'success', text: 'Passed' },
          failed: { color: 'error', text: 'Failed' },
          pending: { color: 'warning', text: isOptimistic ? 'Generating...' : 'Pending' },
        }
        
        const config = statusConfig[executionStatus as keyof typeof statusConfig] || statusConfig.never_run
        
        return (
          <Badge 
            status={config.color as any} 
            text={config.text}
          />
        )
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      sorter: true,
      sortOrder: sortConfig?.field === 'created_at' ? sortConfig.order : null,
      defaultSortOrder: 'descend',
      render: (date: string) => {
        if (!date) return 'Unknown'
        const createdDate = new Date(date)
        const now = new Date()
        const diffTime = now.getTime() - createdDate.getTime()
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
        
        if (diffDays === 0) {
          const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
          if (diffHours === 0) {
            const diffMinutes = Math.floor(diffTime / (1000 * 60))
            return `${diffMinutes}m ago`
          }
          return `${diffHours}h ago`
        } else if (diffDays < 7) {
          return `${diffDays}d ago`
        } else {
          return createdDate.toLocaleDateString()
        }
      },
    },
    {
      title: 'Est. Time',
      dataIndex: 'execution_time_estimate',
      key: 'execution_time_estimate',
      width: 100,
      sorter: true,
      sortOrder: sortConfig?.field === 'execution_time_estimate' ? sortConfig.order : null,
      render: (time: number) => {
        if (!time) return 'Unknown'
        if (time < 60) return `${time}s`
        if (time < 3600) return `${Math.floor(time / 60)}m`
        return `${Math.floor(time / 3600)}h`
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (record: TestCase) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onView(record.id)}
            />
          </Tooltip>
          <Tooltip title="Edit Test">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit(record.id)}
            />
          </Tooltip>
          <Tooltip title="Execute Test">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => onExecute([record.id])}
              style={{ color: '#52c41a' }}
            />
          </Tooltip>
          <Tooltip title="Delete Test">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => onDelete(record.id)}
              danger
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedRowKeys: React.Key[]) => {
      onSelect(selectedRowKeys as string[])
    },
    getCheckboxProps: (record: TestCase) => ({
      disabled: record.metadata?.execution_status === 'running',
      name: record.name,
    }),
  }

  return (
    <Table
      columns={columns}
      dataSource={tests}
      loading={loading}
      rowKey="id"
      rowSelection={rowSelection}
      scroll={{ x: 1200 }}
      pagination={{
        current: pagination?.current || 1,
        pageSize: pagination?.pageSize || 20,
        total: pagination?.total || tests.length,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) =>
          `${range[0]}-${range[1]} of ${total} test cases`,
        pageSizeOptions: ['10', '20', '50', '100'],
      }}
      size="middle"
      onChange={onTableChange}
      onRow={(record) => ({
        onDoubleClick: () => onView(record.id),
        style: {
          cursor: 'pointer',
          opacity: record.metadata?.optimistic ? 0.7 : 1,
          backgroundColor: record.metadata?.optimistic ? '#f6ffed' : undefined,
        },
      })}
    />
  )
}

export default TestCaseTable