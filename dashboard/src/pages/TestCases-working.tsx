import React, { useState } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Space,
  Button,
  Input,
  Select,
  Tag,
  message,
  Alert,
  Modal,
  Form,
} from 'antd'
import {
  ReloadOutlined,
  SearchOutlined,
  PlusOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  EditOutlined,
  EyeOutlined,
  CodeOutlined,
  FunctionOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import apiService, { EnhancedTestCase } from '../services/api'
import useAIGeneration from '../hooks/useAIGeneration'
import KernelDriverInfo from '../components/KernelDriverInfo'
import TestCaseModal from '../components/TestCaseModal-safe'
import TestCaseTable from '../components/TestCaseTable'

const { Text, Title } = Typography
const { TextArea } = Input

const TestCases: React.FC = () => {
  const [searchText, setSearchText] = useState('')
  const [filters, setFilters] = useState({
    testType: undefined,
    subsystem: undefined,
    status: undefined,
  })
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [aiGenModalVisible, setAiGenModalVisible] = useState(false)
  const [aiGenType, setAiGenType] = useState<'diff' | 'function' | 'kernel'>('diff')
  const [aiGenForm] = Form.useForm()

  // Test Case Modal state
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view')

  // AI Generation hook
  const { generateFromDiff, generateFromFunction, generateKernelDriver, isGenerating } = useAIGeneration({
    onSuccess: () => {
      setAiGenModalVisible(false)
      aiGenForm.resetFields()
      // Force immediate refresh of the test list
      setTimeout(() => {
        refetch()
      }, 1000)
    },
    preserveFilters: true,
    enableOptimisticUpdates: true,
  })

  // Test Case Modal handlers
  const handleViewTest = async (testId: string) => {
    try {
      console.log('🔍 Attempting to view test:', testId)
      
      // First try to get from API
      try {
        const test = await apiService.getTestById(testId)
        console.log('✅ Found test in API:', test)
        setSelectedTestCase(test)
        setModalMode('view')
        setModalVisible(true)
        return
      } catch (apiError: any) {
        console.log('⚠️ API fetch failed:', apiError.response?.status, apiError.message)
        
        // If API fails, try to find in current test data (mock or API)
        const currentTest = tests.find(t => t.id === testId)
        if (currentTest) {
          console.log('✅ Found test in current data:', currentTest)
          setSelectedTestCase(currentTest)
          setModalMode('view')
          setModalVisible(true)
          return
        }
        
        // If not found anywhere, throw the original error
        throw apiError
      }
    } catch (error: any) {
      console.error('❌ Error loading test case:', error)
      if (error.response?.status === 404) {
        message.error(`Test case ${testId} not found`)
      } else {
        message.error('Failed to load test case details')
      }
    }
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedTestCase(null)
  }

  const handleEditTest = (testId: string) => {
    const test = filteredTests.find(t => t.id === testId)
    if (test) {
      setSelectedTestCase(test)
      setModalMode('edit')
      setModalVisible(true)
    } else {
      message.error('Test case not found')
    }
  }

  const handleDeleteTest = (testId: string) => {
    message.info(`Delete functionality for test ${testId} - coming soon`)
    // TODO: Implement delete functionality
  }

  const handleExecuteTests = (testIds: string[]) => {
    message.success(`Starting execution of ${testIds.length} test case${testIds.length !== 1 ? 's' : ''}`)
    // TODO: Implement execute functionality
  }

  const handleTableChange = (paginationConfig: any, filters: any, sorter: any) => {
    // Handle table changes like sorting, pagination, etc.
    console.log('Table changed:', { paginationConfig, filters, sorter })
  }

  const handleSaveTest = async (updatedTestCase: EnhancedTestCase) => {
    try {
      // In a real implementation, call the API to update the test
      // await apiService.updateTest(updatedTestCase.id, updatedTestCase)
      
      // For now, just show success message
      message.success(`Test case ${updatedTestCase.name} updated successfully`)
      
      // Refresh the test list
      refetch()
    } catch (error) {
      console.error('Error updating test case:', error)
      message.error('Failed to update test case')
    }
  }

  // Fetch test cases
  const { data: testCasesData, isLoading, error, refetch } = useQuery(
    ['testCases', searchText, filters, Date.now()], // Add cache busting
    () => apiService.getTests({
      page: 1,
      page_size: 50,
      test_type: filters.testType,
      status: filters.status,
    }),
    {
      refetchInterval: 10000,
      retry: false,
      cacheTime: 0, // Disable caching
      staleTime: 0, // Always consider data stale
      onError: (error) => {
        console.error('Failed to fetch test cases:', error)
      },
    }
  )

  console.log('TestCases Debug:', {
    hasData: !!testCasesData,
    dataTests: testCasesData?.tests?.length || 0,
    error: !!error,
    isLoading
  })

  // Mock data when API is not available - Enhanced with better metadata
  const mockTestCases: EnhancedTestCase[] = [
    {
      id: 'test-001',
      name: 'Kernel Boot Test',
      description: 'Tests kernel boot sequence and initialization with comprehensive validation',
      test_type: 'integration',
      target_subsystem: 'kernel/core',
      code_paths: ['kernel/init/main.c', 'kernel/init/init_task.c'],
      execution_time_estimate: 45,
      test_script: '#!/bin/bash\n# Kernel boot test script\necho "Testing kernel boot sequence"\n# Add test logic here',
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      metadata: {
        execution_status: 'completed',
        generation_method: 'manual',
        last_execution: '2024-01-15T14:20:00Z',
      }
    },
    {
      id: 'test-002',
      name: 'Memory Allocation Test',
      description: 'Tests kmalloc and memory management functions with stress testing',
      test_type: 'unit',
      target_subsystem: 'kernel/mm',
      code_paths: ['mm/slab.c', 'mm/kmalloc.c'],
      execution_time_estimate: 30,
      test_script: '#!/bin/bash\n# Memory allocation test script\necho "Testing memory allocation"\n# Add test logic here',
      created_at: '2024-01-15T11:00:00Z',
      updated_at: '2024-01-15T11:00:00Z',
      metadata: {
        execution_status: 'never_run',
        generation_method: 'ai_function',
      }
    },
    {
      id: 'test-003',
      name: 'Network Driver Test',
      description: 'Tests network interface driver functionality with packet injection',
      test_type: 'integration',
      target_subsystem: 'drivers/net',
      code_paths: ['drivers/net/ethernet/intel/e1000e/netdev.c'],
      execution_time_estimate: 60,
      test_script: '#!/bin/bash\n# Network driver test script\necho "Testing network driver"\n# Add test logic here',
      created_at: '2024-01-15T12:00:00Z',
      updated_at: '2024-01-15T12:00:00Z',
      metadata: {
        execution_status: 'failed',
        generation_method: 'ai_diff',
        last_execution: '2024-01-15T15:45:00Z',
      }
    },
    {
      id: 'test-004',
      name: 'File System Stress Test',
      description: 'Comprehensive stress tests for file system operations and performance',
      test_type: 'performance',
      target_subsystem: 'kernel/fs',
      code_paths: ['fs/ext4/inode.c', 'fs/ext4/super.c'],
      execution_time_estimate: 120,
      test_script: '#!/bin/bash\n# File system stress test script\necho "Testing file system stress"\n# Add test logic here',
      created_at: '2024-01-15T13:00:00Z',
      updated_at: '2024-01-15T13:00:00Z',
      metadata: {
        execution_status: 'running',
        generation_method: 'ai_kernel_driver',
        last_execution: '2024-01-15T16:00:00Z',
      },
      requires_root: true,
      kernel_module: true,
      driver_files: {
        'fs_stress_test.c': '/* File system stress test kernel module */\n#include <linux/module.h>\n#include <linux/kernel.h>\n#include <linux/fs.h>\n\n// Generated kernel test driver code\nstatic int __init fs_stress_init(void) {\n    printk(KERN_INFO "FS Stress Test Module Loaded\\n");\n    return 0;\n}\n\nstatic void __exit fs_stress_exit(void) {\n    printk(KERN_INFO "FS Stress Test Module Unloaded\\n");\n}\n\nmodule_init(fs_stress_init);\nmodule_exit(fs_stress_exit);\nMODULE_LICENSE("GPL");',
        'Makefile': 'obj-m += fs_stress_test.o\n\nKERNEL_DIR := /lib/modules/$(shell uname -r)/build\nPWD := $(shell pwd)\n\nall:\n\tmake -C $(KERNEL_DIR) M=$(PWD) modules\n\nclean:\n\tmake -C $(KERNEL_DIR) M=$(PWD) clean',
        'install.sh': '#!/bin/bash\n# Installation script for fs stress test driver\necho "Installing FS stress test driver..."\nsudo insmod fs_stress_test.ko\necho "Driver installed successfully"',
        'test.sh': '#!/bin/bash\n# Test execution script\necho "Running file system stress test"\n# Load the module\nsudo ./install.sh\n# Run tests\necho "Executing stress tests..."\n# Unload module\nsudo rmmod fs_stress_test\necho "Test completed"'
      }
    },
    {
      id: 'test-005',
      name: 'Scheduler Performance Test',
      description: 'Tests CPU scheduler performance and fairness algorithms',
      test_type: 'performance',
      target_subsystem: 'kernel/sched',
      code_paths: ['kernel/sched/core.c', 'kernel/sched/fair.c'],
      execution_time_estimate: 90,
      test_script: '#!/bin/bash\n# Scheduler performance test\necho "Testing scheduler performance"\n# Performance benchmarks here',
      created_at: '2024-01-15T14:00:00Z',
      updated_at: '2024-01-15T14:00:00Z',
      metadata: {
        execution_status: 'completed',
        generation_method: 'ai_function',
        last_execution: '2024-01-15T17:30:00Z',
      }
    },
    {
      id: 'test-006',
      name: 'Security Vulnerability Scan',
      description: 'Automated security scanning for common kernel vulnerabilities',
      test_type: 'security',
      target_subsystem: 'kernel/security',
      code_paths: ['security/security.c'],
      execution_time_estimate: 180,
      test_script: '#!/bin/bash\n# Security vulnerability scan\necho "Running security scans"\n# Security tests here',
      created_at: '2024-01-15T15:00:00Z',
      updated_at: '2024-01-15T15:00:00Z',
      metadata: {
        execution_status: 'never_run',
        generation_method: 'manual',
      }
    },
  ]

  const tests = testCasesData?.tests || mockTestCases
  
  console.log('Using tests:', {
    source: testCasesData?.tests ? 'API' : 'Mock',
    count: tests.length,
    testIds: tests.map(t => t.id).slice(0, 3)
  })

  // Filter tests based on search and filters
  const filteredTests = tests.filter(test => {
    const matchesSearch = !searchText || 
      test.name.toLowerCase().includes(searchText.toLowerCase()) ||
      test.description.toLowerCase().includes(searchText.toLowerCase()) ||
      test.target_subsystem.toLowerCase().includes(searchText.toLowerCase())
    
    const matchesType = !filters.testType || test.test_type === filters.testType
    const matchesSubsystem = !filters.subsystem || test.target_subsystem === filters.subsystem
    const matchesStatus = !filters.status || test.metadata?.execution_status === filters.status
    
    return matchesSearch && matchesType && matchesSubsystem && matchesStatus
  })

  // Calculate statistics with enhanced metrics
  const totalTests = filteredTests.length
  const neverRunTests = filteredTests.filter(t => t.metadata?.execution_status === 'never_run').length
  const aiGeneratedTests = filteredTests.filter(t => t.metadata?.generation_method !== 'manual').length
  const manualTests = totalTests - aiGeneratedTests
  const runningTests = filteredTests.filter(t => t.metadata?.execution_status === 'running').length
  const failedTests = filteredTests.filter(t => t.metadata?.execution_status === 'failed').length
  const completedTests = filteredTests.filter(t => t.metadata?.execution_status === 'completed').length
  const kernelDriverTests = filteredTests.filter(t => 
    t.metadata?.generation_method === 'ai_kernel_driver' || 
    t.requires_root === true || 
    t.kernel_module === true
  ).length

  const testTypes = [
    { label: 'Unit Test', value: 'unit' },
    { label: 'Integration Test', value: 'integration' },
    { label: 'Performance Test', value: 'performance' },
    { label: 'Security Test', value: 'security' },
  ]

  const subsystems = [
    { label: 'Kernel Core', value: 'kernel/core' },
    { label: 'Memory Management', value: 'kernel/mm' },
    { label: 'File System', value: 'kernel/fs' },
    { label: 'Networking', value: 'kernel/net' },
    { label: 'Block Drivers', value: 'drivers/block' },
    { label: 'Network Drivers', value: 'drivers/net' },
  ]

  const statusOptions = [
    { label: 'Never Run', value: 'never_run' },
    { label: 'Running', value: 'running' },
    { label: 'Completed', value: 'completed' },
    { label: 'Failed', value: 'failed' },
  ]

  return (
    <div style={{ padding: '0 24px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 24 
      }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>
          Test Cases
        </h2>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => setAiGenModalVisible(true)}
          >
            AI Generate Tests
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => message.info('Create test functionality coming soon')}
          >
            Create Test
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={async () => {
              try {
                console.log('Testing direct API call...')
                const result = await apiService.getTests({ page: 1, page_size: 50 })
                console.log('Direct API result:', result)
                message.success(`Direct API call successful: ${result.tests.length} tests`)
              } catch (error) {
                console.error('Direct API call failed:', error)
                message.error('Direct API call failed')
              }
            }}
          >
            Test API
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              // Force refresh by invalidating cache
              window.location.reload()
            }}
          >
            Force Refresh
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              refetch()
              message.info('Refreshing test case list...')
            }}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Connection Status */}
      {error && (
        <Alert
          message="Backend Connection"
          description="Using mock data - backend API not available. Start the backend server to see real test data."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Enhanced Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Test Cases"
              value={totalTests}
              valueStyle={{ color: '#1890ff' }}
              suffix={
                <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                  {runningTests > 0 && `${runningTests} running`}
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="AI Generated"
              value={aiGeneratedTests}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                  {kernelDriverTests > 0 && `${kernelDriverTests} kernel drivers`}
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Completed"
              value={completedTests}
              valueStyle={{ color: '#722ed1' }}
              suffix={
                <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                  {failedTests > 0 && `${failedTests} failed`}
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Never Run"
              value={neverRunTests}
              valueStyle={{ color: '#fa8c16' }}
              suffix={
                <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                  {manualTests > 0 && `${manualTests} manual`}
                </div>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="Search test cases..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Test Type"
              value={filters.testType}
              onChange={(value) => setFilters(prev => ({ ...prev, testType: value }))}
              options={testTypes}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Subsystem"
              value={filters.subsystem}
              onChange={(value) => setFilters(prev => ({ ...prev, subsystem: value }))}
              options={subsystems}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="Status"
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              options={statusOptions}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Space>
              <Button
                onClick={() => {
                  setSearchText('')
                  setFilters({ testType: undefined, subsystem: undefined, status: undefined })
                }}
              >
                Clear Filters
              </Button>
              {selectedRowKeys.length > 0 && (
                <Button
                  type="primary"
                  onClick={() => {
                    message.success(`Starting execution of ${selectedRowKeys.length} test cases`)
                    setSelectedRowKeys([])
                  }}
                >
                  Run Selected ({selectedRowKeys.length})
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        <TestCaseTable
          tests={filteredTests}
          loading={isLoading}
          selectedRowKeys={selectedRowKeys}
          pagination={{
            current: 1,
            pageSize: 20,
            total: filteredTests.length,
          }}
          onRefresh={refetch}
          onSelect={setSelectedRowKeys}
          onView={handleViewTest}
          onEdit={handleEditTest}
          onDelete={handleDeleteTest}
          onExecute={handleExecuteTests}
          onTableChange={handleTableChange}
        />
      </Card>

      {/* AI Test Generation Modal */}
      <Modal
        title="AI Test Generation"
        open={aiGenModalVisible}
        onCancel={() => setAiGenModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={aiGenType === 'diff' ? 'primary' : 'default'}
              icon={<CodeOutlined />}
              onClick={() => setAiGenType('diff')}
            >
              From Code Diff
            </Button>
            <Button
              type={aiGenType === 'function' ? 'primary' : 'default'}
              icon={<FunctionOutlined />}
              onClick={() => setAiGenType('function')}
            >
              From Function
            </Button>
            <Button
              type={aiGenType === 'kernel' ? 'primary' : 'default'}
              icon={<RobotOutlined />}
              onClick={() => setAiGenType('kernel')}
            >
              Kernel Test Driver
            </Button>
          </Space>
        </div>

        <KernelDriverInfo visible={aiGenType === 'kernel'} />

        {aiGenType === 'diff' ? (
          <Form
            form={aiGenForm}
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
                <Button onClick={() => setAiGenModalVisible(false)}>
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
        ) : aiGenType === 'function' ? (
          <Form
            form={aiGenForm}
            layout="vertical"
            onFinish={(values) => {
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
                  initialValue="unknown"
                >
                  <Select
                    placeholder="Select subsystem"
                    options={[
                      { label: 'Kernel Core', value: 'kernel/core' },
                      { label: 'Memory Management', value: 'kernel/mm' },
                      { label: 'File System', value: 'kernel/fs' },
                      { label: 'Networking', value: 'kernel/net' },
                      { label: 'Block Drivers', value: 'drivers/block' },
                      { label: 'Character Drivers', value: 'drivers/char' },
                      { label: 'Network Drivers', value: 'drivers/net' },
                      { label: 'x86 Architecture', value: 'arch/x86' },
                      { label: 'ARM64 Architecture', value: 'arch/arm64' },
                    ]}
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
                <Button onClick={() => setAiGenModalVisible(false)}>
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
            form={aiGenForm}
            layout="vertical"
            onFinish={(values) => {
              console.log('Kernel driver form submitted with values:', values)
              try {
                generateKernelDriver({
                  functionName: values.functionName,
                  filePath: values.filePath,
                  subsystem: values.subsystem || 'unknown',
                  testTypes: values.testTypes || ['unit', 'integration']
                })
              } catch (error) {
                console.error('Error calling generateKernelDriver:', error)
              }
            }}
          >
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: 4 }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                <ExclamationCircleOutlined style={{ color: '#fa8c16', marginRight: 8 }} />
                <strong>Kernel Test Driver Generation</strong>
              </div>
              <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                This generates a complete kernel module (.ko) that tests kernel functions directly in kernel space.
                Requires root privileges and kernel headers for compilation and execution.
              </div>
            </div>

            <Form.Item
              name="functionName"
              label="Kernel Function Name"
              rules={[{ required: true, message: 'Please enter kernel function name' }]}
            >
              <Input placeholder="e.g., kmalloc, schedule, netif_rx" />
            </Form.Item>

            <Form.Item
              name="filePath"
              label="Source File Path"
              rules={[{ required: true, message: 'Please enter source file path' }]}
            >
              <Input placeholder="e.g., mm/slab.c, kernel/sched/core.c, net/core/dev.c" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="subsystem"
                  label="Kernel Subsystem"
                  initialValue="unknown"
                >
                  <Select
                    placeholder="Select kernel subsystem"
                    options={[
                      { label: 'Kernel Core', value: 'kernel/core' },
                      { label: 'Memory Management', value: 'kernel/mm' },
                      { label: 'File System', value: 'kernel/fs' },
                      { label: 'Networking', value: 'kernel/net' },
                      { label: 'Block Drivers', value: 'drivers/block' },
                      { label: 'Character Drivers', value: 'drivers/char' },
                      { label: 'Network Drivers', value: 'drivers/net' },
                      { label: 'x86 Architecture', value: 'arch/x86' },
                      { label: 'ARM64 Architecture', value: 'arch/arm64' },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="testTypes"
                  label="Test Types"
                  initialValue={['unit', 'integration']}
                >
                  <Select
                    mode="multiple"
                    placeholder="Select test types"
                    options={[
                      { label: 'Unit Tests', value: 'unit' },
                      { label: 'Integration Tests', value: 'integration' },
                      { label: 'Performance Tests', value: 'performance' },
                      { label: 'Stress Tests', value: 'stress' },
                      { label: 'Error Injection', value: 'error_injection' },
                      { label: 'Concurrency Tests', value: 'concurrency' }
                    ]}
                  />
                </Form.Item>
              </Col>
            </Row>

            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4 }}>
              <div style={{ fontSize: '12px', color: '#52c41a', fontWeight: 500, marginBottom: 4 }}>
                Generated Kernel Driver Will Include:
              </div>
              <ul style={{ fontSize: '12px', color: '#8c8c8c', margin: 0, paddingLeft: 16 }}>
                <li>Complete kernel module source code (.c file)</li>
                <li>Makefile for compilation</li>
                <li>Installation and test execution scripts</li>
                <li>Comprehensive test functions for the target kernel function</li>
                <li>/proc interface for result collection</li>
                <li>Proper cleanup and error handling</li>
              </ul>
            </div>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setAiGenModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isGenerating}
                  icon={<RobotOutlined />}
                >
                  Generate Kernel Driver
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Test Case Detail Modal */}
      <TestCaseModal
        testCase={selectedTestCase}
        visible={modalVisible}
        mode={modalMode}
        onClose={handleCloseModal}
        onSave={handleSaveTest}
        onModeChange={setModalMode}
      />
    </div>
  )
}

export default TestCases