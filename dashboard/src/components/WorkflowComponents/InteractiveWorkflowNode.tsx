import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Tag,
  Tooltip,
  Progress,
  Modal,
  Descriptions,
  List,
  Typography,
  Badge,
  Divider,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const { Text, Paragraph } = Typography

interface WorkflowNodeProps {
  id: string
  title: string
  description: string
  status: 'waiting' | 'process' | 'finish' | 'error'
  icon: React.ReactNode
  color: string
  progress?: number
  duration?: number
  details?: string
  metrics?: Record<string, any>
  onExecute?: () => void
  onPause?: () => void
  onViewDetails?: () => void
  isExecutable?: boolean
}

const InteractiveWorkflowNode: React.FC<WorkflowNodeProps> = ({
  id,
  title,
  description,
  status,
  icon,
  color,
  progress = 0,
  duration,
  details,
  metrics,
  onExecute,
  onPause,
  onViewDetails,
  isExecutable = false,
}) => {
  const [detailsVisible, setDetailsVisible] = useState(false)

  const getStatusIcon = () => {
    switch (status) {
      case 'finish':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
      case 'process':
        return <LoadingOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '16px' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9', fontSize: '16px' }} />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'finish': return '#52c41a'
      case 'process': return '#1890ff'
      case 'error': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const getCardStyle = () => ({
    borderColor: getStatusColor(),
    borderWidth: '2px',
    borderStyle: status === 'process' ? 'solid' : 'solid',
    boxShadow: status === 'process' ? `0 0 10px ${getStatusColor()}20` : undefined,
    transition: 'all 0.3s ease',
  })

  return (
    <>
      <Card
        size="small"
        style={getCardStyle()}
        title={
          <Space>
            {icon}
            <Text strong style={{ fontSize: '14px' }}>{title}</Text>
            {getStatusIcon()}
          </Space>
        }
        extra={
          <Space>
            {duration && (
              <Tag color="blue" style={{ fontSize: '10px' }}>
                {duration}s
              </Tag>
            )}
            <Tag color={color} style={{ fontSize: '10px' }}>
              {status.toUpperCase()}
            </Tag>
          </Space>
        }
        actions={[
          ...(isExecutable && status === 'waiting' ? [
            <Tooltip title="Execute this step">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={onExecute}
                size="small"
              >
                Execute
              </Button>
            </Tooltip>
          ] : []),
          ...(status === 'process' ? [
            <Tooltip title="Pause execution">
              <Button
                type="text"
                icon={<PauseCircleOutlined />}
                onClick={onPause}
                size="small"
              >
                Pause
              </Button>
            </Tooltip>
          ] : []),
          <Tooltip title="View details">
            <Button
              type="text"
              icon={<InfoCircleOutlined />}
              onClick={() => setDetailsVisible(true)}
              size="small"
            >
              Details
            </Button>
          </Tooltip>
        ]}
      >
        <div style={{ minHeight: '60px' }}>
          <Paragraph style={{ fontSize: '12px', margin: '0 0 8px 0' }}>
            {description}
          </Paragraph>
          
          {status === 'process' && (
            <Progress 
              percent={progress} 
              size="small" 
              strokeColor={color}
              showInfo={false}
            />
          )}
          
          {metrics && (
            <div style={{ marginTop: '8px' }}>
              <Space wrap size="small">
                {Object.entries(metrics).map(([key, value]) => (
                  <Badge
                    key={key}
                    count={value}
                    style={{ backgroundColor: color }}
                    title={key}
                  />
                ))}
              </Space>
            </div>
          )}
        </div>
      </Card>

      <Modal
        title={
          <Space>
            {icon}
            <span>{title}</span>
            {getStatusIcon()}
          </Space>
        }
        open={detailsVisible}
        onCancel={() => setDetailsVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailsVisible(false)}>
            Close
          </Button>,
          ...(isExecutable && status === 'waiting' ? [
            <Button key="execute" type="primary" icon={<PlayCircleOutlined />} onClick={onExecute}>
              Execute Step
            </Button>
          ] : [])
        ]}
        width={600}
      >
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Description">
            {description}
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Space>
              {getStatusIcon()}
              <span style={{ textTransform: 'capitalize' }}>{status}</span>
            </Space>
          </Descriptions.Item>
          {duration && (
            <Descriptions.Item label="Estimated Duration">
              {duration} seconds
            </Descriptions.Item>
          )}
          {status === 'process' && (
            <Descriptions.Item label="Progress">
              <Progress percent={progress} strokeColor={color} />
            </Descriptions.Item>
          )}
          {details && (
            <Descriptions.Item label="Technical Details">
              {details}
            </Descriptions.Item>
          )}
        </Descriptions>

        {metrics && Object.keys(metrics).length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <Divider orientation="left">Metrics</Divider>
            <List
              size="small"
              dataSource={Object.entries(metrics)}
              renderItem={([key, value]) => (
                <List.Item>
                  <List.Item.Meta
                    title={key}
                    description={typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Modal>
    </>
  )
}

export default InteractiveWorkflowNode