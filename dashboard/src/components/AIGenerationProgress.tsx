import React from 'react'
import { Progress, Typography, Space, Spin } from 'antd'
import { RobotOutlined } from '@ant-design/icons'

const { Text } = Typography

interface AIGenerationProgressProps {
  isGenerating: boolean
  type?: 'diff' | 'function'
  progress?: number
  message?: string
}

const AIGenerationProgress: React.FC<AIGenerationProgressProps> = ({
  isGenerating,
  type,
  progress = 0,
  message
}) => {
  if (!isGenerating) return null

  const defaultMessage = type === 'diff' 
    ? 'Analyzing code diff and generating test cases...'
    : 'Analyzing function and generating test cases...'

  return (
    <div style={{ 
      padding: '16px', 
      backgroundColor: '#f6ffed', 
      border: '1px solid #b7eb8f',
      borderRadius: '6px',
      marginBottom: '16px'
    }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <Spin size="small" />
          <RobotOutlined style={{ color: '#52c41a' }} />
          <Text strong>AI Test Generation in Progress</Text>
        </Space>
        
        <Text type="secondary">
          {message || defaultMessage}
        </Text>
        
        {progress > 0 && (
          <Progress 
            percent={progress} 
            size="small" 
            status="active"
            strokeColor="#52c41a"
          />
        )}
      </Space>
    </div>
  )
}

export default AIGenerationProgress