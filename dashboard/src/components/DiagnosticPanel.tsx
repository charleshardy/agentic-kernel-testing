import React from 'react'
import { Modal, Tabs, Card, List, Tag, Space, Button } from 'antd'
import { BugOutlined, InfoCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'

interface DiagnosticPanelProps {
  visible: boolean
  onClose: () => void
}

const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({
  visible,
  onClose
}) => {
  // Mock diagnostic data
  const systemInfo = {
    version: '1.0.0',
    uptime: '2h 34m',
    environment: 'development',
    apiEndpoint: '/api/v1',
    webSocketEndpoint: '/ws/environments/allocation'
  }

  const connectionInfo = {
    webSocket: {
      status: 'connected',
      url: 'ws://localhost:3000/ws/environments/allocation',
      lastMessage: new Date(),
      messageCount: 42
    },
    sse: {
      status: 'connected',
      url: 'http://localhost:3000/api/environments/allocation/events',
      lastEvent: new Date(),
      eventCount: 18
    }
  }

  const recentErrors = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 300000),
      level: 'warning',
      message: 'WebSocket reconnection attempt',
      details: 'Connection lost, attempting to reconnect'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 600000),
      level: 'error',
      message: 'API request timeout',
      details: 'GET /api/environments/allocation timed out after 30s'
    }
  ]

  const getErrorIcon = (level: string) => {
    switch (level) {
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />
      case 'info': return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      default: return <InfoCircleOutlined />
    }
  }

  const tabItems = [
    {
      key: 'system',
      label: 'System Info',
      children: (
        <Card size="small">
          <List
            size="small"
            dataSource={Object.entries(systemInfo)}
            renderItem={([key, value]) => (
              <List.Item>
                <Space>
                  <strong>{key}:</strong>
                  <span>{String(value)}</span>
                </Space>
              </List.Item>
            )}
          />
        </Card>
      )
    },
    {
      key: 'connections',
      label: 'Connections',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Card title="WebSocket" size="small">
            <List
              size="small"
              dataSource={Object.entries(connectionInfo.webSocket)}
              renderItem={([key, value]) => (
                <List.Item>
                  <Space>
                    <strong>{key}:</strong>
                    <span>{key === 'status' ? 
                      <Tag color={value === 'connected' ? 'green' : 'red'}>{String(value)}</Tag> :
                      String(value)
                    }</span>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
          <Card title="Server-Sent Events" size="small">
            <List
              size="small"
              dataSource={Object.entries(connectionInfo.sse)}
              renderItem={([key, value]) => (
                <List.Item>
                  <Space>
                    <strong>{key}:</strong>
                    <span>{key === 'status' ? 
                      <Tag color={value === 'connected' ? 'green' : 'red'}>{String(value)}</Tag> :
                      String(value)
                    }</span>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Space>
      )
    },
    {
      key: 'errors',
      label: 'Recent Errors',
      children: (
        <List
          dataSource={recentErrors}
          renderItem={(error) => (
            <List.Item>
              <List.Item.Meta
                avatar={getErrorIcon(error.level)}
                title={
                  <Space>
                    <Tag color={error.level === 'error' ? 'red' : 'orange'}>
                      {error.level.toUpperCase()}
                    </Tag>
                    {error.message}
                  </Space>
                }
                description={
                  <div>
                    <div>{error.details}</div>
                    <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                      {error.timestamp.toLocaleString()}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )
    }
  ]

  return (
    <Modal
      title={
        <Space>
          <BugOutlined />
          System Diagnostics
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          Close
        </Button>
      ]}
      width={800}
    >
      <Tabs items={tabItems} />
    </Modal>
  )
}

export default DiagnosticPanel