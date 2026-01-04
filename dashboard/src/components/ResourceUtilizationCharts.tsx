import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { 
  Card, 
  Row, 
  Col, 
  Progress, 
  Statistic, 
  Select, 
  Button, 
  Space, 
  Alert, 
  Tooltip, 
  Badge,
  Switch,
  Slider,
  Typography,
  Divider,
  Tag,
  Spin,
  Result
} from 'antd'
import { 
  LineChartOutlined, 
  BarChartOutlined, 
  DashboardOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  FullscreenOutlined,
  ExportOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { Environment, TimeRange, ResourceMetric } from '../types/environment'
import { ErrorBoundary, ErrorAlert, ErrorRecovery } from './ErrorHandling'
import { useErrorHandler } from '../hooks/useErrorHandler'
import { useToast } from './ErrorHandling/ToastNotification'

const { Text, Title } = Typography
const { Option } = Select

interface ResourceUtilizationChartsProps {
  environments: Environment[]
  timeRange: TimeRange
  chartType: 'realtime' | 'historical'
  metrics: ResourceMetric[]
  onExportData?: () => void
  enableAlerts?: boolean
  thresholds?: ResourceThresholds
  autoRefresh?: boolean
  refreshInterval?: number
}

interface ResourceThresholds {
  cpu: { warning: number; critical: number }
  memory: { warning: number; critical: number }
  disk: { warning: number; critical: number }
  network: { warning: number; critical: number }
}

interface ResourceDataPoint {
  timestamp: string
  cpu: number
  memory: number
  disk: number
  network: number
  environmentId: string
  environmentType: string
}

interface AggregateMetrics {
  avgCpu: number
  avgMemory: number
  avgDisk: number
  avgNetwork: number
  maxCpu: number
  maxMemory: number
  maxDisk: number
  maxNetwork: number
  totalEnvironments: number
  activeEnvironments: number
  warningCount: number
  criticalCount: number
}

const DEFAULT_THRESHOLDS: ResourceThresholds = {
  cpu: { warning: 70, critical: 85 },
  memory: { warning: 75, critical: 90 },
  disk: { warning: 80, critical: 95 },
  network: { warning: 80, critical: 95 }
}

const CHART_COLORS = {
  cpu: '#1890ff',
  memory: '#52c41a',
  disk: '#faad14',
  network: '#722ed1',
  warning: '#fa8c16',
  critical: '#ff4d4f',
  healthy: '#52c41a'
}

const ResourceUtilizationCharts: React.FC<ResourceUtilizationChartsProps> = ({
  environments,
  timeRange,
  chartType,
  metrics,
  onExportData,
  enableAlerts = true,
  thresholds = DEFAULT_THRESHOLDS,
  autoRefresh = true,
  refreshInterval = 5000
}) => {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu', 'memory', 'disk'])
  const [chartView, setChartView] = useState<'line' | 'area' | 'bar'>('line')
  const [showAggregateOnly, setShowAggregateOnly] = useState(false)
  const [selectedEnvironments, setSelectedEnvironments] = useState<string[]>([])
  const [alertsEnabled, setAlertsEnabled] = useState(enableAlerts)
  const [customThresholds, setCustomThresholds] = useState(thresholds)
  const [historicalData, setHistoricalData] = useState<ResourceDataPoint[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [dataError, setDataError] = useState<Error | null>(null)

  // Error handling
  const { handleError, clearError, withErrorHandling } = useErrorHandler({
    showToast: true,
    autoRetry: true,
    logErrors: true
  })
  const toast = useToast()

  // Generate mock historical data for demonstration with error handling
  useEffect(() => {
    const generateHistoricalData = withErrorHandling(async () => {
      setIsLoading(true)
      setDataError(null)
      
      try {
        // Simulate potential network delay and errors
        if (Math.random() < 0.1) { // 10% chance of simulated error
          throw new Error('Failed to fetch resource utilization data')
        }
        
        await new Promise(resolve => setTimeout(resolve, 500)) // Simulate network delay
        
        const data: ResourceDataPoint[] = []
        const now = new Date()
        const points = chartType === 'realtime' ? 30 : 100
        
        for (let i = points; i >= 0; i--) {
          const timestamp = new Date(now.getTime() - i * (chartType === 'realtime' ? 10000 : 60000))
          
          environments.forEach(env => {
            // Generate realistic fluctuating data based on current values
            const baseVariation = 0.1 // 10% variation
            const timeVariation = Math.sin(i * 0.1) * 0.05 // 5% time-based variation
            
            data.push({
              timestamp: timestamp.toISOString(),
              cpu: Math.max(0, Math.min(100, env.resources.cpu + (Math.random() - 0.5) * baseVariation * 100 + timeVariation * 100)),
              memory: Math.max(0, Math.min(100, env.resources.memory + (Math.random() - 0.5) * baseVariation * 100 + timeVariation * 100)),
              disk: Math.max(0, Math.min(100, env.resources.disk + (Math.random() - 0.5) * baseVariation * 100 + timeVariation * 100)),
              network: Math.max(0, Math.min(100, Math.random() * 100)), // Network is more variable
              environmentId: env.id,
              environmentType: env.type
            })
          })
        }
        
        setHistoricalData(data)
        toast.success('Resource data updated', 'Successfully loaded latest resource utilization data')
      } catch (error) {
        setDataError(error as Error)
        handleError(error, {
          component: 'ResourceUtilizationCharts',
          action: 'generateHistoricalData',
          chartType,
          environmentCount: environments.length
        })
      } finally {
        setIsLoading(false)
      }
    }, {
      component: 'ResourceUtilizationCharts',
      action: 'generateHistoricalData'
    })

    generateHistoricalData()
    
    if (autoRefresh && chartType === 'realtime') {
      const interval = setInterval(generateHistoricalData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [environments, chartType, autoRefresh, refreshInterval, withErrorHandling, handleError, toast])

  // Calculate aggregate metrics
  const aggregateMetrics = useMemo((): AggregateMetrics => {
    if (environments.length === 0) {
      return {
        avgCpu: 0, avgMemory: 0, avgDisk: 0, avgNetwork: 0,
        maxCpu: 0, maxMemory: 0, maxDisk: 0, maxNetwork: 0,
        totalEnvironments: 0, activeEnvironments: 0,
        warningCount: 0, criticalCount: 0
      }
    }

    const activeEnvs = environments.filter(env => env.status === 'running' || env.status === 'ready')
    const totalEnvs = environments.length
    
    const cpuValues = activeEnvs.map(env => env.resources.cpu)
    const memoryValues = activeEnvs.map(env => env.resources.memory)
    const diskValues = activeEnvs.map(env => env.resources.disk)
    const networkValues = activeEnvs.map(env => env.resources.network?.bytesIn || 0)

    const avgCpu = cpuValues.reduce((sum, val) => sum + val, 0) / Math.max(1, cpuValues.length)
    const avgMemory = memoryValues.reduce((sum, val) => sum + val, 0) / Math.max(1, memoryValues.length)
    const avgDisk = diskValues.reduce((sum, val) => sum + val, 0) / Math.max(1, diskValues.length)
    const avgNetwork = networkValues.reduce((sum, val) => sum + val, 0) / Math.max(1, networkValues.length)

    // Count environments exceeding thresholds
    let warningCount = 0
    let criticalCount = 0
    
    activeEnvs.forEach(env => {
      const isCpuWarning = env.resources.cpu >= customThresholds.cpu.warning
      const isCpuCritical = env.resources.cpu >= customThresholds.cpu.critical
      const isMemoryWarning = env.resources.memory >= customThresholds.memory.warning
      const isMemoryCritical = env.resources.memory >= customThresholds.memory.critical
      const isDiskWarning = env.resources.disk >= customThresholds.disk.warning
      const isDiskCritical = env.resources.disk >= customThresholds.disk.critical
      
      if (isCpuCritical || isMemoryCritical || isDiskCritical) {
        criticalCount++
      } else if (isCpuWarning || isMemoryWarning || isDiskWarning) {
        warningCount++
      }
    })

    return {
      avgCpu,
      avgMemory,
      avgDisk,
      avgNetwork,
      maxCpu: Math.max(...cpuValues, 0),
      maxMemory: Math.max(...memoryValues, 0),
      maxDisk: Math.max(...diskValues, 0),
      maxNetwork: Math.max(...networkValues, 0),
      totalEnvironments: totalEnvs,
      activeEnvironments: activeEnvs.length,
      warningCount,
      criticalCount
    }
  }, [environments, customThresholds])

  // Prepare chart data
  const chartData = useMemo(() => {
    if (showAggregateOnly) {
      // Group by timestamp and calculate averages
      const groupedData = historicalData.reduce((acc, point) => {
        const timestamp = point.timestamp
        if (!acc[timestamp]) {
          acc[timestamp] = { timestamp, cpu: [], memory: [], disk: [], network: [] }
        }
        acc[timestamp].cpu.push(point.cpu)
        acc[timestamp].memory.push(point.memory)
        acc[timestamp].disk.push(point.disk)
        acc[timestamp].network.push(point.network)
        return acc
      }, {} as Record<string, any>)

      return Object.values(groupedData).map((group: any) => ({
        timestamp: new Date(group.timestamp).toLocaleTimeString(),
        cpu: group.cpu.reduce((sum: number, val: number) => sum + val, 0) / group.cpu.length,
        memory: group.memory.reduce((sum: number, val: number) => sum + val, 0) / group.memory.length,
        disk: group.disk.reduce((sum: number, val: number) => sum + val, 0) / group.disk.length,
        network: group.network.reduce((sum: number, val: number) => sum + val, 0) / group.network.length
      }))
    } else {
      // Filter by selected environments if any
      const filteredData = selectedEnvironments.length > 0 
        ? historicalData.filter(point => selectedEnvironments.includes(point.environmentId))
        : historicalData

      return filteredData.map(point => ({
        ...point,
        timestamp: new Date(point.timestamp).toLocaleTimeString()
      }))
    }
  }, [historicalData, showAggregateOnly, selectedEnvironments])

  // Get resource status color
  const getResourceStatusColor = useCallback((value: number, resourceType: keyof ResourceThresholds) => {
    const threshold = customThresholds[resourceType]
    if (value >= threshold.critical) return CHART_COLORS.critical
    if (value >= threshold.warning) return CHART_COLORS.warning
    return CHART_COLORS.healthy
  }, [customThresholds])

  // Render chart based on selected view
  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    }

    const renderLines = () => selectedMetrics.map(metric => (
      <Line
        key={metric}
        type="monotone"
        dataKey={metric}
        stroke={CHART_COLORS[metric as keyof typeof CHART_COLORS]}
        strokeWidth={2}
        dot={false}
        connectNulls
      />
    ))

    const renderAreas = () => selectedMetrics.map(metric => (
      <Area
        key={metric}
        type="monotone"
        dataKey={metric}
        stackId="1"
        stroke={CHART_COLORS[metric as keyof typeof CHART_COLORS]}
        fill={CHART_COLORS[metric as keyof typeof CHART_COLORS]}
        fillOpacity={0.6}
      />
    ))

    const renderBars = () => selectedMetrics.map(metric => (
      <Bar
        key={metric}
        dataKey={metric}
        fill={CHART_COLORS[metric as keyof typeof CHART_COLORS]}
      />
    ))

    switch (chartView) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[0, 100]} />
            <RechartsTooltip />
            <Legend />
            {renderAreas()}
          </AreaChart>
        )
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[0, 100]} />
            <RechartsTooltip />
            <Legend />
            {renderBars()}
          </BarChart>
        )
      default:
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[0, 100]} />
            <RechartsTooltip />
            <Legend />
            {renderLines()}
          </LineChart>
        )
    }
  }

  // Render environment resource cards with threshold indicators
  const renderEnvironmentCards = () => (
    <Row gutter={[12, 12]}>
      {environments.map(env => {
        const cpuColor = getResourceStatusColor(env.resources.cpu, 'cpu')
        const memoryColor = getResourceStatusColor(env.resources.memory, 'memory')
        const diskColor = getResourceStatusColor(env.resources.disk, 'disk')
        
        const hasWarning = env.resources.cpu >= customThresholds.cpu.warning ||
                          env.resources.memory >= customThresholds.memory.warning ||
                          env.resources.disk >= customThresholds.disk.warning
        
        const hasCritical = env.resources.cpu >= customThresholds.cpu.critical ||
                           env.resources.memory >= customThresholds.memory.critical ||
                           env.resources.disk >= customThresholds.disk.critical

        return (
          <Col key={env.id} xs={24} sm={12} md={8} lg={6}>
            <Card 
              size="small" 
              style={{ 
                border: hasCritical ? `2px solid ${CHART_COLORS.critical}` : 
                        hasWarning ? `2px solid ${CHART_COLORS.warning}` : undefined
              }}
              title={
                <Space>
                  <Text strong style={{ fontSize: '12px' }}>
                    {env.id.slice(0, 8)}...
                  </Text>
                  <Tag color={env.status === 'running' ? 'green' : 'orange'}>
                    {env.status}
                  </Tag>
                  {hasCritical && <Badge status="error" />}
                  {hasWarning && !hasCritical && <Badge status="warning" />}
                </Space>
              }
              extra={
                <Tooltip title={`${env.type} - ${env.architecture}`}>
                  <InfoCircleOutlined style={{ fontSize: '12px' }} />
                </Tooltip>
              }
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <Text style={{ fontSize: '11px' }}>CPU:</Text>
                  <Progress 
                    percent={Math.round(env.resources.cpu)} 
                    size="small"
                    strokeColor={cpuColor}
                    format={percent => `${percent}%`}
                  />
                </div>
                <div>
                  <Text style={{ fontSize: '11px' }}>Memory:</Text>
                  <Progress 
                    percent={Math.round(env.resources.memory)} 
                    size="small"
                    strokeColor={memoryColor}
                    format={percent => `${percent}%`}
                  />
                </div>
                <div>
                  <Text style={{ fontSize: '11px' }}>Disk:</Text>
                  <Progress 
                    percent={Math.round(env.resources.disk)} 
                    size="small"
                    strokeColor={diskColor}
                    format={percent => `${percent}%`}
                  />
                </div>
                {env.assignedTests && env.assignedTests.length > 0 && (
                  <Text style={{ fontSize: '10px', color: '#666' }}>
                    Tests: {env.assignedTests.length}
                  </Text>
                )}
              </Space>
            </Card>
          </Col>
        )
      })}
    </Row>
  )

  // Enhanced export function with error handling
  const handleExportData = useCallback(async () => {
    try {
      setIsLoading(true)
      
      if (onExportData) {
        await onExportData()
      } else {
        // Default export functionality
        const exportData = {
          timestamp: new Date().toISOString(),
          environments: environments.map(env => ({
            id: env.id,
            type: env.type,
            status: env.status,
            resources: env.resources
          })),
          aggregateMetrics,
          historicalData: historicalData.slice(-100), // Last 100 data points
          thresholds: customThresholds
        }
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
          type: 'application/json' 
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `resource-utilization-${Date.now()}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
      
      toast.success('Export completed', 'Resource utilization data has been exported successfully')
    } catch (error) {
      handleError(error, {
        component: 'ResourceUtilizationCharts',
        action: 'exportData'
      })
    } finally {
      setIsLoading(false)
    }
  }, [onExportData, environments, aggregateMetrics, historicalData, customThresholds, toast, handleError])

  // Error recovery actions
  const recoveryActions = useMemo(() => [
    {
      id: 'refresh-data',
      label: 'Refresh Data',
      description: 'Reload resource utilization data',
      action: async () => {
        setDataError(null)
        window.location.reload()
      },
      icon: <ReloadOutlined />,
      type: 'primary' as const
    },
    {
      id: 'reset-thresholds',
      label: 'Reset Thresholds',
      description: 'Reset alert thresholds to default values',
      action: async () => {
        setCustomThresholds(DEFAULT_THRESHOLDS)
        toast.info('Thresholds reset', 'Alert thresholds have been reset to default values')
      },
      icon: <SettingOutlined />
    }
  ], [toast])

  // Handle threshold changes with validation
  const handleThresholdChange = useCallback((
    resourceType: keyof ResourceThresholds,
    values: [number, number]
  ) => {
    try {
      const [warning, critical] = values
      
      if (warning >= critical) {
        throw new Error('Warning threshold must be less than critical threshold')
      }
      
      if (warning < 0 || critical > 100) {
        throw new Error('Thresholds must be between 0 and 100')
      }
      
      setCustomThresholds(prev => ({
        ...prev,
        [resourceType]: { warning, critical }
      }))
    } catch (error) {
      handleError(error, {
        component: 'ResourceUtilizationCharts',
        action: 'handleThresholdChange',
        resourceType,
        values
      })
    }
  }, [handleError])

  // If there's a critical data error, show error recovery
  if (dataError) {
    return (
      <ErrorBoundary>
        <ErrorRecovery
          error={dataError}
          recoveryActions={recoveryActions}
          onRetry={async () => {
            setDataError(null)
            window.location.reload()
          }}
          onRecovered={() => {
            setDataError(null)
            toast.success('Recovery successful', 'Resource utilization monitoring has been restored')
          }}
        />
      </ErrorBoundary>
    )
  }

  // Loading state
  if (isLoading && historicalData.length === 0) {
    return (
      <Card style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>
          <Typography.Text>Loading resource utilization data...</Typography.Text>
        </div>
      </Card>
    )
  }

  // Empty state
  if (environments.length === 0) {
    return (
      <Result
        icon={<DashboardOutlined />}
        title="No Environments Available"
        subTitle="There are no environments to monitor. Please ensure environments are properly configured and running."
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
            Refresh
          </Button>
        }
      />
    )
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        handleError(error, {
          component: 'ResourceUtilizationCharts',
          action: 'render',
          errorInfo: errorInfo.componentStack
        })
      }}
    >
    <div style={{ position: isFullscreen ? 'fixed' : 'relative', 
                  top: isFullscreen ? 0 : 'auto',
                  left: isFullscreen ? 0 : 'auto',
                  right: isFullscreen ? 0 : 'auto',
                  bottom: isFullscreen ? 0 : 'auto',
                  zIndex: isFullscreen ? 1000 : 'auto',
                  backgroundColor: isFullscreen ? 'white' : 'transparent',
                  padding: isFullscreen ? '24px' : '0' }}>
      
      {/* Alert Summary */}
      {alertsEnabled && (aggregateMetrics.criticalCount > 0 || aggregateMetrics.warningCount > 0) && (
        <Alert
          message={
            <Space>
              <WarningOutlined />
              Resource Threshold Alerts
            </Space>
          }
          description={
            <Space>
              {aggregateMetrics.criticalCount > 0 && (
                <Tag color="red">{aggregateMetrics.criticalCount} Critical</Tag>
              )}
              {aggregateMetrics.warningCount > 0 && (
                <Tag color="orange">{aggregateMetrics.warningCount} Warning</Tag>
              )}
            </Space>
          }
          type={aggregateMetrics.criticalCount > 0 ? "error" : "warning"}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card 
        title={
          <Space>
            <DashboardOutlined />
            Resource Utilization Monitoring
            <Badge count={aggregateMetrics.activeEnvironments} showZero color="blue" />
            {chartType === 'realtime' && autoRefresh && (
              <Tag color="green" icon={<ReloadOutlined spin />}>Live</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Select
              mode="multiple"
              placeholder="Select metrics"
              value={selectedMetrics}
              onChange={setSelectedMetrics}
              style={{ minWidth: 200 }}
            >
              <Option value="cpu">CPU</Option>
              <Option value="memory">Memory</Option>
              <Option value="disk">Disk</Option>
              <Option value="network">Network</Option>
            </Select>
            
            <Select value={chartView} onChange={setChartView} style={{ width: 100 }}>
              <Option value="line"><LineChartOutlined /> Line</Option>
              <Option value="area"><BarChartOutlined /> Area</Option>
              <Option value="bar"><BarChartOutlined /> Bar</Option>
            </Select>

            <Tooltip title="Show aggregate data only">
              <Switch
                checkedChildren="Aggregate"
                unCheckedChildren="Individual"
                checked={showAggregateOnly}
                onChange={setShowAggregateOnly}
              />
            </Tooltip>

            {onExportData && (
              <Button 
                icon={<ExportOutlined />} 
                onClick={handleExportData}
                loading={isLoading}
                size="small"
              >
                Export
              </Button>
            )}

            <Button 
              icon={<FullscreenOutlined />} 
              onClick={() => setIsFullscreen(!isFullscreen)}
              size="small"
            >
              {isFullscreen ? 'Exit' : 'Fullscreen'}
            </Button>
          </Space>
        }
      >
        {/* Aggregate Statistics */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic
              title="Average CPU Usage"
              value={Math.round(aggregateMetrics.avgCpu)}
              suffix="%"
              valueStyle={{ 
                color: getResourceStatusColor(aggregateMetrics.avgCpu, 'cpu'),
                fontSize: '20px'
              }}
              prefix={<DashboardOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Average Memory Usage"
              value={Math.round(aggregateMetrics.avgMemory)}
              suffix="%"
              valueStyle={{ 
                color: getResourceStatusColor(aggregateMetrics.avgMemory, 'memory'),
                fontSize: '20px'
              }}
              prefix={<DashboardOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Average Disk Usage"
              value={Math.round(aggregateMetrics.avgDisk)}
              suffix="%"
              valueStyle={{ 
                color: getResourceStatusColor(aggregateMetrics.avgDisk, 'disk'),
                fontSize: '20px'
              }}
              prefix={<DashboardOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Active Environments"
              value={aggregateMetrics.activeEnvironments}
              suffix={`/ ${aggregateMetrics.totalEnvironments}`}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
              prefix={<DashboardOutlined />}
            />
          </Col>
        </Row>

        {/* Real-time Charts */}
        <Card size="small" title="Resource Trends" style={{ marginBottom: 16 }}>
          <ResponsiveContainer width="100%" height={300}>
            {renderChart()}
          </ResponsiveContainer>
        </Card>

        {/* Environment Filter */}
        {!showAggregateOnly && environments.length > 5 && (
          <Card size="small" title="Environment Filter" style={{ marginBottom: 16 }}>
            <Select
              mode="multiple"
              placeholder="Select environments to display in chart"
              value={selectedEnvironments}
              onChange={setSelectedEnvironments}
              style={{ width: '100%' }}
              maxTagCount="responsive"
            >
              {environments.map(env => (
                <Option key={env.id} value={env.id}>
                  {env.id.slice(0, 12)}... ({env.type})
                </Option>
              ))}
            </Select>
          </Card>
        )}

        {/* Threshold Configuration */}
        <Card size="small" title="Alert Thresholds" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Text strong>CPU Thresholds</Text>
              <div>
                <Text>Warning: {customThresholds.cpu.warning}%</Text>
                <Slider
                  range
                  min={0}
                  max={100}
                  value={[customThresholds.cpu.warning, customThresholds.cpu.critical]}
                  onChange={(values) => handleThresholdChange('cpu', values as [number, number])}
                />
                <Text>Critical: {customThresholds.cpu.critical}%</Text>
              </div>
            </Col>
            <Col span={6}>
              <Text strong>Memory Thresholds</Text>
              <div>
                <Text>Warning: {customThresholds.memory.warning}%</Text>
                <Slider
                  range
                  min={0}
                  max={100}
                  value={[customThresholds.memory.warning, customThresholds.memory.critical]}
                  onChange={(values) => handleThresholdChange('memory', values as [number, number])}
                />
                <Text>Critical: {customThresholds.memory.critical}%</Text>
              </div>
            </Col>
            <Col span={6}>
              <Text strong>Disk Thresholds</Text>
              <div>
                <Text>Warning: {customThresholds.disk.warning}%</Text>
                <Slider
                  range
                  min={0}
                  max={100}
                  value={[customThresholds.disk.warning, customThresholds.disk.critical]}
                  onChange={(values) => handleThresholdChange('disk', values as [number, number])}
                />
                <Text>Critical: {customThresholds.disk.critical}%</Text>
              </div>
            </Col>
            <Col span={6}>
              <Space direction="vertical">
                <Switch
                  checkedChildren="Alerts On"
                  unCheckedChildren="Alerts Off"
                  checked={alertsEnabled}
                  onChange={setAlertsEnabled}
                />
                <Button 
                  icon={<SettingOutlined />} 
                  size="small"
                  onClick={() => setCustomThresholds(DEFAULT_THRESHOLDS)}
                >
                  Reset Defaults
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Individual Environment Resource Cards */}
        <Card size="small" title="Environment Resource Details">
          {renderEnvironmentCards()}
        </Card>
      </Card>
    </div>
    </ErrorBoundary>
  )
}

export default ResourceUtilizationCharts