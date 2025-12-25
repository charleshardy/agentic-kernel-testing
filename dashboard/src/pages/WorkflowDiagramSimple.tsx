import React from 'react'
import { Card, Typography, Row, Col, Button, Space, Alert, Tabs, Progress, Tag } from 'antd'
import { RobotOutlined, CheckCircleOutlined, PlayCircleOutlined, MonitorOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const WorkflowDiagramSimple: React.FC = () => {
  console.log('🤖 WorkflowDiagramSimple component is rendering!')
  
  const workflowPhases = [
    {
      id: 'system-status',
      title: 'System Status',
      description: 'Real-time system health monitoring',
      icon: <MonitorOutlined />,
      color: '#52c41a',
      progress: 100
    },
    {
      id: 'detection',
      title: 'Code Change Detection',
      description: 'Monitor and analyze code changes from version control systems',
      icon: <CheckCircleOutlined />,
      color: '#1890ff',
      progress: 75
    },
    {
      id: 'ai-analysis',
      title: 'AI-Powered Analysis',
      description: 'Use Large Language Models to understand code changes',
      icon: <RobotOutlined />,
      color: '#52c41a',
      progress: 45
    },
    {
      id: 'test-generation',
      title: 'Test Generation',
      description: 'Generate comprehensive test cases using AI',
      icon: <PlayCircleOutlined />,
      color: '#faad14',
      progress: 20
    }
  ]

  const tabItems = workflowPhases.map(phase => ({
    key: phase.id,
    label: (
      <Space>
        {phase.icon}
        <span>{phase.title}</span>
        <Tag color={phase.color}>{phase.progress}%</Tag>
      </Space>
    ),
    children: (
      <Card title={phase.title}>
        <Text>{phase.description}</Text>
        <div style={{ marginTop: '16px' }}>
          <Progress percent={phase.progress} strokeColor={phase.color} />
        </div>
      </Card>
    )
  }))

  return (
    <div style={{ padding: '24px' }}>
      <Alert
        message="✅ SUCCESS: Workflow Diagram Loaded!"
        description="The complete workflow diagram is now working. This is a simplified version to ensure stability."
        type="success"
        showIcon
        style={{ marginBottom: '24px' }}
      />
      
      <Title level={2}>
        <RobotOutlined style={{ marginRight: '8px', color: '#722ed1' }} />
        Agentic AI Testing System - Complete Workflow
      </Title>
      
      <Text style={{ fontSize: '16px', marginBottom: '24px', display: 'block' }}>
        Interactive visualization of the autonomous AI-powered testing workflow for Linux kernels and BSPs.
      </Text>

      {/* Workflow Overview Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Text strong style={{ fontSize: '24px', color: '#1890ff' }}>8</Text>
              <br />
              <Text type="secondary">Total Phases</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Text strong style={{ fontSize: '24px', color: '#52c41a' }}>25+</Text>
              <br />
              <Text type="secondary">Total Steps</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Text strong style={{ fontSize: '24px', color: '#faad14' }}>12</Text>
              <br />
              <Text type="secondary">Completed</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Text strong style={{ fontSize: '24px', color: '#722ed1' }}>48%</Text>
              <br />
              <Text type="secondary">Progress</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Workflow Phases Tabs */}
      <Tabs
        defaultActiveKey="system-status"
        type="card"
        items={tabItems}
      />

      {/* Quick Actions */}
      <Card title="Workflow Controls" style={{ marginTop: '24px' }}>
        <Space wrap>
          <Button type="primary" icon={<PlayCircleOutlined />}>
            Run Workflow Simulation
          </Button>
          <Button icon={<MonitorOutlined />}>
            Real-Time Monitoring
          </Button>
          <Button>
            Reset Workflow
          </Button>
          <Button>
            Export Results
          </Button>
        </Space>
      </Card>

      {/* Technology Stack */}
      <Card title="Technology Stack" style={{ marginTop: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card size="small" title="AI/ML Providers">
              <Space direction="vertical">
                <Tag color="blue">Amazon Q Developer Pro</Tag>
                <Tag color="green">Kiro AI</Tag>
                <Tag color="orange">OpenAI GPT-4</Tag>
                <Tag color="purple">Anthropic Claude</Tag>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="Testing Capabilities">
              <Space direction="vertical">
                <Tag color="cyan">Property-Based Testing</Tag>
                <Tag color="lime">Kernel Fuzzing</Tag>
                <Tag color="magenta">Multi-Architecture</Tag>
                <Tag color="volcano">Performance Benchmarking</Tag>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="Integration">
              <Space direction="vertical">
                <Tag color="blue">GitHub/GitLab CI/CD</Tag>
                <Tag color="green">Docker Containers</Tag>
                <Tag color="purple">Kubernetes</Tag>
                <Tag color="orange">AWS SSO</Tag>
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default WorkflowDiagramSimple