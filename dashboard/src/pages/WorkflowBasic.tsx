import React from 'react'
import { Card, Typography, Space, Button, Row, Col, Tag, Divider } from 'antd'
import { 
  CheckCircleOutlined, 
  RobotOutlined, 
  ArrowLeftOutlined,
  ExperimentOutlined,
  MonitorOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

const WorkflowBasic: React.FC = () => {
  const navigate = useNavigate()
  
  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }} />
            <Title level={2} style={{ color: '#2e7d32', marginBottom: '8px' }}>
              Basic Workflow View
            </Title>
            <Text type="secondary">
              Simplified overview of the AI testing workflow
            </Text>
          </div>

          <Divider />

          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card size="small" title="🔍 Code Analysis Phase">
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text>• VCS webhook detection</Text>
                  <Text>• Git diff analysis</Text>
                  <Text>• AST code structure analysis</Text>
                </Space>
              </Card>
            </Col>
            <Col span={24}>
              <Card size="small" title="🤖 AI Processing Phase">
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text>• LLM code understanding</Text>
                  <Text>• Impact score calculation</Text>
                  <Text>• Test case generation</Text>
                </Space>
              </Card>
            </Col>
            <Col span={24}>
              <Card size="small" title="⚡ Execution Phase">
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text>• Multi-environment testing</Text>
                  <Text>• Performance monitoring</Text>
                  <Text>• Results analysis</Text>
                </Space>
              </Card>
            </Col>
          </Row>

          <Divider />

          <div style={{ textAlign: 'center' }}>
            <Space wrap>
              <Button 
                type="primary"
                icon={<RobotOutlined />}
                onClick={() => navigate('/workflow-complex')}
              >
                View Complete Workflow
              </Button>
              <Button 
                icon={<ExperimentOutlined />}
                onClick={() => navigate('/workflow-minimal')}
              >
                Minimal View
              </Button>
              <Button 
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/workflow')}
              >
                Back to Overview
              </Button>
            </Space>
          </div>

          <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '6px' }}>
            <Text type="secondary">
              <strong>Status:</strong> This basic workflow view provides a simplified overview of the autonomous testing process. 
              For detailed interactive visualization, use the Complete Workflow view.
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default WorkflowBasic