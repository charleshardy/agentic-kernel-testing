import React, { useState, useEffect, useCallback } from 'react'
import { Card, Row, Col, Typography, Space, Button, Alert, Spin, notification } from 'antd'
import { 
  CloudServerOutlined, 
  ReloadOutlined, 
  EyeOutlined,
  SettingOutlined,
  WifiOutlined,
  BugOutlined
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import EnvironmentTable from './EnvironmentTable'
import ResourceUtilizationCharts from './ResourceUtilizationCharts'
import EnvironmentManagementControls, { EnvironmentCreationConfig } from './EnvironmentManagementControls'
import AllocationQueueViewer from './AllocationQueueViewer'
import AllocationHistoryViewer from './AllocationHistoryViewer'
import EnvironmentPreferenceModal from './EnvironmentPreferenceModal'
import ConnectionStatus from './ConnectionStatus'
import DiagnosticPanel from './DiagnosticPanel'
import CapacityIndicator from './CapacityIndicator'
import apiService from '../services/api'
import useRealTimeUpdates from '../hooks/useRealTimeUpdates'
import useErrorHandling from '../hooks/useErrorHandling'
import { 
  EnvironmentAllocationDashboardProps, 
  EnvironmentAllocationState,
  Environment,
  AllocationRequest,
  EnvironmentAction,
  EnvironmentFilter,
  AllocationEvent,
  HardwareRequirements,
  AllocationPreferences
} from '../types/environment'
import { ErrorCategory } from '../types/errors'

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
  const [preferenceModalVisible, setPreferenceModalVisible] = useState(false)
  const [diagnosticPanelVisible, setDiagnosticPanelVisible] = useState(false)

  // Error handling hook
  const {
    handleApiError,
    handleWebSocketError,
    withErrorHandling,
    createAllocationError,
    createEnvironmentError,
    createNetworkError,
    hasErrors,
    lastError
  } = useErrorHandling({
    onError: (error) => {
      console.error('Environment Allocation Dashboard Error:', error)
    },
    autoRetry: true,
    fallbackData: {
      environments: [],
      queue: [],
      resourceUtilization: [],
      history: []
    }
  })

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
        const error = createNetworkError(
          'WEBSOCKET_DISCONNECTED',
          'Real-time connection lost',
          undefined,
          undefined,
          { connectionType: 'websocket', health }
        )
        // Error will be handled by the notification system
        
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
    }, [createNetworkError])
  })

  // Fetch environment allocation data with real-time updates and error handling
  const { 
    data: allocationData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery(
    ['environmentAllocation', planId],
    () => withErrorHandling(
      () => apiService.getEnvironmentAllocation(),
      { 
        operation: 'fetch_environment_allocation',
        planId,
        endpoint: '/api/environments/allocation'
      }
    ),
    {
      refetchInterval: isAutoRefresh && realTimeUpdates.connectionHealth !== 'healthy' ? refreshInterval : false,
      refetchOnWindowFocus: true,
      onSuccess: (data) => {
        if (data) {
          setState(prev => ({
            ...prev,
            environments: data.environments || [],
            allocationQueue: data.queue || [],
            resourceUtilization: data.resourceUtilization || [],
            allocationHistory: data.history || [],
            capacityMetrics: data.capacityMetrics
          }))
        }
      },
      onError: (error: any) => {
        handleApiError(error, '/api/environments/allocation')
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

  // Handle environment actions (reset, maintenance, etc.) with error handling
  const handleEnvironmentAction = async (envId: string, action: EnvironmentAction) => {
    return withErrorHandling(
      async () => {
        await apiService.performEnvironmentAction(envId, action)
        // Refresh data after action
        refetch()
        
        notification.success({
          message: 'Environment Action Completed',
          description: `Successfully performed ${action.type} on environment ${envId.slice(0, 8)}...`,
          duration: 3
        })
      },
      {
        operation: 'environment_action',
        environmentId: envId,
        actionType: action.type,
        endpoint: `/api/environments/${envId}/actions/${action.type}`
      }
    )
  }

  // Handle bulk environment actions with error handling
  const handleBulkEnvironmentAction = async (envIds: string[], action: EnvironmentAction) => {
    return withErrorHandling(
      async () => {
        await apiService.performBulkEnvironmentAction(envIds, action)
        // Refresh data after action
        refetch()
        // Clear selection after successful bulk action
        setSelectedEnvironments([])
        
        notification.success({
          message: 'Bulk Environment Action Completed',
          description: `Successfully performed ${action.type} on ${envIds.length} environments`,
          duration: 3
        })
      },
      {
        operation: 'bulk_environment_action',
        environmentIds: envIds,
        actionType: action.type,
        endpoint: `/api/environments/bulk-actions/${action.type}`
      }
    )
  }

  // Handle environment creation with error handling
  const handleCreateEnvironment = async (config: EnvironmentCreationConfig) => {
    return withErrorHandling(
      async () => {
        const result = await apiService.createEnvironment(config)
        // Refresh data after creation
        refetch()
        
        notification.success({
          message: 'Environment Created',
          description: `Successfully created ${config.type} environment with ${config.cpuCores} cores and ${config.memoryMB}MB memory`,
          duration: 4
        })
        
        return result
      },
      {
        operation: 'create_environment',
        environmentConfig: config,
        endpoint: '/api/environments'
      }
    )
  }

  // Handle allocation request priority change with error handling
  const handleAllocationPriorityChange = useCallback(async (requestId: string, priority: number) => {
    return withErrorHandling(
      async () => {
        await apiService.updateAllocationRequestPriority(requestId, priority)
        // Refresh data after priority change
        refetch()
        
        notification.success({
          message: 'Priority Updated',
          description: `Allocation request priority updated to ${priority}`,
          duration: 3
        })
      },
      {
        operation: 'update_allocation_priority',
        requestId,
        priority,
        endpoint: `/api/environments/allocation/request/${requestId}`
      }
    )
  }, [refetch, withErrorHandling])

  // Handle bulk allocation request cancellation with error handling
  const handleBulkAllocationCancel = useCallback(async (requestIds: string[]) => {
    return withErrorHandling(
      async () => {
        await apiService.bulkCancelAllocationRequests(requestIds)
        // Refresh data after cancellation
        refetch()
        
        notification.success({
          message: 'Allocation Requests Cancelled',
          description: `Successfully cancelled ${requestIds.length} allocation requests`,
          duration: 3
        })
      },
      {
        operation: 'bulk_cancel_allocation',
        requestIds,
        endpoint: '/api/environments/allocation/bulk-cancel'
      }
    )
  }, [refetch, withErrorHandling])

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
  }

  // Manual refresh with real-time connection check and error handling
  const handleManualRefresh = useCallback(() => {
    withErrorHandling(
      async () => {
        await refetch()
        
        // Also reconnect real-time connections if they're not healthy
        if (realTimeUpdates.connectionHealth !== 'healthy') {
          realTimeUpdates.reconnectAll()
        }
        
        notification.success({
          message: 'Data Refreshed',
          description: 'Environment allocation data has been updated',
          duration: 2
        })
      },
      {
        operation: 'manual_refresh',
        endpoint: '/api/environments/allocation'
      }
    )
  }, [refetch, realTimeUpdates, withErrorHandling])

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

  if (error && !hasErrors) {
    // Handle query errors that weren't caught by our error handling
    const errorDetails = handleApiError(error, '/api/environments/allocation')
    
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Failed to Load Environment Data"
          description={
            <div>
              <p>Unable to fetch environment allocation information.</p>
              {errorDetails.suggestedActions && errorDetails.suggestedActions.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <strong>Suggested actions:</strong>
                  <ul style={{ marginTop: 4, marginBottom: 0 }}>
                    {errorDetails.suggestedActions.map(action => (
                      <li key={action.id}>{action.description}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          }
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={() => refetch()}>
                Retry
              </Button>
              <Button 
                size="small" 
                icon={<BugOutlined />}
                onClick={() => setDiagnosticPanelVisible(true)}
              >
                Diagnostics
              </Button>
            </Space>
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
              setPreferenceModalVisible(true)
            }}
          >
            Environment Preferences
          </Button>
          <Button
            icon={<BugOutlined />}
            onClick={() => setDiagnosticPanelVisible(true)}
            type={hasErrors ? 'primary' : 'default'}
            danger={hasErrors}
          >
            Diagnostics {hasErrors && `(${lastError?.severity})`}
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
        {/* System Capacity Overview */}
        {state.capacityMetrics && (
          <Col span={24}>
            <CapacityIndicator
              capacityMetrics={state.capacityMetrics}
              showDetails={true}
              size="default"
            />
          </Col>
        )}

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
      </Row>

      {/* Allocation History */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <AllocationHistoryViewer
            autoRefresh={autoRefresh}
            refreshInterval={refreshInterval}
          />
        </Col>
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

      {/* Environment Preference Modal */}
      <EnvironmentPreferenceModal
        visible={preferenceModalVisible}
        onClose={() => setPreferenceModalVisible(false)}
        testId={planId}
        availableEnvironments={state.environments}
        onApplyPreferences={(requirements, preferences) => {
          // Handle preference application with error handling
          withErrorHandling(
            async () => {
              // This would typically save preferences via API
              console.log('Applied preferences:', { requirements, preferences })
              
              notification.success({
                message: 'Preferences Applied',
                description: 'Environment preferences have been saved and will be used for future allocations.'
              })
            },
            {
              operation: 'apply_preferences',
              requirements,
              preferences
            }
          )
        }}
      />

      {/* Diagnostic Panel */}
      {diagnosticPanelVisible && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)', 
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            width: '90%', 
            height: '90%', 
            overflow: 'auto' 
          }}>
            <DiagnosticPanel
              visible={diagnosticPanelVisible}
              onClose={() => setDiagnosticPanelVisible(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default EnvironmentAllocationDashboard