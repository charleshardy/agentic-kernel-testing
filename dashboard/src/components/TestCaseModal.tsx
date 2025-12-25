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
  Collapse,
  Tooltip,
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
  SettingOutlined,
  DownloadOutlined,
  CopyOutlined,
  ToolOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow, prism as prismTheme } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { TestCase, EnhancedTestCase } from '../services/api'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs
const { Panel } = Collapse

interface TestCaseModalProps {
  testCase: EnhancedTestCase | null
  visible: boolean
  mode: 'view' | 'edit'
  onClose: () => void
  onSave: (testCase: EnhancedTestCase) => void
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
  const [sourceViewModal, setSourceViewModal] = useState<{visible: boolean, filename: string, content: string, language: string}>({
    visible: false,
    filename: '',
    content: '',
    language: ''
  })

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
        const updatedTestCase: EnhancedTestCase = {
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
      case 'ai_kernel_driver':
        return <SettingOutlined />
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
      case 'ai_kernel_driver':
        return 'orange'
      case 'manual':
      default:
        return 'default'
    }
  }

  const getGenerationMethodLabel = (method: string) => {
    switch (method) {
      case 'ai_diff':
        return 'AI from Diff'
      case 'ai_function':
        return 'AI from Function'
      case 'ai_kernel_driver':
        return 'AI Kernel Driver'
      case 'manual':
      default:
        return 'Manual'
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

  // Check if this is a kernel driver test
  const isKernelDriverTest = () => {
    return testCase?.test_metadata?.generation_method === 'ai_kernel_driver' ||
           testCase?.metadata?.generation_method === 'ai_kernel_driver' ||
           testCase?.generation_info?.method === 'ai_kernel_driver' ||
           testCase?.test_metadata?.kernel_module === true ||
           testCase?.metadata?.kernel_module === true ||
           testCase?.requires_root === true ||
           testCase?.kernel_module === true ||
           (testCase?.test_metadata?.driver_files && Object.keys(testCase.test_metadata.driver_files).length > 0) ||
           (testCase?.metadata?.driver_files && Object.keys(testCase.metadata.driver_files).length > 0) ||
           (testCase?.generation_info?.driver_files && Object.keys(testCase.generation_info.driver_files).length > 0) ||
           (testCase?.driver_files && Object.keys(testCase.driver_files).length > 0)
  }

  // Get kernel driver files
  const getKernelDriverFiles = () => {
    // Check multiple possible locations for driver files
    if (testCase?.test_metadata?.driver_files) {
      return testCase.test_metadata.driver_files
    }
    if (testCase?.metadata?.driver_files) {
      return testCase.metadata.driver_files
    }
    if (testCase?.generation_info?.driver_files) {
      return testCase.generation_info.driver_files
    }
    if (testCase?.driver_files) {
      return testCase.driver_files
    }
    
    return null
  }

  // Copy text to clipboard
  const copyToClipboard = (text: string, filename: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success(`${filename} copied to clipboard`)
    }).catch(() => {
      message.error('Failed to copy to clipboard')
    })
  }

  // Get file language for syntax highlighting
  const getFileLanguage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'c':
      case 'h':
        return 'c'
      case 'sh':
        return 'bash'
      case 'py':
        return 'python'
      case 'md':
        return 'markdown'
      case 'json':
        return 'json'
      case 'yaml':
      case 'yml':
        return 'yaml'
      default:
        if (filename === 'Makefile' || filename.includes('Makefile')) {
          return 'makefile'
        }
        return 'text'
    }
  }

  // Open source view modal
  const openSourceView = (filename: string, content: string) => {
    setSourceViewModal({
      visible: true,
      filename,
      content,
      language: getFileLanguage(filename)
    })
  }

  // Close source view modal
  const closeSourceView = () => {
    setSourceViewModal({
      visible: false,
      filename: '',
      content: '',
      language: ''
    })
  }

  // Get file icon
  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'c':
      case 'h':
        return <CodeOutlined style={{ color: '#00599C' }} />
      case 'sh':
        return <ToolOutlined style={{ color: '#4EAA25' }} />
      case 'py':
        return <CodeOutlined style={{ color: '#3776AB' }} />
      case 'md':
        return <FileTextOutlined style={{ color: '#083FA1' }} />
      default:
        if (filename === 'Makefile' || filename.includes('Makefile')) {
          return <SettingOutlined style={{ color: '#427819' }} />
        }
        return <FileTextOutlined />
    }
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
            icon={getGenerationMethodIcon(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
            color={getGenerationMethodColor(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
          >
            {getGenerationMethodLabel(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
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
                <SyntaxHighlighter
                  language="bash"
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    borderRadius: '6px',
                    fontSize: '12px',
                    lineHeight: '1.45',
                    maxHeight: '400px',
                    overflow: 'auto',
                  }}
                  showLineNumbers={true}
                  wrapLines={true}
                  codeTagProps={{
                    style: {
                      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                    }
                  }}
                >
                  {testCase.test_script || '# No test script available'}
                </SyntaxHighlighter>
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

        {isKernelDriverTest() && (
          <TabPane
            tab={
              <span>
                <SettingOutlined />
                Kernel Driver Files
              </span>
            }
            key="kernel-files"
          >
            <div>
              <Alert
                message="AI-Generated Kernel Test Driver"
                description="This test case includes a complete kernel module with source code, build system, and execution scripts."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              {/* Driver Information */}
              <Card size="small" title="Driver Information" style={{ marginBottom: 16 }}>
                <Alert
                  message="Generated Kernel Test Driver"
                  description="This test was generated as a complete kernel module for direct kernel function testing."
                  type="success"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Descriptions column={2} size="small">
                  {/* Generation Information */}
                  <Descriptions.Item label="Generation Method">
                    <Tag
                      icon={getGenerationMethodIcon(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
                      color={getGenerationMethodColor(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
                    >
                      {getGenerationMethodLabel(testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual')}
                    </Tag>
                  </Descriptions.Item>
                  
                  {(testCase.generation_info?.source_data?.function_name) && (
                    <Descriptions.Item label="Target Function">
                      <Text code style={{ fontSize: '14px' }}>
                        {testCase.generation_info?.source_data?.function_name}
                      </Text>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.source_data?.file_path) && (
                    <Descriptions.Item label="Source File">
                      <Text code>{testCase.generation_info?.source_data?.file_path}</Text>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.source_data?.subsystem) && (
                    <Descriptions.Item label="Kernel Subsystem">
                      <Tag color="blue">{testCase.generation_info?.source_data?.subsystem}</Tag>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.metadata?.kernel_module) && (
                    <Descriptions.Item label="Kernel Module">
                      <Text code>{testCase.metadata?.kernel_module}</Text>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.requires_root) && (
                    <Descriptions.Item label="Requires Root">
                      <Tag color="orange">Yes</Tag>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.metadata?.requires_kernel_headers) && (
                    <Descriptions.Item label="Kernel Headers">
                      <Tag color="blue">Required</Tag>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.ai_model) && (
                    <Descriptions.Item label="AI Model">
                      <Text code>{testCase.generation_info?.ai_model}</Text>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.generated_at) && (
                    <Descriptions.Item label="Generated At">
                      <Text>{formatDate(testCase.generation_info?.generated_at)}</Text>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.source_data?.test_types) && (
                    <Descriptions.Item label="Test Types" span={2}>
                      <Space wrap>
                        {(testCase.generation_info?.source_data?.test_types || []).map((type: string) => (
                          <Tag key={type} color="purple">{type}</Tag>
                        ))}
                      </Space>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.source_data?.driver_files) && (
                    <Descriptions.Item label="Generated Files" span={2}>
                      <Space wrap>
                        {(testCase.generation_info?.source_data?.driver_files || []).map((file: string) => (
                          <Tag key={file} icon={getFileIcon(file)}>{file}</Tag>
                        ))}
                      </Space>
                    </Descriptions.Item>
                  )}
                  
                  {(testCase.generation_info?.generation_params) && (
                    <Descriptions.Item label="Generation Parameters" span={2}>
                      <div>
                        {Object.entries(testCase.generation_info?.generation_params || {}).map(([key, value]) => (
                          <Tag key={key} style={{ marginBottom: 4 }}>
                            {key}: {String(value)}
                          </Tag>
                        ))}
                      </div>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>

              {/* Generated Files with Source Code */}
              {getKernelDriverFiles() && (
                <Card size="small" title="Generated Files" style={{ marginBottom: 16 }}>
                  <Alert
                    message="Kernel Driver Source Files"
                    description="Complete source code files generated for the kernel test driver with syntax highlighting."
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  
                  {/* Quick Access Links */}
                  <Card size="small" title="Quick Access - View Source Code" style={{ marginBottom: 16, backgroundColor: '#f8f9fa' }}>
                    <Space wrap>
                      {Object.entries(getKernelDriverFiles() || {}).map(([filename, content]) => (
                        <Button
                          key={filename}
                          type="link"
                          icon={getFileIcon(filename)}
                          onClick={() => openSourceView(filename, content as string)}
                          style={{ 
                            padding: '4px 8px',
                            height: 'auto',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Text strong style={{ color: '#1890ff' }}>{filename}</Text>
                          <Tag color="blue" style={{ fontSize: '10px', padding: '0 4px' }}>{getFileLanguage(filename).toUpperCase()}</Tag>
                        </Button>
                      ))}
                    </Space>
                  </Card>
                  
                  <Collapse>
                    {Object.entries(getKernelDriverFiles() || {}).map(([filename, content]) => (
                      <Panel
                        header={
                          <Space>
                            {getFileIcon(filename)}
                            <Text strong>{filename}</Text>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              ({typeof content === 'string' ? content.length : 0} chars)
                            </Text>
                          </Space>
                        }
                        key={filename}
                        extra={
                          <Space onClick={(e) => e.stopPropagation()}>
                            <Tooltip title="View source code">
                              <Button
                                size="small"
                                icon={<CodeOutlined />}
                                onClick={() => openSourceView(filename, content as string)}
                              />
                            </Tooltip>
                            <Tooltip title="Copy to clipboard">
                              <Button
                                size="small"
                                icon={<CopyOutlined />}
                                onClick={() => copyToClipboard(content as string, filename)}
                              />
                            </Tooltip>
                            <Tooltip title="Download file">
                              <Button
                                size="small"
                                icon={<DownloadOutlined />}
                                onClick={() => {
                                  const blob = new Blob([content as string], { type: 'text/plain' })
                                  const url = URL.createObjectURL(blob)
                                  const link = document.createElement('a')
                                  link.href = url
                                  link.download = filename
                                  document.body.appendChild(link)
                                  link.click()
                                  document.body.removeChild(link)
                                  URL.revokeObjectURL(url)
                                }}
                              />
                            </Tooltip>
                          </Space>
                        }
                      >
                        <div style={{ marginTop: 8 }}>
                          <SyntaxHighlighter
                            language={getFileLanguage(filename)}
                            style={tomorrow}
                            customStyle={{
                              margin: 0,
                              borderRadius: '6px',
                              fontSize: '12px',
                              lineHeight: '1.4',
                            }}
                            showLineNumbers={true}
                            wrapLines={true}
                            codeTagProps={{
                              style: {
                                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                              }
                            }}
                          >
                            {content as string}
                          </SyntaxHighlighter>
                        </div>
                      </Panel>
                    ))}
                  </Collapse>
                </Card>
              )}



              {/* Kernel Driver Capabilities */}
              <Card size="small" title="Kernel Driver Capabilities" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <div>
                      <Text strong>Testing Capabilities:</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 16, fontSize: '12px' }}>
                        <li>Direct kernel function calls</li>
                        <li>Memory management testing</li>
                        <li>Error injection and fault tolerance</li>
                        <li>Performance measurement</li>
                        <li>Concurrency and race condition testing</li>
                      </ul>
                    </div>
                  </Col>
                  <Col span={12}>
                    <div>
                      <Text strong>Safety Features:</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 16, fontSize: '12px' }}>
                        <li>Automatic resource cleanup</li>
                        <li>Error handling and recovery</li>
                        <li>Timeout protection</li>
                        <li>Kernel log integration</li>
                        <li>Safe module unloading</li>
                      </ul>
                    </div>
                  </Col>
                </Row>
              </Card>

              {/* Build and Execution Instructions */}
              <Card size="small" title="Build & Execution Instructions">
                <Collapse>
                  <Panel header="Build Commands" key="build">
                    <div style={{ marginBottom: 12 }}>
                      <Text strong>Prerequisites:</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                        <li>Linux kernel headers for your kernel version</li>
                        <li>GCC compiler and build tools</li>
                        <li>Root privileges for module loading</li>
                      </ul>
                    </div>
                    <SyntaxHighlighter
                      language="bash"
                      style={tomorrow}
                      customStyle={{
                        margin: 0,
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                    >
{`# Build the kernel module
make clean
make

# Load the module (requires root)
sudo insmod ${testCase.metadata?.kernel_module || 'test_module.ko'}`}
                    </SyntaxHighlighter>
                  </Panel>

                  <Panel header="Test Execution" key="execution">
                    <SyntaxHighlighter
                      language="bash"
                      style={tomorrow}
                      customStyle={{
                        margin: 0,
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                    >
{`# View test results
cat /proc/${(testCase.metadata?.kernel_module || 'test_module.ko').replace('.ko', '_results')}

# Check kernel messages
dmesg | tail -20

# Unload the module
sudo rmmod ${(testCase.metadata?.kernel_module || 'test_module.ko').replace('.ko', '')}`}
                    </SyntaxHighlighter>
                  </Panel>

                  <Panel header="Safety Information" key="safety">
                    <Alert
                      message="Kernel Module Safety"
                      description={
                        <div>
                          <p>This kernel module includes comprehensive safety features:</p>
                          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                            <li><SafetyOutlined /> Automatic cleanup on module unload</li>
                            <li><SafetyOutlined /> Error handling and bounds checking</li>
                            <li><SafetyOutlined /> Resource leak prevention</li>
                            <li><SafetyOutlined /> Timeout protection for long-running tests</li>
                            <li><SafetyOutlined /> Kernel log integration for debugging</li>
                          </ul>
                          <p style={{ marginTop: 12, marginBottom: 0 }}>
                            <strong>Recommendation:</strong> Test in an isolated environment or virtual machine first.
                          </p>
                        </div>
                      }
                      type="success"
                      showIcon
                    />
                  </Panel>
                </Collapse>
              </Card>
            </div>
          </TabPane>
        )}


      </Tabs>

      {/* Source View Modal */}
      <Modal
        title={
          <Space>
            <CodeOutlined />
            <Text strong>{sourceViewModal.filename}</Text>
            <Tag color="blue">{sourceViewModal.language.toUpperCase()}</Tag>
          </Space>
        }
        open={sourceViewModal.visible}
        onCancel={closeSourceView}
        width="90%"
        style={{ top: 20 }}
        footer={
          <Space>
            <Button onClick={closeSourceView}>Close</Button>
            <Button
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(sourceViewModal.content, sourceViewModal.filename)}
            >
              Copy All
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => {
                const blob = new Blob([sourceViewModal.content], { type: 'text/plain' })
                const url = URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = sourceViewModal.filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(url)
              }}
            >
              Download
            </Button>
          </Space>
        }
      >
        <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
          <SyntaxHighlighter
            language={sourceViewModal.language}
            style={tomorrow}
            customStyle={{
              margin: 0,
              borderRadius: '8px',
              fontSize: '14px',
              lineHeight: '1.5',
            }}
            showLineNumbers={true}
            wrapLines={true}
            codeTagProps={{
              style: {
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
              }
            }}
          >
            {sourceViewModal.content}
          </SyntaxHighlighter>
        </div>
      </Modal>
    </Modal>
  )
}

export default TestCaseModal