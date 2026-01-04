import React, { useMemo, useCallback, useState } from 'react'
import { Card, Table, Tag, Progress, Button, Space, Tooltip, Input, Select } from 'antd'
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  SettingOutlined,
  SearchOutlined,
  FilterOutlined
} from '@ant-design/icons'
import { FixedSizeList as List } from 'react-window'
import { Environment, EnvironmentAction } from '../types/environment'
import { useVirtualization } from '../hooks/useVirtualization'
import { useDebounce } from '../hooks/usePerformanceOptimization'
import { useKeyboardNavigation, useAriaAttributes, useScreenReader } from '../hooks/useAccessibility'

const { Search } = Input
const { Option } = Select

interface VirtualizedEnvironmentTableProps {
  environments: Environment[]
  onEnvironmentSelect: (envId: string) => void
  onEnvironmentAction: (envId: string, action: EnvironmentAction) => void
  showResourceUsage?: boolean
  height?: number
  itemHeight?: number
  enableVirtualization?: boolean
}

interface EnvironmentRowProps {
  environment: Environment
  onSelect: (envId: string) => void
  onAction: (envId: string, action: EnvironmentAction) => void
  showResourceUsage: boolean
  style?: React.CSSProperties
  isSelected?: boolean
  index: number
}

const EnvironmentRow: React.FC<EnvironmentRowProps> = ({
  environment,
  onSelect,
  onAction,
  showResourceUsage,
  style,
  isSelected,
  index
}) => {
  const { getOptionProps } = useAriaAttributes()
  const { announce } = useScreenReader()

  const handleSelect = useCallback(() => {
    onSelect(environment.id)
    announce(`Selected environment ${environment.id}`, 'polite')
  }, [environment.id, onSelect, announce])

  const handleAction = useCallback((action: EnvironmentAction) => {
    onAction(environment.id, action)
    announce(`${action} action triggered for environment ${environment.id}`, 'assertive')
  }, [environment.id, onAction, announce])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'green'
      case 'ready': return 'blue'
      case 'allocating': return 'orange'
      case 'error': return 'red'
      case 'maintenance': return 'purple'
      default: return 'default'
    }
  }

  const getResourceColor = (usage: number) => {
    if (usage >= 90) return '#ff4d4f'
    if (usage >= 75) return '#faad14'
    return '#52c41a'
  }

  return (
    <div
      style={{
        ...style,
        display: 'flex',
        alignItems: 'center',
        padding: '8px 16px',
        borderBottom: '1px solid #f0f0f0',
        backgroundColor: isSelected ? '#e6f7ff' : 'white',
        cursor: 'pointer'
      }}
      onClick={handleSelect}
      {...getOptionProps(`env-${index}`, isSelected || false, false)}
      role="row"
      tabIndex={isSelected ? 0 : -1}
    >
      {/* Environment ID */}
      <div style={{ flex: '0 0 200px', fontFamily: 'monospace', fontSize: '12px' }}>
        <Tooltip title={environment.id}>
          {environment.id.length > 20 ? `${environment.id.slice(0, 20)}...` : environment.id}
        </Tooltip>
      </div>

      {/* Type */}
      <div style={{ flex: '0 0 120px' }}>
        <Tag color="blue">{environment.type}</Tag>
      </div>

      {/* Status */}
      <div style={{ flex: '0 0 120px' }}>
        <Tag color={getStatusColor(environment.status)}>
          {environment.status.toUpperCase()}
        </Tag>
      </div>

      {/* Architecture */}
      <div style={{ flex: '0 0 100px', fontSize: '12px' }}>
        {environment.architecture}
      </div>

      {/* Assigned Tests */}
      <div style={{ flex: '0 0 100px', textAlign: 'center' }}>
        <Tag color={environment.assignedTests.length > 0 ? 'green' : 'default'}>
          {environment.assignedTests.length}
        </Tag>
      </div>

      {/* Resource Usage */}
      {showResourceUsage && (
        <div style={{ flex: '0 0 300px' }}>
          <Space size="small">
            <Tooltip title={`CPU: ${environment.resources.cpu.toFixed(1)}%`}>
              <Progress
                type="circle"
                size={24}
                percent={Math.round(environment.resources.cpu)}
                strokeColor={getResourceColor(environment.resources.cpu)}
                format={() => 'C'}
              />
            </Tooltip>
            <Tooltip title={`Memory: ${environment.resources.memory.toFixed(1)}%`}>
              <Progress
                type="circle"
                size={24}
                percent={Math.round(environment.resources.memory)}
                strokeColor={getResourceColor(environment.resources.memory)}
                format={() => 'M'}
              />
            </Tooltip>
            <Tooltip title={`Disk: ${environment.resources.disk.toFixed(1)}%`}>
              <Progress
                type="circle"
                size={24}
                percent={Math.round(environment.resources.disk)}
                strokeColor={getResourceColor(environment.resources.disk)}
                format={() => 'D'}
              />
            </Tooltip>
          </Space>
        </div>
      )}

      {/* Actions */}
      <div style={{ flex: '1', textAlign: 'right' }}>
        <Space size="small">
          {environment.status === 'running' && (
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                handleAction('pause')
              }}
              aria-label={`Pause environment ${environment.id}`}
            />
          )}
          {environment.status === 'ready' && (
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                handleAction('start')
              }}
              aria-label={`Start environment ${environment.id}`}
            />
          )}
          <Button
            size="small"
            icon={<StopOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleAction('stop')
            }}
            aria-label={`Stop environment ${environment.id}`}
          />
          <Button
            size="small"
            icon={<SettingOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleAction('configure')
            }}
            aria-label={`Configure environment ${environment.id}`}
          />
        </Space>
      </div>
    </div>
  )
}

