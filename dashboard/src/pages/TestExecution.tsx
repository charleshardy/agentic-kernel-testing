import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Row,
  Col,
  message,
} from 'antd'
import {
  PlusOutlined,
  RobotOutlined,
  CodeOutlined,
  FunctionOutlined,
} from '@ant-design/icons'
import { useMutation, useQueryClient, useQuery } from 'react-query'
import { useDashboardStore } from '../store'
import apiService from '../services/api'
import useAIGeneration from '../hooks/useAIGeneration'
import DiagnosticWrapper from '../components/DiagnosticWrapper'
import RealTimeExecutionMonitor from '../components/RealTimeExecutionMonitor'
import DirectAPITest from '../components/DirectAPITest'

const { Title } = Typography
const { TextArea } = Input

interface TestExecutionProps {}

const TestExecution: React.FC<TestExecutionProps> = () => {
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(false)
  const [isAutoGenModalVisible, setIsAutoGenModalVisible] = useState(false)
  const [autoGenType, setAutoGenType] = useState<'diff' | 'function'>('diff')
  const [form] = Form.useForm()
  const [autoGenForm] = Form.useForm()
  const queryClient = useQueryClient()

  // Fetch environments for the form
  const { data: environments } = useQuery(
    'environments',
    () => apiService.getEnvironments(),
    {
      onError: (error) => {
        console.log('Failed to fetch environments:', error)
      }
    }
  )

  // AI Generation hook with custom handlers
  const { generateFromDiff, generateFromFunction, isGenerating } = useAIGeneration({
    onSuccess: (response, type) => {
      setIsAutoGenModalVisible(false)
      autoGenForm.resetFields()
      message.success(`Successfully generated tests from ${type}`)
    },
    preserveFilters: true,
    enableOptimisticUpdates: false,
  })

  // Submit new tests mutation
  const submitTestsMutation = useMutation(
    (testData: any) => apiService.submitTests([testData]),
    {
      onSuccess: () => {
        message.success('Tests submitted successfully')
        setIsSubmitModalVisible(false)
        form.resetFields()
        queryClient.invalidateQueries('activeExecutions')
      },
      onError: (error: any) => {
        message.error(`Failed to submit tests: ${error.message}`)
      },
    }
  )

  const handleViewExecution = (planId: string) => {
    // Navigate to detailed execution view or show modal
    message.info(`Viewing execution details for ${planId}`)
    // TODO: Implement detailed execution view
  }

  const handleSubmitTest = (values: any) => {
    console.log('Submitting test with values:', values)
    const testData = {
      name: values.name,
      description: values.description,
      test_type: values.test_type,
      target_subsystem: values.subsystem,
      test_script: values.test_script,
      execution_time_estimate: parseInt(values.execution_time) || 60,
      metadata: {
        priority: values.priority || 5,
        environment_preference: values.environment,
      },
    }

    submitTestsMutation.mutate(testData)
  }



  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
    { label: 'Fuzz Test', value: 'fuzz' },
  ]

  const subsystems = [
    'kernel/core',
    'kernel/mm',
    'kernel/fs',
    'kernel/net',
    'drivers/block',
    'drivers/char',
    'drivers/net',
    'arch/x86',
    'arch/arm64',
  ]

  return (
    <DiagnosticWrapper componentName="TestExecution">
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Title level={2}>Test Execution</Title>
          <Space>
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={() => setIsAutoGenModalVisible(true)}
            >
              AI Generate Tests
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={() => setIsSubmitModalVisible(true)}
            >
              Manual Submit
            </Button>
          </Space>
        </div>

        {/* Direct API Test Component for Debugging */}
        <DirectAPITest />

        {/* Real-time Execution Monitor */}
        <RealTimeExecutionMonitor onViewExecution={handleViewExecution} />

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={isAutoGenModalVisible}
        onCancel={() => setIsAutoGenModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={autoGenType === 'diff' ? 'primary' : 'default'}
              icon={<CodeOutlined />}
              onClick={() => setAutoGenType('diff')}
            >
              From Code Diff
            </Button>
            <Button
              type={autoGenType === 'function' ? 'primary' : 'default'}
              icon={<FunctionOutlined />}
              onClick={() => setAutoGenType('function')}
            >
              From Function
            </Button>
          </Space>
        </div>

        {autoGenType === 'diff' ? (
          <Form
            form={autoGenForm}
            layout="vertical"
            onFinish={(values) => {
              generateFromDiff({
                diff: values.diff,
                maxTests: values.maxTests || 20,
                testTypes: values.testTypes || ['unit']
              })
            }}
          >
            <Form.Item
              name="diff"
              label="Code Diff"
              rules={[{ required: true, message: 'Please paste your git diff' }]}
            >
              <TextArea
                rows={8}
                placeholder="Paste your git diff here..."
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="maxTests"
                  label="Max Tests to Generate"
                  initialValue={20}
                >
                  <Input type="number" min={1} max={100} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="testTypes"
                  label="Test Types"
                  initialValue={['unit']}
                >
                  <Select
                    mode="multiple"
                    placeholder="Select test types"
                    options={testTypes}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setIsAutoGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        ) : (
          <Form
            form={autoGenForm}
            layout="vertical"
            onFinish={(values) => {
              console.log('AI Generation form values:', values)
              generateFromFunction({
                functionName: values.functionName,
                filePath: values.filePath,
                subsystem: values.subsystem || 'unknown',
                maxTests: values.maxTests || 10
              })
            }}
          >
            <Form.Item
              name="functionName"
              label="Function Name"
              rules={[{ required: true, message: 'Please enter function name' }]}
            >
              <Input placeholder="e.g., schedule_task" />
            </Form.Item>

            <Form.Item
              name="filePath"
              label="File Path"
              rules={[{ required: true, message: 'Please enter file path' }]}
            >
              <Input placeholder="e.g., kernel/sched/core.c" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="subsystem"
                  label="Subsystem"
                  rules={[{ required: true, message: 'Please select a subsystem' }]}
                >
                  <Select
                    placeholder="Select subsystem"
                    options={subsystems.map(s => ({ label: s, value: s }))}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="maxTests"
                  label="Max Tests to Generate"
                  initialValue={10}
                >
                  <Input type="number" min={1} max={50} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setIsAutoGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Tests
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Submit Test Modal */}
      <Modal
        title="Submit New Test"
        open={isSubmitModalVisible}
        onCancel={() => setIsSubmitModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitTest}
        >
          <Form.Item
            name="name"
            label="Test Name"
            rules={[{ required: true, message: 'Please enter test name' }]}
          >
            <Input placeholder="Enter test name" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={3} placeholder="Describe what this test does" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="test_type"
                label="Test Type"
                rules={[{ required: true, message: 'Please select test type' }]}
              >
                <Select placeholder="Select test type" options={testTypes} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="subsystem"
                label="Target Subsystem"
                rules={[{ required: true, message: 'Please select subsystem' }]}
              >
                <Select
                  placeholder="Select subsystem"
                  options={subsystems.map(s => ({ label: s, value: s }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="test_script"
            label="Test Script"
            rules={[{ required: true, message: 'Please enter test script' }]}
          >
            <TextArea
              rows={6}
              placeholder="#!/bin/bash&#10;# Enter your test script here"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="execution_time"
                label="Estimated Time (seconds)"
              >
                <Input type="number" placeholder="60" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="Priority"
              >
                <Select
                  placeholder="Select priority"
                  options={[
                    { label: 'Low (1)', value: 1 },
                    { label: 'Normal (5)', value: 5 },
                    { label: 'High (8)', value: 8 },
                    { label: 'Critical (10)', value: 10 },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="environment"
            label="Preferred Environment"
          >
            <Select
              placeholder="Any available environment"
              options={Array.isArray(environments) ? environments.map(env => ({
                label: `${env.config?.architecture} - ${env.config?.cpu_model}`,
                value: env.id,
              })) : []}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsSubmitModalVisible(false)}>
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={submitTestsMutation.isLoading}
              >
                Submit Test
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
      </div>
    </DiagnosticWrapper>
  )
}

export default TestExecution