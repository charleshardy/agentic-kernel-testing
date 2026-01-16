import React from 'react'
import { Card, Steps, Tag, Space, Typography, Tooltip } from 'antd'
import {
  ClockCircleOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  CodeOutlined,
  CloudDownloadOutlined,
  RocketOutlined,
  FileZipOutlined
} from '@ant-design/icons'

const { Text } = Typography

interface BuildStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startedAt?: string
  completedAt?: string
  durationSeconds?: number
  errorMessage?: string
}

interface BuildFlowVisualizationProps {
  jobId: string
  status: 'queued' | 'building' | 'completed' | 'failed' | 'cancelled'
  stages?: BuildStage[]
}

/**
 * Build Flow Visualization Component
 * 
 * Displays the build execution flow with stages:
 * 1. Clone Repository
 * 2. Configure Build
 * 3. Execute Build
 * 4. Collect Artifacts
 * 
 * Shows real-time progress and status for each stage.
 */
const BuildFlowVisualization: React.FC<BuildFlowVisualizationProps> = ({
  jobId,
  status,
  stages
}) => {
  // Default stages if not provided
  const defaultStages: BuildStage[] = [
    { name: 'Clone Repository', status: 'pending' },
    { name: 'Configure Build', status: 'pending' },
    { name: 'Execute Build', status: 'pending' },
    { name: 'Collect Artifacts', status: 'pending' }
  ]

  const buildStages = stages || defaultStages

  // Determine current stage based on job status
  const getCurrentStage = (): number => {
    if (status === 'queued') return -1
    if (status === 'cancelled') return -1
    
    // Find the last non-pending stage
    for (let i = buildStages.length - 1; i >= 0; i--) {
      if (buildStages[i].status !== 'pending') {
        return i
      }
    }
    
    // If building but no stages started, show first stage
    if (status === 'building') return 0
    
    return -1
  }

  const getStageIcon = (stage: BuildStage, index: number) => {
    const iconMap: Record<string, React.ReactNode> = {
      'Clone Repository': <CloudDownloadOutlined />,
      'Configure Build': <CodeOutlined />,
      'Execute Build': <RocketOutlined />,
      'Collect Artifacts': <FileZipOutlined />
    }

    const baseIcon = iconMap[stage.name] || <SyncOutlined />

    switch (stage.status) {
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'pending':
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getStageStatus = (stage: BuildStage): 'wait' | 'process' | 'finish' | 'error' => {
    switch (stage.status) {
      case 'running':
        return 'process'
      case 'completed':
        return 'finish'
      case 'failed':
        return 'error'
      case 'pending':
      default:
        return 'wait'
    }
  }

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '-'
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}m ${secs}s`
  }

  const getStageDescription = (stage: BuildStage): React.ReactNode => {
    if (stage.errorMessage) {
      return <Text type="danger" style={{ fontSize: 12 }}>{stage.errorMessage}</Text>
    }
    
    if (stage.status === 'completed' && stage.durationSeconds) {
      return (
        <Text type="secondary" style={{ fontSize: 12 }}>
          Completed in {formatDuration(stage.durationSeconds)}
        </Text>
      )
    }

    if (stage.status === 'running') {
      return <Text type="secondary" style={{ fontSize: 12 }}>In progress...</Text>
    }

    return null
  }

  const getOverallStatus = (): 'wait' | 'process' | 'finish' | 'error' => {
    if (status === 'failed') return 'error'
    if (status === 'completed') return 'finish'
    if (status === 'building') return 'process'
    return 'wait'
  }

  const currentStage = getCurrentStage()

  return (
    <Card 
      title={
        <Space>
          <SyncOutlined />
          <span>Build Flow</span>
          {status === 'building' && (
            <Tag color="processing" icon={<LoadingOutlined />}>
              Building
            </Tag>
          )}
          {status === 'queued' && (
            <Tag color="default" icon={<ClockCircleOutlined />}>
              Queued
            </Tag>
          )}
          {status === 'completed' && (
            <Tag color="success" icon={<CheckCircleOutlined />}>
              Completed
            </Tag>
          )}
          {status === 'failed' && (
            <Tag color="error" icon={<CloseCircleOutlined />}>
              Failed
            </Tag>
          )}
          {status === 'cancelled' && (
            <Tag color="warning">Cancelled</Tag>
          )}
        </Space>
      }
      size="small"
      style={{ marginTop: 16 }}
    >
      {status === 'queued' ? (
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <ClockCircleOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">Build job is queued and waiting for an available build server</Text>
          </div>
        </div>
      ) : (
        <Steps
          current={currentStage}
          status={getOverallStatus()}
          direction="vertical"
          items={buildStages.map((stage, index) => ({
            title: (
              <Space>
                {stage.name}
                {stage.status === 'running' && (
                  <Tag color="processing" icon={<LoadingOutlined />}>
                    Running
                  </Tag>
                )}
              </Space>
            ),
            description: getStageDescription(stage),
            status: getStageStatus(stage),
            icon: getStageIcon(stage, index)
          }))}
        />
      )}
    </Card>
  )
}

export default BuildFlowVisualization
