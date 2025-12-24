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

const TestCaseModalSafe: React.FC<TestCaseModalProps> = ({
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
      try {
        form.setFieldsValue({
          name: testCase.name || '',
          description: testCase.description || '',
          test_type: testCase.test_type || '',
          target_subsystem: testCase.target_subsystem || '',
          execution_time_estimate: testCase.execution_time_estimate || 0,
          test_script: testCase.test_script || '',
        })
      } catch (error) {
        console.error('Error setting form values:', error)
      }
    }
  }, [testCase, visible, form])

  const handleSave = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()
      
      if (testCase) {
        const updatedTestCase: EnhancedTestCase = {
          ...testCase,
          ...values,
          execution_time_estimate: parseInt(values.execution_time_estimate) || testCase.execution_time_estimate,
          updated_at: new Date().toISOString(),
        }
        
        await onSave(updatedTestCase)
        message.success('Test case updated successfully')
        onModeChange('view')
      }
    } catch (error) {
      console.error('Validation failed:', error)
      message.error('Failed to update test case')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    if (mode === 'edit') {
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
    { label: 'Kernel Driver', value: 'kernel_driver' },
  ]

  const subsystems = [
    { label: 'Kernel Core', value: 'kernel/core' },
    { label: 'Memory Management', value: 'kernel/mm' },
    { label: 'File System', value: 'kernel/fs' },
    { label: 'Networking', value: 'kernel/net' },
    { label: 'Block Drivers', value: 'drivers/block' },
    { label: 'Character Drivers', value: 'drivers/char' },
    { label: 'Network Drivers', value: 'drivers/net' },
  ]

  const getGenerationMethodIcon = (method: string) => {
    switch (method) {
      case 'ai_diff': return <CodeOutlined />
      case 'ai_function': return <FunctionOutlined />
      case 'ai_kernel_driver': return <SettingOutlined />
      case 'manual':
      default: return <UserOutlined />
    }
  }

  const getGenerationMethodColor = (method: string) => {
    switch (method) {
      case 'ai_diff': return 'blue'
      case 'ai_function': return 'green'
      case 'ai_kernel_driver': return 'orange'
      case 'manual':
      default: return 'default'
    }
  }

  const getGenerationMethodLabel = (method: string) => {
    switch (method) {
      case 'ai_diff': return 'AI from Diff'
      case 'ai_function': return 'AI from Function'
      case 'ai_kernel_driver': return 'AI Kernel Driver'
      case 'manual':
      default: return 'Manual'
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
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return 'Invalid Date'
    }
  }

  // Check if this is a kernel driver test
  const isKernelDriverTest = () => {
    if (!testCase) return false
    
    try {
      return testCase.metadata?.generation_method === 'ai_kernel_driver' ||
             testCase.generation_info?.method === 'ai_kernel_driver' ||
             testCase.test_type === 'kernel_driver' ||
             testCase.metadata?.kernel_module === true ||
             testCase.requires_root === true ||
             (testCase.metadata?.driver_files && Object.keys(testCase.metadata.driver_files).length > 0) ||
             (testCase.driver_files && Object.keys(testCase.driver_files).length > 0)
    } catch (error) {
      console.error('Error checking kernel driver test:', error)
      return false
    }
  }

  // Get kernel driver files safely
  const getKernelDriverFiles = () => {
    if (!testCase) return null
    
    try {
      if (testCase.metadata?.driver_files && Object.keys(testCase.metadata.driver_files).length > 0) {
        return testCase.metadata.driver_files
      }
      if (testCase.driver_files && Object.keys(testCase.driver_files).length > 0) {
        return testCase.driver_files
      }
      if (testCase.generation_info?.driver_files && Object.keys(testCase.generation_info.driver_files).length > 0) {
        return testCase.generation_info.driver_files
      }
    } catch (error) {
      console.error('Error getting kernel driver files:', error)
    }
    
    return null
  }

  // Copy text to clipboard
  const copyToClipboard = (text: string, filename: string) => {
    try {
      navigator.clipboard.writeText(text).then(() => {
        message.success(`${filename} copied to clipboard`)
      }).catch(() => {
        message.error('Failed to copy to clipboard')
      })
    } catch (error) {
      console.error('Clipboard error:', error)
      message.error('Clipboard not supported')
    }
  }

  // Download file
  const downloadFile = (content: string, filename: string) => {
    try {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      message.error('Failed to download file')
    }
  }

  if (!testCase) {
    return null
  }

  const generationMethod = testCase.metadata?.generation_method || testCase.generation_info?.method || 'manual'

  return (
    <Modal
      title={
        <Space>
          <Text strong style={{ fontSize: '16px' }}>
            {mode === 'edit' ? 'Edit Test Case' : 'Test Case Details'}
          </Text>
          <Tag
            icon={getGenerationMethodIcon(generationMethod)}
            color={getGenerationMethodColor(generationMethod)}
          >
            {getGenerationMethodLabel(generationMethod)}
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
                  <Text strong>{testCase.name || 'Unnamed Test'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Description" span={2}>
                  <Text>{testCase.description || 'No description provided'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Test Type">
                  <Tag color="blue">{(testCase.test_type || 'unknown').toUpperCase()}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Target Subsystem">
                  <Text code>{testCase.target_subsystem || 'unknown'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Execution Time">
                  <Space>
                    <ClockCircleOutlined />
                    <Text>{formatExecutionTime(testCase.execution_time_estimate || 0)}</Text>
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

              {getKernelDriverFiles() && (
                <Card size="small" title="Generated Files" style={{ marginBottom: 16 }}>
                  <Alert
                    message="Kernel Driver Source Files"
                    description="Complete source code files generated for the kernel test driver."
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  
                  <Collapse>
                    {Object.entries(getKernelDriverFiles() || {}).map(([filename, content]) => (
                      <Panel
                        header={
                          <Space>
                            <FileTextOutlined />
                            <Text strong>{filename}</Text>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              ({typeof content === 'string' ? content.length : 0} chars)
                            </Text>
                          </Space>
                        }
                        key={filename}
                        extra={
                          <Space onClick={(e) => e.stopPropagation()}>
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
                                onClick={() => downloadFile(content as string, filename)}
                              />
                            </Tooltip>
                          </Space>
                        }
                      >
                        <div style={{ marginTop: 8 }}>
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
                              {content as string}
                            </pre>
                          </div>
                        </div>
                      </Panel>
                    ))}
                  </Collapse>
                </Card>
              )}

              <Card size="small" title="Build & Execution Instructions">
                <Alert
                  message="Build Commands"
                  description={
                    <div>
                      <p><strong>Prerequisites:</strong></p>
                      <ul>
                        <li>Linux kernel headers for your kernel version</li>
                        <li>GCC compiler and build tools</li>
                        <li>Root privileges for module loading</li>
                      </ul>
                      <p><strong>Build and run:</strong></p>
                      <pre style={{ backgroundColor: '#f6f8fa', padding: '8px', borderRadius: '4px' }}>
{`# Build the kernel module
make clean
make

# Load the module (requires root)
sudo insmod test_module.ko

# View test results
dmesg | tail -20

# Unload the module
sudo rmmod test_module`}
                      </pre>
                    </div>
                  }
                  type="info"
                  showIcon
                />
              </Card>
            </div>
          </TabPane>
        )}
      </Tabs>
    </Modal>
  )
}

export default TestCaseModalSafe