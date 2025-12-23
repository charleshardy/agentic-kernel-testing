import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const TestExecutionDebugSimple: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={2}>Test Execution Debug (Simple Version)</Title>
        <p>This is a simplified version to test if the component loads correctly.</p>
        <p>If you can see this message, the routing is working and the component is loading.</p>
      </Card>
    </div>
  )
}

export default TestExecutionDebugSimple