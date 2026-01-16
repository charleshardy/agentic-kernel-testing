import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tag,
  Modal,
  Descriptions,
  Progress,
  Alert,
  Tooltip,
  Badge,
  Divider,
  Steps,
  Timeline,
  Tabs,
  List,
  Statistic,
  Drawer,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  WarningOutlined,
  RobotOutlined,
  CodeOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  BugOutlined,
  LineChartOutlined,
  SettingOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  ApiOutlined,
  MonitorOutlined,
  BellOutlined,
  FullscreenOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService from '../services/api'
import InteractiveWorkflowNode from '../components/WorkflowComponents/InteractiveWorkflowNode'
import RealTimeWorkflowExecution from '../components/WorkflowComponents/RealTimeWorkflowExecution'
import WorkflowSystemStatus from '../components/WorkflowComponents/WorkflowSystemStatus'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface WorkflowStep {
  id: string
  title: string
  description: string
  status: 'waiting' | 'process' | 'finish' | 'error'
  icon: React.ReactNode
  details?: string
  duration?: number
  progress?: number
  subSteps?: WorkflowStep[]
}

interface WorkflowPhase {
  id: string
  title: string
  description: string
  steps: WorkflowStep[]
  color: string
  icon: React.ReactNode
}

const WorkflowDiagram: React.FC = () => {
  console.log('🤖 WorkflowDiagram component is rendering!')
  
  // Add error boundary
  try {
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [activePhase, setActivePhase] = useState<string>('system-status')
  const [simulationRunning, setSimulationRunning] = useState(false)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [executionDrawerVisible, setExecutionDrawerVisible] = useState(false)
  const [fullScreenMode, setFullScreenMode] = useState(false)

  // Fetch real system status
  const { data: healthData } = useQuery(
    'workflowHealth',
    () => apiService.getHealth(),
    {
      refetchInterval: 5000,
      retry: false,
    }
  )

  // Define the complete workflow phases
  const workflowPhases: WorkflowPhase[] = [
    {
      id: 'detection',
      title: 'Code Change Detection',
      description: 'Monitor and analyze code changes from version control systems',
      color: '#1890ff',
      icon: <CodeOutlined />,
      steps: [
        {
          id: 'vcs-webhook',
          title: 'VCS Webhook Trigger',
          description: 'Receive webhook from GitHub/GitLab on commit/PR',
          status: 'finish',
          icon: <ApiOutlined />,
          details: 'Monitors GitHub, GitLab, and other VCS platforms for code changes',
          duration: 0.5,
        },
        {
          id: 'diff-analysis',
          title: 'Git Diff Analysis',
          description: 'Parse code changes to identify modified files and functions',
          status: 'finish',
          icon: <CodeOutlined />,
          details: 'Extracts changed files, functions, and calculates impact scores',
          duration: 2.0,
        },
        {
          id: 'ast-analysis',
          title: 'AST Code Analysis',
          description: 'Analyze code structure using Abstract Syntax Tree',
          status: 'process',
          icon: <BugOutlined />,
          details: 'Deep code analysis to understand structural changes and dependencies',
          duration: 3.5,
          progress: 65,
        },
      ],
    },
    {
      id: 'ai-analysis',
      title: 'AI-Powered Analysis',
      description: 'Use Large Language Models to understand code changes and assess impact',
      color: '#52c41a',
      icon: <RobotOutlined />,
      steps: [
        {
          id: 'llm-understanding',
          title: 'LLM Code Understanding',
          description: 'AI analyzes code changes using multiple LLM providers',
          status: 'waiting',
          icon: <RobotOutlined />,
          details: 'Supports Amazon Q, Kiro AI, OpenAI GPT-4, Anthropic Claude, Amazon Bedrock',
          duration: 15.0,
        },
        {
          id: 'impact-calculation',
          title: 'Impact Score Calculation',
          description: 'Calculate risk and impact scores for changes',
          status: 'waiting',
          icon: <BarChartOutlined />,
          details: 'Assigns numerical impact scores based on code complexity and criticality',
          duration: 2.0,
        },
        {
          id: 'subsystem-identification',
          title: 'Subsystem Identification',
          description: 'Identify affected kernel subsystems',
          status: 'waiting',
          icon: <SettingOutlined />,
          details: 'Maps changes to specific kernel subsystems (mm, fs, net, drivers, etc.)',
          duration: 1.5,
        },
      ],
    },
    {
      id: 'test-generation',
      title: 'Intelligent Test Generation',
      description: 'Generate comprehensive test cases using AI and property-based testing',
      color: '#faad14',
      icon: <ExperimentOutlined />,
      steps: [
        {
          id: 'ai-test-generator',
          title: 'AI Test Generator',
          description: 'Generate targeted test cases using LLMs',
          status: 'waiting',
          icon: <RobotOutlined />,
          details: 'Creates 10+ test cases per modified function within 5 minutes',
          duration: 45.0,
        },
        {
          id: 'property-tests',
          title: 'Property-Based Tests',
          description: 'Generate formal correctness properties',
          status: 'waiting',
          icon: <SafetyOutlined />,
          details: '50+ correctness properties with 100+ iterations each',
          duration: 20.0,
        },
        {
          id: 'fuzz-tests',
          title: 'Fuzz Test Generation',
          description: 'Create fuzzing strategies for security testing',
          status: 'waiting',
          icon: <BugOutlined />,
          details: 'Generates inputs for system calls, ioctl handlers, network protocols',
          duration: 10.0,
        },
      ],
    },
    {
      id: 'test-plan-management',
      title: 'Test Plan Management',
      description: 'Organize test cases into executable test plans',
      color: '#722ed1',
      icon: <DatabaseOutlined />,
      steps: [
        {
          id: 'create-test-plan',
          title: 'Create Test Plan',
          description: 'Create and configure test plan with target hardware',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Define test plan name, description, and target hardware specifications',
          duration: 2.0,
        },
        {
          id: 'add-tests-to-plan',
          title: 'Add Tests to Plan',
          description: 'Add generated test cases to the test plan',
          status: 'waiting',
          icon: <ExperimentOutlined />,
          details: 'Select and organize test cases within the test plan',
          duration: 3.0,
        },
      ],
    },
    {
      id: 'hardware-allocation',
      title: 'Hardware Allocation',
      description: 'Allocate and assign physical or virtual hardware resources',
      color: '#13c2c2',
      icon: <MonitorOutlined />,
      steps: [
        {
          id: 'allocate-hardware',
          title: 'Allocate Physical Board',
          description: 'Reserve physical hardware board for testing',
          status: 'waiting',
          icon: <MonitorOutlined />,
          details: 'Select and reserve ARM, x86, or RISC-V physical boards from hardware lab',
          duration: 5.0,
        },
        {
          id: 'assign-to-plan',
          title: 'Assign Board to Test Plan',
          description: 'Link allocated hardware to test plan',
          status: 'waiting',
          icon: <ApiOutlined />,
          details: 'Associate reserved hardware with test plan for execution',
          duration: 2.0,
        },
      ],
    },
    {
      id: 'build-compilation',
      title: 'Build & Compilation',
      description: 'Compile test cases and kernel modules for target architecture',
      color: '#fa8c16',
      icon: <CodeOutlined />,
      steps: [
        {
          id: 'identify-architecture',
          title: 'Identify Target Architecture',
          description: 'Determine target architecture from assigned hardware',
          status: 'waiting',
          icon: <SettingOutlined />,
          details: 'Extract architecture (x86_64, ARM64, RISC-V) from hardware configuration',
          duration: 1.0,
        },
        {
          id: 'compile-tests',
          title: 'Compile Test Cases',
          description: 'Build test executables on build server',
          status: 'waiting',
          icon: <CodeOutlined />,
          details: 'Cross-compile test cases and dependencies for target architecture',
          duration: 45.0,
        },
        {
          id: 'compile-kernel-modules',
          title: 'Compile Kernel Modules',
          description: 'Build kernel modules if required',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Compile kernel modules (.ko files) for kernel testing',
          duration: 30.0,
        },
        {
          id: 'verify-artifacts',
          title: 'Verify Build Artifacts',
          description: 'Validate compiled binaries and checksums',
          status: 'waiting',
          icon: <SafetyOutlined />,
          details: 'Verify binary compatibility, checksums, and dependencies',
          duration: 5.0,
        },
      ],
    },
    {
      id: 'deployment',
      title: 'Test Deployment',
      description: 'Deploy compiled artifacts to target hardware',
      color: '#eb2f96',
      icon: <CloudServerOutlined />,
      steps: [
        {
          id: 'transfer-artifacts',
          title: 'Transfer Build Artifacts',
          description: 'Copy compiled tests to target hardware',
          status: 'waiting',
          icon: <CloudServerOutlined />,
          details: 'Transfer binaries, libraries, and configuration files via SSH/SCP',
          duration: 15.0,
        },
        {
          id: 'install-dependencies',
          title: 'Install Dependencies',
          description: 'Install required libraries and tools',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Install runtime dependencies and configure environment',
          duration: 20.0,
        },
        {
          id: 'verify-deployment',
          title: 'Verify Deployment',
          description: 'Validate test environment readiness',
          status: 'waiting',
          icon: <CheckCircleOutlined />,
          details: 'Check file permissions, paths, and environment configuration',
          duration: 5.0,
        },
      ],
    },
    {
      id: 'execution',
      title: 'Test Execution',
      description: 'Execute tests on deployed hardware with real-time monitoring',
      color: '#52c41a',
      icon: <PlayCircleOutlined />,
      steps: [
        {
          id: 'start-execution',
          title: 'Start Test Execution',
          description: 'Begin running test cases on target hardware',
          status: 'waiting',
          icon: <PlayCircleOutlined />,
          details: 'Execute test plan with real-time progress monitoring',
          duration: 120.0,
        },
        {
          id: 'monitor-execution',
          title: 'Monitor Execution',
          description: 'Track test progress and capture live logs',
          status: 'waiting',
          icon: <MonitorOutlined />,
          details: 'Real-time log streaming, progress tracking, and status updates',
          duration: 120.0,
        },
        {
          id: 'collect-results',
          title: 'Collect Test Results',
          description: 'Gather test outcomes, logs, and artifacts',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Capture stdout, stderr, exit codes, core dumps, and performance metrics',
          duration: 10.0,
        },
      ],
    },
    {
      id: 'analysis',
      title: 'Result Analysis',
      description: 'Analyze test results using AI-powered insights',
      color: '#1890ff',
      icon: <BarChartOutlined />,
      steps: [
        {
          id: 'ai-failure-analysis',
          title: 'AI Failure Analysis',
          description: 'Analyze failures using LLM-powered root cause analysis',
          status: 'waiting',
          icon: <RobotOutlined />,
          details: 'AI analyzes logs, stack traces, and error patterns to identify root causes',
          duration: 25.0,
        },
        {
          id: 'coverage-analysis',
          title: 'Coverage Analysis',
          description: 'Calculate code coverage metrics',
          status: 'waiting',
          icon: <BarChartOutlined />,
          details: 'Line, branch, and function coverage with gap identification',
          duration: 15.0,
        },
        {
          id: 'performance-analysis',
          title: 'Performance Analysis',
          description: 'Analyze performance metrics and detect regressions',
          status: 'waiting',
          icon: <LineChartOutlined />,
          details: 'Compare execution times, memory usage, and throughput against baselines',
          duration: 10.0,
        },
        {
          id: 'security-analysis',
          title: 'Security Analysis',
          description: 'Scan for security vulnerabilities',
          status: 'waiting',
          icon: <SafetyOutlined />,
          details: 'Identify potential security issues, memory leaks, and race conditions',
          duration: 20.0,
        },
      ],
    },
    {
      id: 'defect-reporting',
      title: 'Defect Reporting',
      description: 'Create and track defects from test failures',
      color: '#f5222d',
      icon: <BugOutlined />,
      steps: [
        {
          id: 'create-defect',
          title: 'Create Defect Report',
          description: 'Generate defect report from failure',
          status: 'waiting',
          icon: <BugOutlined />,
          details: 'Auto-populate defect with reproduction steps, logs, and environment details',
          duration: 5.0,
        },
        {
          id: 'link-artifacts',
          title: 'Link Artifacts',
          description: 'Attach logs, core dumps, and traces to defect',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Associate all relevant artifacts with the defect for debugging',
          duration: 3.0,
        },
        {
          id: 'assign-defect',
          title: 'Assign & Notify',
          description: 'Assign defect to developer and send notifications',
          status: 'waiting',
          icon: <BellOutlined />,
          details: 'Route defect to appropriate team member and send alerts',
          duration: 2.0,
        },
      ],
    },
    {
      id: 'summary-generation',
      title: 'Summary Generation',
      description: 'Generate comprehensive test execution summary',
      color: '#faad14',
      icon: <LineChartOutlined />,
      steps: [
        {
          id: 'aggregate-results',
          title: 'Aggregate Results',
          description: 'Compile all test results and metrics',
          status: 'waiting',
          icon: <DatabaseOutlined />,
          details: 'Aggregate pass/fail statistics, coverage, performance, and security findings',
          duration: 5.0,
        },
        {
          id: 'generate-trends',
          title: 'Generate Trends',
          description: 'Compare with historical data and identify trends',
          status: 'waiting',
          icon: <LineChartOutlined />,
          details: 'Analyze trends, detect regressions, and identify flaky tests',
          duration: 10.0,
        },
        {
          id: 'create-report',
          title: 'Create Summary Report',
          description: 'Generate comprehensive test summary',
          status: 'waiting',
          icon: <BarChartOutlined />,
          details: 'Create detailed report with visualizations, recommendations, and action items',
          duration: 8.0,
        },
        {
          id: 'export-summary',
          title: 'Export Summary',
          description: 'Export summary in multiple formats',
          status: 'waiting',
          icon: <ApiOutlined />,
          details: 'Export as PDF, HTML, JSON, or send to external systems',
          duration: 3.0,
        },
      ],
    },
    {
      id: 'reporting',
      title: 'Reporting & Integration',
      description: 'Report results and integrate with development workflows',
      color: '#fa8c16',
      icon: <BellOutlined />,
      steps: [
        {
          id: 'vcs-updates',
          title: 'VCS Status Updates',
          description: 'Post results back to GitHub/GitLab',
          status: 'waiting',
          icon: <ApiOutlined />,
          details: 'Updates PR status with detailed test results and logs',
          duration: 5.0,
        },
        {
          id: 'notifications',
          title: 'Developer Notifications',
          description: 'Send notifications via multiple channels',
          status: 'waiting',
          icon: <BellOutlined />,
          details: 'Email, Slack, Teams notifications for critical issues',
          duration: 2.0,
        },
        {
          id: 'dashboard-updates',
          title: 'Dashboard Updates',
          description: 'Update real-time web dashboard',
          status: 'waiting',
          icon: <MonitorOutlined />,
          details: 'Real-time updates with visualizations and metrics',
          duration: 1.0,
        },
      ],
    },
  ]

  // Simulation function
  const runWorkflowSimulation = () => {
    setSimulationRunning(true)
    setCurrentStepIndex(0)
    
    const allSteps = workflowPhases.flatMap(phase => phase.steps)
    
    const simulateStep = (index: number) => {
      if (index >= allSteps.length) {
        setSimulationRunning(false)
        return
      }
      
      // Update step status to process
      allSteps[index].status = 'process'
      allSteps[index].progress = 0
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        if (allSteps[index].progress !== undefined && allSteps[index].progress < 100) {
          allSteps[index].progress += 10
        } else {
          clearInterval(progressInterval)
          allSteps[index].status = 'finish'
          allSteps[index].progress = 100
          
          // Move to next step after a delay
          setTimeout(() => {
            setCurrentStepIndex(index + 1)
            simulateStep(index + 1)
          }, 500)
        }
      }, 200)
    }
    
    simulateStep(0)
  }

  const resetWorkflow = () => {
    workflowPhases.forEach(phase => {
      phase.steps.forEach(step => {
        step.status = 'waiting'
        step.progress = 0
      })
    })
    // Set first few steps as completed for demo
    workflowPhases[0].steps[0].status = 'finish'
    workflowPhases[0].steps[1].status = 'finish'
    setCurrentStepIndex(0)
    setSimulationRunning(false)
  }

  const showStepDetails = (step: WorkflowStep) => {
    setSelectedStep(step)
    setModalVisible(true)
  }

  const getStepStatusIcon = (status: string, progress?: number) => {
    switch (status) {
      case 'finish':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'process':
        return progress !== undefined ? 
          <LoadingOutlined style={{ color: '#1890ff' }} /> : 
          <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getPhaseProgress = (phase: WorkflowPhase) => {
    const completedSteps = phase.steps.filter(step => step.status === 'finish').length
    return Math.round((completedSteps / phase.steps.length) * 100)
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <RobotOutlined style={{ marginRight: '8px' }} />
          Complete End-to-End Testing Workflow
        </Title>
        <Paragraph>
          Interactive visualization of the complete testing workflow from AI-powered test generation 
          through hardware allocation, compilation, deployment, execution, analysis, defect reporting, 
          and summary generation. Click on any stage to explore details and interact with the workflow.
        </Paragraph>
        
        <Space style={{ marginBottom: '16px' }}>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={runWorkflowSimulation}
            disabled={simulationRunning}
            loading={simulationRunning}
          >
            {simulationRunning ? 'Running Simulation' : 'Run Workflow Simulation'}
          </Button>
          <Button 
            icon={<ReloadOutlined />}
            onClick={resetWorkflow}
            disabled={simulationRunning}
          >
            Reset Workflow
          </Button>
          <Button 
            icon={<MonitorOutlined />}
            onClick={() => setExecutionDrawerVisible(true)}
          >
            Real-Time Execution
          </Button>
          <Button 
            icon={<FullscreenOutlined />}
            onClick={() => setFullScreenMode(!fullScreenMode)}
          >
            {fullScreenMode ? 'Exit Fullscreen' : 'Fullscreen View'}
          </Button>
          <Button 
            icon={<InfoCircleOutlined />}
            onClick={() => {
              Modal.info({
                title: 'Workflow Information',
                width: 600,
                content: (
                  <div>
                    <Paragraph>
                      This workflow represents the complete end-to-end testing process:
                    </Paragraph>
                    <ul>
                      <li><strong>11 Major Phases:</strong> From test generation to summary reporting</li>
                      <li><strong>40+ Individual Steps:</strong> Each with specific functions and interactions</li>
                      <li><strong>AI-Powered Generation:</strong> Automated test case creation from code analysis</li>
                      <li><strong>Hardware Management:</strong> Physical and virtual environment allocation</li>
                      <li><strong>Build & Compilation:</strong> Cross-platform test compilation for target architectures</li>
                      <li><strong>Deployment & Execution:</strong> Automated deployment and real-time execution monitoring</li>
                      <li><strong>Intelligent Analysis:</strong> AI-powered failure analysis and root cause identification</li>
                      <li><strong>Defect Tracking:</strong> Automated defect creation with full context</li>
                      <li><strong>Comprehensive Reporting:</strong> Detailed summaries with trends and recommendations</li>
                    </ul>
                  </div>
                ),
              })
            }}
          >
            About Workflow
          </Button>
        </Space>

        {healthData && (
          <Alert
            message="System Status: Connected"
            description={`Backend API is healthy. Uptime: ${Math.round((healthData.uptime || 0) / 60)} minutes. All components operational.`}
            type="success"
            showIcon
            closable
            style={{ marginBottom: '16px' }}
          />
        )}
      </div>

      {/* Workflow Overview Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={6}>
              <Card size="small">
                <Statistic
                  title="Total Phases"
                  value={workflowPhases.length}
                  prefix={<SettingOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small">
                <Statistic
                  title="Total Steps"
                  value={workflowPhases.reduce((acc, phase) => acc + phase.steps.length, 0)}
                  prefix={<ExperimentOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small">
                <Statistic
                  title="Completed Steps"
                  value={workflowPhases.reduce((acc, phase) => 
                    acc + phase.steps.filter(step => step.status === 'finish').length, 0
                  )}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small">
                <Statistic
                  title="Overall Progress"
                  value={Math.round(
                    (workflowPhases.reduce((acc, phase) => 
                      acc + phase.steps.filter(step => step.status === 'finish').length, 0
                    ) / workflowPhases.reduce((acc, phase) => acc + phase.steps.length, 0)) * 100
                  )}
                  suffix="%"
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>
        </Col>
        <Col xs={24} lg={8}>
          <Card size="small" title="System Status" style={{ height: '100%' }}>
            {healthData ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>API Status:</Text>
                  <Badge status="success" text="Connected" />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>Uptime:</Text>
                  <Text>{Math.round((healthData.uptime || 0) / 60)} min</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>Components:</Text>
                  <Text>{Object.keys(healthData.components || {}).length} active</Text>
                </div>
              </Space>
            ) : (
              <Alert
                message="Backend Offline"
                description="Demo mode active"
                type="warning"
                showIcon
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Workflow Phases */}
      <div style={fullScreenMode ? { 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0, 
        backgroundColor: 'white', 
        zIndex: 1000, 
        padding: '24px',
        overflow: 'auto'
      } : {}}>
        <Tabs 
          activeKey={activePhase} 
          onChange={setActivePhase} 
          type="card"
          items={[
            // System Status Tab
            {
              key: 'system-status',
              label: (
                <Space>
                  <MonitorOutlined />
                  <span>System Status</span>
                  <Badge 
                    status={healthData ? 'success' : 'warning'}
                    text={healthData ? 'Online' : 'Offline'}
                  />
                </Space>
              ),
              children: <WorkflowSystemStatus />
            },
            // Workflow Phase Tabs
            ...workflowPhases.map((phase) => ({
              key: phase.id,
              label: (
                <Space>
                  {phase.icon}
                  <span>{phase.title}</span>
                  <Badge 
                    count={`${getPhaseProgress(phase)}%`} 
                    style={{ backgroundColor: phase.color }}
                  />
                </Space>
              ),
              children: (
                <Card 
                  title={
                    <Space>
                      {phase.icon}
                      <span>{phase.title}</span>
                      <Tag color={phase.color}>
                        {phase.steps.filter(s => s.status === 'finish').length}/{phase.steps.length} Complete
                      </Tag>
                    </Space>
                  }
                  extra={
                    <Progress 
                      percent={getPhaseProgress(phase)} 
                      size="small" 
                      strokeColor={phase.color}
                    />
                  }
                >
                  <Paragraph style={{ marginBottom: '16px' }}>
                    {phase.description}
                  </Paragraph>
                  
                  {/* Interactive Workflow Nodes Grid */}
                  <Row gutter={[16, 16]}>
                    {phase.steps.map((step, index) => (
                      <Col xs={24} sm={12} lg={8} key={step.id}>
                        <InteractiveWorkflowNode
                          id={step.id}
                          title={step.title}
                          description={step.description}
                          status={step.status}
                          icon={step.icon}
                          color={phase.color}
                          progress={step.progress}
                          duration={step.duration}
                          details={step.details}
                          isExecutable={step.status === 'waiting'}
                          onExecute={() => {
                            // Simulate step execution
                            const updatedSteps = [...phase.steps]
                            updatedSteps[index] = { ...step, status: 'process', progress: 0 }
                            
                            // Simulate progress
                            let progress = 0
                            const interval = setInterval(() => {
                              progress += 10
                              updatedSteps[index].progress = progress
                              
                              if (progress >= 100) {
                                clearInterval(interval)
                                updatedSteps[index].status = 'finish'
                                updatedSteps[index].progress = 100
                              }
                            }, 200)
                          }}
                          onViewDetails={() => showStepDetails(step)}
                        />
                      </Col>
                    ))}
                  </Row>
                </Card>
              )
            }))
          ]}
        />
      </div>

      {/* Step Details Modal */}
      <Modal
        title={
          <Space>
            {selectedStep?.icon}
            <span>{selectedStep?.title}</span>
            <Tag color={
              selectedStep?.status === 'finish' ? 'green' :
              selectedStep?.status === 'process' ? 'blue' :
              selectedStep?.status === 'error' ? 'red' : 'default'
            }>
              {selectedStep?.status}
            </Tag>
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>
        ]}
        width={600}
      >
        {selectedStep && (
          <div>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Description">
                {selectedStep.description}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Space>
                  {getStepStatusIcon(selectedStep.status, selectedStep.progress)}
                  <span style={{ textTransform: 'capitalize' }}>{selectedStep.status}</span>
                </Space>
              </Descriptions.Item>
              {selectedStep.duration && (
                <Descriptions.Item label="Estimated Duration">
                  {selectedStep.duration} seconds
                </Descriptions.Item>
              )}
              {selectedStep.progress !== undefined && (
                <Descriptions.Item label="Progress">
                  <Progress percent={selectedStep.progress} size="small" />
                </Descriptions.Item>
              )}
              {selectedStep.details && (
                <Descriptions.Item label="Details">
                  {selectedStep.details}
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedStep.subSteps && selectedStep.subSteps.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <Title level={5}>Sub-steps:</Title>
                <List
                  size="small"
                  dataSource={selectedStep.subSteps}
                  renderItem={(subStep) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={getStepStatusIcon(subStep.status)}
                        title={subStep.title}
                        description={subStep.description}
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Technology Stack Information */}
      <Card 
        title="Technology Stack & Capabilities" 
        style={{ marginTop: '24px' }}
        size="small"
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card size="small" title="AI/ML Providers">
              <List size="small">
                <List.Item>
                  <Badge color="blue" text="Amazon Q Developer Pro" />
                </List.Item>
                <List.Item>
                  <Badge color="green" text="Kiro AI" />
                </List.Item>
                <List.Item>
                  <Badge color="orange" text="OpenAI GPT-4" />
                </List.Item>
                <List.Item>
                  <Badge color="purple" text="Anthropic Claude" />
                </List.Item>
                <List.Item>
                  <Badge color="gold" text="Amazon Bedrock" />
                </List.Item>
              </List>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="Testing Capabilities">
              <List size="small">
                <List.Item>
                  <Badge color="cyan" text="Property-Based Testing (50+ properties)" />
                </List.Item>
                <List.Item>
                  <Badge color="lime" text="Syzkaller Kernel Fuzzing" />
                </List.Item>
                <List.Item>
                  <Badge color="magenta" text="Multi-Architecture Support" />
                </List.Item>
                <List.Item>
                  <Badge color="volcano" text="Performance Benchmarking" />
                </List.Item>
                <List.Item>
                  <Badge color="geekblue" text="Security Vulnerability Detection" />
                </List.Item>
              </List>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="Integration & Deployment">
              <List size="small">
                <List.Item>
                  <Badge color="blue" text="GitHub/GitLab CI/CD" />
                </List.Item>
                <List.Item>
                  <Badge color="green" text="Docker Containerization" />
                </List.Item>
                <List.Item>
                  <Badge color="purple" text="Kubernetes Orchestration" />
                </List.Item>
                <List.Item>
                  <Badge color="orange" text="AWS SSO Authentication" />
                </List.Item>
                <List.Item>
                  <Badge color="red" text="Real-time Notifications" />
                </List.Item>
              </List>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Real-Time Execution Drawer */}
      <Drawer
        title="Real-Time Workflow Execution"
        placement="right"
        width={800}
        open={executionDrawerVisible}
        onClose={() => setExecutionDrawerVisible(false)}
        extra={
          <Button 
            icon={<FullscreenOutlined />}
            onClick={() => {
              setExecutionDrawerVisible(false)
              // Open in new tab or modal for full screen experience
              Modal.info({
                title: 'Real-Time Execution',
                width: '90%',
                style: { top: 20 },
                content: <RealTimeWorkflowExecution />,
                footer: null,
              })
            }}
          >
            Fullscreen
          </Button>
        }
      >
        <RealTimeWorkflowExecution 
          onWorkflowComplete={(results) => {
            console.log('Workflow completed:', results)
            // Handle workflow completion
          }}
        />
      </Drawer>
    </div>
  )
  } catch (error) {
    console.error('❌ WorkflowDiagram component error:', error)
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Workflow Diagram Error"
          description={`There was an error loading the workflow diagram: ${error}`}
          type="error"
          showIcon
        />
        <Button 
          type="primary" 
          onClick={() => window.location.reload()}
          style={{ marginTop: '16px' }}
        >
          Reload Page
        </Button>
      </div>
    )
  }
}

export default WorkflowDiagram