const VirtualizedEnvironmentTable: React.FC<VirtualizedEnvironmentTableProps> = ({
  environments,
  onEnvironmentSelect,
  onEnvironmentAction,
  showResourceUsage = true,
  height = 400,
  itemHeight = 60,
  enableVirtualization = true
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState<string>('')

  // Debounced search
  const debouncedSearch = useDebounce((query: string) => {
    setSearchQuery(query)
  }, 300)

  // Filter environments
  const filteredEnvironments = useMemo(() => {
    return environments.filter(env => {
      const matchesSearch = !searchQuery || 
        env.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        env.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        env.architecture.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesStatus = !statusFilter || env.status === statusFilter
      const matchesType = !typeFilter || env.type === typeFilter

      return matchesSearch && matchesStatus && matchesType
    })
  }, [environments, searchQuery, statusFilter, typeFilter])

  // Virtualization setup
  const virtualizationConfig = {
    itemHeight,
    containerHeight: height,
    threshold: 50 // Only virtualize if more than 50 items
  }

  const {
    virtualizedItems,
    containerProps,
    innerProps,
    shouldVirtualize
  } = useVirtualization(filteredEnvironments, virtualizationConfig)

  // Keyboard navigation
  const {
    focusedIndex,
    getItemProps,
    getContainerProps
  } = useKeyboardNavigation(
    filteredEnvironments,
    (index, environment) => {
      setSelectedEnvironmentId(environment.id)
      onEnvironmentSelect(environment.id)
    },
    { loop: true }
  )

  // Handle environment selection
  const handleEnvironmentSelect = useCallback((envId: string) => {
    setSelectedEnvironmentId(envId)
    onEnvironmentSelect(envId)
  }, [onEnvironmentSelect])

  // Get unique values for filters
  const uniqueStatuses = useMemo(() => 
    [...new Set(environments.map(env => env.status))], [environments]
  )
  const uniqueTypes = useMemo(() => 
    [...new Set(environments.map(env => env.type))], [environments]
  )

  // Render virtualized row
  const renderRow = useCallback(({ index, style }: { index: number, style: React.CSSProperties }) => {
    const environment = shouldVirtualize ? virtualizedItems[index]?.data : filteredEnvironments[index]
    if (!environment) return null

    const actualIndex = shouldVirtualize ? virtualizedItems[index]?.index : index
    const isSelected = environment.id === selectedEnvironmentId || focusedIndex === actualIndex

    return (
      <EnvironmentRow
        key={environment.id}
        environment={environment}
        onSelect={handleEnvironmentSelect}
        onAction={onEnvironmentAction}
        showResourceUsage={showResourceUsage}
        style={shouldVirtualize ? style : undefined}
        isSelected={isSelected}
        index={actualIndex}
      />
    )
  }, [
    shouldVirtualize,
    virtualizedItems,
    filteredEnvironments,
    selectedEnvironmentId,
    focusedIndex,
    handleEnvironmentSelect,
    onEnvironmentAction,
    showResourceUsage
  ])

  return (
    <Card
      title={
        <Space>
          <span>Environments</span>
          <Tag color="blue">{filteredEnvironments.length}</Tag>
          {shouldVirtualize && <Tag color="green">Virtualized</Tag>}
        </Space>
      }
      extra={
        <Space>
          <Search
            placeholder="Search environments..."
            onChange={(e) => debouncedSearch(e.target.value)}
            style={{ width: 200 }}
            allowClear
            aria-label="Search environments"
          />
          <Select
            placeholder="Status"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 120 }}
            allowClear
            aria-label="Filter by status"
          >
            {uniqueStatuses.map(status => (
              <Option key={status} value={status}>
                {status.toUpperCase()}
              </Option>
            ))}
          </Select>
          <Select
            placeholder="Type"
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 120 }}
            allowClear
            aria-label="Filter by type"
          >
            {uniqueTypes.map(type => (
              <Option key={type} value={type}>
                {type}
              </Option>
            ))}
          </Select>
        </Space>
      }
    >
      {/* Table Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 16px',
          backgroundColor: '#fafafa',
          borderBottom: '2px solid #f0f0f0',
          fontWeight: 'bold',
          fontSize: '12px'
        }}
        role="row"
      >
        <div style={{ flex: '0 0 200px' }}>Environment ID</div>
        <div style={{ flex: '0 0 120px' }}>Type</div>
        <div style={{ flex: '0 0 120px' }}>Status</div>
        <div style={{ flex: '0 0 100px' }}>Architecture</div>
        <div style={{ flex: '0 0 100px', textAlign: 'center' }}>Tests</div>
        {showResourceUsage && (
          <div style={{ flex: '0 0 300px' }}>Resource Usage</div>
        )}
        <div style={{ flex: '1', textAlign: 'right' }}>Actions</div>
      </div>

      {/* Virtualized Content */}
      {shouldVirtualize && enableVirtualization ? (
        <div {...containerProps} {...getContainerProps()} role="table" aria-label="Environment list">
          <div {...innerProps}>
            <List
              height={height}
              itemCount={virtualizedItems.length}
              itemSize={itemHeight}
              itemData={virtualizedItems}
            >
              {renderRow}
            </List>
          </div>
        </div>
      ) : (
        <div
          style={{ maxHeight: height, overflow: 'auto' }}
          {...getContainerProps()}
          role="table"
          aria-label="Environment list"
        >
          {filteredEnvironments.map((environment, index) => (
            <EnvironmentRow
              key={environment.id}
              environment={environment}
              onSelect={handleEnvironmentSelect}
              onAction={onEnvironmentAction}
              showResourceUsage={showResourceUsage}
              isSelected={environment.id === selectedEnvironmentId || focusedIndex === index}
              index={index}
            />
          ))}
        </div>
      )}

      {filteredEnvironments.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          No environments found matching the current filters.
        </div>
      )}
    </Card>
  )
}

export default VirtualizedEnvironmentTable