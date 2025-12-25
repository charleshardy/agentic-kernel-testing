import React, { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Space,
  Button,
  Table,
  Tag,
  message,
  Alert,
  Spin,
} from 'antd'
import {
  ReloadOutlined,
  PlusOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  EditOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import axios from 'axios'

const { Text } = Typography

interface EnhancedTestCase {
  id: string
  name: string
  description: string
  test_type: string
  target_subsystem: string
  code_paths: string[]
  execution_time_estimate: number
  test_script: string
  created_at: string
  updated_at: string
  metadata: {
    execution_status?: string
    generation_method?: string
    [key: string]: any
  }
}

const TestCases: React.FC = (): React.ReactElement => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [testCases, setTestCases] = useState<EnhancedTestCase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Direct API call without any library
  const fetchTestCases = async () => {
    try {
      console.log('🔄 Fetching test cases with direct axios...')
      setIsLoading(true)
      setError(null)
      
      // Get auth token first
      let token = localStorage.getItem('auth_token')
      if (!token) {
        console.log('🔑 Getting auth token...')
        const authResponse = await axios.post('http://localhost:8000/api/v1/auth/login', {
          username: 'admin',
          password: 'admin123'
        })
        token = authResponse.data.data.access_token
        localStorage.setItem('auth_token', token)
      }
      
      // Fetch test cases
      const response = await axios.get('http://localhost:8000/api/v1/tests', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        params: {
          page: 1,
          page_size: 50
        }
      })
      
      console.log('✅ Direct fetch successful:', response.data)
      
      if (response.data.success && response.data.data.tests) {
        setTestCases(response.data.data.tests)
        setError(null)
      } else {
        throw new Error('Invalid response format')
      }
    } catch (err: any) {
      console.error('❌ Direct fetch failed:', err)
      setError(err.message)
      
      // Use mock data as fallback
      const mockTestCases: EnhancedTestCase[] = [
        {
          id: 'test-001',
          name: 'Kernel Boot Test (Mock)',
          description: 'Tests kernel boot sequence and initialization',
          test_type: 'integration',
          target_subsystem: 'kernel/core',
          code_paths: ['kernel/init/main.c', 'kernel/init/init_task.c'],
          execution_time_estimate: 45,
          test_script: '#!/bin/bash\necho "Testing kernel boot sequence"',
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
          metadata: {
            execution_status: 'completed',
            generation_method: 'manual',
          }
        },
        {
          id: 'test-002',
          name: 'Memory Allocation Test (Mock)',
          description: 'Tests kmalloc and memory management functions',
          test_type: 'unit',
          target_subsystem: 'kernel/mm',
          code_paths: ['mm/slab.c', 'mm/kmalloc.c'],
          execution_time_estimate: 30,
          test_script: '#!/bin/bash\necho "Testing memory allocation"',
          created_at: '2024-01-15T11:00:00Z',
          updated_at: '2024-01-15T11:00:00Z',
          metadata: {
            execution_status: 'never_run',
            generation_method: 'ai_function',
          }
        },
      ]
      setTestCases(mockTestCases)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch on component mount
  useEffect(() => {
    fetchTestCases()
  }, [])

  console.log('TestCases No-Query Debug:', {
    testCasesCount: testCases.length,
    isLoading,
    error,
    hasTestCases: testCases.length > 0
  })

  // Calculate statistics
  const totalTests = testCases.length
  const aiGeneratedTests = testCases.filter(t => t.metadata?.generation_method !== 'manual').length
  const manualTests = totalTests - aiGeneratedTests

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green'
      case 'running': return 'blue'
      case 'failed': return 'red'
      case 'never_run': return 'default'
      default: return 'default'
    }
  }

  const getGenerationMethodColor = (method: string) => {
    switch (method) {
      case 'manual': return 'default'
      case 'ai_diff': return 'blue'
      case 'ai_function': return 'green'
      case 'ai_kernel_driver': return 'purple'
      default: return 'default'
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: EnhancedTestCase) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'test_type',
      key: 'test_type',
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      ),
    },
    {
      title: 'Subsystem',
      dataIndex: 'target_subsystem',
      key: 'target_subsystem',
      render: (subsystem: string) => (
        <Tag>{subsystem}</Tag>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: EnhancedTestCase) => {
        const status = record.metadata?.execution_status || 'never_run'
        return <Tag color={getStatusColor(status)}>{status.replace('_', ' ')}</Tag>
      },
    },
    {
      title: 'Generation',
      key: 'generation',
      render: (record: EnhancedTestCase) => {
        const method = record.metadata?.generation_method || 'manual'
        return <Tag color={getGenerationMethodColor(method)}>{method.replace('_', ' ')}</Tag>
      },
    },
    {
      title: 'Est. Time',
      dataIndex: 'execution_time_estimate',
      key: 'execution_time_estimate',
      render: (time: number) => `${time}s`,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: EnhancedTestCase) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => message.info(`Viewing test: ${record.name}`)}
          >
            View
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => message.info(`Editing test: ${record.name}`)}
          >
            Edit
          </Button>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            type="primary"
            onClick={() => message.success(`Starting execution of: ${record.name}`)}
            disabled={record.metadata?.execution_status === 'running'}
          >
            Run
          </Button>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedRowKeys: React.Key[]) => setSelectedRowKeys(selectedRowKeys as string[]),
    getCheckboxProps: (record: EnhancedTestCase) => ({
      disabled: record.metadata?.execution_status === 'running',
    }),
  }

  if (isLoading) {
    return (
      <div style={{ padding: '0 24px' }}>
        <div style={{ textAlign: 'center', padding: '100px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, fontSize: '16px' }}>Loading test cases...</div>
        </div>
      </div>
    )
  }

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
          Test Cases (No Query Version)
        </h2>
        <Space>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => message.info('AI Generation coming soon')}
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
            onClick={() => {
              fetchTestCases()
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
          message="Backend Connection Issue"
          description={`API Error: ${error}. Using mock data as fallback.`}
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Test Cases"
              value={totalTests}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="AI Generated"
              value={aiGeneratedTests}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Manual Tests"
              value={manualTests}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Test Cases Table */}
      <Card title={`Test Cases (${totalTests} ${totalTests === 1 ? 'test' : 'tests'})`}>
        <Table
          columns={columns}
          dataSource={testCases}
          rowKey="id"
          loading={false}
          rowSelection={rowSelection}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} tests`,
          }}
        />
      </Card>
    </div>
  )
}

export default TestCases