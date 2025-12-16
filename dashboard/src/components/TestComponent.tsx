import React from 'react'
import { Card, Button, Alert } from 'antd'

const TestComponent: React.FC = () => {
  const [count, setCount] = React.useState(0)

  return (
    <Card title="Test Component" style={{ margin: '20px' }}>
      <Alert
        message="Component Test"
        description="This is a simple test component to verify React and Ant Design are working correctly."
        type="success"
        showIcon
        style={{ marginBottom: '16px' }}
      />
      
      <p>Counter: {count}</p>
      
      <Button 
        type="primary" 
        onClick={() => setCount(count + 1)}
      >
        Increment
      </Button>
      
      <Button 
        style={{ marginLeft: '8px' }}
        onClick={() => setCount(0)}
      >
        Reset
      </Button>
    </Card>
  )
}

export default TestComponent