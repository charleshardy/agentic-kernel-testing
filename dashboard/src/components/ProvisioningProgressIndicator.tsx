import React from 'react'
import { 
  Progress, 
  Steps, 
  Card, 
  Typography, 
  Space, 
  Tag, 
  Tooltip,
  Statistic,
  Alert
} from 'antd'
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  LoadingOutlined,
  WarningOutlined
} from '@ant-design/icons'
import { ProvisioningProgress, ProvisioningStage } from '../types/environment'

const { Text, Title } = Typography
const { Step } = Steps

interface ProvisioningProgressIndicatorProps {
  progress: ProvisioningProgress
  environmentId: string
  showDetails?: boolean
  size?: 'small' | 'default' | 'large'
}

/**
 * Component for displaying environment provisioning progress with stage-specific indicators
 * Shows clear progress indicators, distinguishes between different provisioning stages,
 * and provides estimated completion times
 */
const ProvisioningProgressIndicator: React.FC<ProvisioningProgressIndicatorProps> = ({
  progress,
  environmentId,
  showDetails = true,
  size = 'default'
}) => {
  // Get status for current stage
  const getStageStatus = (stage: ProvisioningStage, currentStage: ProvisioningStage) => {
    const stages = [
      ProvisioningStage.INITIALIZING,
      ProvisioningStage.ALLOCATING_RESOURCES,
      ProvisioningStage.CREATING_ENVIRONMENT,
      ProvisioningStage.CONFIGURING_NETWORK,
      ProvisioningStage.INSTALLING_SOFTWARE,
      ProvisioningStage.RUNNING_HEALTH_CHECKS,
      ProvisioningStage.FINALIZING,
      ProvisioningStage.COMPLETED
    ]
    
    const currentIndex = stages.indexOf(currentStage)
    const stageIndex = stages.indexOf(stage)
    
    if (currentStage === ProvisioningStage.FAILED) {
      return stageIndex <= currentIndex ? 'error' : 'wait'
    }
    
    if (stageIndex < currentIndex) {
      return 'finish'
    } else if (stageIndex === currentIndex) {
      return 'process'
    } else {
      return 'wait'
    }
  }

  // Get icon for stage
  const getStageIcon = (stage: ProvisioningStage, currentStage: ProvisioningStage) => {
    const status = getStageStatus(stage, currentStage)
    
    switch (status) {
      case 'finish':
        return <CheckCircleOutlined />
      case 'process':
        return <LoadingOutlined spin />
      case 'error':
        return <ExclamationCircleOutlined />
      default:
        return undefined
    }
  }

  // Get progress bar status
  const getProgressStatus = () => {
    if (progress.currentStage === ProvisioningStage.FAILED) {
      return 'exception'
    } else if (progress.currentStage === ProvisioningStage.COMPLETED) {
      return 'success'
    } else {
      return 'active'
    }
  }

  // Format remaining time
  const formatRemainingTime = (seconds?: number) => {
    if (!seconds || seconds <= 0) return 'Unknown'
    
    if (seconds < 60) {
      return `${Math.round(seconds)}s`
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`
    } else {
      return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
    }
  }

  // Get stage color
  const getStageColor = (stage: ProvisioningStage) => {
    switch (stage) {
      case ProvisioningStage.COMPLETED:
        return 'success'
      case ProvisioningStage.FAILED:
        return 'error'
      case ProvisioningStage.INITIALIZING:
        return 'processing'
      case ProvisioningStage.FINALIZING:
        return 'warning'
      default:
        return 'default'
    }
  }

  const stages = [
    { key: ProvisioningStage.INITIALIZING, title: 'Initialize', description: 'Setting up environment' },
    { key: ProvisioningStage.ALLOCATING_RESOURCES, title: 'Allocate', description: 'Reserving resources' },
    { key: ProvisioningStage.CREATING_ENVIRONMENT, title: 'Create', description: 'Creating environment' },
    { key: ProvisioningStage.CONFIGURING_NETWORK, title: 'Network', description: 'Configuring network' },
    { key: ProvisioningStage.INSTALLING_SOFTWARE, title: 'Install', description: 'Installing software' },
    { key: ProvisioningStage.RUNNING_HEALTH_CHECKS, title: 'Health Check', description: 'Running health checks' },
    { key: ProvisioningStage.FINALIZING, title: 'Finalize', description: 'Finalizing setup' },
    { key: ProvisioningStage.COMPLETED, title: 'Complete', description: 'Environment ready' }
  ]

  if (size === 'small') {
    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Progress
            percent={Math.round(progress.progressPercentage)}
            size="small"
            status={getProgressStatus()}
            showInfo={false}
            style={{ flex: 1 }}
          />
          <Tag color={getStageColor(progress.currentStage)} style={{ margin: 0 }}>
            {progress.stageDetails.stageName}
          </Tag>
        </div>
        {progress.remainingTimeSeconds && progress.remainingTimeSeconds > 0 && (
          <Text type="secondary" style={{ fontSize: '12px' }}>
            <ClockCircleOutlined /> {formatRemainingTime(progress.remainingTimeSeconds)} remaining
          </Text>
        )}
      </Space>
    )
  }

  return (
    <Card 
      title={
        <Space>
          <LoadingOutlined spin={progress.currentStage !== ProvisioningStage.COMPLETED && progress.currentStage !== ProvisioningStage.FAILED} />
          Provisioning Progress
          <Text type="secondary">({environmentId.slice(0, 8)}...)</Text>
        </Space>
      }
      size={size}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Overall Progress */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text strong>Overall Progress</Text>
            <Text>{Math.round(progress.progressPercentage)}%</Text>
          </div>
          <Progress
            percent={Math.round(progress.progressPercentage)}
            status={getProgressStatus()}
            strokeWidth={8}
          />
        </div>

        {/* Current Stage Info */}
        <div style={{ 
          padding: 16, 
          background: '#f5f5f5', 
          borderRadius: 6,
          border: '1px solid #d9d9d9'
        }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Tag color={getStageColor(progress.currentStage)} style={{ margin: 0 }}>
                  {progress.stageDetails.stageName}
                </Tag>
                <Text>{progress.stageDetails.stageDescription}</Text>
              </Space>
              <Text type="secondary">
                Stage {progress.stageDetails.stageIndex + 1} of {progress.stageDetails.totalStages}
              </Text>
            </div>
            
            {progress.remainingTimeSeconds && progress.remainingTimeSeconds > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Space>
                  <ClockCircleOutlined />
                  <Text>Estimated completion:</Text>
                </Space>
                <Text strong>{formatRemainingTime(progress.remainingTimeSeconds)}</Text>
              </div>
            )}
          </Space>
        </div>

        {/* Detailed Stage Progress */}
        {showDetails && (
          <div>
            <Title level={5} style={{ marginBottom: 16 }}>Stage Details</Title>
            <Steps
              current={progress.stageDetails.stageIndex}
              status={progress.currentStage === ProvisioningStage.FAILED ? 'error' : 'process'}
              size="small"
              direction="vertical"
            >
              {stages.map((stage, index) => (
                <Step
                  key={stage.key}
                  title={stage.title}
                  description={stage.description}
                  status={getStageStatus(stage.key, progress.currentStage)}
                  icon={getStageIcon(stage.key, progress.currentStage)}
                />
              ))}
            </Steps>
          </div>
        )}

        {/* Error Alert */}
        {progress.currentStage === ProvisioningStage.FAILED && (
          <Alert
            message="Provisioning Failed"
            description="Environment provisioning encountered an error. Please check logs for details."
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
          />
        )}

        {/* Success Alert */}
        {progress.currentStage === ProvisioningStage.COMPLETED && (
          <Alert
            message="Provisioning Complete"
            description="Environment has been successfully provisioned and is ready for use."
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
          />
        )}

        {/* Timestamps */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          padding: '8px 0',
          borderTop: '1px solid #f0f0f0',
          fontSize: '12px',
          color: '#666'
        }}>
          <span>Started: {new Date(progress.startedAt).toLocaleString()}</span>
          <span>Updated: {new Date(progress.lastUpdated).toLocaleString()}</span>
        </div>
      </Space>
    </Card>
  )
}

export default ProvisioningProgressIndicator