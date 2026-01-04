import React, { useState, useEffect, useCallback } from 'react'
import { Card, Statistic, Row, Col, Progress, Alert, Button, Space, Typography, Tag } from 'antd'
import { 
  DashboardOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  BugOutlined
} from '@ant-design/icons'
import { useMemoryMonitor, usePerformanceTiming } from '../hooks/usePerformanceOptimization'
import { useReducedMotion } from '../hooks/useAccessibility'

const { Text } = Typography

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  componentCount: number
  updateFrequency: number
  errorCount: number
  warningCount: number
}

interface PerformanceMonitorProps {
  enabled?: boolean
  showDetails?: boolean
  onOptimizationSuggestion?: (suggestion: string) => void
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  enabled = process.env.NODE_ENV === 'development',
  showDetails = false,
  onOptimizationSuggestion
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    componentCount: 0,
    updateFrequency: 0,
    errorCount: 0,
    warningCount: 0
  })
  const [isVisible, setIsVisible] = useState(false)
  const [performanceScore, setPerformanceScore] = useState(100)

  const { getMemoryUsage, logMemoryUsage } = useMemoryMonitor()
  const { measureTiming } = usePerformanceTiming()
  const prefersReducedMotion = useReducedMotion()

  // Collect performance metrics
  const collectMetrics = useCallback(() => {
    const memoryInfo = getMemoryUsage()
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    
    // Simulate component counting (in real app, this would be tracked)
    const componentCount = document.querySelectorAll('[data-testid]').length || 
                          document.querySelectorAll('[class*="ant-"]').length

    // Calculate render time from performance entries
    const paintEntries = performance.getEntriesByType('paint')
    const renderTime = paintEntries.length > 0 
      ? paintEntries[paintEntries.length - 1].startTime 
      : navigation?.loadEventEnd - navigation?.navigationStart || 0

    const newMetrics: PerformanceMetrics = {
      renderTime,
      memoryUsage: memoryInfo ? memoryInfo.usagePercentage : 0,
      componentCount,
      updateFrequency: 60, // Simulated - would track actual update frequency
      errorCount: 0, // Would be tracked from error boundary
      warningCount: 0 // Would be tracked from console warnings
    }

    setMetrics(newMetrics)

    // Calculate performance score
    let score = 100
    if (renderTime > 1000) score -= 20
    if (memoryInfo && memoryInfo.usagePercentage > 80) score -= 30
    if (componentCount > 500) score -= 15
    if (newMetrics.errorCount > 0) score -= 25
    if (newMetrics.warningCount > 0) score -= 10

    setPerformanceScore(Math.max(0, score))

    // Generate optimization suggestions
    if (onOptimizationSuggestion) {
      if (renderTime > 1000) {
        onOptimizationSuggestion('Consider implementing virtualization for large lists')
      }
      if (memoryInfo && memoryInfo.usagePercentage > 80) {
        onOptimizationSuggestion('Memory usage is high - consider implementing cleanup in useEffect')
      }
      if (componentCount > 500) {
        onOptimizationSuggestion('Large number of components detected - consider code splitting')
      }
    }
  }, [getMemoryUsage, onOptimizationSuggestion])

  // Monitor performance periodically
  useEffect(() => {
    if (!enabled) return

    const interval = setInterval(collectMetrics, 5000)
    collectMetrics() // Initial collection

    return () => clearInterval(interval)
  }, [enabled, collectMetrics])

  // Performance observer for real-time metrics
  useEffect(() => {
    if (!enabled || !window.PerformanceObserver) return

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach(entry => {
        if (entry.entryType === 'measure') {
          console.log(`Performance: ${entry.name} took ${entry.duration.toFixed(2)}ms`)
        }
      })
    })

    observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] })

    return () => observer.disconnect()
  }, [enabled])

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#52c41a'
    if (score >= 70) return '#faad14'
    if (score >= 50) return '#fa8c16'
    return '#ff4d4f'
  }

  const getScoreStatus = (score: number) => {
    if (score >= 90) return 'Excellent'
    if (score >= 70) return 'Good'
    if (score >= 50) return 'Fair'
    return 'Poor'
  }

  const handleOptimize = () => {
    // Trigger garbage collection if available
    if ('gc' in window && typeof (window as any).gc === 'function') {
      (window as any).gc()
    }
    
    // Clear performance entries
    performance.clearMarks()
    performance.clearMeasures()
    
    // Log memory usage
    logMemoryUsage('After optimization')
    
    // Recollect metrics
    collectMetrics()
  }

  if (!enabled) return null

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}>
      {!isVisible ? (
        <Button
          type="primary"
          shape="circle"
          icon={<DashboardOutlined />}
          onClick={() => setIsVisible(true)}
          style={{ 
            backgroundColor: getScoreColor(performanceScore),
            borderColor: getScoreColor(performanceScore)
          }}
          title={`Performance Score: ${performanceScore}`}
        />
      ) : (
        <Card
          title={
            <Space>
              <DashboardOutlined />
              Performance Monitor
              <Tag color={getScoreColor(performanceScore)}>
                {getScoreStatus(performanceScore)}
              </Tag>
            </Space>
          }
          size="small"
          style={{ width: 400, maxHeight: 500, overflow: 'auto' }}
          extra={
            <Button
              type="text"
              size="small"
              icon={<CloseCircleOutlined />}
              onClick={() => setIsVisible(false)}
            />
          }
        >
          {/* Performance Score */}
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <Progress
              type="circle"
              percent={performanceScore}
              strokeColor={getScoreColor(performanceScore)}
              format={percent => (
                <div>
                  <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{percent}</div>
                  <div style={{ fontSize: '12px' }}>Score</div>
                </div>
              )}
            />
          </div>

          {/* Key Metrics */}
          <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Statistic
                title="Render Time"
                value={metrics.renderTime}
                suffix="ms"
                valueStyle={{ 
                  fontSize: '14px',
                  color: metrics.renderTime > 1000 ? '#ff4d4f' : '#52c41a'
                }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Memory Usage"
                value={metrics.memoryUsage.toFixed(1)}
                suffix="%"
                valueStyle={{ 
                  fontSize: '14px',
                  color: metrics.memoryUsage > 80 ? '#ff4d4f' : '#52c41a'
                }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Components"
                value={metrics.componentCount}
                valueStyle={{ 
                  fontSize: '14px',
                  color: metrics.componentCount > 500 ? '#fa8c16' : '#52c41a'
                }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Update Rate"
                value={metrics.updateFrequency}
                suffix="fps"
                valueStyle={{ 
                  fontSize: '14px',
                  color: metrics.updateFrequency < 30 ? '#ff4d4f' : '#52c41a'
                }}
              />
            </Col>
          </Row>

          {/* Warnings and Errors */}
          {(metrics.errorCount > 0 || metrics.warningCount > 0) && (
            <Alert
              message="Performance Issues Detected"
              description={
                <Space direction="vertical" size="small">
                  {metrics.errorCount > 0 && (
                    <Text type="danger">
                      {metrics.errorCount} error{metrics.errorCount > 1 ? 's' : ''} detected
                    </Text>
                  )}
                  {metrics.warningCount > 0 && (
                    <Text type="warning">
                      {metrics.warningCount} warning{metrics.warningCount > 1 ? 's' : ''} detected
                    </Text>
                  )}
                </Space>
              }
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Accessibility Notice */}
          {prefersReducedMotion && (
            <Alert
              message="Reduced Motion Detected"
              description="Animations have been disabled based on user preferences"
              type="info"
              showIcon
              icon={<CheckCircleOutlined />}
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Actions */}
          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={handleOptimize}
            >
              Optimize
            </Button>
            <Button
              size="small"
              icon={<BugOutlined />}
              onClick={() => logMemoryUsage('Manual check')}
            >
              Log Memory
            </Button>
          </Space>

          {/* Detailed Metrics */}
          {showDetails && (
            <div style={{ marginTop: 16, fontSize: '12px' }}>
              <Text type="secondary">
                Detailed metrics available in browser DevTools Performance tab
              </Text>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

export default PerformanceMonitor