import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, Statistic, Progress, Timeline, Tag, Divider, Row, Col } from 'antd'
import { 
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  TrophyOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  RocketOutlined,
  ToolOutlined,
  DatabaseOutlined,
  NetworkOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

export interface DeploymentSummary {
  deployment_id: string
  plan_id: string
  environment_id: string
  status: 'completed' | 'failed' | 'cancelled'
  start_time: string
  end_time: string
  total_duration_seconds: number
  artifacts_deployed: number
  dependencies_installed: number
  steps_completed: number
  steps_total: number
  retry_count: number
  error_message?: string
  performance_metrics: PerformanceMetrics
  step_details: StepDetail[]
  resource_usage: ResourceUsage
  validation_results?: ValidationResults
}

export interface PerformanceMetrics {
  artifact_transfer_time_seconds: number
  dependency_installation_time_seconds: number
  validation_time_seconds: number
  average_step_duration_seconds: number
  throughput_artifacts_per_minute: number
  network_latency_ms: number
  disk_io_operations: number
  memory_peak_usage_mb: number
}

export interface StepDetail {
  step_name: string
  status: 'completed' | 'failed' | 'skipped'
  start_time: string
  end_time?: string
  duration_seconds: number
  artifacts_processed?: number
  bytes_transferred?: number
  error_message?: string
}

export interface ResourceUsage {
  cpu_usage_percent: number
  memory_usage_mb: number
  disk_usage_mb: number
  network_bytes_sent: number
  network_bytes_received: number
  temporary_files_created: number
  temporary_files_cleaned: number
}

export interface ValidationResults {
  checks_passed: number
  checks_failed: number
  checks_total: number
  success_rate_percent: number
  critical_issues: number
  warnings: number
}

interface DeploymentCompletionReportProps {
  summary: DeploymentSummary
  onDownloadReport?: (deploymentId: string) => void
  onShareReport?: (deploymentId: string) => void
  showPerformanceDetails?: boolean
  showResourceUsage?: boolean
}

const DeploymentCompletionReport: React.FC<DeploymentCompletionReportProps> = ({
  summary,
  onDownloadReport,
  onShareReport,
  showPerformanceDetails = true,
  showResourceUsage = true
}) => {
  const [expandedSections, setExpandedSections] = useState<string[]>(['overview'])

  // Calculate success rate and performance grade
  const successRate = (summary.steps_completed / summary.steps_total) * 100
  const isSuccessful = summary.status === 'completed'
  
  // Performance grading based on duration and efficiency
  const getPerformanceGrade = (): { grade: string; color: string; description: string } => {
    const avgStepDuration = summary.performance_metrics.average_step_duration_seconds
    const throughput = summary.performance_metrics.throughput_artifacts_per_minute
    
    if (avgStepDuration < 30 && throughput > 10) {
      return { grade: 'A+', color: '#52c41a', description: 'Excellent Performance' }
    } else if (avgStepDuration < 60 && throughput > 5) {
      return { grade: 'A', color: '#73d13d', description: 'Good Performance' }
    } else if (avgStepDuration < 120 && throughput > 2) {
      return { grade: 'B', color: '#faad14', description: 'Average Performance' }
    } else if (avgStepDuration < 300) {
      return { grade: 'C', color: '#fa8c16', description: 'Below Average Performance' }
    } else {
      return { grade: 'D', color: '#ff4d4f', description: 'Poor Performance' }
    }
  }

  const performanceGrade = getPerformanceGrade()

  // Format duration for display
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  // Format bytes for display
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Get status icon and color
  const getStatusDisplay = () => {
    switch (summary.status) {
      case 'completed':
        return { 
          icon: <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '24px' }} />,
          color: '#52c41a',
          text: 'COMPLETED SUCCESSFULLY'
        }
      case 'failed':
        return { 
          icon: <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '24px' }} />,
          color: '#ff4d4f',
          text: 'DEPLOYMENT FAILED'
        }
      case 'cancelled':
        return { 
          icon: <WarningOutlined style={{ color: '#faad14', fontSize: '24px' }} />,
          color: '#faad14',
          text: 'DEPLOYMENT CANCELLED'
        }
      default:
        return { 
          icon: <InfoCircleOutlined style={{ color: '#1890ff', fontSize: '24px' }} />,
          color: '#1890ff',
          text: 'UNKNOWN STATUS'
        }
    }
  }

  const statusDisplay = getStatusDisplay()

  return (
    <div className="deployment-completion-report">
      {/* Header Section */}
      <Card style={{ marginBottom: '16px' }}>
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Space direction="vertical" size="large">
            {statusDisplay.icon}
            <Title level={2} style={{ color: statusDisplay.color, margin: 0 }}>
              {statusDisplay.text}
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Deployment ID: {summary.deployment_id}
            </Text>
            <Space>
              <Tag color="blue">Plan: {summary.plan_id}</Tag>
              <Tag color="green">Environment: {summary.environment_id}</Tag>
              <Tag color="purple">Duration: {formatDuration(summary.total_duration_seconds)}</Tag>
            </Space>
          </Space>
        </div>

        {/* Quick Actions */}
        <Divider />
        <div style={{ textAlign: 'center' }}>
          <Space>
            {onDownloadReport && (
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={() => onDownloadReport(summary.deployment_id)}
              >
                Download Report
              </Button>
            )}
            {onShareReport && (
              <Button 
                icon={<ShareAltOutlined />}
                onClick={() => onShareReport(summary.deployment_id)}
              >
                Share Report
              </Button>
            )}
          </Space>
        </div>
      </Card>

      {/* Summary Statistics */}
      <Card title="Deployment Summary" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Success Rate"
              value={successRate}
              precision={1}
              suffix="%"
              valueStyle={{ color: successRate >= 90 ? '#52c41a' : successRate >= 70 ? '#faad14' : '#ff4d4f' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Artifacts Deployed"
              value={summary.artifacts_deployed}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Dependencies Installed"
              value={summary.dependencies_installed}
              prefix={<ToolOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Retry Attempts"
              value={summary.retry_count}
              prefix={<RocketOutlined />}
              valueStyle={{ color: summary.retry_count > 0 ? '#fa8c16' : '#52c41a' }}
            />
          </Col>
        </Row>

        {/* Performance Grade */}
        <Divider />
        <div style={{ textAlign: 'center' }}>
          <Space direction="vertical">
            <div>
              <TrophyOutlined style={{ fontSize: '32px', color: performanceGrade.color }} />
            </div>
            <Title level={3} style={{ color: performanceGrade.color, margin: 0 }}>
              Performance Grade: {performanceGrade.grade}
            </Title>
            <Text type="secondary">{performanceGrade.description}</Text>
          </Space>
        </div>
      </Card>
      {/* Step-by-Step Timeline */}
      <Card title="Deployment Timeline" style={{ marginBottom: '16px' }}>
        <Timeline>
          {summary.step_details.map((step, index) => {
            const stepIcon = step.status === 'completed' ? 
              <CheckCircleOutlined style={{ color: '#52c41a' }} /> :
              step.status === 'failed' ?
              <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> :
              <ClockCircleOutlined style={{ color: '#faad14' }} />

            return (
              <Timeline.Item key={index} dot={stepIcon}>
                <div>
                  <Space>
                    <Text strong>{step.step_name.replace('_', ' ').toUpperCase()}</Text>
                    <Tag color={step.status === 'completed' ? 'green' : step.status === 'failed' ? 'red' : 'orange'}>
                      {step.status.toUpperCase()}
                    </Tag>
                    <Text type="secondary">{formatDuration(step.duration_seconds)}</Text>
                  </Space>
                  
                  {step.artifacts_processed && (
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary">
                        Processed {step.artifacts_processed} artifacts
                      </Text>
                    </div>
                  )}
                  
                  {step.bytes_transferred && (
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary">
                        Transferred {formatBytes(step.bytes_transferred)}
                      </Text>
                    </div>
                  )}
                  
                  {step.error_message && (
                    <div style={{ marginTop: '4px' }}>
                      <Text type="danger">{step.error_message}</Text>
                    </div>
                  )}
                  
                  <div style={{ marginTop: '4px' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {new Date(step.start_time).toLocaleTimeString()} - {
                        step.end_time ? new Date(step.end_time).toLocaleTimeString() : 'In Progress'
                      }
                    </Text>
                  </div>
                </div>
              </Timeline.Item>
            )
          })}
        </Timeline>
      </Card>

      {/* Performance Metrics */}
      {showPerformanceDetails && (
        <Card title="Performance Analysis" style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small" title="Timing Breakdown">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>Artifact Transfer:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Progress 
                        percent={Math.round((summary.performance_metrics.artifact_transfer_time_seconds / summary.total_duration_seconds) * 100)}
                        format={() => formatDuration(summary.performance_metrics.artifact_transfer_time_seconds)}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Text>Dependency Installation:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Progress 
                        percent={Math.round((summary.performance_metrics.dependency_installation_time_seconds / summary.total_duration_seconds) * 100)}
                        format={() => formatDuration(summary.performance_metrics.dependency_installation_time_seconds)}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Text>Validation:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Progress 
                        percent={Math.round((summary.performance_metrics.validation_time_seconds / summary.total_duration_seconds) * 100)}
                        format={() => formatDuration(summary.performance_metrics.validation_time_seconds)}
                      />
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} md={12}>
              <Card size="small" title="Efficiency Metrics">
                <Row gutter={[8, 8]}>
                  <Col span={12}>
                    <Statistic
                      title="Throughput"
                      value={summary.performance_metrics.throughput_artifacts_per_minute}
                      precision={1}
                      suffix="artifacts/min"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Avg Step Duration"
                      value={summary.performance_metrics.average_step_duration_seconds}
                      precision={1}
                      suffix="s"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Network Latency"
                      value={summary.performance_metrics.network_latency_ms}
                      suffix="ms"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Disk I/O Ops"
                      value={summary.performance_metrics.disk_io_operations}
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* Resource Usage */}
      {showResourceUsage && (
        <Card title="Resource Utilization" style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card size="small" title="System Resources">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>CPU Usage:</Text>
                    <Progress 
                      percent={summary.resource_usage.cpu_usage_percent}
                      status={summary.resource_usage.cpu_usage_percent > 80 ? 'exception' : 'normal'}
                    />
                  </div>
                  <div>
                    <Text>Memory Usage:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{summary.resource_usage.memory_usage_mb} MB</Text>
                      <Text type="secondary"> (Peak: {summary.performance_metrics.memory_peak_usage_mb} MB)</Text>
                    </div>
                  </div>
                  <div>
                    <Text>Disk Usage:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{formatBytes(summary.resource_usage.disk_usage_mb * 1024 * 1024)}</Text>
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card size="small" title="Network Activity">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>Data Sent:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{formatBytes(summary.resource_usage.network_bytes_sent)}</Text>
                    </div>
                  </div>
                  <div>
                    <Text>Data Received:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{formatBytes(summary.resource_usage.network_bytes_received)}</Text>
                    </div>
                  </div>
                  <div>
                    <Text>Total Transfer:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>
                        {formatBytes(summary.resource_usage.network_bytes_sent + summary.resource_usage.network_bytes_received)}
                      </Text>
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card size="small" title="File Management">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>Temp Files Created:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{summary.resource_usage.temporary_files_created}</Text>
                    </div>
                  </div>
                  <div>
                    <Text>Temp Files Cleaned:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text strong>{summary.resource_usage.temporary_files_cleaned}</Text>
                    </div>
                  </div>
                  <div>
                    <Text>Cleanup Rate:</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Progress 
                        percent={summary.resource_usage.temporary_files_created > 0 ? 
                          Math.round((summary.resource_usage.temporary_files_cleaned / summary.resource_usage.temporary_files_created) * 100) : 100}
                        size="small"
                        status={summary.resource_usage.temporary_files_cleaned < summary.resource_usage.temporary_files_created ? 'exception' : 'success'}
                      />
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* Validation Results */}
      {summary.validation_results && (
        <Card title="Validation Summary" style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic
                  title="Validation Success Rate"
                  value={summary.validation_results.success_rate_percent}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: summary.validation_results.success_rate_percent >= 90 ? '#52c41a' : 
                           summary.validation_results.success_rate_percent >= 70 ? '#faad14' : '#ff4d4f' 
                  }}
                />
                
                <div>
                  <Text>Checks Passed: </Text>
                  <Text strong style={{ color: '#52c41a' }}>
                    {summary.validation_results.checks_passed}
                  </Text>
                  <Text> / {summary.validation_results.checks_total}</Text>
                </div>
                
                <div>
                  <Text>Checks Failed: </Text>
                  <Text strong style={{ color: '#ff4d4f' }}>
                    {summary.validation_results.checks_failed}
                  </Text>
                </div>
              </Space>
            </Col>
            
            <Col xs={24} md={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text>Critical Issues: </Text>
                  <Tag color={summary.validation_results.critical_issues > 0 ? 'red' : 'green'}>
                    {summary.validation_results.critical_issues}
                  </Tag>
                </div>
                
                <div>
                  <Text>Warnings: </Text>
                  <Tag color={summary.validation_results.warnings > 0 ? 'orange' : 'green'}>
                    {summary.validation_results.warnings}
                  </Tag>
                </div>
                
                <div style={{ marginTop: '16px' }}>
                  <Progress
                    type="circle"
                    size={80}
                    percent={summary.validation_results.success_rate_percent}
                    format={(percent) => `${percent}%`}
                    status={summary.validation_results.success_rate_percent >= 90 ? 'success' : 
                            summary.validation_results.success_rate_percent >= 70 ? 'normal' : 'exception'}
                  />
                </div>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Error Details (if failed) */}
      {summary.status === 'failed' && summary.error_message && (
        <Card title="Failure Analysis" style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>Error Message:</Text>
              <Paragraph style={{ marginTop: '8px', padding: '12px', backgroundColor: '#fff2f0', border: '1px solid #ffccc7', borderRadius: '4px' }}>
                <Text type="danger">{summary.error_message}</Text>
              </Paragraph>
            </div>
            
            <div>
              <Text strong>Recommendations:</Text>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>Review the deployment logs for detailed error information</li>
                <li>Check environment connectivity and resource availability</li>
                <li>Verify artifact integrity and dependencies</li>
                {summary.retry_count < 3 && <li>Consider retrying the deployment after addressing issues</li>}
                {summary.retry_count >= 3 && <li>Contact system administrator for manual intervention</li>}
              </ul>
            </div>
          </Space>
        </Card>
      )}

      {/* Footer Information */}
      <Card size="small">
        <div style={{ textAlign: 'center', color: '#666', fontSize: '12px' }}>
          <Space direction="vertical">
            <Text type="secondary">
              Report generated on {new Date().toLocaleString()}
            </Text>
            <Text type="secondary">
              Deployment started: {new Date(summary.start_time).toLocaleString()} | 
              Completed: {new Date(summary.end_time).toLocaleString()}
            </Text>
            <Text type="secondary">
              Total execution time: {formatDuration(summary.total_duration_seconds)}
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default DeploymentCompletionReport