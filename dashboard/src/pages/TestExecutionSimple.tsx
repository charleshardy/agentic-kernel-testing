import React from 'react'
import { Card, Button, Typography } from 'antd'
import { RobotOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'

const { Title } = Typography

const TestExecutionSimple: React.FC = () => {
  console.log('TestExecutionSimple component rendering...')

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Test Execution</Title>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => console.log('AI Generate Tests clicked')}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => console.log('Manual Submit clicked')}
          >
            Manual Submit
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => console.log('Refresh clicked')}
          >
            Refresh
          </Button>
        </div>
      </div>

      <Card title="Test Execution Status">
        <p>This is a simplified version of the Test Execution page.</p>
        <p>If you can see this, React and Ant Design are working correctly.</p>
      </Card>
    </div>
  )
}

export default TestExecutionSimple