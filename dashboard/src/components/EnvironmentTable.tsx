import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { Table, Tag, Badge, Space, Progress, Tooltip, Button, Skeleton } from 'antd'
import { FixedSizeList as List } from 'react-window'
import { 
  EyeOutlined, 
  SettingOutlined, 
  ReloadOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { Environment, EnvironmentAction, EnvironmentFilter } from '../types/environment'
import StatusChangeIndicator from './StatusChangeIndicator'

interface EnvironmentTableProps {
  environments: Environment[]
  onEnvironmentSelect: (envId: string) => void
  onEnvironmentAction: (envId: string, action: EnvironmentAction) => void
  showResourceUsage: boolean
  filterOptions: EnvironmentFilter
  selectedEnvironments?: string[]
  onSelectionChange?: (selectedIds: string[]) => void
  realTimeUpdates?: boolean
  lastUpdateTime?: Date
  loading?: boolean
  enableVirtualization?: boolean
  virtualizationThreshold?: number
}

const EnvironmentTable: React.FC<EnvironmentTableProps> = ({
  environments,
  onEnvironmentSelect,
  onEnvironmentAction,
  showResourceUsage,
  filterOptions,
  selectedEnvironments = [],
  onSelectionChange,
  realTimeUpdates = true,
  lastUpdateTime,
  loading = false,
  enableVirtualization = true,
  virtualizationThreshold = 50
}) => {
  const [previousEnvironments, setPreviousEnvironments] = useState<Environment[]>([])
  const [updatingEnvironments, setUpdatingEnvironments] = useState<Set<string>>(new Set())
  const [focusedRowIndex, setFocusedRowIndex] = useState<number>(-1)
  const environmentsRef = useRef<Environment[]>([])
  const tableRef = useRef<HTMLDivElement>(null)

  // Memoize environments to prevent unnecessary re-renders
  const memoizedEnvironments = useMemo(() => environments, [environments])

  // Track environment changes for animations with debouncing
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (environmentsRef.current.length > 0) {
        setPreviousEnvironments(environmentsRef.current)
      }
      environmentsRef.current = memoizedEnvironments
    }, 100) // Debounce updates

    return () => clearTimeout(timeoutId)
  }, [memoizedEnvironments])

  // Handle environment status changes with visual feedback
  const handleStatusChange = useCallback((envId: string, newStatus: any, previousStatus?: any) => {
    console.log(`🎨 Environment ${envId} status changed: ${previousStatus} → ${newStatus}`)
    
    // Show updating state briefly
    setUpdatingEnvironments(prev => new Set(prev).add(envId))
    
    setTimeout(() => {
      setUpdatingEnvironments(prev => {
        const newSet = new Set(prev)
        newSet.delete(envId)
        return newSet
      })
    }, 1000)
  }, [])

  // Get previous status for an environment
  const getPreviousStatus = useCallback((envId: string) => {
    const prevEnv = previousEnvironments.find(env => env.id === envId)
    return prevEnv?.status
  }, [previousEnvironments])

  // Enhanced resource usage display with real-time indicators
  const renderResourceUsage = useCallback((env: Environment) => {
    const isHighUsage = (value: number) => value > 80
    const isMediumUsage = (value: number) => value > 60
    
    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '11px', width: '30px' }} aria-label="CPU Usage">CPU:</span>
          <Progress 
            percent={env.resources.cpu} 
            size="small" 
            status={isHighUsage(env.resources.cpu) ? 'exception' : isMediumUsage(env.resources.cpu) ? 'active' : 'success'}
            strokeColor={isHighUsage(env.resources.cpu) ? '#ff4d4f' : isMediumUsage(env.resources.cpu) ? '#faad14' : '#52c41a'}
            showInfo={false}
            aria-label={`CPU usage: ${env.resources.cpu.toFixed(1)}%`}
          />
          <span style={{ fontSize: '10px', color: '#666', minWidth: '35px' }}>
            {env.resources.cpu.toFixed(1)}%
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '11px', width: '30px' }} aria-label="Memory Usage">MEM:</span>
          <Progress 
            percent={env.resources.memory} 
            size="small" 
            status={isHighUsage(env.resources.memory) ? 'exception' : isMediumUsage(env.resources.memory) ? 'active' : 'success'}
            strokeColor={isHighUsage(env.resources.memory) ? '#ff4d4f' : isMediumUsage(env.resources.memory) ? '#faad14' : '#52c41a'}
            showInfo={false}
            aria-label={`Memory usage: ${env.resources.memory.toFixed(1)}%`}
          />
          <span style={{ fontSize: '10px', color: '#666', minWidth: '35px' }}>
            {env.resources.memory.toFixed(1)}%
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '11px', width: '30px' }} aria-label="Disk Usage">DSK:</span>
          <Progress 
            percent={env.resources.disk} 
            size="small" 
            status={isHighUsage(env.resources.disk) ? 'exception' : isMediumUsage(env.resources.disk) ? 'active' : 'success'}
            strokeColor={isHighUsage(env.resources.disk) ? '#ff4d4f' : isMediumUsage(env.resources.disk) ? '#faad14' : '#52c41a'}
            showInfo={false}
            aria-label={`Disk usage: ${env.resources.disk.toFixed(1)}%`}
          />
          <span style={{ fontSize: '10px', color: '#666', minWidth: '35px' }}>
            {env.resources.disk.toFixed(1)}%
          </span>
        </div>
      </Space>
    )
  }, [])

  // Enhanced assigned tests display
  const renderAssignedTests = useCallback((tests: string[]) => {
    if (!tests || tests.length === 0) {
      return <span style={{ color: '#999', fontSize: '12px' }} aria-label="No tests assigned">No tests</span>
    }
    
    return (
      <Space wrap size="small" role="list" aria-label={`${tests.length} assigned tests`}>
        {tests.slice(0, 2).map(test => (
          <Tag key={test} size="small" color="blue" role="listitem">
            {test.slice(0, 8)}...
          </Tag>
        ))}
        {tests.length > 2 && (
          <Tooltip title={`${tests.length - 2} more tests: ${tests.slice(2).join(', ')}`}>
            <Tag size="small" color="default" role="listitem">
              +{tests.length - 2}
            </Tag>
          </Tooltip>
        )}
      </Space>
    )
  }, [])

  // Enhanced environment type display
  const renderEnvironmentType = useCallback((type: string) => {
    const typeColors: Record<string, string> = {
      'qemu-x86': 'blue',
      'qemu-arm': 'cyan',
      'docker': 'green',
      'physical': 'orange',
      'container': 'purple'
    }
    
    return (
      <Tag color={typeColors[type] || 'default'} aria-label={`Environment type: ${type}`}>
        {type.toUpperCase()}
      </Tag>
    )
  }, [])

  // Keyboard navigation handler
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (!memoizedEnvironments.length) return

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setFocusedRowIndex(prev => Math.min(prev + 1, memoizedEnvironments.length - 1))
        break
      case 'ArrowUp':
        event.preventDefault()
        setFocusedRowIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
      case ' ':
        event.preventDefault()
        if (focusedRowIndex >= 0 && focusedRowIndex < memoizedEnvironments.length) {
          onEnvironmentSelect(memoizedEnvironments[focusedRowIndex].id)
        }
        break
      case 'Escape':
        setFocusedRowIndex(-1)
        break
    }
  }, [memoizedEnvironments, focusedRowIndex, onEnvironmentSelect])

  const columns = [
    {
      title: 'Environment ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      render: (id: string) => (
        <Tooltip title={id}>
          <span style={{ 
            fontFamily: 'monospace', 
            fontSize: '12px',
            color: selectedEnvironments.includes(id) ? '#1890ff' : undefined,
            fontWeight: selectedEnvironments.includes(id) ? 'bold' : 'normal'
          }}>
            {id.slice(0, 12)}...
          </span>
        </Tooltip>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: renderEnvironmentType
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: any, env: Environment) => (
        <StatusChangeIndicator
          status={status}
          previousStatus={getPreviousStatus(env.id)}
          isUpdating={updatingEnvironments.has(env.id)}
          showAnimation={realTimeUpdates}
          size="default"
          showText={true}
          lastUpdated={env.lastUpdated || lastUpdateTime}
          environmentId={env.id}
          onStatusChange={(newStatus, prevStatus) => handleStatusChange(env.id, newStatus, prevStatus)}
          enableNotifications={false} // Disable individual notifications to avoid spam
          animationDuration={1500}
        />
      )
    },
    {
      title: 'Architecture',
      dataIndex: 'architecture',
      key: 'architecture',
      width: 100,
      render: (arch: string) => (
        <Tag color="geekblue" style={{ fontSize: '11px' }}>
          {arch}
        </Tag>
      )
    },
    {
      title: 'Assigned Tests',
      dataIndex: 'assignedTests',
      key: 'assignedTests',
      width: 180,
      render: renderAssignedTests
    },
    ...(showResourceUsage ? [{
      title: 'Resource Usage',
      key: 'resources',
      width: 200,
      render: (_: any, env: Environment) => renderResourceUsage(env)
    }] : []),
    {
      title: 'Health',
      dataIndex: 'health',
      key: 'health',
      width: 100,
      render: (health: string) => {
        const healthColors: Record<string, string> = {
          'healthy': 'success',
          'degraded': 'warning',
          'unhealthy': 'error',
          'unknown': 'default'
        }
        return (
          <Badge 
            status={healthColors[health] as any || 'default'} 
            text={health.toUpperCase()} 
          />
        )
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: any, env: Environment) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button 
              size="small" 
              icon={<EyeOutlined />} 
              onClick={(e) => {
                e.stopPropagation()
                onEnvironmentSelect(env.id)
              }}
            />
          </Tooltip>
          <Tooltip title="Quick Actions">
            <Button 
              size="small" 
              icon={<SettingOutlined />} 
              onClick={(e) => {
                e.stopPropagation()
                // Show quick actions menu
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  // Row selection configuration
  const rowSelection = onSelectionChange ? {
    selectedRowKeys: selectedEnvironments,
    onChange: (selectedRowKeys: React.Key[]) => {
      onSelectionChange(selectedRowKeys as string[])
    },
    getCheckboxProps: (record: Environment) => ({
      disabled: record.status === 'error' || record.status === 'offline'
    })
  } : undefined

  return (
    <div>
      {/* Real-time update indicator */}
      {realTimeUpdates && lastUpdateTime && (
        <div style={{ 
          marginBottom: 12, 
          padding: '4px 8px', 
          backgroundColor: '#f6ffed', 
          border: '1px solid #b7eb8f',
          borderRadius: '4px',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}>
          <ThunderboltOutlined style={{ color: '#52c41a' }} />
          <span>Live updates enabled</span>
          <span style={{ color: '#666' }}>•</span>
          <ClockCircleOutlined style={{ color: '#666' }} />
          <span style={{ color: '#666' }}>
            Last update: {lastUpdateTime.toLocaleTimeString()}
          </span>
        </div>
      )}
      
      <Table
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
          style: { 
            cursor: 'pointer',
            backgroundColor: selectedEnvironments.includes(record.id) ? '#e6f7ff' : undefined
          },
          className: updatingEnvironments.has(record.id) ? 'environment-updating' : undefined
        })}
        scroll={{ x: 1200 }}
      />
      
      {/* Inject CSS for updating animation */}
      <style>{`
        .environment-updating {
          background-color: #f0f9ff !important;
          animation: environmentUpdate 2s ease-in-out;
        }
        
        @keyframes environmentUpdate {
          0% { background-color: #e6f7ff; }
          50% { background-color: #bae7ff; }
          100% { background-color: #f0f9ff; }
        }
      `}</style>
    </div>
  )
}

export default EnvironmentTable