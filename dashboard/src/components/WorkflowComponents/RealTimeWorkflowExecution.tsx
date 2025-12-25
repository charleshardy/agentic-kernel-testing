import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Alert,
  Progress,
  Timeline,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Divider,
  Statistic,
  List,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  CodeOutlined,
  RobotOutlined,
  ExperimentOutlined,
  MonitorOutlined,
  BarChartOutlined,
  BellOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation } from 'react-query'
import apiService from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface WorkflowExecutionProps {
  onWorkflowComplete?: (results: any) => void
}

interface ExecutionStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
  duration?: number
  output?: string
  error?: string
}

interface WorkflowExecution {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  steps: ExecutionStep[]
  startTime: string
  endTime?: string
  totalDuration?: number
  metadata?: Record<string, any>
}

const RealTimeWorkflowExecution: React.FC<WorkflowExecutionProps> = ({
  onWorkflowComplete
}) => {
  const [currentExecution, setCurrentExecution] = useState<WorkflowExecution | null>(null)
  const [executionModalVisible, setExecutionModalVisible] = useState(false)
  const [newExecutionForm] = Form.useForm()

  // Fetch active workflow executions
  const { data: activeExecutions, refetch: refetchExecutions } = useQuery(
    'workflowExecutions',
    () => apiService.getActiveExecutions(),
    {
      refetchInterval: 2000, // Poll every 2 seconds
      onError: (error) => {
        console.log('Workflow executions not available:', error)
      },
      retry: false,
    }
  )

  // Start new workflow execution
  const startWorkflowMutation = useMutation(
    (params: { codeChange?: string; testTypes?: string[]; priority?: string }) => 
      apiService.submitTestGeneration({
        code_change: params.codeChange || 'demo-change',
        test_types: params.testTypes || ['unit', 'integration'],
        priority: params.priority || 'medium',
      }),
    {
      onSuccess: (data) => {
        message.success('Workflow execution started successfully')
        setExecutionModalVisible(false)
        newExecutionForm.resetFields()
        refetchExecutions()
        
        // Create mock execution for demo
        const mockExecution: WorkflowExecution = {
          id: data.submission_id || `exec-${Date.now()}`,
          status: 'running',
          startTime: new Date().toISOString(),
          steps: [
            { id: 'code-analysis', name: 'Code Analysis', status: 'running' },
            { id: 'ai-generation', name: 'AI Test Generation', status: 'pending' },
            { id: 'test-execution', name: 'Test Execution', status: 'pending' },
            { id: 'result-analysis', name: 'Result Analysis', status: 'pending' },
          ],
        }
        setCurrentExecution(mockExecution)
        simulateWorkflowExecution(mockExecution)
      },
      onError: (error) => {
        console.error('Failed to start workflow:', error)
        message.error('Failed to start workflow execution')
      },
    }
  )

  // Cancel workflow execution
  const cancelWorkflowMutation = useMutation(
    (executionId: string) => apiService.cancelExecution(executionId),
    {
      onSuccess: () => {
        message.success('Workflow execution cancelled')
        if (currentExecution) {
          setCurrentExecution({
            ...currentExecution,
            status: 'cancelled',
            endTime: new Date().toISOString(),
          })
        }
        refetchExecutions()
      },
      onError: (error) => {
        console.error('Failed to cancel workflow:', error)
        message.error('Failed to cancel workflow execution')
      },
    }
  )

  // Simulate workflow execution for demo purposes
  const simulateWorkflowExecution = (execution: WorkflowExecution) => {
    let currentStepIndex = 0
    
    const updateStep = (stepIndex: number, status: ExecutionStep['status'], output?: string) => {
      setCurrentExecution(prev => {
        if (!prev) return null
        
        const updatedSteps = [...prev.steps]
        updatedSteps[stepIndex] = {
          ...updatedSteps[stepIndex],
          status,
          output,
          startTime: status === 'running' ? new Date().toISOString() : updatedSteps[stepIndex].startTime,
          endTime: status === 'completed' || status === 'failed' ? new Date().toISOString() : undefined,
        }
        
        return {
          ...prev,
          steps: updatedSteps,
        }
      })
    }

    const executeNextStep = () => {
      if (currentStepIndex >= execution.steps.length) {
        // Workflow completed
        setCurrentExecution(prev => prev ? {
          ...prev,
          status: 'completed',
          endTime: new Date().toISOString(),
        } : null)
        
        if (onWorkflowComplete) {
          onWorkflowComplete({
            executionId: execution.id,
            status: 'completed',
            results: 'Mock workflow execution completed successfully',
          })
        }
        return
      }

      const step = execution.steps[currentStepIndex]
      updateStep(currentStepIndex, 'running')

      // Simulate step execution time
      const executionTime = Math.random() * 5000 + 2000 // 2-7 seconds
      
      setTimeout(() => {
        const success = Math.random() > 0.1 // 90% success rate
        
        if (success) {
          updateStep(currentStepIndex, 'completed', `${step.name} completed successfully`)
          currentStepIndex++
          setTimeout(executeNextStep, 1000) // 1 second delay between steps
        } else {
          updateStep(currentStepIndex, 'failed', `${step.name} failed with error`)
          setCurrentExecution(prev => prev ? {
            ...prev,
            status: 'failed',
            endTime: new Date().toISOString(),
          } : null)
        }
      }, executionTime)
    }

    // Start execution after a short delay
    setTimeout(executeNextStep, 1000)
  }

  const startNewWorkflow = () => {
    setExecutionModalVisible(true)
  }

  const handleStartExecution = (values: any) => {
    startWorkflowMutation.mutate({
      codeChange: values.codeChange,
      testTypes: values.testTypes,
      priority: values.priority,
    })
  }

  const getStepIcon = (status: ExecutionStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <div style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#d9d9d9' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green'
      case 'running': return 'blue'
      case 'failed': return 'red'
      case 'cancelled': return 'orange'
      default: return 'default'
    }
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <MonitorOutlined />
            <span>Real-Time Workflow Execution</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={startNewWorkflow}
              disabled={currentExecution?.status === 'running'}
            >
              Start New Workflow
            </Button>
            {currentExecution?.status === 'running' && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={() => cancelWorkflowMutation.mutate(currentExecution.id)}
              >
                Cancel
              </Button>
            )}
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchExecutions()}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        {currentExecution ? (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
              <Col xs={24} sm={6}>
                <Statistic
                  title="Execution ID"
                  value={currentExecution.id.slice(0, 8)}
                  prefix={<MonitorOutlined />}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="Status"
                  value={currentExecution.status.toUpperCase()}
                  valueStyle={{ color: getStatusColor(currentExecution.status) === 'green' ? '#52c41a' : 
                                      getStatusColor(currentExecution.status) === 'blue' ? '#1890ff' :
                                      getStatusColor(currentExecution.status) === 'red' ? '#ff4d4f' : '#faad14' }}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="Progress"
                  value={Math.round((currentExecution.steps.filter(s => s.status === 'completed').length / currentExecution.steps.length) * 100)}
                  suffix="%"
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="Duration"
                  value={Math.round((new Date().getTime() - new Date(currentExecution.startTime).getTime()) / 1000)}
                  suffix="s"
                />
              </Col>
            </Row>

            <Progress
              percent={Math.round((currentExecution.steps.filter(s => s.status === 'completed').length / currentExecution.steps.length) * 100)}
              status={currentExecution.status === 'failed' ? 'exception' : 
                     currentExecution.status === 'running' ? 'active' : 'normal'}
              style={{ marginBottom: '16px' }}
            />

            <Timeline>
              {currentExecution.steps.map((step, index) => (
                <Timeline.Item
                  key={step.id}
                  dot={getStepIcon(step.status)}
                  color={
                    step.status === 'completed' ? 'green' :
                    step.status === 'running' ? 'blue' :
                    step.status === 'failed' ? 'red' : 'gray'
                  }
                >
                  <div>
                    <Space>
                      <Text strong>{step.name}</Text>
                      <Tag color={getStatusColor(step.status)}>
                        {step.status.toUpperCase()}
                      </Tag>
                    </Space>
                    {step.output && (
                      <div style={{ marginTop: '4px' }}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {step.output}
                        </Text>
                      </div>
                    )}
                    {step.error && (
                      <div style={{ marginTop: '4px' }}>
                        <Text type="danger" style={{ fontSize: '12px' }}>
                          Error: {step.error}
                        </Text>
                      </div>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <MonitorOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
            <Title level={4} type="secondary">No Active Workflow Execution</Title>
            <Paragraph type="secondary">
              Start a new workflow execution to see real-time progress and step-by-step execution details.
            </Paragraph>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={startNewWorkflow}>
              Start New Workflow
            </Button>
          </div>
        )}

        {activeExecutions && activeExecutions.length > 0 && (
          <div style={{ marginTop: '24px' }}>
            <Divider orientation="left">Recent Executions</Divider>
            <List
              size="small"
              dataSource={activeExecutions.slice(0, 5)}
              renderItem={(execution) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text>{execution.plan_id.slice(0, 12)}...</Text>
                        <Tag color={getStatusColor(execution.overall_status)}>
                          {execution.overall_status}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary">
                          {execution.completed_tests}/{execution.total_tests} tests
                        </Text>
                        <Progress 
                          percent={Math.round(execution.progress * 100)} 
                          size="small" 
                          showInfo={false}
                        />
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Card>

      {/* New Workflow Execution Modal */}
      <Modal
        title="Start New Workflow Execution"
        open={executionModalVisible}
        onCancel={() => setExecutionModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={newExecutionForm}
          layout="vertical"
          onFinish={handleStartExecution}
        >
          <Form.Item
            name="codeChange"
            label="Code Change Description"
            rules={[{ required: true, message: 'Please describe the code change' }]}
          >
            <TextArea
              rows={4}
              placeholder="Describe the code changes that triggered this workflow..."
            />
          </Form.Item>

          <Form.Item
            name="testTypes"
            label="Test Types"
            initialValue={['unit', 'integration']}
          >
            <Select
              mode="multiple"
              placeholder="Select test types to generate"
              options={[
                { label: 'Unit Tests', value: 'unit' },
                { label: 'Integration Tests', value: 'integration' },
                { label: 'Performance Tests', value: 'performance' },
                { label: 'Security Tests', value: 'security' },
                { label: 'Fuzz Tests', value: 'fuzz' },
              ]}
            />
          </Form.Item>

          <Form.Item
            name="priority"
            label="Priority"
            initialValue="medium"
          >
            <Select
              placeholder="Select execution priority"
              options={[
                { label: 'Low', value: 'low' },
                { label: 'Medium', value: 'medium' },
                { label: 'High', value: 'high' },
                { label: 'Critical', value: 'critical' },
              ]}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={startWorkflowMutation.isLoading}>
                Start Execution
              </Button>
              <Button onClick={() => setExecutionModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RealTimeWorkflowExecution