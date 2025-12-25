import React, { useState } from 'react'
import { Card, Typography, Tabs, Row, Col, Button, Space, Progress, Tag, Statistic } from 'antd'
import { 
  RobotOutlined, 
  PlayCircleOutlined, 
  CheckCircleOutlined, 
  CodeOutlined,
  ExperimentOutlined,
  MonitorOutlined,
  ArrowLeftOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography

const WorkflowMinimal: React.FC = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')
  
  const workflowPhases = [
    { 
      key: 'detection', 
      title: 'Code Detection', 
      progress: 100, 
      status: 'success',
      description: 'Monitor code changes from VCS'
    },
    { 
      key: 'ai-analysis', 
      title: 'AI Analysis', 
      progress: 65, 
      status: 'active',
      description: 'LLM-powered code understanding'
    },
    { 
      key: 'test-gen', 
      title: 'Test Generation', 
      progress: 0, 
      status: 'normal',
      description: 'Generate comprehensive test cases'
    },
    { 
      key: 'execution', 
      title: 'Execution', 
      progress: 0, 
      status: 'normal',
      description: 'Multi-environment testing'
    }
  ]
  
  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <Title level={2}>
          <RobotOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
          Minimal Workflow View
        </Title>
        <Paragraph>
          Simplified visualization of the autonomous AI testing workflow
        </Paragraph>
      </div>
      
      {/* Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Phases"
              value={8}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Steps"
              value={25}
              suffix="+"
              prefix={<CodeOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Completed"
              value={3}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Progress"
              value={41}
              suffix="%"
              prefix={<MonitorOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
        items={[
          {
            key: 'overview',
            label: (
              <Space>
                <MonitorOutlined />
                <span>Overview</span>
              </Space>
            ),
            children: (
              <Card title="Workflow Progress Overview">
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  {workflowPhases.map((phase, index) => (
                    <Card key={phase.key} size="small">
                      <Row align="middle" gutter={16}>
                        <Col flex="auto">
                          <Space direction="vertical" size="small">
                            <Text strong>{phase.title}</Text>
                            <Text type="secondary">{phase.description}</Text>
                          </Space>
                        </Col>
                        <Col>
                          <Progress 
                            percent={phase.progress} 
                            size="small" 
                            status={phase.status as any}
                            style={{ minWidth: '120px' }}
                          />
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </Space>
              </Card>
            )
          },
          {
            key: 'system-status',
            label: (
              <Space>
                <CheckCircleOutlined />
                <span>System Status</span>
                <Tag color="green">Online</Tag>
              </Space>
            ),
            children: (
              <Card title="System Health Status">
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={8}>
                    <Card size="small" title="API Server">
                      <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        <Text>Healthy</Text>
                      </Space>
                    </Card>
                  </Col>
                  <Col xs={24} md={8}>
                    <Card size="small" title="Database">
                      <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        <Text>Connected</Text>
                      </Space>
                    </Card>
                  </Col>
                  <Col xs={24} md={8}>
                    <Card size="small" title="AI Services">
                      <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        <Text>Available</Text>
                      </Space>
                    </Card>
                  </Col>
                </Row>
              </Card>
            )
          },
          {
            key: 'current-phase',
            label: (
              <Space>
                <PlayCircleOutlined />
                <span>Current Phase</span>
                <Tag color="blue">AI Analysis</Tag>
              </Space>
            ),
            children: (
              <Card title="AI Analysis Phase - In Progress">
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Paragraph>
                    Currently analyzing code changes using Large Language Models to understand 
                    impact and generate targeted test cases.
                  </Paragraph>
                  
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={8}>
                      <Card size="small" title="LLM Processing">
                        <Progress percent={75} size="small" status="active" />
                        <Text type="secondary">Analyzing code structure</Text>
                      </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Card size="small" title="Impact Scoring">
                        <Progress percent={45} size="small" status="active" />
                        <Text type="secondary">Calculating risk scores</Text>
                      </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Card size="small" title="Subsystem Mapping">
                        <Progress percent={20} size="small" />
                        <Text type="secondary">Identifying affected areas</Text>
                      </Card>
                    </Col>
                  </Row>
                </Space>
              </Card>
            )
          }
        ]}
      />

      {/* Actions */}
      <Card title="Navigation" style={{ marginTop: '24px', textAlign: 'center' }}>
        <Space wrap>
          <Button 
            type="primary" 
            icon={<RobotOutlined />}
            onClick={() => navigate('/workflow-complex')}
          >
            View Complete Workflow
          </Button>
          <Button 
            icon={<MonitorOutlined />}
            onClick={() => navigate('/workflow-simple')}
          >
            Simple Diagram
          </Button>
          <Button 
            icon={<ReloadOutlined />}
          >
            Refresh Status
          </Button>
          <Button 
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/workflow')}
          >
            Back to Overview
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default WorkflowMinimal