import React from 'react'
import { Card, Typography, Button, Space, Row, Col, Statistic, Divider } from 'antd'
import { 
  RobotOutlined, 
  ThunderboltOutlined, 
  BarChartOutlined, 
  SafetyOutlined,
  MonitorOutlined,
  CodeOutlined,
  ExperimentOutlined,
  CloudServerOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

const SimpleTest: React.FC = () => {
  const navigate = useNavigate()
  
  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header Section */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <Title level={1}>
          <RobotOutlined style={{ color: '#1890ff', marginRight: '12px' }} />
          Agentic AI Testing Workflow
        </Title>
        <Paragraph style={{ fontSize: '16px', color: '#666', maxWidth: '600px', margin: '0 auto' }}>
          Autonomous AI-powered testing platform for Linux kernels and Board Support Packages (BSPs) 
          across diverse hardware configurations.
        </Paragraph>
      </div>

      {/* Statistics Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="Workflow Phases"
              value={8}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="Test Steps"
              value={25}
              suffix="+"
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="AI Providers"
              value={5}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="Architectures"
              value={3}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Core Capabilities */}
      <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
        <Col xs={24} lg={12}>
          <Card title="🤖 AI-Powered Analysis" size="small">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text>• Autonomous test generation using LLMs</Text>
              <Text>• Code change impact analysis</Text>
              <Text>• Root cause failure analysis</Text>
              <Text>• AI-powered fix suggestions</Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🔧 Multi-Environment Testing" size="small">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text>• Virtual environments (QEMU, KVM)</Text>
              <Text>• Physical hardware boards</Text>
              <Text>• x86_64, ARM64, RISC-V support</Text>
              <Text>• Fault injection testing</Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🛡️ Security & Performance" size="small">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text>• Syzkaller kernel fuzzing</Text>
              <Text>• Vulnerability detection</Text>
              <Text>• Performance benchmarking</Text>
              <Text>• Regression monitoring</Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🔗 CI/CD Integration" size="small">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text>• GitHub/GitLab webhooks</Text>
              <Text>• Real-time notifications</Text>
              <Text>• Automated reporting</Text>
              <Text>• Build pipeline integration</Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* Navigation Section */}
      <Card title="🚀 Explore Workflow Views" style={{ textAlign: 'center' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Paragraph>
            Choose a workflow view to explore the autonomous testing process:
          </Paragraph>
          
          <Row gutter={[16, 16]} justify="center">
            <Col>
              <Button 
                type="primary" 
                size="large"
                icon={<RobotOutlined />}
                onClick={() => navigate('/workflow-complex')}
              >
                Complete Workflow
              </Button>
            </Col>
            <Col>
              <Button 
                size="large"
                icon={<BarChartOutlined />}
                onClick={() => navigate('/workflow-minimal')}
              >
                Minimal View
              </Button>
            </Col>
            <Col>
              <Button 
                size="large"
                icon={<MonitorOutlined />}
                onClick={() => navigate('/workflow-simple')}
              >
                Simple Diagram
              </Button>
            </Col>
          </Row>
          
          <Divider type="vertical" style={{ height: '20px' }} />
          
          <Button 
            onClick={() => navigate('/')}
            style={{ marginTop: '16px' }}
          >
            ← Back to Dashboard
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default SimpleTest