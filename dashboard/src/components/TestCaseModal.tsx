import React, { useState, useEffect } from 'react'
import {
  Modal,
  Tabs,
  Form,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Divider,
  Tag,
  Alert,
  Row,
  Col,
  Card,
  Descriptions,
  Badge,
  message,
} from 'antd'
import {
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  CodeOutlined,
  InfoCircleOutlined,
  RobotOutlined,
  UserOutlined,
  FunctionOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { TestCase } from '../services/api'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs

interface TestCaseModalProps {
  testCase: TestCase | null
  visible: boolean
  mode: 'view' | 'edit'
  onClose: () => void
  onSave: (testCase: TestCase) => void
  onModeChange: (mode: 'view' | 'edit') => void
}

const TestCaseModal: React.FC<TestCaseModalProps> = ({
  testCase,
  visible,
  mode,
  onClose,
  onSave,
  onModeChange,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('details')

  // Initialize form when testCase changes
  useEffect(() => {
    if (testCase && visible) {
      form.setFieldsValue({
        name: testCase.name,
        description: testCase.description,
        test_type: testCase.test_type,
        target_subsystem: testCase.target_subsystem,
        execution_time_estimate: testCase.execution_time_estimate,
        test_script: testCase.test_script,
      })
    }
  }, [testCase, visible, form])

  const handleSave = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()
      
      // Additional validation for test script
      if (values.test_script) {
        const scriptLength = values.test_script.trim().length
        if (scriptLength < 10) {
          form.setFields([{
            name: 'test_script',
            errors: ['Test script must be at least 10 characters long']
          }])
          return
        }
        
        // Check for potential script issues
        const script = values.test_script.trim()
        if (!script.includes('#!/') && !script.includes('echo') && !script.includes('test')) {
          // Warn about potentially incomplete script
          console.warn('Script may be incomplete - no shebang or common test commands found')
        }
      }
      
      if (testCase) {
        const updatedTestCase: TestCase = {
          ...testCase,
          ...values,
          // Ensure execution_time_estimate is a number
          execution_time_estimate: parseInt(values.execution_time_estimate) || testCase.execution_time_estimate,
          updated_at: new Date().toISOString(),
        }
        
        await onSave(updatedTestCase)
        message.success('Test case updated successfully')
        onModeChange('view')
      }
    } catch (error) {
      console.error('Validation failed:', error)
      // Form validation errors are automatically displayed by Ant Design
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    if (mode === 'edit') {
      // Reset form to original values
      if (testCase) {
        form.setFieldsValue({
          name: testCase.name,
          description: testCase.description,
          test_type: testCase.test_type,
          target_subsystem: testCase.target_subsystem,
          execution_time_estimate: testCase.execution_time_estimate,
          test_script: testCase.test_script,
        })
      }
      onModeChange('view')
    } else {
      onClose()
    }
  }

  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
    { label: 'Fuzz Test', value: 'fuzz' },
  ]

  const subsystems = [
    { label: 'Kernel Core', value: 'kernel/core' },
    { label: 'Memory Management', value: 'kernel/mm' },
    { label: 'File System', value: 'kernel/fs' },
    { label: 'Networking', value: 'kernel/net' },
    { label: 'Block Drivers', value: 'drivers/block' },
    { label: 'Character Drivers', value: 'drivers/char' },
    { label: 'Network Drivers', value: 'drivers/net' },
    { label: 'x86 Architecture', value: 'arch/x86' },
    { label: 'ARM64 Architecture', value: 'arch/arm64' },
  ]

  const getGenerationMethodIcon = (method: string) => {
    switch (method) {
      case 'ai_diff':
        return <CodeOutlined />
      case 'ai_function':
        return <FunctionOutlined />
      case 'manual':
      default:
        return <UserOutlined />
    }
  }

  const getGenerationMethodColor = (method: string) => {
    switch (method) {
      case 'ai_diff':
        return 'blue'
      case 'ai_function':
        return 'green'
      case 'manual':
      default:
        return 'default'
    }
  }

  const formatExecutionTime = (seconds: number) => {
    if (!seconds) return 'Unknown'
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    return `${Math.floor(seconds / 3600)}h`
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown'
    return new Date(dateString).toLocaleString()
  }

  if (!testCase) {
    return null
  }

  return (
    <Modal
      title={
        <Space>
          <Text strong style={{ fontSize: '16px' }}>
            {mode === 'edit' ? 'Edit Test Case' : 'Test Case Details'}
          </Text>
          <Tag
            icon={getGenerationMethodIcon(testCase.metadata?.generation_method || 'manual')}
            color={getGenerationMethodColor(testCase.metadata?.generation_method || 'manual')}
          >
            {testCase.metadata?.generation_method === 'ai_diff' ? 'AI from Diff' :
             testCase.metadata?.generation_method === 'ai_function' ? 'AI from Function' :
             'Manual'}
          </Tag>
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      width={900}
      style={{ top: 20 }}
      footer={
        <Space>
          {mode === 'view' ? (
            <>
              <Button onClick={onClose}>Close</Button>
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => onModeChange('edit')}
              >
                Edit
              </Button>
            </>
          ) : (
            <>
              <Button onClick={handleCancel} icon={<CloseOutlined />}>
                Cancel
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={loading}
                onClick={handleSave}
              >
                Save Changes
              </Button>
            </>
          )}
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <InfoCircleOutlined />
              Details
            </span>
          }
          key="details"
        >
          {mode === 'view' ? (
            <div>
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="Test Name" span={2}>
                  <Text strong>{testCase.name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Description" span={2}>
                  <Text>{testCase.description || 'No description provided'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Test Type">
                  <Tag color="blue">{testCase.test_type?.toUpperCase() || 'UNKNOWN'}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Target Subsystem">
                  <Text code>{testCase.target_subsystem || 'unknown'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Execution Time">
                  <Space>
                    <ClockCircleOutlined />
                    <Text>{formatExecutionTime(testCase.execution_time_estimate)}</Text>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Badge
                    status={
                      testCase.metadata?.execution_status === 'completed' ? 'success' :
                      testCase.metadata?.execution_status === 'failed' ? 'error' :
                      testCase.metadata?.execution_status === 'running' ? 'processing' :
                      'default'
                    }
                    text={
                      testCase.metadata?.execution_status === 'never_run' ? 'Never Run' :
                      testCase.metadata?.execution_status === 'running' ? 'Running' :
                      testCase.metadata?.execution_status === 'completed' ? 'Completed' :
                      testCase.metadata?.execution_status === 'failed' ? 'Failed' :
                      'Unknown'
                    }
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Created">
                  <Text>{formatDate(testCase.created_at)}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Last Updated">
                  <Text>{formatDate(testCase.updated_at)}</Text>
                </Descriptions.Item>
                {testCase.metadata?.last_execution && (
                  <Descriptions.Item label="Last Execution" span={2}>
                    <Text>{formatDate(testCase.metadata.last_execution)}</Text>
                  </Descriptions.Item>
                )}
              </Descriptions>

              {testCase.code_paths && testCase.code_paths.length > 0 && (
                <>
                  <Divider orientation="left">Code Paths</Divider>
                  <div>
                    {testCase.code_paths.map((path, index) => (
                      <Tag key={index} style={{ marginBottom: 4 }}>
                        <FileTextOutlined /> {path}
                      </Tag>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="name"
                    label="Test Name"
                    rules={[
                      { required: true, message: 'Please enter a test name' },
                      { min: 3, message: 'Test name must be at least 3 characters' },
                    ]}
                  >
                    <Input placeholder="Enter test name" />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    name="description"
                    label="Description"
                    rules={[
                      { required: true, message: 'Please enter a description' },
                    ]}
                  >
                    <TextArea
                      rows={3}
                      placeholder="Describe what this test validates"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="test_type"
                    label="Test Type"
                    rules={[{ required: true, message: 'Please select a test type' }]}
                  >
                    <Select
                      placeholder="Select test type"
                      options={testTypes}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="target_subsystem"
                    label="Target Subsystem"
                    rules={[{ required: true, message: 'Please select a subsystem' }]}
                  >
                    <Select
                      placeholder="Select target subsystem"
                      options={subsystems}
                      showSearch
                      filterOption={(input, option) =>
                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    name="execution_time_estimate"
                    label="Execution Time Estimate (seconds)"
                    rules={[
                      { required: true, message: 'Please enter execution time estimate' },
                      { type: 'number', min: 1, message: 'Must be at least 1 second' },
                    ]}
                  >
                    <Input
                      type="number"
                      placeholder="Enter estimated execution time in seconds"
                      addonAfter="seconds"
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <CodeOutlined />
              Test Script
            </span>
          }
          key="script"
        >
          {mode === 'view' ? (
            <div>
              <Alert
                message="Test Script"
                description="This is the executable test script that will be run during test execution."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Card size="small" title="Script Content">
                <div
                  style={{
                    backgroundColor: '#f6f8fa',
                    border: '1px solid #d0d7de',
                    borderRadius: '6px',
                    padding: '16px',
                    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                    fontSize: '12px',
                    lineHeight: '1.45',
                    overflow: 'auto',
                    maxHeight: '400px',
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {testCase.test_script || 'No test script available'}
                  </pre>
                </div>
              </Card>
              {testCase.test_script && (
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    Script length: {testCase.test_script.length} characters, 
                    {testCase.test_script.split('\n').length} lines
                  </Text>
                </div>
              )}
            </div>
          ) : (
            <Form form={form} layout="vertical">
              <Alert
                message="Test Script Editor"
                description="Edit the test script below. The script should be executable code that validates the functionality."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form.Item
                name="test_script"
                label={
                  <Space>
                    <Text>Test Script</Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      (Use Ctrl+A to select all, Tab for indentation)
                    </Text>
                  </Space>
                }
                rules={[
                  { required: true, message: 'Please enter the test script' },
                  { min: 10, message: 'Test script must be at least 10 characters' },
                ]}
              >
                <TextArea
                  rows={18}
                  placeholder={`#!/bin/bash
# Test script example
# This script should validate the functionality being tested

set -e  # Exit on any error

echo "Starting test execution..."

# Add your test logic here
# Example:
# if [ condition ]; then
#   echo "Test passed"
#   exit 0
# else
#   echo "Test failed"
#   exit 1
# fi

echo "Test completed successfully"`}
                  style={{
                    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                    fontSize: '12px',
                    lineHeight: '1.4',
                    resize: 'vertical',
                  }}
                  onKeyDown={(e) => {
                    // Handle Tab key for indentation
                    if (e.key === 'Tab') {
                      e.preventDefault()
                      const target = e.target as HTMLTextAreaElement
                      const start = target.selectionStart
                      const end = target.selectionEnd
                      const value = target.value
                      
                      // Insert tab character
                      const newValue = value.substring(0, start) + '  ' + value.substring(end)
                      target.value = newValue
                      
                      // Update form field
                      form.setFieldValue('test_script', newValue)
                      
                      // Set cursor position
                      setTimeout(() => {
                        target.selectionStart = target.selectionEnd = start + 2
                      }, 0)
                    }
                  }}
                />
              </Form.Item>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Alert
                    message="Script Validation Tips"
                    description={
                      <ul style={{ margin: 0, paddingLeft: 16 }}>
                        <li>Use proper exit codes (0 for success, non-zero for failure)</li>
                        <li>Include error handling with 'set -e' for bash scripts</li>
                        <li>Add descriptive echo statements for debugging</li>
                        <li>Test your script locally before saving</li>
                      </ul>
                    }
                    type="info"
                    showIcon
                    style={{ height: 'fit-content' }}
                  />
                </Col>
                <Col span={12}>
                  <Alert
                    message="Common Script Types"
                    description={
                      <ul style={{ margin: 0, paddingLeft: 16 }}>
                        <li><Text code>#!/bin/bash</Text> - Bash scripts</li>
                        <li><Text code>#!/usr/bin/python3</Text> - Python scripts</li>
                        <li><Text code>#!/bin/sh</Text> - Shell scripts</li>
                        <li><Text code>make test</Text> - Makefile targets</li>
                      </ul>
                    }
                    type="info"
                    showIcon
                    style={{ height: 'fit-content' }}
                  />
                </Col>
              </Row>
            </Form>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <RobotOutlined />
              Generation Source
            </span>
          }
          key="metadata"
        >
          <div>
            <Title level={5}>Generation Information</Title>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Generation Method">
                <Tag
                  icon={getGenerationMethodIcon(testCase.metadata?.generation_method || 'manual')}
                  color={getGenerationMethodColor(testCase.metadata?.generation_method || 'manual')}
                >
                  {testCase.metadata?.generation_method === 'ai_diff' ? 'AI from Code Diff' :
                   testCase.metadata?.generation_method === 'ai_function' ? 'AI from Function' :
                   'Manual Creation'}
                </Tag>
              </Descriptions.Item>
              {testCase.metadata?.generated_at && (
                <Descriptions.Item label="Generated At">
                  <Text>{formatDate(testCase.metadata.generated_at)}</Text>
                </Descriptions.Item>
              )}
              {testCase.metadata?.ai_model && (
                <Descriptions.Item label="AI Model">
                  <Text code>{testCase.metadata.ai_model}</Text>
                </Descriptions.Item>
              )}
              {testCase.metadata?.generation_params && (
                <Descriptions.Item label="Generation Parameters">
                  <div>
                    {Object.entries(testCase.metadata.generation_params).map(([key, value]) => (
                      <Tag key={key} style={{ marginBottom: 4 }}>
                        {key}: {String(value)}
                      </Tag>
                    ))}
                  </div>
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* Display source information based on generation method */}
            {testCase.metadata?.generation_method === 'ai_diff' && testCase.metadata?.source_data && (
              <>
                <Divider orientation="left">Source Code Diff</Divider>
                <Alert
                  message="Generated from Code Diff"
                  description="This test was generated by analyzing the following code changes."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Card size="small" title="Diff Content">
                  <div
                    style={{
                      backgroundColor: '#f6f8fa',
                      border: '1px solid #d0d7de',
                      borderRadius: '6px',
                      padding: '16px',
                      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                      fontSize: '12px',
                      lineHeight: '1.45',
                      overflow: 'auto',
                      maxHeight: '400px',
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {testCase.metadata.source_data.diff_content || 
                       testCase.metadata.source_data.diff || 
                       'Diff content not available'}
                    </pre>
                  </div>
                </Card>
                {testCase.metadata.source_data.files_changed && (
                  <Card size="small" title="Files Changed" style={{ marginTop: 16 }}>
                    <div>
                      {testCase.metadata.source_data.files_changed.map((file: string, index: number) => (
                        <Tag key={index} icon={<FileTextOutlined />} style={{ marginBottom: 4 }}>
                          {file}
                        </Tag>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}

            {testCase.metadata?.generation_method === 'ai_function' && testCase.metadata?.source_data && (
              <>
                <Divider orientation="left">Source Function Information</Divider>
                <Alert
                  message="Generated from Function Analysis"
                  description="This test was generated by analyzing the specified function."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Descriptions column={1} bordered size="small">
                  {testCase.metadata.source_data.function_name && (
                    <Descriptions.Item label="Function Name">
                      <Text code style={{ fontSize: '14px' }}>
                        {testCase.metadata.source_data.function_name}
                      </Text>
                    </Descriptions.Item>
                  )}
                  {testCase.metadata.source_data.file_path && (
                    <Descriptions.Item label="File Path">
                      <Text code>{testCase.metadata.source_data.file_path}</Text>
                    </Descriptions.Item>
                  )}
                  {testCase.metadata.source_data.subsystem && (
                    <Descriptions.Item label="Subsystem">
                      <Text code>{testCase.metadata.source_data.subsystem}</Text>
                    </Descriptions.Item>
                  )}
                  {testCase.metadata.source_data.function_signature && (
                    <Descriptions.Item label="Function Signature">
                      <div
                        style={{
                          backgroundColor: '#f6f8fa',
                          border: '1px solid #d0d7de',
                          borderRadius: '6px',
                          padding: '12px',
                          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                          fontSize: '12px',
                          marginTop: '8px',
                        }}
                      >
                        <pre style={{ margin: 0 }}>
                          {testCase.metadata.source_data.function_signature}
                        </pre>
                      </div>
                    </Descriptions.Item>
                  )}
                </Descriptions>
                {testCase.metadata.source_data.function_code && (
                  <Card size="small" title="Function Code" style={{ marginTop: 16 }}>
                    <div
                      style={{
                        backgroundColor: '#f6f8fa',
                        border: '1px solid #d0d7de',
                        borderRadius: '6px',
                        padding: '16px',
                        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                        fontSize: '12px',
                        lineHeight: '1.45',
                        overflow: 'auto',
                        maxHeight: '400px',
                      }}
                    >
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {testCase.metadata.source_data.function_code}
                      </pre>
                    </div>
                  </Card>
                )}
              </>
            )}

            {testCase.metadata?.generation_method === 'manual' && (
              <>
                <Divider orientation="left">Manual Test Information</Divider>
                <Alert
                  message="Manually Created Test"
                  description="This test was created manually by a developer."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                {testCase.metadata?.author && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="Author">
                      <Space>
                        <UserOutlined />
                        <Text>{testCase.metadata.author}</Text>
                      </Space>
                    </Descriptions.Item>
                  </Descriptions>
                )}
              </>
            )}

            {/* Raw metadata for debugging */}
            {Object.keys(testCase.metadata || {}).length > 0 && (
              <>
                <Divider orientation="left">Raw Metadata</Divider>
                <Card size="small" title="Debug Information">
                  <div
                    style={{
                      backgroundColor: '#f6f8fa',
                      border: '1px solid #d0d7de',
                      borderRadius: '6px',
                      padding: '16px',
                      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                      fontSize: '12px',
                      lineHeight: '1.45',
                      overflow: 'auto',
                      maxHeight: '300px',
                    }}
                  >
                    <pre style={{ margin: 0 }}>
                      {JSON.stringify(testCase.metadata, null, 2)}
                    </pre>
                  </div>
                </Card>
              </>
            )}
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  )
}

export default TestCaseModal