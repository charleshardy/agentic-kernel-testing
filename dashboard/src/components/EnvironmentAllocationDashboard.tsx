import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Typography, Space, Button, Alert, Spin } from 'antd'
import { 
  CloudServerOutlined, 
  ReloadOutlined, 
  EyeOutlined,
  SettingOutlined 
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import EnvironmentTable from './EnvironmentTable'
import apiService from '../services/api'
import { 
  EnvironmentAllocationDashboardProps, 
  EnvironmentAllocationState,
  Environment,
  AllocationRequest,
  EnvironmentAction,
  EnvironmentFilter
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
      refetchInterval: isAutoRefresh ? refreshInterval : false,
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
  }

  // Handle environment actions (reset, maintenance, etc.)
  const handleEnvironmentAction = async (envId: string, action: EnvironmentAction) => {
    try {
      await apiService.performEnvironmentAction(envId, action)
      // Refresh data after action
      refetch()
    } catch (error) {
      console.error('Failed to perform environment action:', error)
      // TODO: Show error notification
    }
  }

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
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
            {isAutoRefresh ? 'Live' : 'Paused'}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Refresh
          </Button>
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
              isAutoRefresh && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Auto-refreshing every {refreshInterval / 1000}s
                </Text>
              )
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
        {/* TODO: Add ResourceUtilizationCharts component */}
        {/* TODO: Add AllocationQueueViewer component */}
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