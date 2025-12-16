import React from 'react'
import { Card, Tag, Typography, Space, Divider, Alert } from 'antd'
import { 
  CodeOutlined, 
  SettingOutlined, 
  SafetyOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons'

const { Text, Title } = Typography

interface KernelDriverInfoProps {
  visible: boolean
}

const KernelDriverInfo: React.FC<KernelDriverInfoProps> = ({ visible }) => {
  if (!visible) return null

  return (
    <Card 
      size="small" 
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <SettingOutlined />
          <span>Kernel Test Driver Generation</span>
        </Space>
      }
    >
      <Alert
        message="Advanced Kernel Testing"
        description="Generate complete kernel modules that test kernel functions directly in kernel space for comprehensive validation."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <Title level={5} style={{ margin: '0 0 8px 0' }}>
            <CodeOutlined /> Generated Components
          </Title>
          <ul style={{ fontSize: '12px', margin: 0, paddingLeft: 16 }}>
            <li>Kernel module source code (.c)</li>
            <li>Makefile for compilation</li>
            <li>Installation scripts</li>
            <li>Test execution scripts</li>
            <li>/proc interface for results</li>
          </ul>
        </div>

        <div>
          <Title level={5} style={{ margin: '0 0 8px 0' }}>
            <ThunderboltOutlined /> Test Capabilities
          </Title>
          <ul style={{ fontSize: '12px', margin: 0, paddingLeft: 16 }}>
            <li>Direct kernel function calls</li>
            <li>Memory management testing</li>
            <li>Scheduler behavior validation</li>
            <li>Network stack testing</li>
            <li>Error injection & fault tolerance</li>
          </ul>
        </div>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <div>
        <Title level={5} style={{ margin: '0 0 8px 0' }}>
          <SafetyOutlined /> Requirements & Safety
        </Title>
        <Space wrap>
          <Tag color="orange">Root Privileges Required</Tag>
          <Tag color="blue">Kernel Headers Needed</Tag>
          <Tag color="green">Isolated Test Environment</Tag>
          <Tag color="purple">Automatic Cleanup</Tag>
        </Space>
        
        <div style={{ marginTop: 8, fontSize: '11px', color: '#8c8c8c' }}>
          <ExclamationCircleOutlined style={{ marginRight: 4 }} />
          Kernel modules are compiled and loaded safely with proper error handling and cleanup.
        </div>
      </div>
    </Card>
  )
}

export default KernelDriverInfo