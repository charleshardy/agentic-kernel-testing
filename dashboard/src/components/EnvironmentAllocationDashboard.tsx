import React, { useState, useEffect, useCallback } from 'react'
import { Card, Row, Col, Typography, Space, Button, Alert, Spin, notification } from 'antd'
import { 
  CloudServerOutlined, 
  ReloadOutlined, 
  EyeOutlined,
  SettingOutlined,
  WifiOutlined
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import EnvironmentTable from './EnvironmentTable'
import ResourceUtilizationCharts from './ResourceUtilizationCharts'
import EnvironmentManagementControls, { EnvironmentCreationConfig } from './EnvironmentManagementControls'
import AllocationQueueViewer from './AllocationQueueViewer'
import ConnectionStatus from './ConnectionStatus'
import apiService from '../services/api'
import useRealTimeUpdates from '../hooks/useRealTimeUpdates'
import { 
  EnvironmentAllocationDashboardProps, 
  EnvironmentAllocationState,
  Environment,
  AllocationRequest,
  EnvironmentAction,
  EnvironmentFilter,
  AllocationEvent
} from '../types/environment'

const { Title, Text } = Typography

/**
 * Main container component for Environment Allocation UI
 * Orchestrates all environment allocation views and provides real-time updates
 */
const EnvironmentAllocationDashboard: React.FC<EnvironmentAllocationDashboardProps> = ({
  planId,
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const [state, setState] = useState<EnvironmentAllocationState>({
    environments: [],
    allocationQueue: [],
    resourceUtilization: [],
    allocationHistory: [],
    selectedEnvironment: undefined
  })

  const [isAutoRefresh, setIsAutoRefresh] = useState(autoRefresh)
  const [environmentFilter, setEnvironmentFilter] = useState<EnvironmentFilter>({})
  const [lastStatusUpdate, setLastStatusUpdate] = useState<Date | null>(null)
  const [selectedEnvironments, setSelectedEnvironments] = useState<Environment[]>([])

  // Real-time updates hook
  const realTimeUpdates = useRealTimeUpdates({
    enableWebSocket: true,
    enableSSE: true,
    onEnvironmentUpdate: useCallback((environment: Environment) => {
      console.log('🔄 Environment update received:', environment)
      setLastStatusUpdate(new Date())
      
      // Show notification for significant status changes
      const significantStatuses = ['error', 'offline', 'ready']
      if (significantStatuses.includes(environment.status)) {
        notification.info({
          message: 'Environment Status Changed',
          description: `Environment ${environment.id.slice(0, 8)}... is now ${environment.status.toUpperCase()}`,
          duration: 3,
          placement: 'topRight'
        })
      }
    }, []),
    onAllocationUpdate: useCallback((request: AllocationRequest) => {
      console.log('🔄 Allocation update received:', request)
      setLastStatusUpdate(new Date())
    }, []),
    onAllocationEvent: useCallback((event: AllocationEvent) => {
      console.log('🔄 Allocation event received:', event)
      setLastStatusUpdate(new Date())
      
      // Show notification for allocation events
      if (event.type === 'allocated') {
        notification.success({
          message: 'Environment Allocated',
          description: `Test ${event.testId} has been allocated to environment ${event.environmentId.slice(0, 8)}...`,
          duration: 4,
          placement: 'topRight'
        })
      }
    }, []),
    onConnectionHealthChange: useCallback((health: 'healthy' | 'degraded' | 'disconnected') => {
      console.log('🔄 Connection health changed:', health)
      
      if (health === 'disconnected') {
        notification.warning({
          message: 'Real-time Connection Lost',
          description: 'Live updates are unavailable. Data will be refreshed periodically.',
          duration: 5,
          placement: 'topRight'
        })
      } else if (health === 'healthy') {
        notification.success({
          message: 'Real-time Connection Restored',
          description: 'Live updates are now available.',
          duration: 3,
          placement: 'topRight'
        })
      }
    }, [])
  })

  // Fetch environment allocation data with real-time updates
  const { 
    data: allocationData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery(
    ['environmentAllocation', planId],
    () => apiService.getEnvironmentAllocation(),
    {
      refetchInterval: isAutoRefresh && realTimeUpdates.connectionHealth !== 'healthy' ? refreshInterval : false,
      refetchOnWindowFocus: true,
      onSuccess: (data) => {
        setState(prev => ({
          ...prev,
          environments: data?.environments || [],
          allocationQueue: data?.queue || [],
          resourceUtilization: data?.resourceUtilization || [],
          allocationHistory: data?.history || []
        }))
      }
    }
  )

  // Handle environment selection
  const handleEnvironmentSelect = (envId: string) => {
    setState(prev => ({
      ...prev,
      selectedEnvironment: prev.selectedEnvironment === envId ? undefined : envId
    }))
    
    // Update selected environments for management controls
    const environment = state.environments.find(env => env.id === envId)
    if (environment) {
      setSelectedEnvironments(prev => {
        const isSelected = prev.some(env => env.id === envId)
        if (isSelected) {
          return prev.filter(env => env.id !== envId)
        } else {
          return [...prev, environment]
        }
      })
    }
  }

  // Handle environment actions (reset, maintenance, etc.)
  const handleEnvironmentAction = async (envId: string, action: EnvironmentAction) => {
    try {
      await apiService.performEnvironmentAction(envId, action)
      // Refresh data after action
      refetch()
    } catch (error) {
      console.error('Failed to perform environment action:', error)
      throw error // Re-throw to let the management controls handle the error
    }
  }

  // Handle bulk environment actions
  const handleBulkEnvironmentAction = async (envIds: string[], action: EnvironmentAction) => {
    try {
      await apiService.performBulkEnvironmentAction(envIds, action)
      // Refresh data after action
      refetch()
      // Clear selection after successful bulk action
      setSelectedEnvironments([])
    } catch (error) {
      console.error('Failed to perform bulk environment action:', error)
      throw error // Re-throw to let the management controls handle the error
    }
  }

  // Handle environment creation
  const handleCreateEnvironment = async (config: EnvironmentCreationConfig) => {
    try {
      await apiService.createEnvironment(config)
      // Refresh data after creation
      refetch()
    } catch (error) {
      console.error('Failed to create environment:', error)
      throw error // Re-throw to let the management controls handle the error
    }
  }

  // Handle allocation request priority change
  const handleAllocationPriorityChange = useCallback(async (requestId: string, priority: number) => {
    try {
      await apiService.updateAllocationRequestPriority(requestId, priority)
      // Refresh data after priority change
      refetch()
    } catch (error) {
      console.error('Failed to update allocation request priority:', error)
      throw error
    }
  }, [refetch])

  // Handle bulk allocation request cancellation
  const handleBulkAllocationCancel = useCallback(async (requestIds: string[]) => {
    try {
      await apiService.bulkCancelAllocationRequests(requestIds)
      // Refresh data after cancellation
      refetch()
    } catch (error) {
      console.error('Failed to cancel allocation requests:', error)
      throw error
    }
  }, [refetch])

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
  }

  // Manual refresh with real-time connection check
  const handleManualRefresh = useCallback(() => {
    refetch()
    
    // Also reconnect real-time connections if they're not healthy
    if (realTimeUpdates.connectionHealth !== 'healthy') {
      realTimeUpdates.reconnectAll()
    }
  }, [refetch, realTimeUpdates])

  // Get connection status for display
  const getConnectionStatusText = () => {
    if (realTimeUpdates.connectionHealth === 'healthy') {
      return 'Live'
    } else if (realTimeUpdates.connectionHealth === 'degraded') {
      return 'Degraded'
    } else {
      return isAutoRefresh ? 'Polling' : 'Paused'
    }
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Failed to Load Environment Data"
          description="Unable to fetch environment allocation information. Please check your connection and try again."
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 24 
      }}>
        <div>
          <Title level={2}>
            <CloudServerOutlined style={{ marginRight: 8 }} />
            Environment Allocation
          </Title>
          <Text type="secondary">
            Real-time monitoring and management of test execution environments
            {planId && (
              <span> for plan: <Text code>{planId}</Text></span>
            )}
          </Text>
        </div>
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={toggleAutoRefresh}
            type={isAutoRefresh ? 'primary' : 'default'}
          >
            {getConnectionStatusText()}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleManualRefresh}
            loading={isLoading}
          >
            Refresh
          </Button>
          <ConnectionStatus
            isConnected={realTimeUpdates.isConnected}
            connectionHealth={realTimeUpdates.connectionHealth}
            lastUpdate={realTimeUpdates.lastUpdate}
            updateCount={realTimeUpdates.updateCount}
            errors={realTimeUpdates.errors}
            webSocketStatus={realTimeUpdates.webSocket}
            sseStatus={realTimeUpdates.sse}
            onReconnect={realTimeUpdates.reconnectAll}
            showDetails={true}
          />
          <Button
            icon={<SettingOutlined />}
            onClick={() => {
              // TODO: Open environment settings/preferences modal
            }}
          >
            Settings
          </Button>
        </Space>
      </div>

      {/* Loading State */}
      {isLoading && state.environments.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>Loading environment allocation data...</Text>
          </div>
        </div>
      )}

      {/* Main Content */}
      <Row gutter={[24, 24]}>
        {/* Environment Management Controls */}
        <Col span={24}>
          <EnvironmentManagementControls
            selectedEnvironments={selectedEnvironments}
            onEnvironmentAction={handleEnvironmentAction}
            onCreateEnvironment={handleCreateEnvironment}
            onBulkAction={handleBulkEnvironmentAction}
            isLoading={isLoading}
          />
        </Col>

        {/* Environment Table - Main View */}
        <Col span={24}>
          <Card
            title={
              <Space>
                <CloudServerOutlined />
                Environment Status
                <Text type="secondary">
                  ({state.environments.length} environments)
                </Text>
              </Space>
            }
            extra={
              <Space>
                {realTimeUpdates.isConnected && (
                  <ConnectionStatus
                    isConnected={realTimeUpdates.isConnected}
                    connectionHealth={realTimeUpdates.connectionHealth}
                    lastUpdate={realTimeUpdates.lastUpdate}
                    updateCount={realTimeUpdates.updateCount}
                    errors={realTimeUpdates.errors}
                    webSocketStatus={realTimeUpdates.webSocket}
                    sseStatus={realTimeUpdates.sse}
                    onReconnect={realTimeUpdates.reconnectAll}
                    showDetails={false}
                  />
                )}
                {isAutoRefresh && realTimeUpdates.connectionHealth !== 'healthy' && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Polling every {refreshInterval / 1000}s
                  </Text>
                )}
                {realTimeUpdates.connectionHealth === 'healthy' && (
                  <Text type="success" style={{ fontSize: '12px' }}>
                    Live updates
                  </Text>
                )}
              </Space>
            }
          >
            <EnvironmentTable
              environments={state.environments}
              onEnvironmentSelect={handleEnvironmentSelect}
              onEnvironmentAction={handleEnvironmentAction}
              showResourceUsage={true}
              filterOptions={environmentFilter}
            />
          </Card>
        </Col>

        {/* Additional components will be added in future tasks */}
        {/* Resource Utilization Charts */}
        <Col span={24}>
          <ResourceUtilizationCharts
            environments={state.environments}
            timeRange={{
              start: new Date(Date.now() - 30 * 60 * 1000), // Last 30 minutes
              end: new Date()
            }}
            chartType="realtime"
            metrics={[
              { name: 'CPU Usage', type: 'cpu', unit: '%' },
              { name: 'Memory Usage', type: 'memory', unit: '%' },
              { name: 'Disk Usage', type: 'disk', unit: '%' },
              { name: 'Network I/O', type: 'network', unit: 'MB/s' }
            ]}
          />
        </Col>

        {/* Allocation Queue Viewer */}
        <Col span={24}>
          <AllocationQueueViewer
            queue={state.allocationQueue}
            estimatedWaitTimes={new Map(
              state.allocationQueue.map(req => [
                req.id, 
                Math.floor(Math.random() * 300) + 60 // Mock estimated wait times (60-360 seconds)
              ])
            )}
            onPriorityChange={handleAllocationPriorityChange}
          />
        </Col>
        {/* TODO: Add AllocationHistory component */}
      </Row>

      {/* Selected Environment Details */}
      {state.selectedEnvironment && (
        <Card
          title={`Environment Details: ${state.selectedEnvironment}`}
          style={{ marginTop: 24 }}
          extra={
            <Button 
              size="small" 
              onClick={() => setState(prev => ({ ...prev, selectedEnvironment: undefined }))}
            >
              Close
            </Button>
          }
        >
          {/* TODO: Add detailed environment information display */}
          <Text type="secondary">
            Detailed environment information will be displayed here.
          </Text>
        </Card>
      )}
    </div>
  )
}

export default EnvironmentAllocationDashboard