import React from 'react'
import { Card, Typography, Button, Space, Alert } from 'antd'
import { RobotOutlined, CheckCircleOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const WorkflowTest: React.FC = () => {
  console.log('🤖 WorkflowTest component rendered successfully!')
  
  return (
    <div style={{ padding: '24px' }}>
      <Alert
        message="✅ SUCCESS: Workflow Route is Working!"
        description="You have successfully accessed the /workflow route. The routing is working correctly."
        type="success"
        showIcon
        style={{ marginBottom: '24px' }}
      />
      
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Title level={2}>
            <RobotOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
            Workflow Test Page
          </Title>
          
          <Paragraph>
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
            <strong>Route Status:</strong> The /workflow route is working correctly!
          </Paragraph>
          
          <Paragraph>
            <strong>Current URL:</strong> {window.location.href}
          </Paragraph>
          
          <Paragraph>
            <strong>Current Path:</strong> {window.location.pathname}
          </Paragraph>
          
          <Paragraph>
            <strong>Timestamp:</strong> {new Date().toLocaleString()}
          </Paragraph>
          
          <Button 
            type="primary" 
            size="large"
            onClick={() => {
              console.log('Loading full workflow diagram...')
              // We'll load the full component here
              window.location.reload()
            }}
          >
            This Route Works! ✅
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default WorkflowTest