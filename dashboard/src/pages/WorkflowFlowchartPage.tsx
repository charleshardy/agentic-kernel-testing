import React, { useState } from 'react';
import {
  Card,
  Typography,
  Space,
  Button,
  Select,
  Row,
  Col,
  Statistic,
  Alert,
  Tabs,
  Tag,
  Divider,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
} from '@ant-design/icons';
import WorkflowFlowchart from '../components/WorkflowFlowchart';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const WorkflowFlowchartPage: React.FC = () => {
  const [activeStage, setActiveStage] = useState<string>('detection');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState<number>(1000);

  // Workflow stages for simulation
  const stages = [
    'detection',
    'ai-analysis',
    'test-generation',
    'test-plan',
    'hardware',
    'assign',
    'build',
    'deployment',
    'execution',
    'analysis',
    'defect',
    'summary',
    'notify',
  ];

  const stageNames: Record<string, string> = {
    'detection': 'Code Change Detection',
    'ai-analysis': 'AI Code Analysis',
    'test-generation': 'Test Generation',
    'test-plan': 'Test Plan Creation',
    'hardware': 'Hardware Allocation',
    'assign': 'Hardware Assignment',
    'build': 'Build & Compilation',
    'deployment': 'Deployment',
    'execution': 'Test Execution',
    'analysis': 'Result Analysis',
    'defect': 'Defect Reporting',
    'summary': 'Summary Generation',
    'notify': 'Notification & Export',
  };

  // Simulate workflow progression
  const startSimulation = () => {
    setIsSimulating(true);
    let currentIndex = 0;

    const interval = setInterval(() => {
      if (currentIndex >= stages.length) {
        clearInterval(interval);
        setIsSimulating(false);
        return;
      }

      setActiveStage(stages[currentIndex]);
      currentIndex++;
    }, simulationSpeed);
  };

  const stopSimulation = () => {
    setIsSimulating(false);
  };

  const resetWorkflow = () => {
    setActiveStage('detection');
    setIsSimulating(false);
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          Complete Testing Workflow - Interactive Flowchart
        </Title>
        <Paragraph>
          Visual representation of the end-to-end testing workflow from code change detection 
          through test execution, analysis, and reporting. This flowchart shows all stages, 
          dependencies, and parallel execution paths.
        </Paragraph>
      </div>

      {/* Control Panel */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space wrap>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={startSimulation}
                disabled={isSimulating}
              >
                Simulate Workflow
              </Button>
              <Button
                icon={<PauseCircleOutlined />}
                onClick={stopSimulation}
                disabled={!isSimulating}
              >
                Stop
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={resetWorkflow}
              >
                Reset
              </Button>
              <Select
                value={simulationSpeed}
                onChange={setSimulationSpeed}
                style={{ width: 150 }}
                disabled={isSimulating}
              >
                <Option value={500}>Fast (0.5s)</Option>
                <Option value={1000}>Normal (1s)</Option>
                <Option value={2000}>Slow (2s)</Option>
              </Select>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space wrap style={{ float: 'right' }}>
              <Select
                value={activeStage}
                onChange={setActiveStage}
                style={{ width: 200 }}
                disabled={isSimulating}
              >
                {stages.map(stage => (
                  <Option key={stage} value={stage}>
                    {stageNames[stage]}
                  </Option>
                ))}
              </Select>
              <Button icon={<DownloadOutlined />}>
                Export
              </Button>
              <Button icon={<InfoCircleOutlined />}>
                Help
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Stages"
              value={20}
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Current Stage"
              value={stageNames[activeStage]}
              valueStyle={{ color: '#52c41a', fontSize: '14px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Parallel Paths"
              value={3}
              suffix="branches"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Est. Duration"
              value="~5"
              suffix="min"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Current Stage Info */}
      {isSimulating && (
        <Alert
          message={`Currently Simulating: ${stageNames[activeStage]}`}
          description="Watch the flowchart below as the workflow progresses through each stage."
          type="info"
          showIcon
          closable
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Flowchart */}
      <Card
        title={
          <Space>
            <Text strong>Workflow Flowchart</Text>
            <Tag color="blue">Interactive</Tag>
            <Tag color="green">Real-time</Tag>
          </Space>
        }
        extra={
          <Space>
            <Button size="small" icon={<ZoomInOutlined />}>Zoom In</Button>
            <Button size="small" icon={<ZoomOutOutlined />}>Zoom Out</Button>
            <Button size="small" icon={<FullscreenOutlined />}>Fullscreen</Button>
          </Space>
        }
      >
        <WorkflowFlowchart activeStage={activeStage} />
      </Card>

      {/* Legend */}
      <Card title="Legend" style={{ marginTop: '24px' }} size="small">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <div style={{ width: 20, height: 20, backgroundColor: '#52c41a', border: '2px solid #52c41a' }} />
              <Text>Completed</Text>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <div style={{ width: 20, height: 20, backgroundColor: '#e6f7ff', border: '2px solid #1890ff' }} />
              <Text>Active/Running</Text>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <div style={{ width: 20, height: 20, backgroundColor: 'white', border: '2px solid #d9d9d9' }} />
              <Text>Pending</Text>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <div style={{ width: 20, height: 20, backgroundColor: 'white', border: '2px solid #ff4d4f' }} />
              <Text>Error/Failed</Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Workflow Details */}
      <Card title="Workflow Stages Details" style={{ marginTop: '24px' }}>
        <Tabs
          defaultActiveKey="1"
          items={[
            {
              key: '1',
              label: 'Detection & Analysis',
              children: (
                <div>
                  <Paragraph>
                    <Text strong>1. Code Change Detection:</Text> VCS webhooks trigger the workflow when code changes are detected.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>2. AI Code Analysis:</Text> Large Language Models analyze code changes to understand impact and complexity.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>3. Test Generation:</Text> AI generates comprehensive test cases covering normal usage, edge cases, and error conditions.
                  </Paragraph>
                </div>
              ),
            },
            {
              key: '2',
              label: 'Planning & Allocation',
              children: (
                <div>
                  <Paragraph>
                    <Text strong>4. Test Plan Creation:</Text> Organize generated tests into executable test plans.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>5. Hardware Allocation:</Text> Reserve physical boards or virtual environments for testing.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>6. Hardware Assignment:</Text> Link allocated hardware resources to test plans.
                  </Paragraph>
                </div>
              ),
            },
            {
              key: '3',
              label: 'Build & Deploy',
              children: (
                <div>
                  <Paragraph>
                    <Text strong>7. Identify Architecture:</Text> Detect target platform (x86_64, ARM64, RISC-V).
                  </Paragraph>
                  <Paragraph>
                    <Text strong>8. Compile Tests:</Text> Cross-compile test cases and kernel modules for target architecture.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>9. Verify Artifacts:</Text> Validate compiled binaries, checksums, and dependencies.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>10-12. Deployment:</Text> Transfer artifacts, install dependencies, and verify deployment readiness.
                  </Paragraph>
                </div>
              ),
            },
            {
              key: '4',
              label: 'Execution & Analysis',
              children: (
                <div>
                  <Paragraph>
                    <Text strong>13-14. Test Execution:</Text> Run tests on hardware and collect results, logs, and metrics.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>15-17. Parallel Analysis:</Text> AI failure analysis, coverage analysis, and performance analysis run concurrently.
                  </Paragraph>
                  <Paragraph>
                    <Text strong>18-20. Reporting:</Text> Create defects, generate summaries, and send notifications.
                  </Paragraph>
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Key Features */}
      <Card title="Key Workflow Features" style={{ marginTop: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Title level={5}>Parallel Execution</Title>
            <Paragraph>
              The workflow supports parallel execution at the analysis stage, where AI failure analysis, 
              coverage analysis, and performance analysis run simultaneously to reduce total execution time.
            </Paragraph>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5}>Build & Compilation</Title>
            <Paragraph>
              A dedicated build stage cross-compiles test cases for target architectures (x86_64, ARM64, RISC-V), 
              ensuring tests can run on diverse hardware platforms.
            </Paragraph>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5}>Hardware Flexibility</Title>
            <Paragraph>
              Tests can execute on both physical hardware boards and virtual environments (QEMU, KVM), 
              providing flexibility for different testing scenarios.
            </Paragraph>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5}>AI-Powered Intelligence</Title>
            <Paragraph>
              Multiple stages leverage AI/LLM capabilities including code analysis, test generation, 
              and failure root cause analysis for intelligent automation.
            </Paragraph>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default WorkflowFlowchartPage;
